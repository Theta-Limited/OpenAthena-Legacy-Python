"""
parseImage.py

This file is responsible for extracting drone sensor data from still-capture image(s) XMP and EXIF metadata

This can be done in near real-time if images are automatically downloaded to a computer from the UAV's paired device

Currently only photos from the following makes have been tested

Support for more drone makes can be added later with help from the OpenAthena
user community.

Please email photo examples, with intact metadata and a locate-able subject in the direct center of image to matthew (at) krupczak (dot) org

If your UAV make or model is not listed here, feel free to help out and make a pull request:
Makes:
    DJI
    Skydio
    Autel Robotics (unverified accuracy)

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

from PIL import Image
from PIL import ExifTags

import difflib

#     write and mangle
#     eli.thegreenplace.net/2012/03/15/processing-xml-in-python-with-elementtree
# try:
#     import xml.etree.cElementTree as ET # C implementation, much faster
# except ImportError:
#     import xml.etree.ElementTree as ET



# unused :(
# from libxmp.utils import file_to_dict # python-xmp-toolkit, (c) ESA

from parseGeoTIFF import getAltFromLatLon, binarySearchNearest
from getTarget import *

"""prompt the user for options input,
       then extract data from image(s)
       and use resolveTarget() to give
       target location(s)

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
        print("\nType \'done\' to finish input\n")
        while imageName.lower() != 'done':
            print(f'Image filenames: {images}')
            imageName = str(input("Enter a drone image filename: "))
            imageName.strip()
            if imageName.lower() != 'done':
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

            exifData = {}
            img = Image.open(thisImage)
            exifDataRaw = img._getexif()
            for tag, value in exifDataRaw.items():
                decodedTag = ExifTags.TAGS.get(tag, tag)
                exifData[decodedTag] = value

            # print(exifData)

            # agisoft.com/forum/index.php?topic=5008.0
            # Alexey Pasumansky
            # makeTag = "tiff:Make="
            if xmp_start != xmp_end:
                # tagStart = xmp_str.find(makeTag)
                # xmpMake = xmp_str[tagStart + len(makeTag) : tagStart + len(makeTag) + 10]
                # xmpMake = str(xmpMake.split('\"',3)[1])
                # print(f'xmpMake: {xmpMake}')
                make = exifData["Make"].upper()
                make = make.strip()
                if make[-1] == "\0":
                    # fix nul terminated string bug
                    # joelonsoftware.com/2003/10/08/the-absolute-minimum-every-software-developer-absolutely-positively-must-know-about-unicode-and-character-sets-no-excuses
                    make = make.rstrip("\0")

                if make == "DJI":
                    sensData = handleDJI(xmp_str)
                    if sensData is not None:
                        y, x, z, azimuth, theta = sensData
                        target = resolveTarget(y, x, z, azimuth, theta, elevationData, xParams, yParams)
                    else:
                        print(f'ERROR with {thisImage}, couldn\'t find sensor data', file=sys.stderr)
                        print(f'skipping {thisImage}', file=sys.stderr)
                        continue
                elif make == "SKYDIO":
                    sensData = handleSKYDIO(xmp_str)
                    if sensData is not None:
                        y, x, z, azimuth, theta = sensData
                        target = resolveTarget(y, x, z, azimuth, theta, elevationData, xParams, yParams)
                    else:
                        print(f'ERROR with {thisImage}, couldn\'t find sensor data', file=sys.stderr)
                        print(f'skipping {thisImage}', file=sys.stderr)
                        continue
                elif make == "AUTEL ROBOTICS":
                    sensData = handleAUTEL(xmp_str, exifData)
                    if sensData is not None:
                        y, x, z, azimuth, theta = sensData
                        target = resolveTarget(y, x, z, azimuth, theta, elevationData, xParams, yParams)
                    else:
                        print(f'ERROR with {thisImage}, couldn\'t find sensor data', file=sys.stderr)
                        print(f'skipping {thisImage}', file=sys.stderr)
                        continue
                elif make == "PARROT":
                    print("Parrot UAS's are not supported in this version")
                    print(f'skipping {thisImage}', file=sys.stderr)
                    continue
                elif False: # your drone make here
                    # <----YOUR HANDLER FUNCTION HERE---->
                    pass
                elif False: # your drone make here
                    # <----YOUR HANDLER FUNCTION HERE---->
                    pass
                else:
                    print(f'ERROR with {thisImage}, make {make} not compatible with this program!', file=sys.stderr)
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
                filename = ''.join(thisImage.split('.')[0:-1]) + ".ATHENA"
                dateTime = exifData["DateTime"]

                file_object = open(filename, 'w')

                m = mgrs.MGRS()
                targetMGRS = m.toMGRS(tarY, tarX)
                targetMGRS10m = m.toMGRS(tarY,tarX, MGRSPrecision=4)
                targetMGRS100m = m.toMGRS(tarY, tarX, MGRSPrecision=3)

                file_object.write(str(tarY) + "\n")
                file_object.write(str(tarX) + "\n")
                file_object.write(str(terrainAlt) + "\n")
                file_object.write(str(finalDist))
                if dateTime is not None:
                    file_object.write(str(dateTime) + "\n")
                file_object.write(targetMGRS + "\n")
                file_object.write(targetMGRS10m + "\n")
                file_object.write(targetMGRS100m + "\n")
                file_object.write("# format: lat, lon, alt, dist, MGRS 1m, MGRS 10m, MGRS 100m")

                file_object.close()
            else:
                print(f'\n\nfilename: {thisImage}')
                dateTime = exifData["DateTime"]
                if dateTime is not None:
                    print(f'Image Date/Time: {dateTime}')

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
                targetMGRS10m = m.toMGRS(tarY,tarX, MGRSPrecision=4)
                targetMGRS100m = m.toMGRS(tarY, tarX, MGRSPrecision=3)
                print(f'NATO MGRS: {targetMGRS}')
                print(f'MGRS 10m: {targetMGRS10m}')
                print(f'MGRS 100m: {targetMGRS100m}\n')
    #

