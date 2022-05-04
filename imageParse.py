"""
imageParse.py

This file is responsible for extracting drone sensor data from still-capture image(s) XMP and EXIF metadata

This can be done in near real-time if images are automatically downloaded to a computer from the UAV's paired device

Currently only photos from a DJI Mavic 2 Zoom are tested, support for more drone models can be added later with help from the OpenAthena
user community

If your UAV model is not listed here, feel free to make a pull request:
    DJI Mavic 2 Zoom

XMP:
en.wikipedia.org/wiki/Extensible_Metadata_Platform

EXIF:
en.wikipedia.org/wiki/EXIF

"""

import time
from osgeo import gdal # en.wikipedia.org/wiki/GDAL
# import mgrs # Military Grid ref converter
import math
# from math import sin, asin, cos, atan2, sqrt
from getTarget import *
import sys

"""prompt the user for options input,
       then extract data from image(s)
       and use resolveTarget() to give
       target location(s)
"""
def imageParse():



if __name__ == "__main__":
    imageParse()
