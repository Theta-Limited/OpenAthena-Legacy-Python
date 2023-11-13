#!/usr/bin/env python3
"""
getTarget.py

This file should contain most of the math-heavy functions

This file will focus on the core math of resolving the location
    of a target in the UAS camera's direct center line-of-sight

"""
import sys
import os
import time
import matplotlib.pyplot as plt
# from osgeo import gdal # Lots of good GeoINT stuff
from geotiff import GeoTiff # alternative to gdal for parsing GeoTiff .tif files
import mgrs # Military Grid ref converter
import math
from math import sin, asin, cos, atan2, sqrt
import numpy as np
import decimal # more float precision with Decimal objects

import config # OpenAthena global variables

import parseGeoTIFF
# from WGS84_SK42_Translator import Translator as converter # rafasaurus' SK42 coord translator
# from SK42_Gauss_Kruger import Projector as Projector      # Matt's Gauss Kruger projector for SK42 (adapted from Nickname Nick)

"""get the pos of current subject of UAS camera
       data entry is done manually
       implementation in resolveTarget function
"""
def getTarget():
    print("Hello World!")
    print("I'm getTarget.py")

    if ("--version" in sys.argv or "-v" in sys.argv or "-V" in sys.argv or
        "V" in sys.argv or "version" in sys.argv):
        #
        sys.exit(config.version)
    elif ("--help" in sys.argv or "-h" in sys.argv or
        "-H" in sys.argv or "H" in sys.argv or "help" in sys.argv):
        #
        outstr = "usage: getTarget.py [Rome-30m-DEM.tif]\n\ngetTarget.py may take a GeoTIFF DEM (.tif) and manual sensor metadata as input,\nprovides a target match location as output (if possible)"
        sys.exit(outstr)
    elif 1 < len(sys.argv) and len(sys.argv) < 3:
        ext = sys.argv[1].split('.')[-1].lower()
        if ext != "tif":
            if ext in ["dt0", "dt1", "dt2", "dt3", "dt4", "dt5"]:
                print(f'FILE FORMAT ERROR: DTED format ".{ext}" not supported. Please use a GeoTIFF ".tif" file!')
            outstr = f'FATAL ERROR: got argument: {sys.argv[1]}, expected GeoTIFF ".tif" DEM!'
            sys.exit(outstr)
        else:
            filename = sys.argv[1].strip()
            elevationData, (x0, dx, dxdy, y0, dydx, dy) = parseGeoTIFF.getGeoFileFromString(filename)
    else:
        elevationData, (x0, dx, dxdy, y0, dydx, dy) = parseGeoTIFF.getGeoFileFromUser()

    print("The shape of the elevation data is: ", elevationData.shape)
    print("The raw Elevation data is: ")
    print(elevationData)

    nrows, ncols = elevationData.shape

    x1 = x0 + dx * ncols
    y1 = y0 + dy * nrows

    # # had to remove this check switching from gdal -> geotiff libraries :(
    # ensureValidGeotiff(dxdy, dydx)

    print(f'x0: {round(x0,4)} dx: {round(dx,9)} ncols: {round(ncols,4)} x1: {round(x1,4)}')
    print(f'y0: {round(y0,4)} dy: {round(dy,9)} nrows: {round(nrows,4)} y1: {round(y1,4)}\n\n')

    xParams = (x0, x1, dx, ncols)
    yParams = (y0, y1, dy, nrows)

    # note that by convention, coord pairs are usually (lat,long)
    #     i.e. (y,x)
    y = inputNumber("Please enter aircraft latitude in (+/-) decimal form: ", y1, y0)
    x = inputNumber("Please enter aircraft longitude in (+/-) decimal form: ", x0, x1)
    z = inputNumber("Please enter altitude (meters above WGS84 ellipsoid) in decimal form: ", -423, 8848)
    azimuth = inputNumber("Please enter camera azimuth (0 is north) in decimal form (degrees): ", -180, 360)
    if (azimuth < 0):

        print(f"\nWarning: using value: {azimuth + 360}\n")

    theta = inputNumber("Please enter angle of declanation (degrees down from forward) in decimal form: ", -90, 90)
    if (theta < 0):

        print(f"\nWarning: using value: {abs(theta)}\n")

    # most of the complex logic is done here
    target = resolveTarget(y, x, z, azimuth, theta, elevationData, xParams, yParams)

    if target is None:
        print(f'\n ERROR: bad calculation!\n')
    else:
        finalDist, tarY, tarX, tarZ, terrainAlt = target
        print(f'\nApproximate range to target: {int(round(finalDist))}\n')
        if tarZ is not None:
            print(f'Approximate WGS84 alt (constructed): {math.ceil(tarZ)}')
        else:
            # edge case where drone camera is pointed straight down
            tarZ = float(terrainAlt)
        print(f'Approximate alt (terrain): {round(terrainAlt)}\n')

        print('Target:')
        print(f'WGS84 (lat, lon): {round(tarY, 6)}, {round(tarX, 6)} Alt: {math.ceil(tarZ)}')
        print(f'Google Maps: https://maps.google.com/?q={round(tarY,6)},{round(tarX,6)}\n')
        # en.wikipedia.org/wiki/Military_Grid_Reference_System
        # via github.com/hobuinc/mgrs
        m = mgrs.MGRS()
        targetMGRS = m.toMGRS(tarY, tarX)
        targetMGRS10m = m.toMGRS(tarY,tarX, MGRSPrecision=4)
        targetMGRS100m = m.toMGRS(tarY, tarX, MGRSPrecision=3)
        gzdEndIndex = 2
        while(targetMGRS[gzdEndIndex].isalpha()):
            gzdEndIndex += 1
        # ANSI escape sequences \033[ for underlining: stackabuse.com/how-to-print-colored-text-in-python
        if os.name != 'nt':
            print(f'NATO MGRS: {targetMGRS[0:gzdEndIndex]}\033[4m{targetMGRS[gzdEndIndex:]}\033[0;0m Alt: \033[4m{math.ceil(tarZ)}\033[0;0m')
        else:
            print(f'NATO MGRS: {targetMGRS} Alt: {math.ceil(tarZ)}')
        print(f'MGRS 10m: {targetMGRS10m}')
        print(f'MGRS 100m: {targetMGRS100m}\n')

        # targetSK42Lat = converter.WGS84_SK42_Lat(float(tarY), float(tarX), float(tarZ))
        # targetSK42Lon = converter.WGS84_SK42_Long(float(tarY), float(tarX), float(tarZ))
        # # Note: This altitude calculation assumes the SK42 and WGS84 ellipsoid have the exact same center
        # #     This is not totally correct, but in practice is close enough to the actual value
        # #     @TODO Could be refined at a later time with better math
        # #     See: https://gis.stackexchange.com/a/88499
        # targetSK42Alt = float(tarZ) - converter.SK42_WGS84_Alt(targetSK42Lat, targetSK42Lon, 0.0)
        # targetSK42Alt = int(round(targetSK42Alt))
        # print('SK42 (истема координат 1942 года):')
        # print(f'    Geodetic (°): {round(targetSK42Lat, 6)}, {round(targetSK42Lon, 6)} Alt: {targetSK42Alt}')
        # targetSK42LatDMS, targetSK42LonDMS = decimalToDegreeMinuteSecond(targetSK42Lat, targetSK42Lon)
        # print('    Geodetic (° \' "):')
        # print('      '+targetSK42LatDMS)
        # print('      '+targetSK42LonDMS)
        # GK_zone, targetSK42_N_GK, targetSK42_E_GK = Projector.SK42_Gauss_Kruger(targetSK42Lat, targetSK42Lon)

        # outstr = strFormatSK42GK(GK_zone, targetSK42_N_GK, targetSK42_E_GK, targetSK42Alt)
        # print(outstr)

