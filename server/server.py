from flask import Flask, request
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
import concurrent.futures
from collections import Counter 
import os
import logging
import cv2
import imutils
import numpy as np
import easyocr

app = Flask(__name__)
api = Api(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4'}

logging.basicConfig(filename='server.log', level=logging.DEBUG)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower(
           ) in app.config['ALLOWED_EXTENSIONS']


class UploadVideo(Resource):
    def post(self):
        if 'video' in request.files:
            file = request.files['video']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                logging.info(f"Received file: {filename}")

                plate = self.process_video(file_path)

                if plate:
                    return {'video_name': filename, 'license_plate': plate}
                else:
                    return {'error': 'no plate detected'}, 400
        logging.warning("No video in request or wrong format")
        return {'error': 'no video in request or wrong format'}, 400

    def recognize_text(self, image):
        reader = easyocr.Reader(['en'])
        return reader.readtext(image)

    def process_frame(self, frame):
        frame = imutils.resize(frame, width=620)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        edged = cv2.Canny(gray, 30, 200)

        cnts = cv2.findContours(
            edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]

        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)
            if len(approx) == 4:
                cv2.drawContours(frame, [approx], -1, (0, 255, 0), 3)

                mask = np.zeros(gray.shape, np.uint8)
                new_image = cv2.drawContours(mask, [approx], 0, 255, -1)
                new_image = cv2.bitwise_and(frame, frame, mask=mask)
                (x, y) = np.where(mask == 255)
                (topx, topy) = (np.min(x), np.min(y))
                (bottomx, bottomy) = (np.max(x), np.max(y))
                cropped = gray[topx:bottomx + 1, topy:bottomy + 1]

                text = self.recognize_text(cropped)
                if text:
                    plate_text = text[0][-2]
                    return plate_text
        return None

    def submit_frames(self, executor, cap, frame_skip):
        futures = []
        frame_counter = 0
        while True:
            ret, frame = cap.read()
            frame_counter += 1
            if not ret:
                break
            if frame_counter % frame_skip == 0:
                future = executor.submit(self.process_frame, frame)
                futures.append(future)
        return futures

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        num_threads = 12
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=num_threads)
        frame_skip = 10  # Number of frames to skip
        futures = self.submit_frames(executor, cap, frame_skip)
        plate_texts = []
        for future in concurrent.futures.as_completed(futures):
            plate_text = future.result()
            if plate_text:
                plate_texts.append(plate_text)
        plate_counter = Counter(plate_texts)
        most_common_plate_text = plate_counter.most_common(1)[0][0]
        cap.release()
        return most_common_plate_text

api.add_resource(UploadVideo, '/upload_video')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
