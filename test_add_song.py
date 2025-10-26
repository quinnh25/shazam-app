import os
import requests

def add_song(youtube_url: str) -> dict:
    
    # TODO: Set the url to the url you used in predict_song.py
    # HINT: will look similar to the url 
    # used in test_search.py:get_prediction()
    url = None
    url = "http://localhost:5003/add"

    # Initialize the package to send to the flask endpoint
    files = {'youtube_url': (None, youtube_url, 'text/plain')}
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        return result['status']
    else:
        print(f"Failed to get prediction: {response.status_code}")
        return None



# TODO: from tracks/audio, select the path of a file to identify
youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# add some noise to the audio for testing
#audio_noisy = add_noise(audio)

# save the noisy audio to a temporary file
#noisy_audio_path = "temp_noisy_audio.mp3"
#import soundfile as sf
#sf.write(noisy_audio_path, audio_noisy, 44100)

# print metadata from the prediction
print(add_song(youtube_url))
