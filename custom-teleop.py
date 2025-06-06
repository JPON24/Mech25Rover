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
# drive and manipulator speeds
speed = 0.5
diff_speed = 0.5

# whether or not autonomously navigating
auton = False

# PID things
lastXErr = 0
lastYErr = 0
avgX = 0
avgY = 0
lowPassThreshold = 0.8
xIntegral = 0

# creates references to the external devices connected to the raspberry pi (only if it can, otherwise null ref)

flame_ref = DigitalInputDevice(5)
servo_l = Servo(6)
servo_r = Servo(13)

# backend positions for the servos for more precise movements 
servo_l_pos = 0
servo_r_pos = 0
servo_fan_pos = 0

# controlling the elevator
# the amount of trigger force required to move elevator
trigger_deadzone = 0.5

# amount to move by per trigger click
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

    servo_l_pos = 0
    servo_r_pos = 0

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
        extend_elevator(-elevator_increment_amount)
    
    # collect trigger input data
    diff_rotate_control_postive = rc.controller.get_trigger(rc.controller.Trigger.RIGHT)
    diff_rotate_control_negative = rc.controller.get_trigger(rc.controller.Trigger.LEFT)

    # move elevator based on trigger data
    if (diff_rotate_control_postive > trigger_deadzone):
        rotate_elevator(1)
    elif (diff_rotate_control_negative > trigger_deadzone):
        rotate_elevator(-1)

    # turn the fan on and off with a servo
    # if right bumper pressed, turn on fan
    # if left bumper pressed, turn off fan
    # add this later when mechanism is confirmed

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
        # speed controls, allowing the speed to be staged up and down between 0% and 100%
        if rc.controller.was_pressed(rc.controller.Button.LB):
            if (speed + 0.1 >= 0.1):
                speed -= 0.1
        elif rc.controller.was_pressed(rc.controller.Button.RB):
            if (speed + 0.1 <= 1):
                speed += 0.1
        
        # set the speed to tthe joystick inputs
        rc.drive.set_speed_angle(joystick_l[1], joystick_r[0])
# END DEF

'''


SERVO ELEVATOR CONTROL SUBSYSTEM


'''

# extends the elevator up and down on increments
def extend_elevator(input):
    global servo_l_pos, servo_r_pos

    # if extending outward
    if (input > 0):
        # if the extension would not be in the correct range, do not let it extend
        if (servo_l_pos - rc.get_delta_time() * input < -1):
            return
        if (servo_r_pos + rc.get_delta_time() * input > 1):
            return

        servo_l_pos -= input
        servo_r_pos += input
    else:
        input = -input
        # if the retraction would not be in the correct range, do not let it retract
        if (servo_l_pos + rc.get_delta_time() * input > 1):
            return
        if (servo_r_pos - rc.get_delta_time() * input < -1):
            return
                    
        servo_l_pos += input
        servo_r_pos -= input

    # set the servos to the internally handled positioning
    set_servo_pos()
# END DEF

# rotates the manipulator on the end of the elevator
def rotate_elevator(input):
    global servo_l_pos, servo_r_pos, diff_speed

    # if rotating the diff to the right
    if (input > 0):
        # if either servo is at the maximum, disable rotation because otherwise the extension will change
        if (servo_l_pos + rc.get_delta_time() * diff_speed > 1):
            return  
        if (servo_r_pos + rc.get_delta_time() * diff_speed > 1):
            return

        # increase values continously
        servo_l_pos += rc.get_delta_time() * diff_speed
        servo_r_pos += rc.get_delta_time() * diff_speed
    else: # if rotating diff left
        # max check
        if (servo_l_pos - rc.get_delta_time() * diff_speed < -1):
            return
        if (servo_r_pos - rc.get_delta_time() * diff_speed < -1):
            return

        # continous move 
        servo_l_pos -= rc.get_delta_time() * diff_speed
        servo_r_pos -= rc.get_delta_time() * diff_speed

    # set the servos to the internally handled positioning
    set_servo_pos()
# END DEF

# sets the actual servo positions to the internally handled positions
def set_servo_pos():
    global servo_l, servo_r, servo_fan, servo_l_pos, servo_r_pos, servo_fan_pos
    servo_l.value = servo_l_pos
    servo_r.value = servo_r_pos
    servo_fan.value = servo_fan_pos
# END DEF

'''


NAVIGATION SUBSYSTEM


'''

