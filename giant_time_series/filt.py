import os
import re
import json
import logging
import pickle
import numpy as np
from osgeo import gdal
from gdalconst import GA_ReadOnly
from glob import glob
from datetime import datetime

import isce
from iscesys.Component.ProductManager import ProductManager as PM

from .utils import get_bperp, gdal_translate


gdal.UseExceptions() # make GDAL raise python exceptions


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


DT_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})')
S1_RE = re.compile(r'^S1\w$')

PLATFORMS = {
    "S1A": "Sentinel-1A",
    "S1B": "Sentinel-1B",
}

SENSORS = {
    "S1": "SAR-C Sentinel1",
    "SMAP": "SMAP Sensor",
}

def filter_ifgs(ifg_prods, min_lat, max_lat, min_lon, max_lon, ref_lat,
                ref_lon, ref_width, ref_height, covth, cohth, range_pixel_size,
                azimuth_pixel_size, inc, filt, netramp, gpsramp, subswath=None):
    """Filter input interferogram products."""

    # align images
    center_lines_utc = []
    ifg_info = {}
    ifg_coverage = {}
    for prod_num, ifg_prod in enumerate(ifg_prods):
        logger.info('#' * 80)
        logger.info('Processing: {} ({} of {}) (current stack count: {})'.format(
                    ifg_prod, prod_num+1, len(ifg_prods)+1, len(ifg_info)))
        logger.info('-' * 80)

        # get IFG metadata
        ifg_met_file = glob("{}/*.met.json".format(ifg_prod))[0]
        with open(ifg_met_file) as f:
            ifg_met = json.load(f)

        # filter out product from different subswath
        swath = ifg_met['swath'][0] if isinstance(ifg_met['swath'], list) else ifg_met['swath']
        if swath != subswath:
            logger.info('Filtered out {}: unmatched subswath {}'.format(ifg_prod,
                        ifg_met['swath']))
            continue

        # extract sensing start and stop dates
        match = DT_RE.search(ifg_met['sensingStart'])
        if not match: raise RuntimeError("Failed to extract start date.")
        start_dt = ''.join(match.groups())
        match = DT_RE.search(ifg_met['sensingStop'])
        if not match: raise RuntimeError("Failed to extract stop date.")
        stop_dt = ''.join(match.groups())
        logger.info('start_dt: {}'.format(start_dt))
        logger.info('stop_dt: {}'.format(stop_dt))

        # extract perpendicular baseline and sensor for ifg.list input file
        cb_pkl = os.path.join(ifg_prod, "PICKLE", "computeBaselines")
        with open(cb_pkl, 'rb') as f:
            catalog = pickle.load(f)
        bperp = get_bperp(catalog)
        sensor = catalog['master']['sensor']['mission']
        if sensor is None: sensor = catalog['slave']['sensor']['mission']
        if sensor is None and catalog['master']['sensor']['imagingmode'] == "TOPS":
            sensor = "S1X"
        if sensor is None:
            logger.warn("{} will be thrown out. Failed to extract sensor".format(ifg_prod))
            continue

        # set platform
        platform = PLATFORMS.get(sensor, None)

        # set no data value
        if S1_RE.search(sensor):
            sensor = "S1"
            no_data = 0.
        elif sensor == "SMAP": no_data = -9999.
        else:
            raise RuntimeError("Unknown sensor: {}".format(sensor))

        # project unwrapped phase and correlation products to common region_of_interest bbox (ROI)
        unw_vrt_in = os.path.join(ifg_prod, "merged", "filt_topophase.unw.geo.vrt")
        unw_vrt_out = os.path.join(ifg_prod, "merged", "aligned.unw.vrt")
        gdal_translate(unw_vrt_in, unw_vrt_out, min_lat, max_lat, min_lon, max_lon, no_data, 2)
        cor_vrt_in = os.path.join(ifg_prod, "merged", "phsig.cor.geo.vrt")
        cor_vrt_out = os.path.join(ifg_prod, "merged", "aligned.cor.vrt")
        gdal_translate(cor_vrt_in, cor_vrt_out, min_lat, max_lat, min_lon, max_lon, no_data, 1)

        # get width and length of aligned/projected images and
        # determine reference point limits
        ds = gdal.Open(cor_vrt_out, GA_ReadOnly)
        gt = ds.GetGeoTransform()
        width = ds.RasterXSize
        length = ds.RasterYSize
        ref_line  = int((ref_lat - gt[3]) / gt[5])
        ref_pixel = int((ref_lon - gt[0]) / gt[1])
        xlim = [0, width]
        ylim = [0, length]
        rxlim = [ref_pixel - ref_width, ref_pixel + ref_width]
        rylim = [ref_line - ref_height, ref_line + ref_height]
        #logger.info("rxlim: {}".format(rxlim))
        #logger.info("rylim: {}".format(rylim))

        # read the coherence data and build mask from coherence threshold
        band = ds.GetRasterBand(1)
        cor = band.ReadAsArray()
        cor_ref = cor[rylim[0]:rylim[1], rxlim[0]:rxlim[1]]
        logger.info("cor_ref: {} {}".format(cor_ref.shape, cor_ref))
        ds = None
        #logger.info("cor: {} {}".format(cor.shape, cor))
        mask = np.nan*np.ones(cor.shape)
        mask[cor >= cohth] = 1.0
        #logger.info("mask_ref: {} {}".format(mask_ref.shape, mask_ref))

        # read the phase data and mask out reference bbox pixels with no data
        ds = gdal.Open(unw_vrt_out, GA_ReadOnly)
        band = ds.GetRasterBand(1)
        phs = band.ReadAsArray()
        ds = None
        #logger.info("phs: {} {}".format(phs.shape, phs))
        mask[phs == no_data] = np.nan
        phs_ref = phs[rylim[0]:rylim[1], rxlim[0]:rxlim[1]]
        mask_ref = mask[rylim[0]:rylim[1], rxlim[0]:rxlim[1]]
        phs_ref = phs_ref*mask_ref
        #logger.info("phs_ref: {} {}".format(phs_ref.shape, phs_ref))
        phs_ref_mean = np.nanmean(phs_ref)
        logger.info("phs_ref mean: {}".format(phs_ref_mean))

        # filter out product with no valid phase data in reference bbox
        # or did not pass coherence threshold
        if np.isnan(phs_ref_mean):
            logger.info('Filtered out {}: no valid data in ref bbox'.format(ifg_prod))
            continue

        # filter out product with ROI coverage of valid data less than threshold
        #cov = np.sum(~np.isnan(mask))/(mask.size*1.)
        #logger.info('coverage: {}'.format(cov))
        #if cov < covth:
        #    logger.info('Filtered out {}: ROI coverage of valid data was below threshold ({} vs. {})'.format(
        #                ifg_prod, cov, covth))
        #    continue

        # filter out product with ROI latitude coverage of valid data less than threshold
        cov = np.sum(~np.isnan(mask), axis=0).max()/(mask.shape[0]*1.)
        logger.info('coverage: {}'.format(cov))
        if cov < covth:
            logger.info('Filtered out {}: ROI latitude coverage of valid data was below threshold ({} vs. {})'.format(
                        ifg_prod, cov, covth))
            continue

        # get wavelength, heading degree and center line UTC
        ifg_xml = os.path.join(ifg_prod, "fine_interferogram.xml")
        pm = PM()
        pm.configure()
        ifg_obj = pm.loadProduct(ifg_xml)
        wavelength = ifg_obj.bursts[0].radarWavelength
        sensing_mid = ifg_obj.bursts[0].sensingMid
        heading_deg = ifg_obj.bursts[0].orbit.getENUHeading(sensing_mid)
        center_line_utc = int((sensing_mid - datetime(year=sensing_mid.year,
                                                      month=sensing_mid.month,
                                                      day=sensing_mid.day)).total_seconds())
        # track sensing mid
        center_lines_utc.append(sensing_mid)

        # create date ID
        dt_id = "{}_{}".format(start_dt, stop_dt)

        # use IFG product with larger coverage
        if os.path.exists(dt_id):
            if cov <= ifg_coverage[dt_id]:
                logger.info('Filtered out {}: already exists with larger coverage ({} vs. {})'.format(
                            ifg_prod, ifg_coverage[dt_id], cov))
                continue
            else:
                logger.info('Larger coverage found for {} ({} vs. {})'.format(
                            dt_id, cov, ifg_coverage[dt_id]))
                os.unlink(dt_id)

        # create soft link for aligned products
        os.symlink(ifg_prod, dt_id)

        # set ifg list info
        ifg_info[dt_id] = {
            'product': ifg_prod,
            'start_dt': start_dt,
            'stop_dt': stop_dt,
            'bperp': bperp,
            'sensor': sensor,
            'sensor_name': SENSORS[sensor],
            'platform': platform,
            'width': width,
            'length': length,
            'xlim': xlim,
            'ylim': ylim,
            'rxlim': rxlim,
            'rylim': rylim,
            'cohth': cohth,
            'wavelength': wavelength,
            'heading_deg': heading_deg,
            'center_line_utc': center_line_utc,
            'range_pixel_size': range_pixel_size,
            'azimuth_pixel_size': azimuth_pixel_size,
            'inc': inc,
            'netramp': netramp,
            'gpsramp': gpsramp,
            'filt': filt,
            'unw_vrt_in': unw_vrt_in,
            'unw_vrt_out': unw_vrt_out,
            'cor_vrt_in': cor_vrt_in,
            'cor_vrt_out': cor_vrt_out,
        }

        # track coverage
        ifg_coverage[dt_id] = cov

        # log success status
        logger.info('Added {} to final input stack'.format(ifg_prod))
    
    return {
        'center_lines_utc': center_lines_utc,
        'ifg_info': ifg_info,
        'ifg_coverage': ifg_coverage,
    }
