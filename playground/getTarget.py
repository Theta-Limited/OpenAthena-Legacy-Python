"""
getTarget.py

This file should contain most of the math-heavy functions

This file will focus instead on the core math of resolving the location
    of a target in the UAS camera's direct center line-of-sight

"""

import time
import matplotlib.pyplot as plt
from osgeo import gdal # Lots of good GeoINT stuff
import mgrs # Military Grid ref converter
import math
from math import sin, asin, cos, atan2, sqrt
import decimal # more float precision with Decimal objects
import geotiff_play
import sys

"""get the pos of current subject of UAS camera
       data entry is done manually
       implementation in resolveTarget function
"""
def getTarget():
    print("Hello World!")
    print("I'm getTarget.py")
    elevationData, (x0, dx, dxdy, y0, dydx, dy) = getGeoFileFromUser()

    print("The shape of the elevation data is: ", elevationData.shape)
    print("The raw Elevation data is: ")
    print(elevationData)

    nrows, ncols = elevationData.shape

    x1 = x0 + dx * ncols
    y1 = y0 + dy * nrows

    ensureValidGeotiff(dxdy, dydx)

    print(f'x0: {round(x0,4)} dx: {round(dx,9)} ncols: {round(ncols,4)} x1: {round(x1,4)}')
    print(f'y0: {round(y0,4)} dy: {round(dy,9)} nrows: {round(nrows,4)} y1: {round(y1,4)}\n\n')

    xParams = (x0, x1, dx, ncols)
    yParams = (y0, y1, dy, nrows)

    # note that by convention, coord pairs are usually (lat,long)
    #     i.e. (y,x)
    y = inputNumber("Please enter aircraft latitude in (+/-) decimal form: ", y1, y0)
    x = inputNumber("Please enter aircraft longitude in (+/-) decimal form: ", x0, x1)
    z = inputNumber("Please enter altitude (meters from sea-level) in decimal form: ", -423, 8848)
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

"""get and open a geoFile named by a string
    e.g. from a command line argument

    if the name is invalid, exit with error

"""
def getGeoFileFromString(geofilename):
    geofilename.strip()
    geoFile = gdal.Open(geofilename)
    if geoFile is None:
        outstr = f'FATAL ERROR: can\'t find file with name \'{geofilename}\''
        sys.exit(outstr)

    band = geoFile.GetRasterBand(1)
    elevationData = band.ReadAsArray()
    return elevationData, geoFile.GetGeoTransform()

"""prompt the user for the entry of a GeoTIFF filename
    if filename is invalid, will re-prompt
    until a valid file name is entered

    returns 2D array elevationData and x and y parameters
"""
def getGeoFileFromUser():
    print("Which GeoTiff file would you like to read?")
    geoFile = None
    while geoFile is None:
        geofilename = str(input("Enter the GeoTIFF filename: "))
        geofilename.strip()
        if geofilename.isdecimal() or geofilename.isnumeric():
            print(f'ERROR: filename {geofilename} does not contain at least 1 non-digit character')
            print('Please try again')
            continue
        else:
            try:
                geoFile = gdal.Open(geofilename)
            except:
                print(f'ERROR: can\'t find file with name \'{geofilename}\'')
                geoFile = None
                print('Please try again')
                continue
    #

    band = geoFile.GetRasterBand(1)
    elevationData = band.ReadAsArray()
    return elevationData, geoFile.GetGeoTransform()

"""check if a geoTiff is invalid, i.e. rotated or skewed

Parameters
----------
dxdy : float
    might be the rate of x change per unit y
    if this is not 0, we have a problem!
dydx : float
    might be the rate of y change per unit x
    if this is not 0, we have a problem!
"""
def ensureValidGeotiff(dxdy, dydx):
    # I'm making the assumption that the image isn't rotated/skewed/etc.
    # This is not the correct method in general, but let's ignore that for now
    # If dxdy or dydx aren't 0, then this will be incorrect
    # we cannot deal with rotated or skewed images in current version
    if dxdy != 0 or dydx != 0:
        outstr = "FATAL ERROR: geoTIFF is rotated or skewed!"
        outstr += "\ncannot proceed with file: "
        outstr += geofilename
        print(outstr, file=sys.stderr)
        sys.exit(outstr)

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
    altitude of aircraft, meters from sea level
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
        terrainAlt = geotiff_play.getAltFromLatLon(y, x, xParams, yParams, elevationData)
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
    #meters of acceptable distance between constructed line and datapoint
    threshold = abs(dx) / 4.0

    #meters of increment for each stepwise check (along constructed line)
    increment = decimal.Decimal(1.0)

    # start at the aircraft's position

    curY = decimal.Decimal(y)
    curX = decimal.Decimal(x)
    curZ = decimal.Decimal(z)
    altDiff = curZ - geotiff_play.getAltFromLatLon(curY, curX, xParams, yParams, elevationData)
    while altDiff > threshold:
        groundAlt = geotiff_play.getAltFromLatLon(curY, curX, xParams, yParams, elevationData)
        altDiff = curZ - groundAlt

        avgAlt = curZ
        # deltaz should always be negative
        curZ += deltaz
        avgAlt = (avgAlt + curZ) / 2
        curY, curX = inverse_haversine((curY,curX), horizScalar*increment, azimuth, avgAlt)
        #check for Out Of Bounds after each iteration
        if curY > y0 or curY < y1 or curX < x0 or curX > x1:
            print(f'ERROR: resolveTarget ran out of bounds at {curY}, {curX}, {curZ}m')
            print('ERROR: Please ensure target location is within geoTIFF dataset bounds')
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
    terrainAlt = geotiff_play.getAltFromLatLon(curY, curX, xParams, yParams, elevationData)

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

"""Inverse Haversine formula
via github.com/jdeniau
given a point, distance, and heading, return the new point (lat lon)
a certain distance along the great circle

for short distances, this is close to the straight line distance

this function assumes the earth is a sphere instead of a slight ellipsoid, which introduces a minor amount of error

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
    lat, lon = point
    lat, lon = map(math.radians, (lat, lon))
    d = distance
    r = 6371000 + alt # average radius of earth + altitude

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

this function assumes the earth is a sphere instead of a slight ellipsoid, which introduces a minor amount of error

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
    r = 6371000 + alt # Radius of earth in meters. Use 3956 for miles. Determines return value units.
    r = decimal.Decimal(r)
    return c * r

if __name__ == "__main__":
    getTarget()