"""handle user input of data, using message for prompt
    guaranteed to return a float in range
    will reprompt until input is valid

Parameters
----------
message : string
    input prompt to display to the user
lowerBound : float
    the lower bound, inclusive, of valid input
uperBound : float
    the upper bound, inclusive of valid input
"""
def inputNumber(message, lowerBound, upperBound):
    while True:
        try:
            userInput = float(input(message))
            if userInput <= lowerBound or upperBound <= userInput:
                print(f'ERROR: input out of bounds. Lower bound is {lowerBound}, Upper bound is {upperBound}')
                print("Please Try Again")
                continue
        except ValueError:
            print("ERROR: Not an decimal number! Try again.")
            continue
        else:
            return userInput
            break

"""given sensor data, returns a tuple (distance, y, x, z, terrainAlt) distance, location, and alitude(s) of target

Parameters
----------
y : float
    latitude of aircraft
x : float
    longitude of aircraft
z : float
    elevation of aircraft, meters above WGS84 reference ellipsoid
    accuracy is greatly improved on most aircraft with
    barometric sensor, sometimes ultrasonic sensors too
azimuth : float
    azimuth represents the direction of the aircraft's camera
    measured in degrees
    starting from North @ 0°, increasing clockwise (e.g. 90° is East)
    usually an integer value, but must be between 0.0 and 360.0
theta : float
    theta represents the angle of declanation of the aircraft's camera
    measured in degrees
    starting at 0° as ideal level with the horizon, increasing as it aims downward
elevationData : 2D array
    elevationData
xParams: tuple
    tuple of 4 elements (x0, x1, dx, ncols)
    x0 is minimum lon. of dataset
    x1 is maximum lon. of dataset
    dx is the lon. change per datapoint increment +x
    ncols is the number of datapoints per row of the dataset
yParams: tuple
    tuple of 4 elements (y0, y1, dy, nrows)
    y0 is maximum lat. of dataset
    y1 is minimum lat. of dataset
    dy is the lat. change per datapoint increment +y
    nrows is the number of datapoints per column of the dataset

"""
def resolveTarget(y, x, z, azimuth, theta, elevationData, xParams, yParams):
    # jpl.nasa.gov/edu/news/2016/3/16/how-many-decimals-of-pi-do-we-really-need
    decimal.getcontext().prec = 30
    y = decimal.Decimal(y)
    x = decimal.Decimal(x)
    z = decimal.Decimal(z)

    azimuth, theta = decimal.Decimal(azimuth), decimal.Decimal(theta)
    # convert azimuth and theta from degrees to radians
    azimuth, theta = math.radians(azimuth), math.radians(theta)
    azimuth  = normalize(azimuth) # 0 <= azimuth < 2pi
    theta = abs(theta) # pitch is technically neg., but we use pos.

    # check if angle is exactly (1e-09) straight downwards,
    #     if so, skip iterative search b/c target is directly
    #     below us:
    if math.isclose((math.pi / 2), theta):
        terrainAlt = parseGeoTIFF.getAltFromLatLon(y, x, xParams, yParams, elevationData)
        if terrainAlt is None:
            return None
        finalDist = z - terrainAlt
        if finalDist < 0:
            print(f'\n ERROR: bad calculation!\n')
            return None
        print(f'\nWARNING: theta is exactly 90 deg, just using GPS lat/lon\n')
        return((finalDist, y, x, None, terrainAlt))

    # safety check: if theta > 90 degrees (pi / 2 radians)
    # then camera is facing backwards
    # to avoid undefined behavior, reverse AZIMUTH,
    # then subtract theta from 180deg to determine
    # a new appropriate THETA for the reverse direction
    #
    # during manual data entry, please avoid absolute values > 90
    if theta > (math.pi / 2):
        azimuth = normalize(azimuth + math.pi)
        theta = math.pi - theta
        print(f'\nWARNING: theta > 90 deg, if target is not behind the aircraft then something is wrong')

    # direction, convert to unit circle (just like math class)
    direction = azimuthToUnitCircleRad(azimuth)

    # from Azimuth, determine rate of x and y change
    #     per unit travel (level with horizon for now)
    deltax, deltay = math.cos(direction), math.sin(direction)
    deltax, deltay = decimal.Decimal(deltax), decimal.Decimal(deltay)

    deltaz = -1 * math.sin(theta) #neg because direction is downward
    deltaz = decimal.Decimal(deltaz)

    # determines by how much of travel per unit is actually horiz
    # pythagoran theorem, deltaz^2 + deltax^2 + deltay^2 = 1
    horizScalar = decimal.Decimal(math.cos(theta))
    deltax, deltay = horizScalar * deltax, horizScalar * deltay

    # # debug output
    # print(f'deltax is {round(deltax, 4)}')
    # print(f'deltay is {round(deltay, 4)}')
    # print(f'deltaz is {round(deltaz, 4)}')

    x0 = xParams[0]
    x1 = xParams[1]

    y0 = yParams[0]
    y1 = yParams[1]

    dx = xParams[2]


    post_spacing_meters = haversine(0, y, dx, y, z) # meters between datapoints, from degrees
    threshold = abs(post_spacing_meters) / decimal.Decimal(8.0) # meters of acceptable distance between constructed line and datapoint. somewhat arbitrary

    # meters of increment for each stepwise check (along constructed line)
    increment = decimal.Decimal(config.increment)

    # start at the aircraft's position
    curY = decimal.Decimal(y)
    curX = decimal.Decimal(x)
    curZ = decimal.Decimal(z)
    groundAlt = parseGeoTIFF.getAltFromLatLon(curY, curX, xParams, yParams, elevationData)
    if groundAlt is None:
        print(f'ERROR: resolveTarget ran out of bounds at {round(curY,4)}, {round(curX,4)}, {round(curZ,1)}m', file=sys.stderr)
        print('ERROR: Please ensure target location is within GeoTIFF dataset bounds', file=sys.stderr)
        return None
    elif (curZ < float(groundAlt)):
        print(f'ERROR: resolveTarget failed, bad sensor or elevation data.\nInitial drone altitude: {round(curZ)}m, terrain altitude: {groundAlt}m\nThis image is unusable.', file=sys.stderr)
        return None
    altDiff = curZ - groundAlt
    while altDiff > threshold:
        groundAlt = parseGeoTIFF.getAltFromLatLon(curY, curX, xParams, yParams, elevationData)
        if groundAlt is None:
            print(f'ERROR: resolveTarget ran out of bounds at {round(curY,4)}, {round(curX,4)}, {round(curZ,1)}m', file=sys.stderr)
            print('ERROR: Please ensure target location is within GeoTIFF dataset bounds', file=sys.stderr)
            return None
        altDiff = curZ - groundAlt

        avgAlt = curZ
        # deltaz should always be negative
        curZ += deltaz
        avgAlt = (avgAlt + curZ) / 2
        curY, curX = inverse_haversine((curY,curX), horizScalar*increment, azimuth, avgAlt)
        #check for Out Of Bounds after each iteration
        if curY > y0 or curY < y1 or curX < x0 or curX > x1:
            print(f'ERROR: resolveTarget ran out of bounds at {round(curY,4)}, {round(curX,4)}, {round(curZ,4)}m')
            print('ERROR: Please ensure target location is within GeoTIFF dataset bounds')
            return None
        #
        #end iteration
    #end loop
    #
    #When the loop ends, curY, curX, and curZ are closeish to the target
    #may be a bit biased ever so slightly long (beyond the target)
    #this algorithm is crude,
    #    could use refinement

    finalHorizDist = abs(haversine(x, y, curX, curY, z))
    finalVertDist = abs(z - curZ)
    # simple pythagorean theorem
    # may be inaccurate for very very large horizontal distances
    finalDist = sqrt(finalHorizDist ** 2 + finalVertDist ** 2)
    terrainAlt = parseGeoTIFF.getAltFromLatLon(curY, curX, xParams, yParams, elevationData)

    return((finalDist, curY, curX, curZ, terrainAlt))

