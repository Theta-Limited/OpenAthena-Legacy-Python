"""
mortar_mode.py

This file is for an alternate targeting mode where target match locations are provided in relative terms (bearing, distance, elevation change) for use by short-distance indirect fire teams (e.g. mortars)

The mortar location may be specified either using WGS84 Geodetic Lat/Lon or NATO MGRS (with altitude optional).

If desired, Magnetic Declination can be optionally specified so that the target bearing will be output in magnetic heading (instead of true heading), e.g. for use with a handheld analog compass. This is not necessary for most digital compasses (e.g. a smartphone)

Only intended for short range distances, otherwise will be inaccurate (curvature of the earth, great circle distance, etc.)

"""
import sys
import time
import math
from math import sin, asin, cos, atan2, sqrt
import decimal # more float precision with Decimal objects

from osgeo import gdal # en.wikipedia.org/wiki/GDAL

# https://pypi.org/project/mgrs/
import mgrs # Military Grid ref converter

from PIL import Image
from PIL import ExifTags

from parseGeoTIFF import getAltFromLatLon, binarySearchNearest
from getTarget import *
from parseImage import *

def mortar_mode():
    images = []

    elevationData = None
    x0, dx, dxdy, y0, dydx, dy = [None] * 6
    x1 = y1 = None
    nrows = ncols = None
    xParams = yParams = [None] * 4
    geofilename = None

    m = mgrs.MGRS()

    lat = None
    lon = None
    my_mgrs = None
    alt = None
    mag = 0.0

    if len(sys.argv) <= 1:
        errstr = f'FATAL ERROR: no location specified, please use --lat YY.YYYY --lon XX.XXXX (WGS84)'
        sys.exit(errstr)

    for i in range(len(sys.argv)):
        segment = sys.argv[i]
        if segment.lower() == "--lat":
            if i + 1 >= len(sys.argv):
                sys.exit("Fatal ERROR: expected value after '--lat'")
            else:
                lat = sys.argv[i + 1]
            try:
                lat = float(lat)
            except ValueError:
                errstr = f"FATAL ERROR: expected Latitude, got: {lat}"
                sys.exit(errstr)
        elif segment.lower() == "--lon":
            if i + 1 >= len(sys.argv):
                sys.exit("Fatal ERROR: expected value after '--lon'")
            else:
                lon = sys.argv[i + 1]
            try:
                lon = float(lon)
            except ValueError:
                errstr = f"FATAL ERROR: expected Longitude, got: {lon}"
                sys.exit(errstr)
        elif segment.lower() == "--mgrs":
            if i + 1 >= len(sys.argv):
                sys.exit("Fatal ERROR: expected value after '--mgrs'")
            else:
                my_mgrs = sys.argv[i + 1]
            try:
                lat, lon = m.toLatLon(my_mgrs)
            except:
                errstr = f"FATAL ERROR: expected NATO MGRS, got: {my_mgrs}"
                sys.exit(errstr)
        elif segment.lower() == "--mag":
            if i + 1 >= len(sys.argv):
                sys.exit("Fatal ERROR: expected value after '--mag'")
            else:
                mag = sys.argv[i + 1]
            try:
                mag = float(mag)
            except ValueError:
                errstr = f"FATAL ERROR: expected compass mag declination, got: {mag}"
                sys.exit(errstr)
        elif segment.lower() == "--alt":
            if i + 1 >= len(sys.argv):
                sys.exit("Fatal ERROR: expected value after '--alt'")
            else:
                alt = sys.argv[i + 1]
            try:
                alt = float(alt)
            except ValueError:
                errstr = f"FATAL ERROR: expected WGS84 altitude, got: {alt}"
                sys.exit(errstr)
        elif segment.split('.')[-1].lower() == "tif":
            geofilename = segment
            elevationData, (x0, dx, dxdy, y0, dydx, dy) = getGeoFileFromString(geofilename)
            nrows, ncols = elevationData.shape
            x1 = x0 + dx * ncols
            y1 = y0 + dy * nrows
            ensureValidGeotiff(dxdy, dydx)
            xParams = (x0, x1, dx, ncols)
            yParams = (y0, y1, dy, nrows)

    #end for loop

    mag = -1 * mag # instead of magnetic -> true heading, we go true -> magnetic (so we must invert)
    if mag != 0.0:
        warnStr = '\033[1;31;m' #ANSI escape sequence, bold and red
        warnStr += f"WARNING: adjusting target headings by {mag}° for use with analog magnetic compass\n"
        warnStr += "    please ensure this offset direction is correct and your compass decl. is set to 0°"
        warnStr +="\033[0;0m" #ANSI escape sequence, reset terminal to normal colors
        warnStr +="\n"
        print(warnStr)

    if lat is None or lon is None:
        errstr = f'FATAL ERROR: no location specified, please use --lat YY.YYYY --lon XX.XXXX (WGS84)'
        sys.exit(errstr)

    if elevationData is None:
        errstr = "FATAL ERROR: no valid GeoTIFF (.tif) Digital Elevation Model provided!"
        sys.exit(errstr)

    if (lat > y0 or lat < y1) or (lon < x0 or lon > x1):
        errstr = f"FATAL ERROR: {round(lat,6)}, {round(lon,6)} is outside of GeoTIFF coverage area\n"
        errstr += f"    Please ensure you are using the correct file\n"
        errstr += f"    Your Location: {round(lat,4)}, {round(lon,4)}\n"
        errstr += f"    {geofilename}:\n"
        errstr += f"        {round(y1,6)} < lat < {round(y0,6)}\n"
        errstr += f"        {round(x0,6)} < lon < {round(x1,6)}\n"
        sys.exit(errstr)

    if alt is None:
        alt = getAltFromLatLon(lat, lon, xParams, yParams, elevationData)

        warnStr = '\033[1;31;m' #ANSI escape sequence, bold and red
        warnStr += "WARNING: you did not input your current altitude\n"
        warnStr += f"    using value {alt}m according to nearest GeoTIFF DEM datapoint\n"
        warnStr += "    your GPS reading may be more accurate than this value"
        warnStr +="\033[0;0m" #ANSI escape sequence, reset terminal to normal colors
        warnStr +="\n"
        print(warnStr)

    # @TODO process targets here

if __name__ == "__main__":
    mortar_mode()
