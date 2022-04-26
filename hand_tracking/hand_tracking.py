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
"""
import sys
import time
import random
import math
import IMU
import datetime
import socketio
"""

import cv2
import mediapipe as mp
import time
import socketio

sio = socketio.Client()

def send_coordinates():
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

    cap = cv2.VideoCapture(0)

    mpHands = mp.solutions.hands
    hands = mpHands.Hands(static_image_mode=False,
                        max_num_hands=1,
                        min_detection_confidence=0.5,
                        min_tracking_confidence=0.5)
    mpDraw = mp.solutions.drawing_utils

    pTime = 0
    cTime = 0

    while True:
        success, img = cap.read()
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)
        #print(results.multi_hand_landmarks)

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                resultString = int(handLms.landmark[mpHands.HandLandmark.INDEX_FINGER_TIP].x * 640) + ',' + int(handLms.landmark[mpHands.HandLandmark.INDEX_FINGER_TIP].y * 480)
                print(resultString)
                sio.emit("hand_coordinates", str(handLms.landmark[mpHands.HandLandmark.INDEX_FINGER_TIP].x * 640) + ',' + str(handLms.landmark[mpHands.HandLandmark.INDEX_FINGER_TIP].y * 480))
                for id, lm in enumerate(handLms.landmark):
                    #if id == 8:     #corresponding to tip of the index finger, see https://google.github.io/mediapipe/solutions/hands.html for reference
                        #print("index tip coords: ", handLms.landmark[mpHands.INDEX_FINGER_TIP].x, ", ", handLms.landmark[mpHands.INDEX_FINGER_TIP].y)
                    h, w, c = img.shape
                    cx, cy = int(lm.x *w), int(lm.y*h)
                    #if id ==0:
                    cv2.circle(img, (cx,cy), 3, (255,0,255), cv2.FILLED)

                mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)


        cTime = time.time()
        fps = 1/(cTime-pTime)
        pTime = cTime

        #cv2.putText(img,str(int(fps)), (10,70), cv2.FONT_HERSHEY_PLAIN, 3, (255,0,255), 3)

        cv2.imshow("Image", cv2.flip(img,1))
        
        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            sio.disconnect()
            break
            
        
        #pause
        time.sleep(0.05)

#SocketIO communcation.
@sio.event
def connect():
    print('connection established')
    sio.start_background_task(send_coordinates)

@sio.event
def disconnect():
    print('disconnected from server')

sio.connect('https://scrbbl-server.herokuapp.com/') #http://192.168.1.34:5050') # Change your IPv4 Address!
