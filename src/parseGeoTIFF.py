#!/usr/bin/env python3
"""
parseGeoTIFF.py

This file is responsible for obtaining elevation data from a given GeoTIFF Digital Elevation Model '.tif' file

May be run in user-interactive mode for displaying a color render of a GeoTIFF DEM
"""
import sys
import time
import matplotlib.pyplot as plt
# from osgeo import gdal
from geotiff import GeoTiff
import math
from math import sin, asin, cos, atan2, sqrt
import numpy as np
import decimal # more float precision with Decimal objects

import config # OpenAthena global variables

import getTarget

def main():

    if ("--version" in sys.argv or "-v" in sys.argv or "-V" in sys.argv or
        "V" in sys.argv or "version" in sys.argv):
        #
        sys.exit(config.version)

    if len(sys.argv) == 1 or ("--help" in sys.argv or "-h" in sys.argv or
        "-H" in sys.argv or "H" in sys.argv or "help" in sys.argv):
        #
        outstr = "usage: parseGeoTIFF.py [Rome-30m-DEM.tif]\n\nparseGeoTIFF.py may display a render of a GeoTIFF Digital Elevation Model.\nA GUI window will appear with an image render,\nmouse-over the image to view a tooltip where:\nx=longitude y=latitude [height above WGS84 reference ellipsoid]\n\nIf you exit the GUI, you will then be prompted for a latitude and longitude.\nYou may exit the program with CTRL+C, otherwise input a latitude and longitude\nto recieve the altitude of the nearest DEM datapoint"

    if 1 < len(sys.argv) and len(sys.argv) < 3:
        ext = sys.argv[1].split('.')[-1].lower()
        if ext != "tif":
            if ext in ["dt0", "dt1", "dt2", "dt3", "dt4", "dt5"]:
                print(f'FILE FORMAT ERROR: DTED format ".{ext}" not supported. Please use a GeoTIFF ".tif" file!')
            outstr = f'FATAL ERROR: got argument: {sys.argv[1]}, expected GeoTIFF (".tif") DEM!'
            sys.exit(outstr)
        else:
            geofile = sys.argv[1].strip()
    else:
        print("Hello World!")
        print("I'm parseGeoTIFF.py")
        print("Which File would you like to read?")
        geofile = input("Enter the GeoTIFF filename: ").strip()
    # geofile = 'Rome-30m-DEM.tif'

    print("Okay, grabbing the GeoTIFF file named: ", geofile, "\n")


    # based on:
    # stackoverflow.com/a/24957068

    # geodata = gdal.Open(geofile)
    geodata = GeoTiff(geofile)

    # band = geodata.GetRasterBand(1)

    elevation = geodata.read()

    try:
        # convert to numpy array for drastic in-memory perf increase
        elevation = np.array(elevation)
    except MemoryError:
        # it is possible, though highly unlikely,
        #     ...that a very large geotiff may exceed memory bounds
        #        this should only happen on 32-bit Python runtime
        #        or computers w/ very little RAM
        #
        # performance will be severely impacted
        elevation = None
        elevation = geodata.read()


    print("The shape of the elevation data is: ", elevation.shape)
    time.sleep(1)



    print("The raw Elevation data is: ")

    time.sleep(0.1)
    print(".")
    time.sleep(0.1)
    print(".")
    time.sleep(0.1)
    print(".")
    time.sleep(0.1)
    print(elevation)

    nrows, ncols = elevation.shape

    # I'm making the assumption that the image isn't rotated/skewed/etc.
    # This is not the correct method in general, but let's ignore that for now
    # If dxdy or dydx aren't 0, then this will be incorrect
    # x0, dx, dxdy, y0, dydx, dy = geodata.GetGeoTransform()
    x0 = geodata.tifTrans.get_x(0,0)
    dx = geodata.tifTrans.get_x(1,0) - x0
    y0 = geodata.tifTrans.get_y(0,0)
    dy = geodata.tifTrans.get_y(0,1) - y0
    dxdy = dydx = 0

    # This should help with type conversion
    # mx+b
    x1 = x0 + dx * ncols
    y1 = y0 + dy * nrows

    print(f'x0: {round(x0,4)} dx: {round(dx,9)} ncols: {round(ncols,4)} x1: {round(x1,4)}')
    print(f'y0: {round(y0,4)} dy: {round(dy,9)} nrows: {round(nrows,4)} y1: {round(y1,4)}')

    # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.imshow.html

    xParams = (x0, x1, dx, ncols)
    yParams = (y0, y1, dy, nrows)
    plt.imshow(elevation, cmap='gist_earth', extent=[x0, x1, y1, y0])
    plt.show()
    while True:
        lat = getTarget.inputNumber('please enter a latitude: ', y1, y0)
        lon = getTarget.inputNumber('please enter a longitude: ', x0, x1)
        result = getAltFromLatLon(lat, lon, xParams, yParams, elevation)
        print(f'Elevation of ({round(lat,6)}, {round(lon,6)}) is: {result}')

