#!/usr/bin/env python
import cv2
import rospy
from std_msgs.msg import *
from sensor_msgs.msg import Image
from object_detection.msg import BlobDetections
from cv_bridge import CvBridge, CvBridgeError
import threading
import numpy as np
from geometry_msgs.msg import Point


class Echo:
    def __init__(self):
        self.node_name = "Echo"
        self.header = std_msgs.msg.Header()
        self.blob_colors = []
        self.blob_sizes = []
        self.blob_positions = []
        self.thread_lock = threading.Lock()
        self.sub_image = rospy.Subscriber("/camera/rgb/image_rect_color",\
                Image, self.cbImage, queue_size=1)
        self.pub_image = rospy.Publisher("~echo_image",\
                Image, queue_size=1)
        self.pub_blob_detections = rospy.Publisher("blob_detections",BlobDetections, queue_size=10)
        self.bridge = CvBridge()

        rospy.loginfo("[%s] Initialized." %(self.node_name))

    def cbImage(self,image_msg):
        thread = threading.Thread(target=self.processImage,args=(image_msg,))
        thread.setDaemon(True)
        thread.start()


    def processImage(self, image_msg):
        if not self.thread_lock.acquire(False):
            return

        image_cv = self.bridge.imgmsg_to_cv2(image_msg)
        height,width,depth = image_cv.shape
        image_cv_hsv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2HSV)

        # print(height)
	
        red_lower = np.array([-7,125,125])
        red_upper = np.array([7,255,255])

        yellow_lower = np.array([25,175,175])
        yellow_upper = np.array([35,255,255])

        green_lower = np.array([50,100,100])
        green_upper = np.array([70,255,255])

        green_mask = cv2.inRange(image_cv_hsv, green_lower, green_upper)
        yellow_mask = cv2.inRange(image_cv_hsv, yellow_lower, yellow_upper)
        red_mask = cv2.inRange(image_cv_hsv, red_lower, red_upper)

        red_obj = cv2.bitwise_and(image_cv, image_cv, mask = red_mask)
        yellow_obj = cv2.bitwise_and(image_cv, image_cv, mask = yellow_mask)
        green_obj = cv2.bitwise_and(image_cv, image_cv, mask = green_mask)

        # full_image = red_obj + yellow_obj + green_obj
        full_image = [red_obj, yellow_obj, green_obj]

        for i in range(0, len(full_image)):
            im_gray = cv2.cvtColor(full_image[i], cv2.COLOR_BGR2GRAY)
            ret, tresh = cv2.threshold(im_gray,127,255,0)
            contours, hierarchy = cv2.findContours(im_gray,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                if cv2.contourArea(contour) > 250:
                    if i == 0:
                        text = "THE RED COLOR"
                        self.blob_colors.append(ColorRGBA(255,0,0,1))
                        text_color = (0,0,255)
                    if i == 1:
                        text = "THE YELLOW COLOUR"
                        self.blob_colors.append(ColorRGBA(0,255,255,1))
                        text_color = (0,255,255)
                    if i == 2:
                        text = "THE GREEN COLLAR"
                        self.blob_colors.append(ColorRGBA(0,255,0,1))
                        text_color = (0,255,0)
                    x,y,w,h = cv2.boundingRect(contour)
                    cv2.rectangle(image_cv, (x,y), (x+w, y+h), (147,20,255),2)
                    cv2.putText(image_cv,text,(x,y),4,1,text_color)
                    cv2.circle(image_cv, (x+(w/2),y+(h/2)), 5, (255,0,0),5)
                    self.blob_sizes.append(Float64(h))
                    print(Point(x+(w/2),y+(h/2),0))
                    self.blob_positions.append(Point(x+(w/2),y+(h/2),0))
        try:
            print(self.header)
            print(self.blob_colors)
            print(self.blob_sizes)
            print(self.blob_positions)
            self.pub_image.publish(\
                self.bridge.cv2_to_imgmsg(image_cv, "bgr8"))
            self.pub_image.publish(self.bridge.cv2_to_imgmsg(image_cv, "bgr8"))
            self.pub_blob_detections.publish(BlobDetections(self.header,self.blob_colors,self.blob_sizes,self.blob_positions))
	    
            del self.blob_colors[:]
            del self.blob_sizes[:]
            del self.blob_positions[:]

        except CvBridgeError as e:
            print(e)
        self.thread_lock.release()

if __name__=="__main__":
    rospy.init_node('Echo')
    e = Echo()
    rospy.spin()

