import time
import matplotlib.pyplot as plt
from osgeo import gdal

print("Hello World!")
print("I'm geotiff_play.py")
print("Which File would you like to read?")

geofile = input("Enter the GeoTIF filename: ")

print("Okay, grabbing the GeoTIF file named: ", geofile)
geodata = gdal.Open(geofile)

# @TODO wtf is this?
#     grabs elevation data from tuple?
band = geodata.GetRasterBand(1)
elevation = band.ReadAsArray()

print("The shape of the elevation data is: ", elevation.shape)
time.sleep(3)
print("The raw Elevation data is: ")
time.sleep(1)
print(".")
time.sleep(1)
print(".")
time.sleep(1)
print(".")
time.sleep(1)
print(elevation)

plt.imshow(elevation, cmap=plt.get_cmap('viridis'))
plt.show()