"""takes a xmp metadata string from a DJI drone,
returns tuple (y, x, z, azimuth, theta)

Parameters
----------
xmp_str : String
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
                            # could be different for other mfns.?
                            "drone-dji:FlightRollDegree=",
                            "drone-dji:FlightYawDegree=",
                            "drone-dji:FlightPitchDegree="]

    dict = xmp_parse( xmp_str, elements)
    if dict is None:
        return None

    # print( xmp_str )

    y = dict["drone-dji:GpsLatitude="]
    x = dict["drone-dji:GpsLongitude="]
    z = dict["drone-dji:AbsoluteAltitude="]

    azimuth = dict["drone-dji:GimbalYawDegree="]

    theta = abs(dict["drone-dji:GimbalPitchDegree="])

    if y is None or x is None or z is None or azimuth is None or theta is None:
        return None
    else:
        return (y, x, z, azimuth, theta)

"""takes a xmp metadata string from a Skydio drone,
returns tuple (y, x, z, azimuth, theta)

Parameters
----------
xmp_str: String
    a string containing the contents of XMP metadata of a Skydio drone image
"""
def handleSKYDIO( xmp_str ):
    # Skydio has multiple frame of reference tags with same children
    #     (i.e. "Yaw", "Pitch", etc.)
    #     will need to parse differently :(
    #
    # More info:
    #     https://support.skydio.com/hc/en-us/articles/4417425974683-Skydio-camera-and-metadata-overview

    element = "drone-skydio:CameraOrientationNED"
    startIndex = xmp_str.find(element)
    if startIndex == -1:
        # element = "drone-skydio:CameraOrientationFLU"
        # startIndex = xmp_str.find(element)
        # if startIndex == -1:
        #     return None
        return None

    values = xmp_str[startIndex + len(element) : startIndex + len(element) + 100]
    theta = values.split('\"')[3]
    azimuth = values.split('\"')[5]

    try:
        theta = float(theta)
        azimuth = float(azimuth)
    except ValueError:
        return None

    theta = abs(theta)

    elements = ["drone-skydio:Latitude=",
                "drone-skydio:Longitude=",
                "drone-skydio:AbsoluteAltitude="]
    gpsDict = xmp_parse(xmp_str, elements)
    if gpsDict is None:
        return None

    y = gpsDict["drone-skydio:Latitude="]
    x = gpsDict["drone-skydio:Longitude="]
    z = gpsDict["drone-skydio:AbsoluteAltitude="]

    if y is None or x is None or z is None or azimuth is None or theta is None:
        return None
    else:
        return (y, x, z, azimuth, theta)

"""takes a xmp metadata string and exifData dictionary from an Autel drone,
returns a tuple (y, x, z, azimuth, theta)

