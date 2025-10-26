# Shazam-App-Template

This will be the backbone of your Shazam clone applications for the rest of the semester. You may fork or copy files from this repository into your own repository in order to get started.

Provided helper files (no need to implement any code):

- `dataloader.py` - interface to work with a tracks dataset as a list of dictionaries (`dataloader.load()`)
- `cm_helper.py` - audio preprocessing, STFT computation, test sample creation
- `cm_visualizations.py` - plots spectrograms with peaks
- `DBcontrol.py` - database for managing many hashes (we'll investigate this later)
- `predict_song.py` - creates a `/predict` endpoint for interfacing with music recognition model

Files:

- `const_map.py` - constellation mapping
- `hasher.py` - creates hashes for representing pairs of peaks in database
- `search.py` - detailed implementation of audio search

Testing:

- `test_hash.py` - creates audio fingerprints
- `test_search.py` - sends a request to `/predict` endpoint

# Week 5

- `test_add_song.py` - TODO: Send a request to `/add_song` endpoint
- `predict_song.py` - TODO: Create a `/add_song` endpoint
- `DB_adder.py` - TODO: Write SQL queries that add an audio fingerprint to the database
- `grid_search.py`, `grid_search.ipynb` - Compute performance metrics, test recognition on different parameters.
- `parameters.py`, `parameters.json` - global access to the different tunable parameters of the model


Codebase modifications:

## Additions for Week 5
`const_map.py:find_peaks_windowed()`
```py
# Week 5: lines 69-70
from parameters import read_parameters
window_size, candidates_per_band, bands = read_parameters("constellation_mapping")
```

`hasher.py:create_hashes()`:
```py
# Week 5: lines 50-51
from parameters import read_parameters
fanout_t, fanout_f = read_parameters("hashing")
```

# Some modifications of Week 4
`const_map.py:remove_duplicate_peaks()`
```py
# use peaksc, not peaks
#for i in range(len(peaks)):
    #for j in range(len(peaks[i:min(i+15, len(peaks)-1)])):
        #j = j+i+1
        #if peaks_are_duplicate(peaks[i], peaks[j]):
            #peaks[j] = None
#return [peak for peak in peaks if peak is not None]

for i in range(len(peaksc)):
    for j in range(len(peaksc[i:min(i+15, len(peaksc)-1)])):
        j = j+i+1
        if peaks_are_duplicate(peaksc[i], peaksc[j]):
            peaksc[j] = None
return [peak for peak in peaksc if peak is not None]
```

`search.py:recognize_music()`
```py
# don't change sr from default value of sr=11025
# sample, sr = preprocess_audio(sample_audio_path, sr=sr)
## ...

sample, sr = preprocess_audio(sample_audio_path)
# ...
```

- `test_search.py:get_prediction()`
- `predict_song.py:predict()`
```py
# line 16 of test_search.py
#with open(audio_path, 'rb') as audio:
    #files = {'audio': (os.path.basename(audio_path), audio, 'audio/flac')}
    #response = requests.post(url, files=files)

with open(audio_path, 'rb') as audio:
    files = {'audio': (audio_path, audio, 'audio/flac')}
    response = requests.post(url, files=files)

# ----------------------------------------

# line 103 of predict_song.py
#scores, _ = recognize_music("./tracks/audio/" + audio_file.filename)
scores, _ = recognize_music(audio_file.filename)
# ....


# audio = "./tracks/audio/TylerTheCreator_DOGTOOTH_QdkbuXIJHfk.flac"
audio = "./audio_samples/Dogtooth_rec.flac"
print(get_prediction(audio))
```


MDST Shazam Library - [download zip file here](https://drive.google.com/drive/folders/1Ui7o23sJjZB6tYUnoAffurmK0YB5nRVv?usp=sharing)

## Loading audio data:

```python
from dataloader import extract_zip, load

# download tracks from Google Drive link above:
# week3tracks_tiny.zip       mp3 format, 92 MB
# week3tracks.zip           flac format, 1 GB

# extract zip archive (can do this from your file manager also)
extract_zip(zip_file="./week3tracks_tiny.zip", audio_directory = "./tracks")

# load track information as a list of dictionaries
tracks_info = load(audio_directory = "./tracks")

print(tracks_info[0])
#{
    #'youtube_url': 'https://www.youtube.com/watch?v=pWIx2mz0cDg',
    #'title': 'Plastic Beach (feat. Mick Jones and Paul Simonon)',
    #'artist': 'Gorillaz',
    #'artwork_url': 'https://i.scdn.co/image/ab67616d0000b273661d019f34569f79eae9e985',
    #'audio_path': 'tracks/audio/Gorillaz_PlasticBeachfeatMickJonesandPaulSimonon_pWIx2mz0cDg.mp3'
#}
```

# Week 3:

1. Complete TODOs in const_map.py to implement our functions for constellation mapping
2. Visualize the same audio file using cm_visualizations.py and compare it to our solution. Are they similar?

Note: If using WSL: Use explorer.exe <\_.html> to visualize your spectrogram peaks.

Solutions are in test_spec\_"audio_name".html

3. Complete TODOs in hasher.py to implement our function for fingerprinting

4. Use test_hash.py to test your hash creation. Check pb_short_hashed.txt for answers/


# Week 4

## TODO:

1. Download the week3tracks.zip files listed below (1GB so be warned)
2. Complete TODOs in hasher.py to implement our function for fingerprinting
3. Investigate predict_song.py. Try to understand how data is being passed into the Flask app.
4. Run test_search.py with predict_song.py running in the background to test your audio search
   algorithm. Replace pre-existing audio_path with any song in ./tracks/audio as a test.

Note: you will need to pip install flask and flask-cors to run the test scripts.