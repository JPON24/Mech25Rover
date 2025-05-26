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
from gpiozero import DigitalInputDevice
import time
import numpy as np

sys.path.insert(0, '../library')
import racecar_core
import racecar_utils as rc_utils

########################################################################################
# Global variables
########################################################################################

rc = racecar_core.create_racecar()

# size of color matrix
flame_ref = DigitalInputDevice(5)

# Declare any global variables here


########################################################################################
# Functions
########################################################################################
# new_servo = Servo(5)
# [FUNCTION] The start function is run once every time the start button is pressed
def start():
    # This tells the car to begin at a standstill
    rc.drive.stop()


# [FUNCTION] After start() is run, this function is run once every frame (ideally at
# 60 frames per second or slower depending on processing speed) until the back button

def update():
    global flame_ref

    if (flame_ref.value == 0):
        write_fire()
    else:
        no_detection_matrix()

def write_fire():
    new_matrix = np.zeros((8,24), dtype=np.uint8)
    
    new_matrix = f(2, new_matrix)
    new_matrix = i(3, new_matrix)
    new_matrix = r(4, new_matrix)
    new_matrix = e(4, new_matrix)

    rc.display.set_matrix(new_matrix)

def f(offset, matrix):
    proc_offset = offset - 1
    for i in range(1,7):    
        matrix[i, proc_offset] = 1
    for i in range(1,5):
        matrix[1, proc_offset+i] = 1
    for i in range(1,5):
        matrix[4, proc_offset+i] = 1

    return matrix

def i(offset, matrix):
    proc_offset = offset + 5
    matrix[1, proc_offset] = 1
    for i in range(3,7):
        matrix[i,proc_offset] = 1

    return matrix

def r(offset, matrix):
    proc_offset = offset + 7
    matrix[2, proc_offset+1] = 1
    for i in range(1,7):
        matrix[i, proc_offset] = 1 
    for i in range(0,3):
        matrix[1,proc_offset+i] = 1 
    
    return matrix

def e(offset, matrix):
    proc_offset = offset + 12
    for i in range(1,7):
        matrix[i, proc_offset] = 1
    for i in range(0,3):
        matrix[1, proc_offset + i] = 1
    for i in range(0,3):
        matrix[4, proc_offset + i] = 1
    for i in range(0,3):
        matrix[6, proc_offset + i] = 1

    return matrix

def detection_matrix():
    # create a matrix of ones for every single pixel
    new_matrix = np.ones((8,24), dtype=np.uint8)
    rc.display.set_matrix(new_matrix)

def no_detection_matrix():
    # create a matrix of zeroes for every single pixel
    new_matrix = np.zeros((8,24), dtype=np.uint8)
    rc.display.set_matrix(new_matrix)

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

________________________________________________________________________________________________________________________________________________________

'''
"""
Copyright MIT
MIT License
bwsix RC101 - Fall 2023

File Name: servotest.py

Title: Demo RACECAR program (servo test)

Purpose: To verify that basic RACECAR functions work properly and that servo simulation works
in the Unity simulator using the racecar API (no GPIOZero or Raspberry Pi hardware needed).

Expected Outcome:
- When started, car simulates servo changes through rc.servo.set_angle()
"""

########################################################################################
# Imports
########################################################################################

import sys
import time

sys.path.insert(0, '../library')
import racecar_core
import racecar_utils as rc_utils

########################################################################################
# Global variables
########################################################################################

rc = racecar_core.create_racecar()

########################################################################################
# Functions
########################################################################################

def start():
    """
    This function is run once when the start button is pressed
    """
    print(">> Servo test starting...")
    rc.drive.stop()

def update():
    """
    This function is run every frame
    """
    # Test servo simulation with angle values
    print("Setting servo angle to 0.0")
    rc.servo.set_angle(0.0)
    time.sleep(1)

    print("Setting servo angle to 0.5")
    rc.servo.set_angle(0.5)
    time.sleep(1)

    print("Setting servo angle to 1.0")
    rc.servo.set_angle(1.0)
    time.sleep(1)

    # Optionally stop the car after test
    rc.drive.stop()

def update_slow():
    """
    Runs once per second; can be used to poll buttons if desired
    """
    if rc.controller.is_down(rc.controller.Button.RB):
        print("Right bumper pressed")

########################################################################################
# Main execution
########################################################################################

if __name__ == "__main__":
    rc.set_start_update(start, update, update_slow)
    rc.go()

'''