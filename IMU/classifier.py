#!/usr/bin/python
#
#    This program  reads the angles from the acceleromteer, gyroscope
#    and mangnetometer on a BerryIMU connected to a Raspberry Pi.
#
#    This program includes two filters (low pass and median) to improve the
#    values returned from BerryIMU by reducing noise.
#
#    The BerryIMUv1, BerryIMUv2 and BerryIMUv3 are supported
#
#    This script is python 2.7 and 3 compatible
#
#    Feel free to do whatever you like with this code.
#    Distributed as-is; no warranty is given.
#
#    http://ozzmaker.com/

import sys
import time
import random
import math
import IMU
import datetime
import socketio

RAD_TO_DEG = 57.29578
M_PI = 3.14159265358979323846
G_GAIN = 0.070          # [deg/s/LSB]  If you change the dps for gyro, you need to update this value accordingly
AA =  0.40              # Complementary filter constant
ACC_LPF_FACTOR = 0.4    # Low pass filter constant for accelerometer
ACC_MEDIANTABLESIZE = 9         # Median filter table size for accelerometer. Higher = smoother but a longer delay

GYRO_X_LIFT = 50
GYRO_Y_LIFT = 40
GYRO_Z_LIFT = 40

GYRO_X_TWIST = 50
GYRO_Y_TWIST = 110
GYRO_Z_TWIST = 50

GYRO_X_CHOP = 40
GYRO_Y_CHOP = 40
GYRO_Z_CHOP = 50

sio = socketio.Client()
############### END Calibration offsets #################

#Just a wee lil' helper function to print an ASCII Title.
def print_title():
    print(r"""

░██████╗░█████╗░██████╗░██████╗░██████╗░██╗░░░░░░░░░░░░░░░░░░░██╗███╗░░░███╗██╗░░░██╗
██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║░░░░░░░░░░░░██╗░░░░██║████╗░████║██║░░░██║
╚█████╗░██║░░╚═╝██████╔╝██████╦╝██████╦╝██║░░░░░░░░░░██████╗░░██║██╔████╔██║██║░░░██║
░╚═══██╗██║░░██╗██╔══██╗██╔══██╗██╔══██╗██║░░░░░░░░░░╚═██╔═╝░░██║██║╚██╔╝██║██║░░░██║
██████╔╝╚█████╔╝██║░░██║██████╦╝██████╦╝███████╗██╗░░░░╚═╝░░░░██║██║░╚═╝░██║╚██████╔╝
╚═════╝░░╚════╝░╚═╝░░╚═╝╚═════╝░╚═════╝░╚══════╝╚═╝░░░░░░░░░░░╚═╝╚═╝░░░░░╚═╝░╚═════╝░                                                                                       
Note: To stop this code, please use 'Ctrl + C' on your keyboard.""")


