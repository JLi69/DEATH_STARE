#flask is the web server so we can run this app in the browser 
from flask import Flask, render_template, Response, redirect, request
import cv2
import threading
import april
import color
import numpy

app = Flask(__name__)
app.config["SECRET_KEY"] = "1716robotics"

cameraDev = [ "/dev/video0", "/dev/video2", "/dev/video4", "/dev/video6" ]
#cameraDev = [ "/dev/video0", "/dev/video2", "/dev/video4" ]
camera = cv2.VideoCapture()
camera.open(cameraDev[0])
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 20)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 15)

cameras = []
imageHoriz = []

#camera dimensions
camWidth = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
camHeight = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)

currentCam = 0

displayApril = False 
displayColor = False

cols = [ [ 0, 0, 0 ], [ 0, 0, 0 ], [ 255, 255, 255 ]]
currentFrame = camera.read()

def readCam(cam, frames, ind):
    while True:
        ret, frame = cam.read()
        if not ret:
            break
        resized = cv2.resize(frame, 
                    (int(240 / cam.get(cv2.CAP_PROP_FRAME_HEIGHT) * cam.get(cv2.CAP_PROP_FRAME_WIDTH)), 240),
                    interpolation=cv2.INTER_LINEAR)
        frames[ind] = resized

def openCam(i, cameras):
    cam = cv2.VideoCapture() 
    cam.open(cameraDev[i]) 
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 20)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 15)
    cameras.append(cam)

def getCams(): 
    cameras = []
    for i in range(len(cameraDev)):
        th = threading.Thread(target=openCam, args=(i, cameras))
        th.start()
    while len(cameras) < len(cameraDev):
        print("Capturing all cameras...")
    return cameras

"""
def getSpecificCams(indices):
    global imageHoriz
    cams = []
    for i in range(len(indices)):
        th = threading.Thread(target=openCam, args=(indices[i], cams))
        th.start()
    while len(cams) < len(indices):
        print("Capturing cameras...")
    for i in range(len(cams)):
        th = threading.Thread(target=readCam, args=(cams[i], imageHoriz, i))
        th.start()
    return cams
"""

# This function gets called by the /video_feed route below
def gen_frames():  # generate frame by frame from camera
    global currentFrame

    # We want to loop this forever
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()  # read the camera frame

        #display april tags
        if displayApril:
            april.displayApril(frame, camera)
        if displayColor:
            color.findColor(frame, camera, numpy.array(cols[1], dtype=numpy.uint8), 
                                           numpy.array(cols[2], dtype=numpy.uint8))

        
        #draw crosshairs
        cv2.rectangle(frame, 
                      (int(camWidth / 2 - 2), int(camHeight / 2 - 16)),
                      (int(camWidth / 2 + 2), int(camHeight / 2 + 16)),
                      [255, 0, 0],2)
        cv2.rectangle(frame, 
                      (int(camWidth / 2 - 16), int(camHeight / 2 - 2)),
                      (int(camWidth / 2 + 16), int(camHeight / 2 + 2)),
                      [255, 0, 0],2)

        # If something goes wrong with the camera, exit the function
        if not success:
            break
        
        currentFrame = frame

        # This step encodes the data into a jpeg image
        ret, buffer = cv2.imencode('.jpg', frame)

        # We have to return bytes to the user
        frame = buffer.tobytes() 

        # Return the image to the browser
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

#switch between cameras
@app.route('/next')
def next():
    global currentCam
    global camera
    global camWidth
    global camHeight

    currentCam += 1
    currentCam %= len(cameraDev) 
    camera.release()
    camera = cv2.VideoCapture()
    camera.open(cameraDev[currentCam])
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 20)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 15)

    print(currentCam) 
    
    camWidth = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    camHeight = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)

    return redirect('/')

@app.route('/toggle_april_tag')
def toggle_april():
    global displayApril
    displayApril = not displayApril
    return redirect('/')

@app.route('/toggle_color_detection')
def toggle_color():
    global displayColor
    displayColor = not displayColor
    return redirect('/')

@app.route('/prev')
def prev():
    global currentCam
    global camera
    global camWidth
    global camHeight    

    currentCam -= 1
    if currentCam < 0:
        currentCam = len(cameraDev) - 1 
    print(currentCam)
    camera.release()
    camera = cv2.VideoCapture()
    camera.open(cameraDev[currentCam])
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 20)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 15) 

    camWidth = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    camHeight = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)

    return redirect('/')

@app.route('/capture_color')
def captureColor():
    global cols
    success, image = camera.read()
    cols = color.getAverage(image, 100)
    cols[1] = [ cols[0][0] - 50, cols[0][1] - 50, cols[0][2] - 50 ]
    cols[2] = [ cols[0][0] + 50, cols[0][1] + 50, cols[0][2] + 50 ]
    return redirect('/')


@app.route('/goto_allcam')
def gotoAllCam():
    global cameras
    camera.release()
    cameras = getCams()
    return redirect('/allcam')

@app.route('/goback')
def goBack():
    global cameras
    global camera
    global currentCam
    for c in cameras:
        c.release()
    cameras = []
    camera = cv2.VideoCapture()
    currentCam = 0
    camera.open(cameraDev[currentCam])
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 20)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 15)
    
    return redirect('/')

@app.route('/allcam')
def all():
    return render_template("allcam.html")

def showAllCams():
    global imageHoriz 
    for i in range(len(cameraDev)):
        th = threading.Thread(target=readCam, args=(cameras[i], imageHoriz, i))
        th.start()

    # We want to loop this forever
    while True:

        allImages = cv2.hconcat(imageHoriz)

        # This step encodes the data into a jpeg image 
        ret, buffer = cv2.imencode('.jpg', allImages)

        # We have to return bytes to the user
        allImages = buffer.tobytes() 

        # Return the image to the browser
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + allImages + b'\r\n')  # concat frame one by one and show result

@app.route('/allCamsImage')
def allCamsImage():
    return Response(showAllCams(), mimetype='multipart/x-mixed-replace; boundary=frame')


def readImg(ind):
    cam = cv2.VideoCapture() 
    cam.open(cameraDev[ind])
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 20)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 15)
    cameras.append(cam)
    while True:
        ret, frame = cam.read()
        # This step encodes the data into a jpeg image 
        ret, buffer = cv2.imencode('.jpg', frame)

        # We have to return bytes to the user
        img = buffer.tobytes() 

        # Return the image to the browser
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n') 

#side camera view
@app.route('/goto_sidecam')
def gotoSideCam():
    global cameras
    camera.release()
    #indices = [ 0, 1, 2 ]
    #cameras = getSpecificCams(indices)
    return redirect('/sidecam')

@app.route("/side1")
def side1():
    return Response(readImg(0), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route("/side2")
def side2():
    return Response(readImg(1), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route("/side3")
def side3():
    return Response(readImg(2), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route("/side4")
def side4():
    return Response(readImg(3), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sidecam')
def sidecam():
    return render_template("sidecam.html")

if __name__ == '__main__':
    for i in range(len(cameraDev)):
        imageHoriz.append(numpy.zeros((240, 240, 3), dtype=numpy.uint8))
    app.run(threaded=True, host="0.0.0.0")
