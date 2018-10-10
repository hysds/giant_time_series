# GIAnT Time Series
GIAnT time series processing of ISCEv2 interferograms

![pipeline](https://user-images.githubusercontent.com/387300/46752714-ca77ff80-cc72-11e8-99f6-502eaa954670.png)

## Release
- current release: v0.0.1

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

## Usage
### Create filtered interferogram stack
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

### Create filtered stitched interferogram stack
1. In `tosca` interface, draw bounding box on the region of interest.
1. Facet on the `S1-IFG-STITCHED` dataset.
1. Facet on the `track number`.
1. Facet on the `dataset version`.
1. Click on `On-Demand`.
1. For `Action`, select `GIAnT - Create filtered stitched IFG stack [\<version\>].
1. In the parameters section below, ensure `track` matches the track you initially faceted on.
1. For `subswath`, select the value that matches the particular `S1-IFG-STITCHED` products you want to create a time series for. This ensures that `S1-IFG-STITCHED` products that stitch only subswaths 1 and 2 are filtered out if you desire to create a time series out of `S1-IFG-STITCHED` products that stitch all 3 subswaths.
1. Populate `ref_point`.
1. Adjust other parameters accordingly.
1. Click `Process Now`.

### Create displacement time series
1. In `tosca` interface, draw bounding box on the region of interest.
1. Facet on the `filtered-ifg-stack` dataset.
1. Click on `On-Demand`.
1. For `Action`, select `GIAnT - Create Displacement Time Series [\<version\>].
1. In the parameters section below, select the inversion `method`: `sbas` or `nsbas`.
1. Click `Process Now`.
