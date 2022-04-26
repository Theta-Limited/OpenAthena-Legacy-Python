"""
getTarget.py

This file should contain most of the math-heavy functions
    for use in an eventual prototype

By far the most dificult part of this project so far has been
    interfacing with the gdal library for GEOINT data

This file will focus instead on the core math of resolving the location
    of a target in the UAS camera's direct center line-of-sight
    ...while under the assumption that getAltFromLatLong() abstracts
       away the GEOINT data implementation

See ../fn_diagram.jpg

"""

import time

# get the pos of current subject of UAS camera
#     implementation can be changed later
def getTarget():
    # note that by convention, coord pairs are usually (lat,long)
    #     i.e. (y,x)
    y = inputNumber("Please enter latitude in decimal form: ")
    x = inputNumber("Please enter longitude in decimal form: ")
    z = inputNumber("Please enter altitude (meters from sea-level) in decimal form: ")
    azimuth = inputNumber("Please enter camera azimuth (0 is north) in decimal form (degrees): ")
    theta = inputNumber("Please enter angle of declanation (degrees) in decimal form: ")

    target = resolveTarget(y, x, z, azimuth, theta)

def inputNumber(message):
  while True:
      try:
          userInput = float(input(message))
      except ValueError:
          print("Not an decimal number! Try again.")
          continue
      else:
          return userInput
          break

# returns a tuple (y, x, z) location of target
def resolveTarget(y, x, z, azimuth, theta):
