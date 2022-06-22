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
    Autel Robotics (CAUTION: sometimes less accurate)
    Parrot
        Anafi

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
# https://pypi.org/project/mgrs/
import mgrs # Military Grid ref converter
# https://pypi.org/project/pyproj/
# import pyproj # Python interface to PROJ (cartographic projections and coordinate transformations library)
from pyproj import Transformer

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
# from WGS84_SK42_Translator import Translator as converter # rafasaurus' SK42 coord translator

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
        # if True:
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
                model = exifData["Model"].upper()
                model = model.strip()
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
                    # will whitelist more models as they are tested
                    if model != "ANAFI":
                        # for instance, the parrot disco fixed-wing doesn't
                        #     have a camera gimbal
                        print(f'ERROR with {thisImage}, Parrot {model} is not supported', file=sys.stderr)
                        print(f'skipping {thisImage}', file=sys.stderr)
                        continue
                    else:
                        sensData = handlePARROT(xmp_str, exifData)
                        if sensData is not None:
                            y, x, z, azimuth, theta = sensData
                            target = resolveTarget(y, x, z, azimuth, theta, elevationData, xParams, yParams)
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
                    print(f'ERROR with {thisImage}, make {make} not compatible with this program!', file=sys.stderr)
                    print(f'skipping {thisImage}', file=sys.stderr)
                    continue

            else:
                print(f'ERROR with {thisImage}, xmp data not found!', file=sys.stderr)
                print(f'skipping {thisImage}', file=sys.stderr)
                continue
        # else:
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
                file_object.write(str(finalDist) + "\n")
                if dateTime is not None:
                    file_object.write(str(dateTime) + "\n")
                else:
                    file_object.write("\n")
                file_object.write(targetMGRS + "\n")
                file_object.write(targetMGRS10m + "\n")
                file_object.write(targetMGRS100m + "\n")
                file_object.write("# format: lat, lon, alt, dist, time, MGRS 1m, MGRS 10m, MGRS 100m\n")
                if make == "AUTEL ROBOTICS":
                    file_object.write(f'# CAUTION: in-accuracies have been observed with Autel drones. This result is from a "{model}" drone')

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

                # normal decimal like GPS co-ords, "WGS84"
                wgs84 = "epsg:4326"
                # SK-42, A.K.A Pulkovo 1942 A.K.A Gauss Kruger
                # alternative, ellipsoidal projection used by
                # many old soviet maps
                #
                # coordinates expressed as Y, X, units in meters
                #
                # ID:
                #     CM 159 E
                #     epsg:4284
                #     https://spatialreference.org/ref/epsg/4284/
                sk42 = "epsg:28468"
                transformer = Transformer.from_crs(wgs84, sk42)
                targetSK42Lon, targetSK42Lat = transformer.transform(float(tarX), float(tarY))
                targetSK42Lon = str(round(targetSK42Lon,0)).split('.')[0]
                targetSK42Lat = str(round(targetSK42Lat,0)).split('.')[0]
                print(f'SK42 (TESTING ONLY): {targetSK42Lat} Y, {targetSK42Lon} X')

                # targetSK42Lat = converter.WGS84_SK42_Lat(float(tarX), float(tarY), float(tarZ))
                # targetSK42Lon = converter.WGS84_SK42_Long(float(tarX), float(tarY), float(tarZ))
                # # reverse lat/lon since it is mistaken in converter code?
                # # I'm not happy with this :(
                # targetSK42Lat, targetSK42Lon = targetSK42Lon, targetSK42Lat
                # print(f'SK42 (TESTING ONLY): {round(targetSK42Lat, 6)}, {round(targetSK42Lon, 6)}')

    #

