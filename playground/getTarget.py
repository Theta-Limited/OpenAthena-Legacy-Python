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
import math

# get the pos of current subject of UAS camera
#     implementation can be changed later
def getTarget():
    # note that by convention, coord pairs are usually (lat,long)
    #     i.e. (y,x)
    y = inputNumber("Please enter latitude in (+/-) decimal form: ", -90, 90)
    x = inputNumber("Please enter longitude in (+/-) decimal form: ", -180, 180)
    z = inputNumber("Please enter altitude (meters from sea-level) in decimal form: ", -423, 8848)
    azimuth = inputNumber("Please enter camera azimuth (0 is north) in decimal form (degrees): ", 0, 360)
    theta = inputNumber("Please enter angle of declanation (degrees down from forward) in decimal form: ", 0, 90)

    target = resolveTarget(y, x, z, azimuth, theta)

# handle user input of data, using message for prompt
#   guaranteed to return a float
def inputNumber(message, lowerBound, upperBound):
    while True:
        try:
            userInput = float(input(message))
            if userInput < lowerBound or upperBound < userInput:
                print(f'ERROR: input out of bounds. Lower bound is {lowerBound}, Upper bound is {upperBound}')
                print("Please Try Again")
                continue
        except ValueError:
            print("ERROR: Not an decimal number! Try again.")
            continue
        else:
            return userInput
            break

# returns a tuple (y, x, z) location of target
def resolveTarget(y, x, z, azimuth, theta):

    # convert azimuth and theta from degrees to radians
    azimuth, theta = math.radians(azimuth), math.radians(theta)

    # from Azimuth, determine rate of x and y change
    #     per unit travel (level with horizon for now)
    deltax = None
    deltay = None

    direction = azimuthToUnitCircleRad(azimuth)
    deltax, deltay = math.sin(direction), math.cos(direction)


    deltaz = None
    # pythagoran theorem, deltaz^2 + sqrt(deltax^2 + deltay^2) = 1^2
    deltaz = -1 * math.sin(theta) #neg because direction is downward
    # determines by how much of travel per unit is actually horiz
    horizScalar = math.cos(theta)
    deltax, deltay = horizScalar * deltax, horizScalar * deltay

    # at this point, deltax^2 + deltay^2 + deltaz^2 = 1
    #     if not, something is wrong
    sumOfSquares = deltax*deltax + deltay*deltay + deltaz*deltaz
    print(f'sum of squares is: {sumOfSquares}')

# convert from azimuth notation (0 is up [+y], inc. clockwise) to
#     math notation(0 is right [+x], inc. counter-clockwise)
#
#     all units in Radians
def azimuthToUnitCircleRad(azimuth):
    # reverse direction of increment
    direction = (-1 * azimuth)
    # rotate 90deg, move origin from +y to +x
    direction -= (0.5 * math.pi)
    direction = normalize(direction)

    return direction

# if a given angle is not between 0 and 2pi,
#     return the same angle in a number that is between 0 and 2pi (rad)
def normalize(direction):
    # the following two routines are mutually-exclusive
    while (direction < 0):
        direction += 2 * math.pi
    while (direction > (2 * math.pi)):
        direction -= 2 * math.pi

    return direction

def main():
    getTarget()

if __name__ == "__main__":
    getTarget()
