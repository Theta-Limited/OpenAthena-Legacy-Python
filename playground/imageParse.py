"""
imageParse.py
-
This file is responsible for extracting drone sensor data from still-capture image(s) XMP and EXIF metadata

This can be done in near real-time if images are automatically downloaded to a computer from the UAV's paired device

Currently only photos from a DJI Mavic 2 Zoom are tested, support for more drone models can be added later with help from the OpenAthena
user community

If your UAV model is not listed here, feel free to make a pull request:
    DJI Mavic 2 Zoom

XMP:
en.wikipedia.org/wiki/Extensible_Metadata_Platform

EXIF:
en.wikipedia.org/wiki/EXIF

"""

import time
import math
# from math import sin, asin, cos, atan2, sqrt
import sys
import xml.sax
# import collections
from osgeo import gdal # en.wikipedia.org/wiki/GDAL
import mgrs # Military Grid ref converter
# broken :(
# from libxmp.utils import file_to_dict # python-xmp-toolkit, (c) ESA


from getTarget import *

"""prompt the user for options input,
       then extract data from image(s)
       and use resolveTarget() to give
       target location(s)

    @TODO not finished yet!
"""
def imageParse():
    images = []
    elevationData = None
    # If provided arguments in command line,
    #     assume the first argument is a geoTiff filename
    #     and every other argument after is a drone image filename
    if len(sys.argv) > 1:
        elevationData, (x0, dx, dxdy, y0, dydx, dy) = getGeoFileFromString(sys.argv[1])
        if len(sys.argv) > 2:
            for imageName in sys.argv[2:]:
                images.append(imageName.strip())
    else:
        # prompt the user for a filename of a GeoTIFF,
        # extract the image's elevationData and x and y params
        elevationData, (x0, dx, dxdy, y0, dydx, dy) = getGeoFileFromUser()

    nrows, ncols = elevationData.shape
    x1 = x0 + dx * ncols
    y1 = y0 + dy * nrows

    if len(sys.argv) > 1:
        print("The shape of the elevation data is: ", elevationData.shape)
        print("The raw Elevation data is: ")
        print(elevationData)

        print(f'x0: {round(x0,4)} dx: {round(dx,9)} ncols: {round(ncols,4)} x1: {round(x1,4)}')
        print(f'y0: {round(y0,4)} dy: {round(dy,9)} nrows: {round(nrows,4)} y1: {round(y1,4)}\n\n')


    ensureValidGeotiff(dxdy, dydx)

    xParams = (x0, x1, dx, ncols)
    yParams = (y0, y1, dy, nrows)

    if not images:
        imageName = ""
        print("\nType \'exit\' to finish input\n")
        while imageName.lower() != 'exit':
            print(f'Image filenames: {images}')
            imageName = str(input("Enter a drone image filename: "))
            imageName.strip()
            if imageName.lower() != 'exit':
                images.append(imageName)
        #
    #

    while images:
        thisImage = images.pop()
        #from stackoverflow.com/a/14637315
        #    if XMP in image is spread in multiple pieces, this
        #    approach will fail to extract data in all
        #    but the first XMP piece of image
        try:
            fd = open(thisImage, 'rb')
            d = str(fd.read())
            xmp_start = d.find('<x:xmpmeta')
            xmp_end = d.find('</x:xmpmeta')
            xmp_str = d[xmp_start:xmp_end+12]
            print(f'filename: {thisImage}')
            print(xmp_str)
            print('\n')

        except:
            print(f'ERROR with filename {thisImage}, skipping...', file=sys.stderr)
            continue
    #


if __name__ == "__main__":
    imageParse()
