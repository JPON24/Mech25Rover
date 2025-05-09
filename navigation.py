"""
Copyright MIT
MIT License
bwsix RC101 - Fall 2023

File Name: demo.py

Title: Demo RACECAR program

Purpose: To verify that basic RACECAR functions work properly and the student has set up
the system correctly to run Python scripts with the RACECAR start/update paradigm in the
Unity simulator.

Expected Outcome: Terminal output and RACECAR movement occurs when buttons are pressed
- When the "A" button is pressed, print a message to the terminal window
- When the "B" button is pressed, RACECAR moves forward and to the right
"""

# screen - 480, 640 (y,x)
# 110 degree fov width

# TEST THIS CODE ON THE COLOR CAMERA SANDBOX ENVIRONMENT
# SHOULD SEEK OUT A BLUE CONE AND DRIVE TOWARDS IT, DECELERATING FROM A CERTAIN DISTANCE

########################################################################################
# Imports
########################################################################################

#racecar sim navigation.py

import sys
from time import time
import math as Math

sys.path.insert(0, '../library')
import racecar_core
import racecar_utils as rc_utils

########################################################################################
# Global variables
########################################################################################

rc = racecar_core.create_racecar()
auton = False
lastXErr = 0
lastYErr = 0
speed = 0.5

avgX = 0
avgY = 0
lowPassThreshold = 0.8

xIntegral = 0

# size of color matrix

# Declare any global variables here


########################################################################################
# Functions
########################################################################################

# [FUNCTION] The start function is run once every time the start button is pressed
def start():
    # init value for closest object, later recalculated by min function
    auton = False
    lastXErr = 0
    lastDist = 0
    speed = 0.5

    avgX = 0
    avgY = 0
    lowPassThreshold = 0.8
    
    xIntegral = 0

    # This tells the car to begin at a standstill
    rc.drive.stop()


# [FUNCTION] After start() is run, this function is run once every frame (ideally at
# 60 frames per second or slower depending on processing speed) until the back button

def update():
    global auton

    # when the controller button is pressed, initialize the autonomous sequence
    if rc.controller.was_pressed(rc.controller.Button.A) and not auton:
        auton = True

   # run full semi-auto sequence 
    if auton:
        xErr, dist = find_object()
        move_to_position(xErr,dist)

def move_to_position(xErr, dist):
    global lastXErr, lastYErr, speed, avgX, avgY, xIntegral

    # 50 cm offset from object
    yErr = (dist - 50)

    canCloseDistance = False

    kpx = 1 #1
    kix = 0.01 # 0.05
    kdx = 0.1 #0.6

    kpy = 1 #1
    kdy = 0.6 #0.6

    # x
    xIntegral += xErr * rc.get_delta_time()

    if (abs(xErr) > 50):
        xDeriv = (xErr - lastXErr)/rc.get_delta_time()
        xOutput = xErr * kpx + kix * xIntegral + xDeriv * kdx
    else:
        xDeriv = (xErr - lastXErr)/rc.get_delta_time()
        xOutput = xErr * kpx + kix * xIntegral + xDeriv * kdx

        xOutput *= -0.1
        canCloseDistance = True
        xIntegral = 0

    # y
    if (dist != 0 and canCloseDistance):
        yDeriv = (yErr - lastYErr)/rc.get_delta_time()
        yOutput = yErr * kpy + yDeriv * kdy
    else:
        yOutput = -1

    xOutput = rc_utils.clamp(xOutput, -1, 1)
    yOutput = rc_utils.clamp(yOutput, -1, 1)

    xOutput = low_pass(xOutput, avgX)
    yOutput = low_pass(yOutput, avgY)

    lastXErr = xErr
    lastYErr = yErr

    rc.drive.set_speed_angle(yOutput, -xOutput)

def low_pass(avg, val):
    global lowPassThreshold
    return (avg * lowPassThreshold) + (val * (1-lowPassThreshold))

def find_object():
    image = rc.camera.get_color_image()
    depthImage = rc.camera.get_depth_image()
    
    # HSV THRESHOLDING FOR RED CONE
    hsvMin = (134,0,0)
    hsvMax = (179,255,255)

    contours = rc_utils.find_contours(image, hsvMin, hsvMax)

    largestContour = rc_utils.get_largest_contour(contours)

    if largestContour is not None:
        rc_utils.draw_contour(image, largestContour, (0,255,0))
        center = rc_utils.get_contour_center(largestContour)
    
        # centroid is represented in (y,x) format 
        centroidX = center[1]
        # print(centroidX)
        centroidXErr = centroidX - 320
        # offset = 0

        # if centroidXErr > 0:
        #     offset = 719 - abs(int(centroidXErr * 0.34))
        # elif centroidXErr < 0:
        #     offset = abs(int(centroidXErr * 0.34))

        # distanceReading = lidarSamples[offset]

        distanceReading = depthImage[center[0],center[1]]

        # print(f'centroidXErr: {centroidXErr}, offset: {offset}, distance: {distanceReading}')
        print(f'centroidXErr: {centroidXErr}, distance: {distanceReading}')
        
        return centroidXErr, distanceReading

    print('no object found')
    return 0,0

def update_slow():
    """
    After start() is run, this function is run at a constant rate that is slower
    than update().  By default, update_slow() is run once per second
    """
    # This prints a message every time that the right bumper is pressed during
    # a call to update_slow.  If we press and hold the right bumper, it
    # will print a message once per second

    if rc.controller.is_down(rc.controller.Button.RB):
        print("The right bumper is currently down (update_slow)")


########################################################################################
# DO NOT MODIFY: Register start and update and begin execution
########################################################################################

if __name__ == "__main__":
    rc.set_start_update(start, update, update_slow)
    rc.go()
