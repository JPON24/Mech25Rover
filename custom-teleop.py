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
from gpiozero import DigitalInputDevice
from gpiozero import Servo
import numpy as np

sys.path.insert(0, '../library')
import racecar_core
import racecar_utils as rc_utils

########################################################################################
# Global variables
########################################################################################

rc = racecar_core.create_racecar()
speed = 0.5
diff_speed = 0.5
auton = False
lastXErr = 0
lastYErr = 0

avgX = 0
avgY = 0
lowPassThreshold = 0.8

xIntegral = 0

flame_ref = DigitalInputDevice(5)
servo_l = Servo(6)
servo_r = Servo(13)

servo_l_pos = 0
servo_r_pos = 0
trigger_deadzone = 0.5
elevator_increment_amount = 0.2

'''


INITIALIZING


'''

def start():
    speed = 0.5
    diff_speed = 0.5
    auton = False
    lastXErr = 0
    lastDist = 0

    avgX = 0
    avgY = 0
    lowPassThreshold = 0.8
    
    xIntegral = 0

    servo_l_pos = 1
    servo_r_pos = -1

    servo_l.initial_value = servo_l_pos
    servo_r.initial_value = servo_r_pos
    trigger_deadzone = 0.5

    elevator_increment_amount = 0.2

    rc.drive.stop()
# END DEF

'''


UPDATE ALL SUBSYSTEMS


'''

def update():
    global speed, auton, flame_ref, servo_l, servo_r, trigger_deadzone, elevator_increment_amount
    
    # settings normalized speed (0-1)
    rc.drive.set_max_speed(speed)

    # get joystick data
    joystick_l = rc.controller.get_joystick(rc.controller.Joystick.LEFT)
    joystick_r = rc.controller.get_joystick(rc.controller.Joystick.RIGHT)
    
    # when the controller button is pressed, initialize the autonomous sequence
    if rc.controller.was_pressed(rc.controller.Button.A):
        auton = True
    elif rc.controller.was_pressed(rc.controller.Button.B): #auton manual override
        auton = False

    # servo controls
    if rc.controller.was_pressed(rc.controller.Button.X):
        extend_elevator(elevator_increment_amount)
    elif rc.controller.was_pressed(rc.controller.Button.Y):
        extend_elevator(elevator_increment_amount)
    
    # collect trigger input data
    diff_rotate_control_postive = rc.controller.get_trigger(rc.controller.Trigger.RIGHT)
    diff_rotate_control_negative = rc.controller.get_trigger(rc.controller.Trigger.LEFT)

    # move elevator based on trigger data
    if (diff_rotate_control_postive > trigger_deadzone):
        rotate_elevator(1)
    elif (diff_rotate_control_negative > trigger_deadzone):
        rotate_elevator(-1)

    # detecing and displaying fires - monitor station
    if (flame_ref.value == 0):
        write_fire()
    else:
        no_detection_matrix()

    # autonomous move
    if (auton):
        xErr, dist = find_object()
        # dist is currently a constant value to ensure that it only moves when it detects a fire
        move_to_position(xErr,dist)
    else: # teleoperated move
        if rc.controller.was_pressed(rc.controller.Button.LB):
            if (speed + 0.1 >= 0.1):
                speed -= 0.1
        elif rc.controller.was_pressed(rc.controller.Button.RB):
            if (speed + 0.1 <= 1):
                speed += 0.1

        rc.drive.set_speed_angle(joystick_l[1], joystick_r[0])
# END DEF

'''


SERVO ELEVATOR CONTROL SUBSYSTEM


'''

def extend_elevator(input):
    global servo_l_pos, servo_r_pos

    if (input > 0):
        if (servo_l_pos + rc.get_delta_time() * input > 1):
            return
        if (servo_r_pos - rc.get_delta_time() * input < -1):
            return

        servo_l_pos += input
        servo_r_pos -= input
    else:
        if (servo_l_pos - rc.get_delta_time() * input < -1):
            return
        if (servo_r_pos + rc.get_delta_time() * input > 1):
            return
                    
        servo_l_pos -= input
        servo_r_pos += input

    set_servo_pos()
