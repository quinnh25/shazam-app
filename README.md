# Shazam-App-Template

This will be the backbone of your Shazam clone applications for the rest of the semester. You may fork or copy files from this repository into your own repository in order to get started. Ignore implementing any code in cm_helper.py and cm_visualizations.py, this is helper code that is not necessary for the algorithm behind this project.

# Week 3:

1. Complete TODOs in const_map.py to implement our functions for constellation mapping
2. Visualize the same audio file using cm_visualizations.py and compare it to our solution. Are they similar?
3. Complete TODOs in hasher.py to implement our function for fingerprinting

- MDST Shazam Library - [download zip file here](https://drive.google.com/drive/folders/1Ui7o23sJjZB6tYUnoAffurmK0YB5nRVv?usp=sharing)

## Loading audio data:
```python
from dataloader import extract_zip, load

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