"""takes a xmp metadata string from a drone image of type "DJI Meta Data",
returns tuple (y, x, z, azimuth, theta)

Parameters
----------
xmp_str : String
    a string containing the contents of XMP metadata of "DJI Meta Data" format
    may contain errant newline sequences, preventing parsing as true XML
elements : String[]
    optionally passed in to override XMP tags to use for search
    e.x.: with Autel drones, replace "drone-dji:GpsLatitude=" with "drone:GpsLatitude", etc.
"""
def handleDJI( xmp_str, elements=None):
    # default, unless overridden
    if elements == None:
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
    # print([e for e in elements if "GpsLongitude" in e][0])

    y = float(dict[[e for e in elements if "GpsLatitude" in e][0]])

    # Autel drones have a typo, "GpsLongtitude" instead of "GpsLongitude"
    #     we must be able to handle either case, with or w/o typo
    #     in case it is fixed later :(
    typoAgnostic = [e for e in elements if "GpsLong" in e]
    for e in typoAgnostic:
        if dict[e] == None:
            typoAgnostic.remove(e)
    if len(typoAgnostic) == 1:
        typoAgnostic = typoAgnostic[0]
    else:
        return None
    x = float(dict[typoAgnostic])

    z = float(dict[[e for e in elements if "AbsoluteAltitude" in e][0]])

    azimuth = float(dict[[e for e in elements if "GimbalYawDegree" in e][0]])

    theta = abs(float(dict[[e for e in elements if "GimbalPitchDegree" in e][0]]))

    if y is None or x is None or z is None or azimuth is None or theta is None:
        return None
    else:
        # # debug printout
        # print(f'y: "{y}" x: "{x}" z: "{z}" azimuth: "{azimuth}" theta: "{theta}"')
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
        return None
    substr = xmp_str[startIndex + len(element) :]

    isNewFormat = False
    canary = substr.split('\"')[1]
    if canary == "Resource":
        isNewFormat = True

    CONED = substr

    # # debug printout
    # print(xmp_str)
    # print(substr)

    if isNewFormat:
        # replace "<" open tag character with ">" close tag character
        #     this way we can use the same character for splitting up the string
        CONED = CONED.replace('<','>')

        theta = CONED.find('Pitch')
        if theta == -1:
            return None
        substr = CONED[theta :]
        theta = substr.split('>')[1]

        azimuth = CONED.find('Yaw')
        if azimuth == -1:
            return None
        substr = CONED[azimuth :]
        azimuth = substr.split('>')[1]

    else:
        theta = CONED.split('\"')[3]
        azimuth = CONED.split('\"')[5]


    try:
        theta = float(theta)
        azimuth = float(azimuth)
    except ValueError:
        errstr = f"ERROR: parsing isNewFormat: {isNewFormat} Skydio image failed"
        errstr += f"with values theta: {theta} azimuth: {azimuth}"
        print(errstr, file=sys.stderr)
        return None

    theta = abs(theta)

    if isNewFormat:
        xmp_str = xmp_str.replace('<','>')

        y = xmp_str.find('drone-skydio:Latitude')
        if y == -1:
            return None
        substr = xmp_str[y :]
        y = substr.split('>')[1]

        x = xmp_str.find('drone-skydio:Longitude')
        if x == -1:
            return None
        substr = xmp_str[x :]
        x = substr.split('>')[1]

        z = xmp_str.find('drone-skydio:AbsoluteAltitude')
        if z == -1:
            return None
        substr = xmp_str[z :]
        z = substr.split('>')[1]
    else:
        elements = ["drone-skydio:Latitude=",
                    "drone-skydio:Longitude=",
                    "drone-skydio:AbsoluteAltitude="]
        gpsDict = xmp_parse(xmp_str, elements)
        if gpsDict is None:
            return None
        y = gpsDict["drone-skydio:Latitude="]
        x = gpsDict["drone-skydio:Longitude="]
        z = gpsDict["drone-skydio:AbsoluteAltitude="]
    #

    try:
        y = float(y)
        x = float(x)
        z = float(z)
    except ValueError:
        errstr = f"ERROR: parsing isNewFormat: {isNewFormat} Skydio image failed"
        errstr += f" with values y: {y} x: {x} z: {z}"
        print(errstr, file=sys.stderr)
        return None
    #

    if y is None or x is None or z is None or azimuth is None or theta is None:
        errstr = f"ERROR: parsing isNewFormat: {isNewFormat} Skydio image failed!"
        errstr += f": \"{y}\", \"{x}\", \"{z}\", \"{azimuth}\", \"{theta}\""
        print(errstr, file=sys.stderr)
        return None
    else:
        # # debug printout
        # print(f'y: "{y}" x: "{x}" z: "{z}" azimuth: "{azimuth}" theta: "{theta}"')
        return (y, x, z, azimuth, theta)