"""convert from azimuth notation (0 is up [+y], inc. clockwise) to
math notation(0 is right [+x], inc. counter-clockwise)
all units in Radians

Parameters
----------
azimuth : float
    an angle in radians, should be between 0 and 2pi
"""
def azimuthToUnitCircleRad(azimuth):
    # reverse direction of increment
    direction = (-1 * azimuth)
    # rotate 90deg, move origin from +y to +x
    direction += (0.5 * math.pi)
    direction = normalize(direction)
    return direction

"""if a given angle is not between 0 and 2pi,
return the same angle in a number that is between 0 and 2pi (rad)

Parameters
----------
direction : float
    an angle in radians, in the set of all real numbers

"""
def normalize(direction):
    # the following two routines are mutually-exclusive
    while (direction < 0):
        direction += 2 * math.pi
    while (direction >= (2 * math.pi)):
        direction -= 2 * math.pi

    return direction

"""Radius At Lat Lon
Given a latitude and longitude, return the radius of the WGS84 Ellipsoid at that reference

return type is a Decimal object, measured in meters

Parameters
----------
lat : (float)
    geodetic latitude. assumed to be WGS84
lon : (float)
    geodetic longitude. assumed to be WGS84

"""
def radius_at_lat_lon(lat, lon):
    A = decimal.Decimal(6378137.0) # equatorial radius of WGS ellipsoid, in meters
    B = decimal.Decimal(6356752.3) # polar radius of WGS ellipsoid, in meters
    r = (A * A * decimal.Decimal(cos(lat))) ** 2 + (B * B * decimal.Decimal(sin(lat))) ** 2 # numerator
    r /= (A * decimal.Decimal(cos(lat))) ** 2 + (B * decimal.Decimal(sin(lat))) ** 2 # denominator
    r = r ** (decimal.Decimal(0.5))  # square root
    return r


