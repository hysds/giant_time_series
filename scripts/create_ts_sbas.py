#!/usr/bin/env python3
"""
Create SBAS-inversion displacement time series.
"""

import os
import sys
import re
import traceback
import argparse
import json
import logging
import hashlib
import shutil
import pickle
import h5py
from subprocess import check_call
from datetime import datetime
from glob import glob

from giant_time_series.filt import filter_ifgs
from giant_time_series.utils import (get_envelope, dataset_exists, call_noerr,
write_dataset_json)

import celeryconfig as conf


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


BASE_PATH = os.path.dirname(__file__)


ID_TMPL = "filtered-ifg-stack_{sensor}-TN{track}-{startdt}Z-{enddt}Z-{hash}-{version}"
DATASET_VERSION = "v0.1"


def main(input_json_file):
    """Main stack generator."""

    # save cwd (working directory)
    cwd = os.getcwd()

    # get time-series input
    input_json_file = os.path.abspath(input_json_file)
    if not os.path.exists(input_json_file):
        raise RuntimeError("Failed to find %s." % input_json_file)
    with open(input_json_file) as f:
        input_json = json.load(f)
    logger.info("input_json: {}".format(json.dumps(input_json, indent=2)))

    # get project
    project = input_json['project']

    # get ifg products
    products = input_json['products']

    # change dir to ifg stack
    ifg_stack_dir = products[0]
    os.chdir(ifg_stack_dir)
    os.makedirs('Stack', 0o755)

    # unzip and move
    check_call("pigz -d {}".format('RAW-STACK.h5.gz'), shell=True)
    shutil.move('RAW-STACK.h5', 'Stack')
    check_call("pigz -d {}".format('PROC-STACK.h5.gz'), shell=True)
    shutil.move('PROC-STACK.h5', 'Stack')

    # SBASInvert.py to create time-series using short baseline approach (least-squares)
    logger.info("Running step 5: SBASInvert.py")
    check_call("{}/SBASInvertWrapper.py".format(BASE_PATH), shell=True)

    # add lat, lon, and time datasets to LS-PARAMS.h5 for THREDDS
    sbas = os.path.join("Stack", "LS-PARAMS.h5")
    check_call("{}/prep_tds.py {} {}".format(BASE_PATH, cor_vrt, sbas), shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json_file", help="input JSON file")
    args = parser.parse_args()
    try: main(args.input_json_file)
    except Exception as e:
        with open('_alt_error.txt', 'w') as f:
            f.write("%s\n" % str(e))
        with open('_alt_traceback.txt', 'w') as f:
            f.write("%s\n" % traceback.format_exc())
        raise
    sys.exit(0)