Parameters
----------
xmp_str: String
    a string containing the contents of XMP metadata of a Autel drone image
exifData: Dict
    a dictionary containing the EXIF metadata of a Autel drone image,
    expressed as key:value pairs
"""
def handleAUTEL(xmp_str, exifData):
    # print(exifData)
    GPSInfo = exifData['GPSInfo']

    # e.g. N or S
    latDir = GPSInfo[1].strip().upper()
    latDeg = GPSInfo[2][0]
    latMin = GPSInfo[2][1]
    latSec = GPSInfo[2][2]

    y = latDeg
    y += (latMin / 60.0)
    y += (latSec / 3600.0)
    if latDir == "S":
        y = y * -1.0
    y = float(y)

    # e.g. E or W
    lonDir = GPSInfo[3].strip().upper()
    lonDeg = GPSInfo[4][0]
    lonMin = GPSInfo[4][1]
    lonSec = GPSInfo[4][2]

    x = lonDeg
    x += (lonMin / 60.0)
    x += (lonSec / 3600.0)
    if lonDir == "W":
        x = x * -1.0
    x = float(x)

    z = GPSInfo[6]
    z = float(z)

    elements = ["Camera:Pitch=",
                "Camera:Yaw=",
                "Camera:Roll="]

    dirDict = xmp_parse(xmp_str, elements)
    azimuth = dirDict["Camera:Yaw="]
    azimuth = float(azimuth)

    theta = dirDict["Camera:Pitch="]
    # AUTEL Camera pitch 0 is down, 90 is forward towards horizon
    # so, we use its complement instead
    theta = 90.0 - theta
    theta = float(theta)
    if theta < 0:
        return None

    if y is None or x is None or z is None or azimuth is None or theta is None:
        return None
    else:
        return (y, x, z, azimuth, theta)


"""takes a xmp metadata string and exifData dictionary from a Parrot drone,
returns a tuple (y, x, z, azimuth, theta)

Parameters
----------
xmp_str: String
    a string containing the contents of XMP metadata of a Parrot drone image
exifData: Dict
    a dictionary containing the EXIF metadata of a Parrot drone image,
    expressed as key:value pairs
"""
def handlePARROT(xmp_str, exifData):
    # https://developer.parrot.com/docs/pdraw/photo-metadata.html
    # https://support.pix4d.com/hc/en-us/articles/202558969-Yaw-Pitch-Roll-and-Omega-Phi-Kappa-angles#How%20to%20convert%20Yaw,%20Pitch,%20Roll%20to%20Omega,%20Phi,%20Kappa
    # https://stackoverflow.com/questions/49790453/enu-ned-frame-conversion-using-quaternions

    # Parrot drone (for some un-godly reason) only gives 3D direction in
    #    East North Up (ENU), not North East Down (NED)
    #
    # very lame!
    #
    # Will have to convert to NED for use with OpenAthena
    # This is really hard (math-wise), will finish later...
    return None

"""takes a xmp metadata string and a list of keys
return a dictionary of key, value pairs
       ...or None if xmp_str is empty

Parameters
----------
xmp_str: String
    a string containing the contents of XMP metadata
elements: String[]
    a list of strings, each string is a key for which to search XMP data
    for its corresponding value
"""
def xmp_parse ( xmp_str, elements ):
    dict = {}
    if len(xmp_str.strip()) > 0:
        for element in elements:
            value = xmp_str[xmp_str.find(element) + len(element) : xmp_str.find(element) + len(element) + 10]
            value = float(value.split('\"',3)[1])
            dict[element] = value
    else:
        return None

    return dict



if __name__ == "__main__":
    parseImage()