"""Inverse Haversine formula
via github.com/jdeniau
given a point, distance, and heading, return the new point (lat lon)
a certain distance along the great circle

for short distances, this is close to the straight line distance


Parameters
----------
point : (float, float)
    a latitude, longitude pair of the start location
distance : float
    the distance (in meters) to 'travel' along the great circle
azimuth : float
    the heading of the direction of travel
    NOTE: here we use azimuth (start @ 0, inc. clockwise),
           NOT like unit circle!
alt : float
    the approximate altitude, added to the radius of the great circle
"""
def inverse_haversine(point, distance, azimuth, alt):
    if distance < 0.0:
        # reverse direction and make distance a positive number
        return inverse_haversine(point, -distance, normalize(azimuth + math.pi), alt)
    lat, lon = point
    lat, lon = map(math.radians, (lat, lon))


    d = decimal.Decimal(distance)
    # r = 6371000 + alt # average radius of earth + altitude # Old, bad
    # calculate WGS84 radius at lat/lon
    #     based on: gis.stackexchange.com/a/20250
    #     R(f)^2 = ( (a^2 cos(f))^2 + (b^2 sin(f))^2 ) / ( (a cos(f))^2 + (b sin(f))^2 )

    r = radius_at_lat_lon(lat, lon)
    r = r + alt # actual height above or below idealized ellipsoid

    brng = azimuth

    return_lat = asin(sin(lat) * cos(d / r) + cos(lat) * sin(d / r) * cos(brng))
    return_lon = lon + atan2(sin(brng) * sin(d / r) * cos(lat), cos(d / r) - sin(lat) * sin(return_lat))

    return_lat, return_lon = map(math.degrees, (return_lat, return_lon))
    return return_lat, return_lon

