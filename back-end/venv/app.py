from flask import Flask, request, send_file, jsonify
import os
import io
import shutil
from werkzeug.utils import secure_filename
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Ensure the upload folders exist
UPLOAD_FOLDER = 'uploads'
FINAL_FOLDER = 'final'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FINAL_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def check_health():
    return jsonify({"message": "Good health"}), 200

   

@app.route('/process-frame', methods=['POST'])
def process_frame():
    if 'frame' not in request.files:
        return jsonify({"message": "No frame part"}), 400
    frame = request.files['frame']
    if frame.filename == '':
        return jsonify({"message": "No selected frame"}), 400

    # Save frame
    frame_path = os.path.join(UPLOAD_FOLDER, 'frame.jpg')
    frame.save(frame_path)

    # Process frame (for demonstration, we just convert it to grayscale)
    image = Image.open(frame_path).convert('L')
    byte_arr = io.BytesIO()
    image.save(byte_arr, format='JPEG')
    byte_arr.seek(0)

    return send_file(byte_arr, mimetype='image/jpeg')

@app.route('/upload-chunk', methods=['POST'])
def upload_chunk():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    chunk_index = request.form.get('index')
    filename = secure_filename(request.form.get('filename'))
    chunk_filename = f"{filename}.part{chunk_index}"
    chunk_filepath = os.path.join(UPLOAD_FOLDER, chunk_filename)
    file.save(chunk_filepath)

    print(f"Received chunk {chunk_index} of file: {filename}")

    return jsonify({"message": f"Chunk {chunk_index} upload successful"}), 200

@app.route('/reassemble-video', methods=['POST'])
def reassemble_video():
    filename = secure_filename(request.json.get('filename', ''))
    if not filename:
        return jsonify({"message": "No filename provided"}), 400

    chunk_files = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.startswith(filename)], key=lambda x: int(x.split('part')[-1]))
    if not chunk_files:
        return jsonify({"message": f"No chunks found for filename: {filename}"}), 400

    final_filepath = os.path.join(FINAL_FOLDER, filename)
    with open(final_filepath, 'wb') as final_file:
        for chunk_file in chunk_files:
            chunk_filepath = os.path.join(UPLOAD_FOLDER, chunk_file)
            with open(chunk_filepath, 'rb') as f:
                shutil.copyfileobj(f, final_file, length=16*1024*1024)  # 16MB buffer size to ensure smooth copying

    # Optionally clean up chunk files
    for chunk_file in chunk_files:
        os.remove(os.path.join(UPLOAD_FOLDER, chunk_file))

    print(f"Reassembled video file: {filename} at {final_filepath}")
    return jsonify({"message": "Reassemble successful", "filename": filename}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
