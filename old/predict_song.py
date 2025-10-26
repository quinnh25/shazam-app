from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from search import recognize_music
import DBcontrol as db
from DBcontrol import init_db

import tempfile
import os
import subprocess
import requests

app = Flask(__name__)
CORS(app)

library = "sql/library.db"
idx = 0

def get_yt_metadata(youtube_url: str, audio_path: str) -> dict:
    track_data = {}
    url = f"https://www.youtube.com/oembed?format=json&url={youtube_url}"
    response = requests.get(url)
    json_data = response.json()
    track_data["youtube_url"] = youtube_url
    track_data["title"] = json_data["title"]
    track_data["artist"] = json_data["author_name"]
    track_data["artwork_url"] = json_data["thumbnail_url"]
    track_data["audio_path"] = audio_path
    return track_data

@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict the song from the uploaded audio file.
    This endpoint accepts a POST request with an audio file (PyDub AudioSegment) and returns
    the predicted song information in JSON format.
    """
    
    # get audio from the request
    if 'audio' not in request.files:
        print("No audio found")
        return jsonify({'error': 'No audio found'})
    
    audio_file = request.files['audio']
    
    print(audio_file.path)
    
    # if not already a wav file then convert to wav
    # if audio_file.filename.endswith('.webm'):
    
    # Create a temporary file for the webm conversion
    # with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_webm:
    #     audio_file.save(temp_webm.name)
    #     temp_webm_path = temp_webm.name
    
    # Convert to WAV using FFmpeg
    # temp_audio_path = temp_webm_path.replace('.webm', '.wav')
    
    # print(f"Converting {temp_webm_path} to {temp__path}")
    
    # subprocess.run([
    #     'ffmpeg', '-i', temp_webm_path,
    #     '-ar', '44100',  # Sample rate
    #     '-ac', '1',      # Mono
    #     '-y',            # Overwrite
    #     temp_audio_path
    # ], check=True, capture_output=True)
    
    # Use scipy to parse the WAV file properly
    #sample_rate, audio_array = wavfile.read(temp_audio_path)
    # Convert to float32 and normalize
    #audio_array = audio_array.astype(np.float32) / (2**15)
    #print(f"Audio loaded: {len(audio_array)} samples at {sample_rate}Hz")
    
    scores, _ = recognize_music("./tracks/audio/" + audio_file.filename)

    
    urls = []
    names = []
    for id in scores:
        urls.append(db.retrieve_song(id[0])["youtube_url"])
        names.append(db.retrieve_song(id[0])["title"])

    # this line will be necessary for recorded files but not right now
    # os.remove("temp_audio_path")
    
    # return the best prediction in a JSON object
    return jsonify({
        'best': scores[0][0],
        'confidence': float(scores[0][1]),
        'urls': urls[0],
        'titles': names[0]
    })
            

if __name__ == '__main__':
    # Initialize the database using our command for now
    init_db()
    
    # Run the Falsk app at this given host and port
    app.run(host='0.0.0.0', port=5003, debug=True)