#!/usr/bin/env python3
"""
Filtered single scene interferogram stack generator.
"""

import os
import sys
import traceback
import argparse
import json
import logging

from giant_time_series.filt import filter_ifgs
from giant_time_series.utils import get_envelope


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


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

    ## get ifg products
    products = input_json['products']

    # get region of interest
    if input_json['region_of_interest']:
        logger.info("Running Time Series with Region of Interest")
        min_lat, max_lat, min_lon, max_lon = input_json['region_of_interest']
    else:
        logger.info("Running Time Series on full data")
        min_lon, max_lon, min_lat, max_lat = ts_common.get_envelope(input_json['products'])
        logger.info("env: {} {} {} {}".format(min_lon, max_lon, min_lat, max_lat))

    # get reference point in radar coordinates and length/width for box
    ref_lat, ref_lon = input_json['ref_point']
    ref_width = int((input_json['ref_box_num_pixels'][0]-1)/2)
    ref_height = int((input_json['ref_box_num_pixels'][1]-1)/2)

    # get coverage threshold
    covth = input_json['coverage_threshold']

    # get coherence threshold
    cohth = input_json['coherence_threshold']

    # get range and azimuth pixel size
    range_pixel_size = input_json['range_pixel_size']
    azimuth_pixel_size = input_json['azimuth_pixel_size']

    # get incidence angle
    inc = input_json['inc']

    # get filt
    filt = input_json['filt']

    # network and gps deramp
    netramp = input_json['netramp']
    gpsramp = input_json['gpsramp']

    ## get subswath
    subswath = input_json['subswath']

    filt_info = filter_ifgs(products, min_lat, max_lat, min_lon, max_lon,
                            ref_lat, ref_lon, ref_width, ref_height, covth,
                            cohth, range_pixel_size, azimuth_pixel_size,
                            inc, filt, netramp, gpsramp, subswath)


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
