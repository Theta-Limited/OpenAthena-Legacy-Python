"""
gui.py

This file is responsible for providing a user-friendly graphical user interface (GUI)

Provides simmilar functionality as parseImage.py

"""

import sys
import time
import math
from math import sin, asin, cos, atan2, sqrt

from osgeo import gdal # en.wikipedia.org/wiki/GDAL
# https://pypi.org/project/mgrs/
import mgrs # Military Grid ref converter
# # # https://pypi.org/project/pyproj/
# from pyproj import Transformer # Python interface to PROJ (cartographic projections and coordinate transformations library)

from PIL import Image
from PIL import ExifTags

from parseGeoTIFF import getAltFromLatLon, binarySearchNearest
from getTarget import *

from WGS84_SK42_Translator import Translator as converter # rafasaurus' SK42 coord translator
from SK42_Gauss_Kruger import Projector as Projector      # Matt's Gauss Kruger projector for SK42 (adapted from Nickname Nick)

from parseImage import *

from tkinter import *
from tkinter import filedialog

def gui():
    m=Tk()
    m.title('OpenAthena GUI')
    m.geometry("500x500")

    sk42 = BooleanVar()
    sk42_l = 'sk42'
    mgrs = BooleanVar()
    mgrs_l = 'mgrs'
    sk42.set(False)
    mgrs.set(True)

    mgrs_cb = Checkbutton(m, text = mgrs_l, variable = mgrs)
    sk42_cb = Checkbutton(m, text = sk42_l, variable = sk42)

    file_ex_l = 'Select a GeoTIFF digital elevation model file'
    label_file_explorer = Label(m,
                            text = file_ex_l,
                            width = 100, height = 4,
                            fg = "blue")

    button_explore_l = 'Browse Files'
    button_explore = Button(m,
                            text = button_explore_l,
                            command = browseGeoTIFF)

    mgrs_cb.grid(column=2, row = 2)
    sk42_cb.grid(column=2, row = 3)

    label_file_explorer.grid(column = 1, row = 1)
    button_explore.grid(column = 1, row = 2)

    m.mainloop()

def browseGeoTIFF():
    filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a GeoTIFF Digital Elevation Model File",
                                          filetypes = (("GeoTIFF",
                                                        ["*.tif*", "*.TIF*"]),
                                                       ("all files",
                                                        "*.*")))

    label_file_explorer.configure(text="File Opened: "+filename)

if __name__ == "__main__":
    gui()
