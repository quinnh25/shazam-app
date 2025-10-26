from cm_helper import compute_stft, preprocess_audio
from const_map import find_peaks
from hasher import create_hashes

path = "audio_samples/pb_recording_short.wav"
audio, sr = preprocess_audio(path)
frequencies, times, magnitudes = compute_stft(audio, sr)
constellation_map = find_peaks(frequencies, times, magnitudes)
fingerprints = create_hashes(constellation_map, song_id=1, sr=sr)
print(f"Number of fingerprints: {len(fingerprints)}")
print("Sample fingerprints (hash: (time, song_id)):")

# print the first 10 fingerprints
# store in a text file for easier viewing
with open("fingerprints.txt", "w") as f:
    for i, (h, v) in enumerate(fingerprints.items()):
        if i >= 10:
            break
        f.write(f"{h}: {v}\n")
