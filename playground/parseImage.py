"""
parseImage.py
-
This file is responsible for extracting drone sensor data from still-capture image(s) XMP and EXIF metadata

This can be done in near real-time if images are automatically downloaded to a computer from the UAV's paired device

Currently only photos from DJI-make drones are supported
, and the only tested model(s) are below
Support for more drone models can be added later with help from the OpenAthena
user community

If your UAV make or model is not listed here, feel free to make a pull request:
Makes:
    DJI
    Models:
        DJI Mavic 2 Zoom

XMP:
en.wikipedia.org/wiki/Extensible_Metadata_Platform

EXIF:
en.wikipedia.org/wiki/EXIF

"""

import sys
import time
import math
from math import sin, asin, cos, atan2, sqrt
import decimal # more float precision with Decimal objects

from osgeo import gdal # en.wikipedia.org/wiki/GDAL
import mgrs # Military Grid ref converter

# unused :(
# import xml.sax
# from libxmp.utils import file_to_dict # python-xmp-toolkit, (c) ESA

from geotiff_play import getAltFromLatLon, binarySearchNearest
from getTarget import *

"""prompt the user for options input,
       then extract data from image(s)
       and use resolveTarget() to give
       target location(s)

    @TODO not finished yet!
"""
def parseImage():
    images = []
    elevationData = None
    headless = False
    if len(sys.argv) > 2:
        headless = True
    # If provided arguments in command line,
    #     the first argument must be a geoTiff filename
    #     and every other argument after is a drone image filename
    if len(sys.argv) > 1:
        if sys.argv[1].split('.')[-1].lower() != "tif":
            outstr = f'FATAL ERROR: got first argument: {sys.argv[1]}, expected GeoTIFF DEM!'
            sys.exit(outstr)

        elevationData, (x0, dx, dxdy, y0, dydx, dy) = getGeoFileFromString(sys.argv[1])

        if headless:
            for imageName in sys.argv[2:]:
                images.append(imageName.strip())
    else:
        # prompt the user for a filename of a GeoTIFF,
        # extract the image's elevationData and x and y params
        elevationData, (x0, dx, dxdy, y0, dydx, dy) = getGeoFileFromUser()

    nrows, ncols = elevationData.shape
    x1 = x0 + dx * ncols
    y1 = y0 + dy * nrows

    if not headless:
        print("The shape of the elevation data is: ", elevationData.shape)
        print("The raw Elevation data is: ")
        print(elevationData)

        print(f'x0: {round(x0,4)} dx: {round(dx,9)} ncols: {round(ncols,4)} x1: {round(x1,4)}')
        print(f'y0: {round(y0,4)} dy: {round(dy,9)} nrows: {round(nrows,4)} y1: {round(y1,4)}\n\n')


    ensureValidGeotiff(dxdy, dydx)

    xParams = (x0, x1, dx, ncols)
    yParams = (y0, y1, dy, nrows)

    if not images: # not run in headless mode
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
        thisImage = thisImage.strip()

        sensData = None, None, None, None, None
        target = None
        try:
            #from stackoverflow.com/a/14637315
            #    if XMP in image is spread in multiple pieces, this
            #    approach will fail to extract data in all
            #    but the first XMP piece of image
            fd = open(thisImage, 'rb') #read as binary
            d = str(fd.read()) # ...but convert to string
            xmp_start = d.find('<x:xmpmeta')
            xmp_end = d.find('</x:xmpmeta')
            xmp_str = d[xmp_start:xmp_end+12]
            fd.close()

            # agisoft.com/forum/index.php?topic=5008.0
            # Alexey Pasumansky
            makeTag = "tiff:Make="
            if xmp_start != xmp_end:
                tagStart = xmp_str.find(makeTag)
                make = xmp_str[tagStart + len(makeTag) : tagStart + len(makeTag) + 10]
                make = str(make.split('\"',3)[1])
                # print(f'make: {make}')
                if make == "DJI":
                    sensData = handleDJI(xmp_str)
                    if sensData is not None:
                        x, y, z, azimuth, theta = sensData
                        target = resolveTarget(x, y, z, azimuth, theta, elevationData, xParams, yParams)
                    else:
                        print(f'ERROR with {thisImage}, couldn\'t find sensor data', file=sys.stderr)
                        print(f'skipping {thisImage}', file=sys.stderr)
                        continue
                elif False: # your drone make here
                    # <----YOUR HANDLER FUNCTION HERE---->
                    pass
                elif False: # your drone make here
                    # <----YOUR HANDLER FUNCTION HERE---->
                    pass
                else:
                    print(f'ERROR with {thisImage}, Mfr. \'{make}\' not compatible with this program', file=sys.stderr)
                    print(f'skipping {thisImage}', file=sys.stderr)
                    continue
            else:
                print(f'ERROR with {thisImage}, xmp data not found!', file=sys.stderr)
                print(f'skipping {thisImage}', file=sys.stderr)
                continue

        except:
            print(f'ERROR with filename {thisImage}, skipping...', file=sys.stderr)
            continue
        #
        if target is not None:
            finalDist, tarY, tarX, tarZ, terrainAlt = target
            if headless:
                # undefined behavior if there is a '.' in full filepath
                #     other than the file extension
                filename = thisImage.split('.')[0] + ".ATHENA"
                file_object = open(filename, 'w')
                file_object.write(str(tarY) + "\n")
                file_object.write(str(tarX) + "\n")
                file_object.write(str(terrainAlt) + "\n")
                file_object.write(str(finalDist))
                file_object.write("\n# format: lat, lon, alt, dist")

                file_object.close()
            else:
                print(f'\n\nfilename: {thisImage}')
                print(f'\nApproximate range to target: {round(finalDist , 2)}\n')

                if tarZ is not None:
                    print(f'Approximate alt (constructed): {round(tarZ , 2)}')
                print(f'Approximate alt (terrain): {terrainAlt}\n')


                print(f'Target (lat, lon): {round(tarY, 7)}, {round(tarX, 7)}')
                print(f'Google Maps: https://maps.google.com/?q={round(tarY,6)},{round(tarX,6)}\n')
                # en.wikipedia.org/wiki/Military_Grid_Reference_System
                # via github.com/hobuinc/mgrs
                m = mgrs.MGRS()
                targetMGRS = m.toMGRS(tarY, tarX)
                print(f'NATO MGRS: {targetMGRS}\n')

    #

