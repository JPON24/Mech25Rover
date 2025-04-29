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
# size of color matrix

# Declare any global variables here


########################################################################################
# Functions
########################################################################################

# [FUNCTION] The start function is run once every time the start button is pressed
def start():
    # init value for closest object, later recalculated by min function
    auton = False

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
        rc.drive.set_speed_angle(0.05,0)
        find_object()


def find_object():
    image = rc.camera.get_color_image()
    
    # HSV THRESHOLDING FOR RED CONE
    hsvMin = (160,0,0)
    hsvMax = (10,255,255)

    lidarSamples = rc.lidar.get_samples()
    
    contours = rc_utils.find_contours(image, hsvMin, hsvMax)

    largestContour = rc_utils.get_largest_contour(contours)

    if largestContour is not None:
        rc_utils.draw_contour(image, largestContour, (0,255,0))
        center = rc_utils.get_contour_center(largestContour)
    
        # centroid is represented in (y,x) format 
        centroidX = center[1]
        centroidXErr = centroidX - 320
        offset = 0

        if centroidXErr > 0:
            offset = 719 - abs(int(centroidXErr * 0.17))
        elif centroidXErr < 0:
            offset = abs(int(centroidXErr * 0.17))

        distanceReading = lidarSamples[offset]

        print('----------')
        print(f'centroidXErr: {centroidXErr}, offset: {offset}, distance: {distanceReading}')
        print('----------')
    else:
        print('no object found')
    return centroidX, distanceReading

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
