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

"""get the pos of current subject of UAS camera
       implementation can be changed later
"""
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

"""given sensor data, returns a tuple (y, x, z) location of target

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
    must be between 0.0 (straight forward) and 90.0 (straight downward)

"""
def resolveTarget(y, x, z, azimuth, theta):

    # convert azimuth and theta from degrees to radians
    azimuth, theta = math.radians(azimuth), math.radians(theta)

    # direction, convert to unit circle (just like math class)
    direction = azimuthToUnitCircleRad(azimuth)

    # from Azimuth, determine rate of x and y change
    #     per unit travel (level with horizon for now)
    deltax, deltay = math.cos(direction), math.sin(direction)

    deltaz = -1 * math.sin(theta) #neg because direction is downward


    # determines by how much of travel per unit is actually horiz
    # pythagoran theorem, deltaz^2 + deltax^2 + deltay^2 = 1
    horizScalar = math.cos(theta)
    deltax, deltay = horizScalar * deltax, horizScalar * deltay


    # at this point, deltax^2 + deltay^2 + deltaz^2 = 1
    #     if not, something is wrong
    sumOfSquares = deltax*deltax + deltay*deltay + deltaz*deltaz
    print(f'sum of squares is 1.0 : {sumOfSquares == 1.0}')
    print(f'deltax is {round(deltax, 4)}')
    print(f'deltay is {round(deltay, 4)}')
    print(f'deltaz is {round(deltaz, 4)}')

    # @TODO: Grab terrain data, trace terrain going forward from aircraft azimuth until point closest to center line of aircraft camera's view frustum, use this point as target location and altitude

# convert from azimuth notation (0 is up [+y], inc. clockwise) to
#     math notation(0 is right [+x], inc. counter-clockwise)
#
#     all units in Radians
def azimuthToUnitCircleRad(azimuth):
    # reverse direction of increment
    direction = (-1 * azimuth)
    # rotate 90deg, move origin from +y to +x
    direction += (0.5 * math.pi)
    direction = normalize(direction)
    print(f'direction is: {math.degrees(direction)}')
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
