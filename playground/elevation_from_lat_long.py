# #Deprecated
# import osgeo.gdal as gdal
# import osgeo.osr as osr
from osgeo import gdal
from osgeo import osr
import numpy as np
from numpy import ma
import sys

# via stackoverflow: https://gis.stackexchange.com/a/29639

def maFromGDAL(filename):
    dataset = gdal.Open(filename, gdal.GA_ReadOnly)

    if dataset is None:
        print('Dataset is None')
        print('This shouldn\'t happen...')
        raise Exception()

    # Get the georeferencing metadata.
    # We don't need to know the CRS unless we want to specify coordinates
    # in a different CRS.
    #projection = dataset.GetProjection()
    geotransform = dataset.GetGeoTransform()

    # We need to know the geographic bounds and resolution of our dataset.
    if geotransform is None:
        dataset = None
        print('geotransform is None')
        print('This shouldn\'t happen...')
        raise Exception()

    # Get the first band.
    band = dataset.GetRasterBand(1)
    # We need to nodata value for our MakedArray later.
    nodata = band.GetNoDataValue()
    # Load the entire dataset into one numpy array.
    image = band.ReadAsArray(0, 0, band.XSize, band.YSize)
    # Close the dataset.
    dataset = None

    # Create a numpy MaskedArray from our regular numpy array.
    # If we want to be really clever, we could subclass MaskedArray to hold
    # our georeference metadata as well.
    # see here: http://docs.scipy.org/doc/numpy/user/basics.subclassing.html
    # For details.
    masked_image = ma.masked_values(image, nodata, copy=False)
    masked_image.fill_value = nodata

    return masked_image, geotransform

def pixelToMap(gt, pos):
    return (gt[0] + pos[0] * gt[1] + pos[1] * gt[2],
            gt[3] + pos[0] * gt[4] + pos[1] * gt[5])

# Reverses the operation of pixelToMap(), according to:
# https://en.wikipedia.org/wiki/World_file because GDAL's Affine GeoTransform
# uses the same values in the same order as an ESRI world file.
# See: http://www.gdal.org/gdal_datamodel.html
def mapToPixel(gt, pos):
    s = gt[0] * gt[4] - gt[3] * gt[1]
    x = (gt[4] * pos[0] - gt[1] * pos[1] + gt[1] * gt[5] - gt[4] * gt[2]) / s
    y = (-gt[3] * pos[0] + gt[0] * pos[1] + gt[3] * gt[2] - gt[0] * gt[5]) / s
    return (x, y)

def valueAtMapPos(image, gt, pos):
    pp = mapToPixel(gt, pos)
    x = int(pp[0])
    y = int(pp[1])

    if x < 0 or y < 0 or x >= image.shape[1] or y >= image.shape[0]:
        print('Something is wrong with coord or dataset')
        print(x)
        print(y)
        raise Exception()

    # Note how we reference the y column first. This is the way numpy arrays
    # work by default. But GDAL assumes x first.
    return image[y, x]

try:
    print(str(sys.argv))
    if (len(sys.argv) == 2):
        print('GOT HERE')

        geofilename = sys.argv[1]
        # print(sys.argv[1])
        # geofile = gdal.Open(geofilename)

        print("Okay, grabbing the GeoTIF file named: ", geofilename)
        image, geotransform = maFromGDAL(geofilename)
        # Something here is bugged but I can't figure out how/why
        val = valueAtMapPos(image, geotransform, (12.61, 41.82))
        print(val)
    else:
        print('ERROR: please provide just the name of a geotiff file')
except:
    print('Something went wrong.')