"""Haversine formula
via stackoverflow.com/a/4913653
determines the great circle distance (meters) between
two lattitude longitude pairs

for short distances, this is close to the straight-line distance

Parameters
----------
lon1 : float
    longitude of the first point
lat1 : float
    latitude of the first point
lon2 : float
    longitude of the second point
lat2 : float
    latitude of the second point
alt : float
    the approximate altitude, added to the radius of the great circle

"""
def haversine(lon1, lat1, lon2, lat2, alt):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    c = decimal.Decimal(c)
    # en.wikipedia.org/wiki/Earth_radius
    r = radius_at_lat_lon((lat1+lat2)/2, (lon1+lon2)/2)
    r = r + decimal.Decimal(alt) # actual height above or below idealized ellipsoid
    return c * r

"""takes two lat/lon pairs (a start A and a destination B) and finds the heading of the shortest direction of travel from A to B
Note: this function will work with Geodetic coords of any ellipsoid (as long as both pairs' ellipsoid are the same)

adapted from https://stackoverflow.com/a/64747209

Parameters
----------
lon1 : float
    longitude of the first point
lat1 : float
    latitude of the first point
lon2 : float
    longitude of the second point
lat2 : float
    latitude of the second point

"""
def haversine_bearing(lon1, lat1, lon2, lat2):
    dLon = (lon2 - lon1)
    x = math.cos(math.radians(lat2)) * math.sin(math.radians(dLon))
    y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(dLon))
    brng = math.atan2(x,y) # arguments intentionally swapped out of order
    brng = normalize(brng)
    brng = math.degrees(brng)

    return brng


