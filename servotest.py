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
from gpiozero import Servo
import time

sys.path.insert(0, '../library')
import racecar_core
import racecar_utils as rc_utils

########################################################################################
# Global variables
########################################################################################

rc = racecar_core.create_racecar()

# size of color matrix

# Declare any global variables here


########################################################################################
# Functions
########################################################################################
new_servo = Servo(5)
# [FUNCTION] The start function is run once every time the start button is pressed
def start():
    # This tells the car to begin at a standstill
    rc.drive.stop()


# [FUNCTION] After start() is run, this function is run once every frame (ideally at
# 60 frames per second or slower depending on processing speed) until the back button

def update():
    global new_servo
    if rc.controller.was_pressed(rc.controller.Button.A):
        new_servo.value = 0
        print("min position")

    if rc.controller.was_pressed(rc.controller.Button.B):
        new_servo.value = 1
        print("max position")

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