# end main func

"""get and open a geoFile named by a string
    e.g. from a command line argument

    if the name is invalid, exit with error

"""
def getGeoFileFromString(geofilename):
    geofilename.strip()
    # geoFile = gdal.Open(geofilename)
    geoFile = GeoTiff(geofilename)
    if geoFile is None:
        outstr = f'FATAL ERROR: can\'t find file with name \'{geofilename}\''
        sys.exit(outstr)

    # band = geoFile.GetRasterBand(1)
    # elevationData = band.ReadAsArray()
    elevationData = geoFile.read()

    try:
        # convert to numpy array for drastic in-memory perf increase
        elevationData = np.array(elevationData)
    except MemoryError:
        # it is possible, though highly unlikely,
        #     ...that a very large geotiff may exceed memory bounds
        #        this should only happen on 32-bit Python runtime
        #        or computers w/ very little RAM
        #
        # performance will be severely impacted
        elevationData = None
        elevationData = geodata.read()

    x0 = geoFile.tifTrans.get_x(0,0)
    dx = geoFile.tifTrans.get_x(1,0) - x0
    y0 = geoFile.tifTrans.get_y(0,0)
    dy = geoFile.tifTrans.get_y(0,1) - y0
    # dxdy, dydx will be != 0 if image is rotated or skewed
    #     unfortunately, I can't figure out how to check this after switching from
    #     ...library 'gdal' to 'geotiff'
    dxdy = dydx = 0
    geoTransform = (x0, dx, dxdy, y0, dydx, dy)

    return elevationData, geoTransform

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
        ext = geofilename.split('.')[-1].lower()
        if ext != "tif":
            if ext in ["dt0", "dt1", "dt2", "dt3", "dt4", "dt5"]:
                print(f'FILE FORMAT ERROR: DTED format ".{ext}" not supported. Please use a GeoTIFF ".tif" file!')
            print('ERROR: user input was: {sys.argv[1]}, but expected GeoTIFF ".tif" DEM!')
            print('Please try again')
            continue
        else:
            try:
                # geoFile = gdal.Open(geofilename) # old 'gdal' invocation
                geoFile = GeoTiff(geofilename) # new 'geotiff' invocation
            except:
                print(f'ERROR: can\'t find file with name \'{geofilename}\'')
                geoFile = None
                print('Please try again')
                continue
    #

    # band = geoFile.GetRasterBand(1)
    # elevationData = band.ReadAsArray()

    elevationData = geoFile.read()

    try:
        # convert to numpy array for drastic in-memory perf increase
        elevationData = np.array(elevationData)
    except MemoryError:
        # it is possible, though highly unlikely,
        #     ...that a very large geotiff may exceed memory bounds
        #        this should only happen on 32-bit Python runtime
        #        or computers w/ very little RAM
        #
        # performance will be severely impacted
        elevationData = None
        elevationData = geodata.read()

    x0 = geoFile.tifTrans.get_x(0,0)
    dx = geoFile.tifTrans.get_x(1,0) - x0
    y0 = geoFile.tifTrans.get_y(0,0)
    dy = geoFile.tifTrans.get_y(0,1) - y0
    # dxdy, dydx will be != 0 if image is rotated or skewed
    #     unfortunately, I can't figure out how to check this after switching from
    #     ...library 'gdal' to 'geotiff'
    dxdy = dydx = 0
    geoTransform = (x0, dx, dxdy, y0, dydx, dy)

    return elevationData, geoTransform

# """check if a geoTiff is invalid, i.e. rotated or skewed
# Parameters
# ----------
# dxdy : float
#     might be the rate of x change per unit y
#     if this is not 0, we have a problem!
# dydx : float
#     might be the rate of y change per unit x
#     if this is not 0, we have a problem!
# """
# def ensureValidGeotiff(dxdy, dydx):
#     # I'm making the assumption that the image isn't rotated/skewed/etc.
#     # This is not the correct method in general, but let's ignore that for now
#     # If dxdy or dydx aren't 0, then this will be incorrect
#     # we cannot deal with rotated or skewed images in current version
#     if dxdy != 0 or dydx != 0:
#         outstr = "FATAL ERROR: GeoTIFF is rotated or skewed!"
#         outstr += "\ncannot proceed with file: "
#         outstr += geofilename
#         print(outstr, file=sys.stderr)
#         sys.exit(outstr)


