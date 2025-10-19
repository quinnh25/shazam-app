import os
import requests

# Initialize the database
from cm_helper import add_noise
from DBcontrol import init_db, retrieve_song_ids

def get_prediction(audio_path: str) -> dict:
    
    # TODO: Set the url to the url you used in predict_fruit.py
    url = "http://localhost:5003/predict"
    
    with open(audio_path, 'rb') as audio:
        files = {'audio': (os.path.basename(audio_path), audio, 'audio/mpeg')}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        return result['titles']
    else:
        print(f"Failed to get prediction: {response.status_code}")
        return None



# TODO: from tracks/audio, select the path of a file to identify
audio = "Dogtooth_rec.flac"

# add some noise to the audio for testing
# audio_noisy = add_noise(audio)

# save the noisy audio to a temporary file
# noisy_audio_path = "temp_noisy_audio.mp3"
# import soundfile as sf
# sf.write(noisy_audio_path, audio_noisy, 44100)

# print metadata from the prediction
print(get_prediction(audio))
