#Should be merged with app.py

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import random

# ==== NEW: Profanity library import ====
from better_profanity import profanity

import whisper
from transformers import pipeline

# ========== Configuration ==========
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mp3', 'wav', 'mov'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ========== Load Models ==========
# Image NSFW model (Hugging Face)
nsfw_model = pipeline("image-classification", model="Falconsai/nsfw_image_detection_384")

# Audio speech-to-text model (Whisper)
whisper_model = whisper.load_model("small")  # Use "tiny" for faster but lower accuracy

# ==== NEW: Initialize profanity word list ====
profanity.load_censor_words()
# You can add custom words on top of the defaults:
# profanity.add_censor_words(['mycustomword1', 'anotherbadword'])

# ========== Helper Functions ==========
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==== UPDATED: Use better_profanity to detect bad language ====
def detect_bad_language(text):
    # returns True if any profane word is found
    return profanity.contains_profanity(text)

def process_image(file_path):
    result = nsfw_model(file_path)
    top_label = result[0]['label']
    return top_label.lower() == "nsfw"

def process_audio(file_path):
    result = whisper_model.transcribe(file_path)
    text = result['text']
    if detect_bad_language(text):
        # you could also get a censored version:
        censored = profanity.censor(text)
        app.logger.debug(f"Profanity found in audio transcript: {censored}")
        return True
    return False

def process_video(file_path):
    cap = cv2.VideoCapture(file_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if frame_count == 0:
        return False  # Cannot process video

    selected_frames = random.sample(range(frame_count), min(5, frame_count))
    nsfw_found = False

    for frame_idx in selected_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue
        temp_image_path = os.path.join(UPLOAD_FOLDER, "temp_frame.jpg")
        cv2.imwrite(temp_image_path, frame)
        result = nsfw_model(temp_image_path)
        top_label = result[0]['label']

        if top_label.lower() == "nsfw":
            nsfw_found = True
            break

    cap.release()
    return nsfw_found

# ========== Routes ==========

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        ext = filename.rsplit('.', 1)[1].lower()

        # --- IMAGE Handling ---
        if ext in ['png', 'jpg', 'jpeg']:
            if process_image(file_path):
                return jsonify({
                    'status': 'blocked',
                    'type': 'image',
                    'reason': 'Obscene image detected.',
                    'request_source': True
                }), 400
            return jsonify({
                'status': 'safe',
                'type': 'image',
                'reason': 'No obscene image found.'
            }), 200

        # --- VIDEO Handling ---
        if ext in ['mp4', 'avi', 'mov']:
            if process_video(file_path):
                return jsonify({
                    'status': 'blocked',
                    'type': 'video',
                    'reason': 'Obscene content detected in video frames.',
                    'request_source': True
                }), 400
            return jsonify({
                'status': 'safe',
                'type': 'video',
                'reason': 'No obscene content found in video.'
            }), 200

        # --- AUDIO Handling ---
        if ext in ['mp3', 'wav']:
            if process_audio(file_path):
                return jsonify({
                    'status': 'blocked',
                    'type': 'audio',
                    'reason': 'Obscene language detected in audio.',
                    'request_source': True
                }), 400
            return jsonify({
                'status': 'safe',
                'type': 'audio',
                'reason': 'No obscene language found in audio.'
            }), 200

    return jsonify({'error': 'Invalid file format'}), 400


@app.route('/submit_source', methods=['POST'])
def submit_source():
    data = request.get_json()
    file_type = data.get('file_type')
    source_info = data.get('source_info')
    # Forward to your alerting system...
    print(f"Received Source Info for {file_type}: {source_info}")
    return jsonify({'status': 'received', 'message': 'Source information forwarded.'}), 200


if __name__ == '__main__':
    app.run(debug=True)