"""given a latitude and longitude, obtain the altitude (elevation)
   estimated from the nearest samples

Parameters
----------
lat: float
     latitude of desired location (e.g y-axis)
lon: float
     longitude of desired location (e.g. x-axis)
xParams: tuple
     tuple of 4 elements (x0, x1, dx, ncols)
     where (not in order)
     x0 is minimum lon. of dataset
     x1 is maximum lon. of dataset
     dx is the lon. change per datapoint increment +x
     ncols is the number of datapoints per row of the dataset
yParams: tuple
     tuple of 4 elements (y0, y1, dy, nrows)
     where (not in order)
     y0 is maximum lat. of dataset
     y1 is minimum lat. of dataset
     dy is the lat. change per datapoint increment +y
     nrows is the number of datapoints per column of the dataset
elevation: list[list]
     list of lists (2D array)
     where
     elevation[0][0] is NW corner of data
     elevation[0][max] is NE corner of data
     elevation[max][0] is SW corner of data
     elevation[max][max] is SE corner of data

"""
def getAltFromLatLon(lat, lon, xParams, yParams, elevation):
    x0, x1, dx, ncols = xParams
    y0, y1, dy, nrows = yParams
    # Out of Bounds (OOB) check
    if (lat > y0 or y1 > lat) or (lon > x1 or x0 > lon):
        return None

    # Kinda dumb
    #     @todo this can be replaced with simple algerbra :/
    xL, xR = binarySearchNearest(x0, ncols, lon, dx)
    yT, yB = binarySearchNearest(y0, nrows, lat, dy)

    x0, x1, dx = decimal.Decimal(x0), decimal.Decimal(x1), decimal.Decimal(dx)
    y0, y1, dy = decimal.Decimal(y0), decimal.Decimal(y1), decimal.Decimal(dy)

    lat, lon = decimal.Decimal(lat), decimal.Decimal(lon)

    L1 = (y0 + yT * dy, x0 + xR * dx, decimal.Decimal(int(elevation[yT][xR])))
    L2 = (y0 + yT * dy, x0 + xL * dx, decimal.Decimal(int(elevation[yT][xL])))
    L3 = (y0 + yB * dy, x0 + xL * dx, decimal.Decimal(int(elevation[yB][xL])))
    L4 = (y0 + yB * dy, x0 + xR * dx, decimal.Decimal(int(elevation[yB][xR])))
    samples = [L1, L2, L3, L4]
    target = (lat, lon)

    power = decimal.Decimal(2.0)
    return idwInterpolation(target, samples, power)

    # xIndex = None
    # if ( abs(lon - (x0 + xL * dx)) < abs(lon - (x0 + xR * dx))):
    #     xIndex = xL
    # else:
    #     xIndex = xR

    # yIndex = None
    # if (abs(lat - (y0 + yT * dy)) < abs(lat - (y0 + yB * dy))):
    #     yIndex = yT
    # else:
    #     yIndex = yB

    # outElevation = elevation[yIndex][xIndex]
    # # return the elevation of the nearest of 4 bounding datapoints
    # return outElevation


def idwInterpolation(target, samples, power):
    sumWeights = decimal.Decimal(0.0)
    sumWeightedElevations = decimal.Decimal(0.0)

    for neighbor in samples:
        distance = getTarget.haversine(target[1], target[0], neighbor[1], neighbor[0], neighbor[2])
        if (abs(distance) <= 0.5):
            return neighbor[2]

        weight = decimal.Decimal(1.0) / (distance ** power)
        sumWeights += weight
        sumWeightedElevations += weight * neighbor[2]

    return sumWeightedElevations / sumWeights


"""given a list and value, return a tuple of the two indexes in list whose value is closest to value

Parameters
----------
start: the start value to the search space items
n: the number of items in search space
val: a value to search for
dN: the change in value of each incremental value (i.e. dX or dY)
"""
def binarySearchNearest(start, n, val, dN):
    if n <= 0:
        print(f'ERROR, tried to search on empty data')
        return None

    if (n == 1):
        # only one item in list
        return (start, start)

    lastIndex = n - 1

    isIncreasing = (dN >= 0)
    if not isIncreasing:
        # if its in decreasing order, uh, don't do that. Make it increasing instead!
        reversedStart = start + n * dN
        reversedDN = -1 * dN

        a1, a2 = binarySearchNearest(reversedStart, n, val, reversedDN)
        # kinda weird, but we reverse index result if we reverse the list
        # reverse each of the two index(s)
        a1 = n - a1 - 1
        a2 = n - a2 - 1
        # reverse the tuple
        return (a2, a1)


    L = 0
    R = lastIndex
    while L <= R:
        m = math.floor((L + R) / 2)
        if start + m * dN < val:
            L = m + 1
        elif start + m * dN > val:
            R = m - 1
        else:
            # exact match
            return (m, m)
    #if we've broken out of the loop, L > R
    #    meaning that the markers have flipped
    #    so either list[L] or list[R] must be closest to val
    return(R, L)
    # if abs(list[L] - val) <= abs(list[R] - val):
    #     return L
    # else:
    #     return R

if __name__ == "__main__":
    main()