"""takes a xmp metadata from a DJI drone,
returns tuple (y, x, z, azimuth, theta)

Parameters
----------
xmp_str : string
    a string containing the contents of XMP metadata of a DJI drone image
    may contain errant newline sequences, preventing parsing as true XML
"""
def handleDJI( xmp_str ):
    elements = ["drone-dji:AbsoluteAltitude=",
                            "drone-dji:GpsLatitude=",
                            "drone-dji:GpsLongitude=",
                            # Gimbal values are absolute
                            "drone-dji:GimbalRollDegree=", #should always be 0
                            "drone-dji:GimbalYawDegree=",
                            "drone-dji:GimbalPitchDegree=",
                            # ...not relative to these values
                            # https://developer.dji.com/iframe/mobile-sdk-doc/android/reference/dji/sdk/Gimbal/DJIGimbal.html
                            # may be different for other mfns.
                            "drone-dji:FlightRollDegree=",
                            "drone-dji:FlightYawDegree=",
                            "drone-dji:FlightPitchDegree="]
    dict = { }
    if len(xmp_str.strip()) > 0:
        for element in elements:
            value = xmp_str[xmp_str.find(element) + len(element) : xmp_str.find(element) + len(element) + 10]
            value = float(value.split('\"',3)[1])
            dict[element] = value
    else:
        return None

    y = dict["drone-dji:GpsLatitude="]
    x = dict["drone-dji:GpsLongitude="]
    z = dict["drone-dji:AbsoluteAltitude="]

    azimuth = dict["drone-dji:GimbalYawDegree="]

    theta = abs(dict["drone-dji:GimbalPitchDegree="])

    if y is None or x is None or z is None or azimuth is None or theta is None:
        return None
    else:
        return (y, x, z, azimuth, theta)

if __name__ == "__main__":
    parseImage()
