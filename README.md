# GIAnT Time Series
GIAnT time series processing of ISCEv2 interferograms

![pipeline](https://user-images.githubusercontent.com/387300/46752714-ca77ff80-cc72-11e8-99f6-502eaa954670.png)

## HySDS Cluster Installation
1. Log into your `mozart` instance.
1. Download HySDS package from the [latest release](https://github.com/hysds/giant_time_series/releases/latest) (replace \<version\>):
   ```
   wget https://github.com/hysds/giant_time_series/releases/download/<version>/container-hysds_giant_time_series.<version>.sdspkg.tar
   ```
1. Import HySDS package:
   ```
   sds pkg import container-hysds_giant_time_series.<version>.sdspkg.tar
   ```

## Filtered Interferogram Stack
### Description
The filtered interferogram (`IFG`) stack dataset (`filtered-ifg-stack`) is primarily the HDF5 `RAW-STACK.h5` and 
`PROC-STACK.h5` outputs of GIAnT's `PrepIgramStack.py` and `ProcessStack.py`, respectively. Prior to
running these PGEs, a first-order filtering step is performed to filter out IFGs whose track and subswaths
don't match those specified. Additionally, IFGs are filtered whose reference bounding box contains no data
that pass the coherence threshold or which do not cover the region of interest.

### Outputs
- `RAW-STACK.h5.gz` - gzip-compressed HDF5 file of the filtered stack of IFGs
- `PROC-STACK.h5.gz` - gzip-compressed HDF5 file of the filtered stack of IFGs with atmospheric and orbit corrections applied
- `browse.png` - visual browse of temporal connectivity
- `gaps.txt` - record of any temporal gaps detected in the stack
- `create_filtered_ifg_stack.log` - verbose log which can be used to determine what IFGs were filtered and why
- `filt_info.pkl` - pickle file containing IFG and filter information
- `data.xml`, `sbas.xml` - other inputs needed by downstream displacement time series PGEs

### Usage
1. In `tosca` interface, draw bounding box on the region of interest.
1. Facet on the `S1-IFG` dataset.
1. Facet on the `track number`.
1. Facet on the `subswath`.
1. Facet on the `dataset version`.
1. Click on `On-Demand`.
1. For `Action`, select `GIAnT - Create filtered single scene IFG stack [\<version\>].
1. In the parameters section below, ensure `track` and `subswath` matches the track and subswath you initially faceted on. This ensures that `S1-IFG` products for other tracks and subswaths are filtered out in case the user failed to facet down to them.
1. Populate `ref_point`.
1. Adjust other parameters accordingly.
1. Click `Process Now`.

## Displacement Time Series
### Description
The displacement time series dataset (`displacement-time-series`) is primarily the 
HDF5 `LS-PARAMS.h5` (for SBAS-inversion) and `NSBAS-PARAMS.h5` (for NSBAS-inversion)
outputs of GIAnT's `SBASInvertWrapper.py` and `NSBASInvertWrapper.py`, respectively.

### Outputs
- `LS-PARAMS.h5.gz` or `NSBAS-PARAMS.h5.gz`- gzip-compressed HDF5 file of the displacement time series produced via the SBAS or NSBAS inversion method
- `browse.png` - visual browse of initial time series step

### Create displacement time series
1. In `tosca` interface, draw bounding box on the region of interest.
1. Facet on the `filtered-ifg-stack` dataset.
1. Click on `On-Demand`.
1. For `Action`, select `GIAnT - Create Displacement Time Series [\<version\>].
1. In the parameters section below, select the inversion `method`: `sbas` or `nsbas`.
1. Click `Process Now`.

### Visualization
- Panoply
  1. Open HDF5 in `Panoply`: File->Open.
  1. Double click on `rawts` (raw time series) or `recons` (reconstructed time series) variable.
  1. Select `Create a georeferenced Longitude-Latitude plot`. Click on `Create`.
  1. Zoom in to the region of interest. On MacOSX, hold down the `command` key while you click and drag a bounding box over the region of interest.
  1. Click on the `Scale` tab and set `Scale Range Min.` to `-100` and `Max.` to `100`. You can play around with the values.
  1. Click on the `Arrays` tab and cycle through the time slices by clicking the `up` arrow button.
  ![panoply](https://user-images.githubusercontent.com/387300/46819763-666c3e80-cd39-11e8-8b0b-74325014b4a3.gif)
