module = "color"
import cv2
from statistics import mean

#pass in an image and it checks the center of image
#and calculates the average color
#return value [ averageColor, lowColor, hiColor ]
def getAverage(image, size):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    height = len(hsv)
    width = len(hsv[0])

    startX = int(width / 2) - int(size / 2)
    startY = int(height / 2) - int(size / 2)

    lowColor = hsv[0][0]
    hiColor = hsv[0][0]

    h = []
    s = []
    v = []

    for i in range(startX, startX + size):
        for j in range(startY, startY + size):
            h.append(hsv[j][i][0])
            s.append(hsv[j][i][1]) 
            v.append(hsv[j][i][2])

            if hsv[j][i][0] < lowColor[0]:
                lowColor = hsv[j][i]
            if hsv[j][i][0] > hiColor[0]:
                hiColor = hsv[j][i]

    averageColor = [ 0, 0, 0 ]
    averageColor[0] = int(mean(h))
    averageColor[1] = int(mean(s))
    averageColor[2] = int(mean(v))
    print(averageColor)

    return [ averageColor, lowColor, hiColor ]

def findColor(image, cam, lowerColor, upperColor):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, lowerColor, upperColor);
    res = cv2.bitwise_and(image, image, mask = mask);
    
    #grayscale image
    gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY);
    ret, thresh = cv2.threshold(gray, 127, 255, 0);

    countours, hierarchy = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    rectangle = {
        "area" : 0,
        "x" : 0,
        "y" : 0,
        "w" : 0,
        "h" : 0
    }

    for contour in countours:
        x, y, w, h = cv2.boundingRect(contour)

        if w * h > rectangle["area"]:
            rectangle["area"] = w * h;
            rectangle["x"] = x;
            rectangle["y"] = y;
            rectangle["w"] = w;
            rectangle["h"] = h;

    #Outline the rectangle
    cv2.rectangle(image, 
                 (rectangle["x"], rectangle["y"]),
                 (rectangle["x"] + rectangle["w"], rectangle["y"] + rectangle["h"]),
                 [0, 255, 0],
                 8)
