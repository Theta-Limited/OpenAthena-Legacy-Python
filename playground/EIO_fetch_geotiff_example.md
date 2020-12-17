# Fetch geotiff file from internet
From python elevation API's [read the docs](http://elevation.bopen.eu/en/stable/quickstart.html#command-line-usage)

## Command line usage

Identify the geographic bounds of the area of interest and fetch the DEM with the eio command. For example to clip the SRTM 30m DEM of Rome, around 41.9N 12.5E, to the Rome-30m-DEM.tif file:

    $ eio clip -o Rome-30m-DEM.tif --bounds 12.35 41.8 12.65 42

The `--bounds` option accepts latitude and longitude coordinates (more precisely in geodetic coordinates in the WGS84 refernce system EPSG:4326 for those who care) given as `left bottom right top` similarly to the `rio` command form `rasterio`.

To clean up stale temporary files and fix the cache in the event of a server error use:

    $ eio clean