"""takes a xmp metadata string and exifData dictionary from an Autel drone,
returns a tuple (y, x, z, azimuth, theta)

WARNING: in-accuracies have been observed from Autel's reported altitude and azimuth
    result quality is sub-optimal, proceed with caution

Parameters
----------
xmp_str: String
    a string containing the contents of XMP metadata of a Autel drone image
exifData: Dict
    a dictionary containing the EXIF metadata of a Autel drone image,
    expressed as key:value pairs
"""
def handleAUTEL(xmp_str, exifData):
    warnStr = '\033[1;31;m' #ANSI escape sequence, underlined and red
    warnStr += 'USER WARNING: in-accuracies have been observed from Autels\'\n'
    warnStr += '    reported altitude, azimuth, and theta. This may result in bad target res.\n\n'
    warnStr += '    PROCEED WITH CAUTION '
    warnStr +="\033[0;0m" #ANSI escape sequence, reset terminal to normal colors
    print(warnStr)


    # # Debug printout
    # print(xmp_str)
    # print("\n")
    # print(exifData)

    metadataAbout = xmp_str.find("rdf:about=") + len("rdf:about=")
    metadataAbout = xmp_str[metadataAbout : metadataAbout + 15]
    metadataAbout = metadataAbout.split(' ')[0]
    metadataAbout = metadataAbout.upper()

    # Newer firmware versions use simmilar XMP tags as DJI
    if metadataAbout == "DJI":
        # autel uses drone:tag instead of drone-dji:tag
        # everything else format is the same as DJI
        # v lame
        elements = ["drone:AbsoluteAltitude=",
                    "drone:GpsLatitude=",
                    # typo in Autel robotics metada
                    #     'Longtitude' instead of 'Longitude'
                    #     OMFG
                    "drone:GpsLongtitude=",
                    # include without typo
                    #     in case the typo is fixed in later firmware ver
                    #     :'(
                    "drone:GpsLongitude=",
                    "drone:GimbalRollDegree=",
                    "drone:GimbalYawDegree=",
                    "drone:GimbalPitchDegree="]
        return handleDJI(xmp_str, elements)
    else:
        # Older firmware versions use proprietary Autel Robotics XMP tags
        #    If the metadata rdf:about is not "Autel Robotics Meta Data"
        #    then this software can't parse metadata, so throw an error
        if not "AUTEL" in metadataAbout:
            errstr = f"ERROR: unexpected metadata format while parsing Autel image: '{metadataAbout}'"
            print(errstr, file=sys.stderr)
            return None

    coords = exifGetYXZ(exifData)
    if coords is None:
        return None
    y, x, z = coords

    elements = ["Camera:Pitch=",
                "Camera:Yaw=",
                "Camera:Roll="]

    canary = xmp_str.find("Camera:Pitch=")
    # print(f'canary: {canary}')

    if canary != -1:
        dirDict = xmp_parse(xmp_str, elements)
        # I've noticed this can be inaccurate sometimes
        #     poor calibration of magnetometer for compass heading?
        azimuth = dirDict["Camera:Yaw="]

        theta = dirDict["Camera:Pitch="]
        try:
            theta = float(theta)
            # AUTEL (old firmware) Camera pitch 0 is down, 90 is forward towards horizon
            # so, we use its complement instead
            theta = 90.0 - theta
            azimuth = float(azimuth)
        except ValueError:
            errstr = f"ERROR: parsing Autel image "
            errstr += f"with values theta: {theta} azimuth: {azimuth}"
            print(errstr, file=sys.stderr)
            return None

        if theta < 0:
            return None
    else:
        # replace "<" open tag character with ">" close tag character
        #     this way we can use the same character for splitting up the string
        searchspace = xmp_str.replace('<','>')

        theta = searchspace.find("Camera:Pitch")
        if theta == -1:
            return None
        substr = searchspace[theta :]
        theta = substr.split('>', 3)[1]

        azimuth = searchspace.find("Camera:Yaw")
        if azimuth == -1:
            return None
        substr = searchspace[azimuth :]
        azimuth = substr.split('>', 3)[1]
        try:
            theta = abs(float(theta))
            # AUTEL (old firmware) Camera pitch 0 is down, 90 is forward towards horizon
            # so, we use its complement instead
            theta = 90 - theta
            azimuth = float(azimuth)
        except ValueError:
            errstr = f"ERROR: parsing Autel image "
            errstr += f"with values theta: {theta} azimuth: {azimuth}"
            print(errstr, file=sys.stderr)
            return None
        if theta < 0:
            return None

    if y is None or x is None or z is None or azimuth is None or theta is None:
        return None
    else:
        # # debug printout
        # print(f'y: "{y}" x: "{x}" z: "{z}" azimuth: "{azimuth}" theta: "{theta}"')
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
    #
    # There are many different Parrot drones out there, each with different specs
    #     for instance, the Parrot Disco fixed-wing doesn't have a camera gimbal.
    #     Each and every drone model will have to be tested for compatibility


    """ Get theta and azimuth from XMP tags
    """
    # replace "<" open tag character with ">" close tag character
    #     this way we can use the same character for splitting up the string
    searchspace = xmp_str.replace('<','>')

    theta = searchspace.find('drone-parrot:CameraPitchDegree')
    if theta == -1:
        return None
    substr = searchspace[theta :]
    theta = substr.split('>')[1]

    azimuth = searchspace.find('drone-parrot:CameraYawDegree')
    if azimuth == -1:
        return None
    substr = searchspace[azimuth :]
    azimuth = substr.split('>')[1]

    """ Get Lat, Lon, and Alt from EXIF GPS tags
    """
    coords = exifGetYXZ(exifData)
    if coords is None:
        return None
    y, x, z = coords

    try:
        theta = float(theta)
        azimuth = float(azimuth)
    except ValueError:
        errstr = f"ERROR: parsing Parrot image "
        errstr += f"with values theta: {theta} azimuth: {azimuth}"
        print(errstr, file=sys.stderr)
        return None

    theta = abs(theta)

    if y is None or x is None or z is None or azimuth is None or theta is None:
        return None
    else:
        # # debug printout
        # print(f'y: "{y}" x: "{x}" z: "{z}" azimuth: "{azimuth}" theta: "{theta}"')
        return (y, x, z, azimuth, theta)

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
            if xmp_str.find(element) == -1:
                dict[element] = None
            else:
                value = xmp_str[xmp_str.find(element) + len(element) : xmp_str.find(element) + len(element) + 10]
                value = value.split('\"',3)[1]
                dict[element] = value
    else:
        return None

    return dict

"""takes a python dictionary generated from EXIF data
return a tuple (y, x, z) of latitude, longitude, and altitude
in decimal form

Parameters
----------
exifData: dict {key : value}
    a Python dictionary object containing key : value pairs of EXIF tags and their
    corresponding values

"""
def exifGetYXZ(exifData):
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

    z = GPSInfo[6]

    try:
        y = float(y)
        x = float(x)
        z = float(z)
    except ValueError:
        print("ERROR: failed to extract GPS data from EXIF values", file=sys.stderr)
        return None

    return (y, x, z)


if __name__ == "__main__":
    parseImage()
