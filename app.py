from flask import Flask, render_template, request, jsonify, Response
from tensorflow.keras.models import load_model
import cv2
import numpy as np
import base64

app = Flask(__name__)

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
anti_spoofing_model = load_model('face_antispoofing_model.h5')  

@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():  
    camera = cv2.VideoCapture(0)  
    while True:
        success, frame = camera.read()  
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def process_image(image_data):

    image_bytes = base64.b64decode(image_data.split(',')[1])
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    if not len(faces):
        return jsonify({'message': 'No faces detected'})
    if len(faces)>1:
        return jsonify({'message': 'Multiple faces detected'})

    (x, y, w, h) = faces[0]

    face_roi = image[y:y+h, x:x+w]

    face_roi = cv2.resize(face_roi, (anti_spoofing_model.input_shape[1], anti_spoofing_model.input_shape[2]))
    face_roi = face_roi.astype('float32') / 255.0  
    face_roi = np.expand_dims(face_roi, axis=0)  

    is_real_face = anti_spoofing_model.predict(face_roi)[0][0] > 0.5

    if is_real_face:
        message = 'Face detected and verified as real!'
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)  
    else:
        message = 'Face detected but might be a spoof (photo, video, etc.)'
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)  

    _, encoded_image = cv2.imencode('.jpg', image)
    encoded_image = base64.b64encode(encoded_image).decode('utf-8')

    return jsonify({'message': message, 'image': encoded_image})  


@app.route('/process_image', methods=['POST'])
def process_image_route():
    image_data = request.get_json()['imageData']
    result = process_image(image_data)
    return result

if __name__ == '__main__':
    app.run(debug=True)
