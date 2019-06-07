#!/usr/bin/env python3
"""
Create displacement time series.
"""

import os
import sys
import re
import traceback
import argparse
import json
import logging
import shutil
import pickle
import multiprocessing
from subprocess import check_call

from giant_time_series.utils import (dataset_exists, prep_tds, call_noerr,
get_bounding_polygon, write_dataset_json)

import celeryconfig as conf


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


BASE_PATH = os.path.dirname(__file__)


ID_RE = re.compile(r'filtered-gunw-merged-stack_(.+)-v.+$')
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

    # get ifg products
    products = input_json['products']
    ifg_stack_dir = products[0]

    # get method
    method = input_json['method']
    if method not in ('sbas', 'nsbas'):
        raise RuntimeError("Invalid method:{}".format(method))
    logger.info("Using method {}-inversion to generate displacement time series.".format(method))

    # set method-dependent vars

    # get time series prod
    match = ID_RE.search(ifg_stack_dir)
    if not match:
        raise RuntimeError("Failed to recognize filtered ifg stack: {}".format(ifg_stack_dir))
    id = "displacement-time-series-{}_{}-{}".format(method, match.group(1), DATASET_VERSION)
    logger.info("Product ID for version {}: {}".format(DATASET_VERSION, id))

    # get endpoint configurations
    es_url = conf.GRQ_ES_URL
    es_index = conf.DATASET_ALIAS
    logger.info("GRQ url: {}".format(es_url))
    logger.info("GRQ index: {}".format(es_index))

    # check if dataset already exists
    if dataset_exists(es_url, es_index, id):
        logger.info("{} was previously generated and exists in GRQ database.".format(id))
        sys.exit(0)

    # change dir to ifg stack
    os.chdir(ifg_stack_dir)
    os.makedirs('Stack', 0o755)

    # unzip and move
    check_call("pigz -d {}".format('RAW-STACK.h5.gz'), shell=True)
    shutil.move('RAW-STACK.h5', 'Stack')
    check_call("pigz -d {}".format('PROC-STACK.h5.gz'), shell=True)
    shutil.move('PROC-STACK.h5', 'Stack')

    # run inversion method
    if method == "sbas":
        # SBASInvert.py to create time-series using short baseline approach (least-squares)
        logger.info("Running SBASInvert.py")
        check_call("{}/SBASInvertWrapper.py".format(BASE_PATH), shell=True)
        ts_file = "LS-PARAMS.h5"
    elif method == "nsbas":
        # NSBASInvert.py to create time-series using partially coherent pixels approach
        logger.info("Running NSBASInvert.py")
        cpu_count = multiprocessing.cpu_count()
        check_call("{}/NSBASInvertWrapper.py -nproc {}".format(BASE_PATH, cpu_count), shell=True)
        ts_file = "NSBAS-PARAMS.h5"

    # read in ifg stack metadata
    with open("{}.met.json".format(ifg_stack_dir)) as f:
        met = json.load(f)

    # unpickle filter info and extract geocode info
    with open('filt_info.pkl', 'rb') as f:
        filt_info = pickle.load(f)
    lats = filt_info['lats']
    lons = filt_info['lons']

    # add lat, lon, and time datasets to time series product for THREDDS
    prep_tds(lats, lons, os.path.join("Stack", ts_file))

    # move back up
    os.chdir(cwd)

    # create product directory
    prod_dir = id
    os.makedirs(prod_dir, 0o755)

    # move time series
    orig_ts_file = os.path.join(ifg_stack_dir, "Stack", ts_file)
    prod_ts_file = os.path.join(prod_dir, ts_file)
    shutil.move(orig_ts_file, prod_ts_file)

    # go to prod dir
    os.chdir(prod_dir)

    # create browse image
    call_noerr('gdal_translate HDF5:"{}"://rawts browse.tif -of GTiff -outsize 50% 50% -b 2'.format(ts_file))
    call_noerr("convert browse.tif browse.png")
    call_noerr("convert -resize 250x250 browse.png browse_small.png")
    call_noerr("rm -f browse.tif")

    # move back up
    os.chdir(cwd)

    # create met json
    met['dataset_type'] = "time-series"
    met['product_type'] = "time-series"
    met['tags'] = method
    met_file = os.path.join(prod_dir, "{}.met.json".format(id))
    with open(met_file, 'w') as f:
        json.dump(met, f, indent=2)

    # compute bounding polygon
    try: geojson_bbox = get_bounding_polygon(prod_ts_file)
    except Exception as e:
        logger.warn("Using less precise bbox due to error. {0}.{1}".format(type(e), e))
        geojson_bbox = [[i[1], i[0]] for i in met['bbox']]

    # create dataset json
    write_dataset_json(prod_dir, id, geojson_bbox, met['timesteps'][0], 
                       met['timesteps'][-1], DATASET_VERSION)

    # compress
    check_call("pigz -f -9 {}".format(prod_ts_file), shell=True)

    # clean out filtered ifg stack
    try: shutil.rmtree(ifg_stack_dir)
    except: pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json_file", help="input JSON file")
    args = parser.parse_args()
    work_dir = os.getcwd()
    try: main(args.input_json_file)
    except Exception as e:
        with open(os.path.join(work_dir, '_alt_error.txt'), 'w') as f:
            f.write("%s\n" % str(e))
        with open(os.path.join(work_dir, '_alt_traceback.txt'), 'w') as f:
            f.write("%s\n" % traceback.format_exc())
        raise
    sys.exit(0)