"""takes a decimal +/- Lat and Lon and returns a tuple of two strings containing Degrees Minutes Seconds each

Note: this funtion will work with Geodetic coords of any ellipsoid

Fn from Glen Bambrick: glenbambrick.com/2015/06/24/dd-to-dms/

Parameters
----------
Lat: float
    A latitude, positive or negative, in degrees
Lon: float
    A longitude, positive or negative, in degrees
"""
def decimalToDegreeMinuteSecond(Lat, Lon):

    split_degx = math.modf(Lon)

    # the whole number [index 1] is the degrees
    degrees_x = int(split_degx[1])

    # multiply the decimal part by 60: 0.3478 * 60 = 20.868
    # split the whole number part of the total as the minutes: 20
    # abs() absoulte value - no negative
    minutes_x = abs(int(math.modf(split_degx[0] * 60)[1]))

    # multiply the decimal part of the split above by 60 to get the seconds
    # 0.868 x 60 = 52.08, round excess decimal places to 2 places
    # abs() absoulte value - no negative
    seconds_x = abs(round(math.modf(split_degx[0] * 60)[0] * 60,2))

    # repeat for Lat
    split_degy = math.modf(Lat)
    degrees_y = int(split_degy[1])
    minutes_y = abs(int(math.modf(split_degy[0] * 60)[1]))
    seconds_y = abs(round(math.modf(split_degy[0] * 60)[0] * 60,2))

    # account for E/W & N/S
    if degrees_x < 0:
        EorW = "W"
    else:
        EorW = "E"

    if degrees_y < 0:
        NorS = "S"
    else:
        NorS = "N"

    # abs() remove negative from degrees, was only needed for if-else above
    latDMS = str(abs(degrees_y)) + "° " + str(minutes_y) + "' " + str(seconds_y) + "\" " + NorS
    lonDMS = str(abs(degrees_x)) + "° " + str(minutes_x) + "' " + str(seconds_x) + "\" " + EorW

    return (latDMS, lonDMS)

"""takes a Gauss Krüger zone, northing, and easting; returns a str formatted for printout

Parameters
----------
GK_zone: int
    an integer number between 1 and 60 (inclusive) representing the 6° longitudinal 'slice'
northing: int
    an integer number < 10,000,000 in meters offset (longitude) from the GK zone origin
    defines a vertical northing line
easting : int
    an integer number < 10,000,000 in meters offset (latitude) from the GK zone origin
    defines a horizontal easting line
SK42Alt : int
    an integer number representing the 𝚫altitude (in meters) from the surface of the 1942 Krassowsky ellipsoid
"""
def strFormatSK42GK(GK_zone, northing, easting, SK42Alt) :
    northing, easting = round(northing), round(easting)
    SK42_N_GK_10k_Grid  = (northing % 100000)
    SK42_E_GK_10k_Grid = (easting % 100000)

    if os.name != 'nt':
        ANSI_start_underline = "\033[4m"
        ANSI_end_underline = "\033[0;0m"
    else:
        ANSI_start_underline = "" # ANSI codes don't work on Windows, do nothing
        ANSI_end_underline = ""

    outstr = ""
    outstr += "    "
    outstr += "Gauss-Krüger (meters): ZONE: "
    outstr += f'{GK_zone} '

    outstr += "X: "
    NgreaterThan10k = int((northing - SK42_N_GK_10k_Grid)/100000)
    outstr += f'{NgreaterThan10k} '

    outstr += ANSI_start_underline
    SK42_N_GK_10k_str = str(SK42_N_GK_10k_Grid).zfill(5)
    outstr += f'{SK42_N_GK_10k_str}'
    outstr += ANSI_end_underline + " "

    outstr += "Y: "
    EgreaterThan10k = int((easting - SK42_E_GK_10k_Grid)/100000)
    outstr += f'{EgreaterThan10k} '

    outstr += ANSI_start_underline
    SK42_E_GK_10k_str = str(SK42_E_GK_10k_Grid).zfill(5)
    outstr += f'{SK42_E_GK_10k_str}'
    outstr += ANSI_end_underline + " "

    outstr += "Alt: "
    outstr += ANSI_start_underline
    outstr += f'{SK42Alt}'
    outstr += ANSI_end_underline
    return outstr

if __name__ == "__main__":
    getTarget()