# this function will get the robot the same line as the object, and then close in on it on the forward axis
def move_to_position(xErr, dist):
    global lastXErr, lastYErr, speed, avgX, avgY, xIntegral

    # 50 cm offset from object as target
    yErr = (dist - 50)

    # handles the staging of the navigation
    canCloseDistance = False

    # pid tuning individualized by axis
    kpx = 1 #1
    kix = 0.01 # 0.05
    kdx = 0.1 #0.6

    kpy = 1 #1
    kdy = 0.6 #0.6

    # recalculate x integral every frame
    xIntegral += xErr * rc.get_delta_time()

    # if not yet pointing at the object, recalculate the rotational output to converge on the point                                                           
    if (abs(xErr) > 50):
        # calculate the rate of change of rotation in cx units
        xDeriv = (xErr - lastXErr)/rc.get_delta_time()
        
        # recalculate rotation output
        xOutput = xErr * kpx + kix * xIntegral + xDeriv * kdx
    else:
        xDeriv = (xErr - lastXErr)/rc.get_delta_time()
        xOutput = xErr * kpx + kix * xIntegral + xDeriv * kdx
        
        # if within a reasonable range minimize rotational changes in order to have a forward movement
        xOutput *= -0.1
        
        # allow the robot to start moving forward toward the object when on the the line
        canCloseDistance = True

        # 0 the turn integral to allow unbiased outputs
        xIntegral = 0

    # y
    if (dist != 0 and canCloseDistance): # dist is 0 in the case of no detection, so if there is a detection recalculate pid
        yDeriv = (yErr - lastYErr)/rc.get_delta_time()
        yOutput = yErr * kpy + yDeriv * kdy
    else:
        # if getting onto the line, move backwards for consistent movements
        yOutput = -1

    # clamps the x and y outputs into a normalized range
    xOutput = rc_utils.clamp(xOutput, -1, 1)
    yOutput = rc_utils.clamp(yOutput, -1, 1)

    # reduces noise in the output to make sure that changes to the output are consistent and accurate
    xOutput = low_pass(xOutput, avgX)
    yOutput = low_pass(yOutput, avgY)

    # recalculated for future derivative
    lastXErr = xErr
    lastYErr = yErr

    # set the drive and turn actuators to the correct positions
    rc.drive.set_speed_angle(yOutput, -xOutput)
# END DEF

# this kind of filter is generally used to attenuate sensor noise 
def low_pass(avg, val):
    global lowPassThreshold
    return (avg * lowPassThreshold) + (val * (1-lowPassThreshold))
# END DEF

# this function is used to find the nearest object within a certain color range
# if it finds this object, it detects the largest of these objects in the view
# the center of mass of this object is found, and thus used later as an offset on the x axis
def find_object():
    global capture # currently unused

    # gets a numpy array in bgr format for each pixel in the camera view
    image = rc.camera.get_color_image()

    # HSV THRESHOLDING FOR RED CONE
    # hsvMin = (134,0,0)
    # hsvMax = (179,255,255)

    # thresholding for deer object
    # hsvMin = (107,0,67)
    # hsvMax = (124,185,207)

    # thresholding for candle object
    hsvMin = (0,0,207)
    hsvMax = (179,255,239)

    # finds the outlines of any object within the given thresholds
    contours = rc_utils.find_contours(image, hsvMin, hsvMax)

    # finds the largest object, and returns it in numpy array form
    largestContour = rc_utils.get_largest_contour(contours)

    # if there is a contour, find its center of mass
    if largestContour is not None:
        # draw contour just draws it onto the image for debug purposes
        rc_utils.draw_contour(image, largestContour, (0,255,0))
        
        # finds the center of mass in y,x format
        center = rc_utils.get_contour_center(largestContour)
     
        centroidX = center[1]

        # creates an error by creating an offset from the center in pixels
        # because the camera has a width of 640 pixels, subtracting 320 creates a target on the midpoint
        centroidXErr = centroidX - 320

        # usually this uses camera or lidar, but because of backend problems it is hardcoded to be a value that continually converges
        distanceReading = 100
        
        return centroidXErr, distanceReading

    # if no object was found, stop moving the robot
    print('no object found')
    rc.drive.set_speed_angle(0,0)
    return (0,0)
# END DEF

'''


LED DISPLAY MATRIX SUBSYSTEM


'''

# this function creates a new reference to the matrix (giving it a completely off state)
# this matrix is then passed in to the letter functions, thus painting these letters onto the matrix
# this temp matrix is then displayed to the actual matrix
def write_fire():
    global auton

    # create a new empty matrix
    new_matrix = np.zeros((8,24), dtype=np.uint8)
    
    # draw letters
    new_matrix = f(2, new_matrix)
    new_matrix = i(3, new_matrix)
    new_matrix = r(4, new_matrix)
    new_matrix = e(4, new_matrix)

    # if a fire is detected, stop autonomously navigating toward the object because the object has been reached
    auton = False

    rc.display.set_matrix(new_matrix)
# END DEF

# render an F on a given matrix
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

# render an I on a given matrix
def i(offset, matrix):
    proc_offset = offset + 5
    matrix[1, proc_offset] = 1
    for i in range(3,7):
        matrix[i,proc_offset] = 1

    return matrix
# END DEF

# render an R on a given matrix
def r(offset, matrix):
    proc_offset = offset + 7
    matrix[2, proc_offset+1] = 1
    for i in range(1,7):
        matrix[i, proc_offset] = 1 
    for i in range(0,3):
        matrix[1,proc_offset+i] = 1 
    
    return matrix
# END DEF

# render an E on a given matrix
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

    # display this turned off state on the matrix
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
