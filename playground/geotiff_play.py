import time
import matplotlib.pyplot as plt
from osgeo import gdal
import math
from getTarget import inputNumber
# import numpy
# import sys

# geotiff_play
# based on:
#    https://stackoverflow.com/questions/24956653/read-elevation-using-gdal-python-from-geotiff

def main():

    print("Hello World!")
    print("I'm geotiff_play.py")
    print("Which File would you like to read?")

    # geofile = input("Enter the GeoTIF filename: ")
    geofile = 'Rome-30m-DEM.tif'

    print("Okay, grabbing the GeoTIF file named: ", geofile)


    geodata = gdal.Open(geofile)

    # @TODO wtf is this?
    #     grabs elevation data from tuple?
    band = geodata.GetRasterBand(1)
    elevation = band.ReadAsArray()

    print("The shape of the elevation data is: ", elevation.shape)
    time.sleep(3)



    print("The raw Elevation data is: ")

    # numpy.set_printoptions(threshold=sys.maxsize)

    time.sleep(1)
    print(".")
    time.sleep(1)
    print(".")
    time.sleep(1)
    print(".")
    time.sleep(1)
    print(elevation)

    # plt.imshow(elevation, cmap=plt.get_cmap('viridisDE'))
    # plt.show()

    nrows, ncols = elevation.shape

    # I'm making the assumption that the image isn't rotated/skewed/etc.
    # This is not the correct method in general, but let's ignore that for now
    # If dxdy or dydx aren't 0, then this will be incorrect
    x0, dx, dxdy, y0, dydx, dy = geodata.GetGeoTransform()

    # This should help with type conversion
    # mx+b ?
    x1 = x0 + dx * ncols
    y1 = y0 + dy * nrows

    # # Dumb identity scalar for debugging
    # # Doesn't work, don't use this
    # x1 = 1
    # y1 = 1

    print(f'x0: {round(x0,4)} dx: {round(dx,9)} ncols: {round(ncols,4)} x1: {round(x1,4)}')
    print(f'y0: {round(y0,4)} dy: {round(dy,9)} nrows: {round(nrows,4)} y1: {round(y1,4)}')

    # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.imshow.html

    xParams = (x0, x1, dx, ncols)
    yParams = (y0, y1, dy, nrows)
    plt.imshow(elevation, cmap='gist_earth', extent=[x0, x1, y1, y0])
    plt.show()
    while True:
        lat = inputNumber('please enter a latitude: ', y1, y0)
        lon = inputNumber('please enter a longitude: ', x0, x1)
        result = getAltFromLatLon(lat, lon, xParams, yParams, elevation)
        print(f'Elevation of ({round(lat,6)}, {round(lon,6)}) is: {result}')

# end main func

"""given a latitude and longitude, obtain the altitude (elevation)
   from the nearest point

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

    # :(
    xlist = []
    xinit = x0
    for i in range(ncols):
        xlist.append(xinit)
        xinit += dx
    xL, xR = binarySearchNearest(xlist, lon)
    print(f'xL: {xlist[xL]} xR: {xlist[xR]}')
    # :(
    ylist = []
    yinit = y0
    for i in range(nrows):
        ylist.append(yinit)
        yinit += dy
    yT, yB = binarySearchNearest(ylist, lat)
    print(f'yT: {ylist[yT]} yB: {ylist[yB]}')
    # we have 4 datapoints nearest to the desired precise location
    # for now we will take a mean of their altitude (elevation)
    # but (@TODO) in the future we should find the point on the 3D plane defined by
    # the three nearest points to the target
    #
    # the greater dx or dy (lower the res of data), the greater the error
    # approximate conversion of degrees to metric here:
    # https://www.usna.edu/Users/oceano/pguth/md_help/html/approx_equivalents.htm
    e1, e2, e3, e4 = elevation[yT][xL], elevation[yB][xL], elevation[yT][xR], elevation[yB][xR]
    meanE = (e1 + e2 + e3 + e4) / 4
    print(f'e1: {e1} e2: {e2} e3: {e3} e4: {e4}')
    return meanE



"""given a list and value, return the index of the element closest to value

Parameters
----------
list: a sorted list of values
val: a value to search for
"""
def binarySearchNearest(list, val):
    if len(list) == 0:
        print(f'ERROR with list: {list}')
        return None

    if (len(list) == 1):
        # only one item in list
        return (0, 0)

    lastIndex = len(list) - 1

    isIncreasing = bool(list[0] < list[lastIndex])
    if not isIncreasing:
        # if its in decreasing order, uh, don't do that. make it increasing instead
        # kinda weird, but we reverse index result if we reverse the list
        reversedList = list.copy()
        reversedList.reverse()

        a1, a2 = binarySearchNearest(reversedList, val)
        a1 = len(list) - a1 - 1
        a2 = len(list) - a2 - 1
        return (a2, a1)


    L = 0
    R = lastIndex
    while L <= R:
        m = math.floor((L + R) / 2)
        if list[m] < val:
            L = m + 1
        elif list[m] > val:
            R = m - 1
        else:
            # exact match
            return (m, m)
    #if we've broken out of the loop, L > R
    #    so either list[L] or list[R] must be closest to val
    return(R, L)
    # if abs(list[L] - val) <= abs(list[R] - val):
    #     return L
    # else:
    #     return R

if __name__ == "__main__":
    main()
