import time
import matplotlib.pyplot as plt
from osgeo import gdal
# import numpy
# import sys

# geotiff_play
# based on:
#    https://stackoverflow.com/questions/24956653/read-elevation-using-gdal-python-from-geotiff

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

plt.imshow(elevation, cmap='gist_earth', extent=[x0, x1, y1, y0])
plt.show()