# END DEF

def rotate_elevator(input):
    global servo_l_pos, servo_r_pos, diff_speed

    if (input > 0):
        if (servo_l_pos + rc.get_delta_time() * diff_speed > 1):
            return
        if (servo_r_pos + rc.get_delta_time() * diff_speed > 1):
            return

        servo_l_pos += rc.get_delta_time() * diff_speed
        servo_r_pos += rc.get_delta_time() * diff_speed
    else:
        if (servo_l_pos - rc.get_delta_time() * diff_speed < -1):
            return
        if (servo_r_pos - rc.get_delta_time() * diff_speed < -1):
            return
                    
        servo_l_pos -= rc.get_delta_time() * diff_speed
        servo_r_pos -= rc.get_delta_time() * diff_speed

    set_servo_pos()
# END DEF

def set_servo_pos():
    global servo_l, servo_r, servo_l_pos, servo_r_pos
    servo_l.value = servo_l_pos
    servo_r.value = servo_r_pos
# END DEF

'''


NAVIGATION SUBSYSTEM


'''

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
# END DEF

def low_pass(avg, val):
    global lowPassThreshold
    return (avg * lowPassThreshold) + (val * (1-lowPassThreshold))
# END DEF

def find_object():
    global capture
    image = rc.camera.get_color_image()

    # HSV THRESHOLDING FOR RED CONE
    # hsvMin = (134,0,0)
    # hsvMax = (179,255,255)

    # thresholding for deer object (and white people apparently?)
    hsvMin = (107,0,67)
    hsvMax = (124,185,207)

    contours = rc_utils.find_contours(image, hsvMin, hsvMax)

    largestContour = rc_utils.get_largest_contour(contours)

    if largestContour is not None:
        rc_utils.draw_contour(image, largestContour, (0,255,0))
        center = rc_utils.get_contour_center(largestContour)
    
        # centroid is represented in (y,x) format 
        centroidX = center[1]
        centroidXErr = centroidX - 320

        # replace distance reading with a rough estimate utilizing the camera
        distanceReading = 100
        
        return centroidXErr, distanceReading

    print('no object found')
    return (0,0)
# END DEF

'''


LED DISPLAY MATRIX SUBSYSTEM


'''

def write_fire():
    global auton

    new_matrix = np.zeros((8,24), dtype=np.uint8)
    
    new_matrix = f(2, new_matrix)
    new_matrix = i(3, new_matrix)
    new_matrix = r(4, new_matrix)
    new_matrix = e(4, new_matrix)

    auton = False

    rc.display.set_matrix(new_matrix)
# END DEF

def f(offset, matrix):
    proc_offset = offset - 1
    for i in range(1,7):    
        matrix[i, proc_offset] = 1
    for i in range(1,5):
        matrix[1, proc_offset+i] = 1
    for i in range(1,5):
        matrix[4, proc_offset+i] = 1

    return matrix
# END DEF

def i(offset, matrix):
    proc_offset = offset + 5
    matrix[1, proc_offset] = 1
    for i in range(3,7):
        matrix[i,proc_offset] = 1

    return matrix
# END DEF

def r(offset, matrix):
    proc_offset = offset + 7
    matrix[2, proc_offset+1] = 1
    for i in range(1,7):
        matrix[i, proc_offset] = 1 
    for i in range(0,3):
        matrix[1,proc_offset+i] = 1 
    
    return matrix
# END DEF

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
# END DEF

def no_detection_matrix():
    # create a matrix of zeroes for every single pixel
    new_matrix = np.zeros((8,24), dtype=np.uint8)
    rc.display.set_matrix(new_matrix)
# END DEF

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
# END DEF

########################################################################################
# DO NOT MODIFY: Register start and update and begin execution
########################################################################################

if __name__ == "__main__":
    rc.set_start_update(start, update, update_slow)
    rc.go()
