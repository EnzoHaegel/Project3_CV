import cv2
import imutils
import numpy as np
import easyocr
import concurrent.futures
from collections import Counter
import os
import time

# Function to recognize text
def recognize_text(image):
    reader = easyocr.Reader(['en'])
    return reader.readtext(image)

# Process a single frame
def process_frame(frame):
    # Preprocessing
    frame = imutils.resize(frame, width=620)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)

    # Find contours
    cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]
    screenCnt = None

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        if len(approx) == 4:
            screenCnt = approx
            break

    if screenCnt is not None:
        cv2.drawContours(frame, [screenCnt], -1, (0, 255, 0), 3)

        # Masking and cropping the number plate region
        mask = np.zeros(gray.shape, np.uint8)
        new_image = cv2.drawContours(mask, [screenCnt], 0, 255, -1)
        new_image = cv2.bitwise_and(frame, frame, mask=mask)
        (x, y) = np.where(mask == 255)
        (topx, topy) = (np.min(x), np.min(y))
        (bottomx, bottomy) = (np.max(x), np.max(y))
        cropped = gray[topx:bottomx + 1, topy:bottomy + 1]

        # Recognize text
        text = recognize_text(cropped)
        if text:
            plate_text = text[0][-2]
            return plate_text

    return None

def submit_frames(executor, cap, frame_skip):
    futures = []
    frame_counter = 0
    while True:
        ret, frame = cap.read()
        frame_counter += 1
        if not ret:
            break
        if frame_counter % frame_skip == 0:
            future = executor.submit(process_frame, frame)
            futures.append(future)
    return futures

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    num_threads = 12
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=num_threads)

    # Number of frames to skip
    frame_skip = 10

    # Submit frames to executor
    futures = submit_frames(executor, cap, frame_skip)

    plate_texts = []
    for future in concurrent.futures.as_completed(futures):
        plate_text = future.result()
        if plate_text:
            plate_texts.append(plate_text)

    plate_counter = Counter(plate_texts)
    most_common_plate_text = plate_counter.most_common(1)[0][0]
    cap.release()
    return most_common_plate_text

# Directory path containing the videos
directory = 'uploads'

# List video files in the directory
video_files = [f for f in os.listdir(directory) if f.endswith('.mp4')]

# Process each video and write results to output file
output_file = 'output.txt'

start_time = time.time()

with open(output_file, 'w') as f:
    for video_file in video_files:
        video_path = os.path.join(directory, video_file)
        plate_text = process_video(video_path)
        f.write(f"Video: {video_file}\n")
        f.write(f"License Plate: {plate_text}\n\n")

elapsed_time = time.time() - start_time

print(f"License plate recognition complete. Results written to {output_file}.")
print(f"Elapsed time: {elapsed_time:.2f} seconds.")