#The MAIN beefy beefer of a function.
def send_gestures():
    #Print an awesome ACSII Title
    print_title()
    
    #Check to ensure user is already in a game room before prompting for username input and proceeding to run code.
    room_check = 1
    while room_check:
        joined_room = input("Have you joined a game room? (y/n)\n")
        if joined_room == "y":
            room_check = 0
        elif joined_room == "n":
            print("Not so fast! Please join a room before continuing.\n")
        else:
            print("Sorry, I didn't get that. Please only type 'y' for yes or 'n' for no.\n")
        
    #Once user has confirmed they have joined a room, prompt for username input.
    username = input("What is your username?\n")

    #Callout to server to link data stream to game user.
    sio.emit('setName', username+"8")

    # Filter variables
    oldXAccRawValue = 0
    oldYAccRawValue = 0
    oldZAccRawValue = 0

    #Initialize Idle Detection Values
    oldACCx = 0.0
    oldACCy = 0.0
    oldACCz = 0.0

    #Setup the tables for the mdeian filter. Fill them all with '1' so we dont get devide by zero error
    acc_medianTable1X = [1] * ACC_MEDIANTABLESIZE
    acc_medianTable1Y = [1] * ACC_MEDIANTABLESIZE
    acc_medianTable1Z = [1] * ACC_MEDIANTABLESIZE
    acc_medianTable2X = [1] * ACC_MEDIANTABLESIZE
    acc_medianTable2Y = [1] * ACC_MEDIANTABLESIZE
    acc_medianTable2Z = [1] * ACC_MEDIANTABLESIZE

    IMU.detectIMU()     # Detect if BerryIMU is connected.
    if(IMU.BerryIMUversion == 99):
        print(" No BerryIMU found... exiting ")
        sys.exit()
    IMU.initIMU()       # Initialise the accelerometer, gyroscope and compass

    action = "None"
    action_list = ["None"] * 5

    while True:
        #Read the accelerometer
        ACCx = IMU.readACCx()
        ACCy = IMU.readACCy()
        ACCz = IMU.readACCz()

        ###############################################
        #### Apply low pass filter                 ####
        ###############################################
        ACCx =  ACCx  * ACC_LPF_FACTOR + oldXAccRawValue*(1 - ACC_LPF_FACTOR);
        ACCy =  ACCy  * ACC_LPF_FACTOR + oldYAccRawValue*(1 - ACC_LPF_FACTOR);
        ACCz =  ACCz  * ACC_LPF_FACTOR + oldZAccRawValue*(1 - ACC_LPF_FACTOR);

        oldXAccRawValue = ACCx
        oldYAccRawValue = ACCy
        oldZAccRawValue = ACCz

        #########################################
        #### Median filter for accelerometer ####
        #########################################

        # cycle the table
        for x in range (ACC_MEDIANTABLESIZE-1,0,-1 ):
            acc_medianTable1X[x] = acc_medianTable1X[x-1]
            acc_medianTable1Y[x] = acc_medianTable1Y[x-1]
            acc_medianTable1Z[x] = acc_medianTable1Z[x-1]

        # Insert the lates values
        acc_medianTable1X[0] = ACCx
        acc_medianTable1Y[0] = ACCy
        acc_medianTable1Z[0] = ACCz

        # Copy the tables
        acc_medianTable2X = acc_medianTable1X[:]
        acc_medianTable2Y = acc_medianTable1Y[:]
        acc_medianTable2Z = acc_medianTable1Z[:]

        # Sort table 2
        acc_medianTable2X.sort()
        acc_medianTable2Y.sort()
        acc_medianTable2Z.sort()

        # The middle value is the value we are interested in
        ACCx = acc_medianTable2X[int(ACC_MEDIANTABLESIZE/2)];
        ACCy = acc_medianTable2Y[int(ACC_MEDIANTABLESIZE/2)];
        ACCz = acc_medianTable2Z[int(ACC_MEDIANTABLESIZE/2)];


        ######################## Classifier magic happening here #########################
    
        if ACCy > 2500 and ACCz < 2500:
            if action_list.count("None") > 4:
                action = "Right_Tilt"
                sio.emit('gesture_detected', action)
                sio.sleep(0.5)
            else:
                action = "None"
        elif ACCy < -2500 and ACCz < -2500:
            if action_list.count("None") > 4:
                action = "Left_Tilt"
                sio.emit('gesture_detected', action)
                sio.sleep(0.5)
            else:
                action = "None"
        elif ACCx > 2500 and ACCz < 2500:
            if action_list.count("None") > 4:
                action = "Forward_Tilt"
                sio.emit('gesture_detected', action)
                sio.sleep(0.5)
            else:
                action = "None"
        elif ACCx < -2500 and ACCz < 2500:
            if action_list.count("None") > 4:
                action = "Backward_Tilt"
                sio.emit('gesture_detected', action)
                sio.sleep(0.5)
            else:
                action = "None"
        else:
            action = "None"


        #Update old ACC values.
        oldACCx = ACCx
        oldACCy = ACCy
        oldACCz = ACCz

        #Update actions list.
        action_list = [action] + action_list
        action_list.pop()

        #Print to console & pause.
        print("Detected: ", action)
        time.sleep(0.05)

#SocketIO communcation.
@sio.event
def connect():
    print('connection established')
    sio.start_background_task(send_gestures)

@sio.event
def disconnect():
    print('disconnected from server')

sio.connect('https://scrbbl-server.herokuapp.com/') #http://192.168.1.34:5050') # Change your IPv4 Address!
