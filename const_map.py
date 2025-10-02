import os

import librosa
import numpy as np
from scipy import signal
from collections import defaultdict
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from cm_helper import compute_fft

from .DBcontrol import connect, retrieve_song, \
    retrieve_song_ids, retrieve_hashes, add_hashes, \
    create_hash_index, create_tables, add_songs

def convert_to_decibel(magnitude: np.array):
    """
    returns spectrogram's amplitude at each freq/time bin, measured in dB
    """
    return 20*np.log10(magnitude + 1e-6)

def visualize_map_interactive(audio_path):
    audio, sr = preprocess_audio(audio_path)
    frequencies, times, magnitudes = compute_fft(audio, sr)
    magnitudes = convert_to_decibel(magnitudes)
    print(magnitudes.shape)

    constellation_map = find_peaks(frequencies, times, magnitudes)
    peak_times = [times[t] for t, f in constellation_map]
    peak_freqs = [f for t, f in constellation_map]

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=magnitudes,
        x=times,
        y=frequencies,
        colorscale='Inferno',
        colorbar=dict(title='Magnitude (dB)'),
        zsmooth='best',
        name="Spectrogram"
    ))

    fig.add_trace(go.Scatter(
        x=peak_times,
        y=peak_freqs,
        mode='markers',
        marker=dict(size=7, color='white', symbol='square-open'),
        name='Constellation Map',
        visible=True
    ))

    # overlay constellation peaks with a toggleable checkbox
    fig.update_layout(
        title='Spectrogram with Constellation Map',
        xaxis_title='Time (s)',
        yaxis_title='Frequency (Hz)',
        yaxis=dict(
            range=[frequencies.min(), frequencies.max()],
            autorange=False  # Prevent auto-padding when scatter appears
        ),
        xaxis=dict(
            range=[times.min(), times.max()],
            autorange=False  # Optional: lock X-axis too
        ),
        margin=dict(t=40, b=40, l=60, r=40),
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                buttons=[
                    dict(label="Show Peaks",
                         method="update",
                         args=[{"visible": [True, True]}]),
                    dict(label="Hide Peaks",
                         method="update",
                         args=[{"visible": [True, False]}]),
                ],
                showactive=True,
                x=1.05,
                xanchor="left",
                y=1.15,
                yanchor="top"
            )
        ]
    )

    fig.show()

# Provided functions for finding if two peaks are "duplicates" (too close to each other)
def peaks_are_duplicate(peak1: tuple[int, float] = None, peak2: tuple[int,float] = None):
    if peak1 is None or peak2 is None:
        return False
    
    # Threshholds for considering two peaks as duplicates. Feel free to play around with these for your app.
    delta_time = 10
    delta_freq = 300
    t1, f1 = peak1
    t2, f2 = peak2
    if abs(t1 - t2) <= delta_time and abs(f1 - f2) <= delta_freq:
        return True
    return False

# Function to remove duplicate peaks that are too close to each other
def remove_duplicate_peaks(peaks: list[tuple[int, float]]):
    
    # create a copy of the peaks list to avoid modifying the original list
    peaks=peaks.copy()
    peaks.sort(key=lambda x: x[0])
    # for each peak, search for duplicates within the next 10 peaks (ordered by time)
    for i in range(len(peaks)):
        for j in range(len(peaks[i:min(i+15, len(peaks)-1)])):
            j = j+i+1
            if peaks_are_duplicate(peaks[i], peaks[j]):
                peaks[j] = None
                
    #
    return [peak for peak in peaks if peak is not None]


def find_peaks(frequencies, times, magnitude,
                             window_size=10,
                             candidates_per_band=6):

    return find_peaks_windowed(frequencies, times, magnitude, window_size, candidates_per_band)

def find_peaks_windowed(frequencies, times, magnitude,
                             window_size=10,
                             candidates_per_band=6):
    """
    find the peaks in the spectrum using a sliding window

    within each window spanning the entire frequency range, find the local maxima within sub tiles of the window, then select `peaks_per_window` peaks across all local maxima

    this helps avoid peaks from being clustered too close together

    use `sub_tile_height=None` to just extract top `peaks_per_window` peaks per window across the audio
    """
    constellation_map = []
        
    # Attempt 3: sliding window across time, extract top peaks from each window after
    #            computing local maxima within frequency bands
    num_freq_bins, num_time_bins = magnitude.shape
    constellation_map = []

    
    # TODO: create frequency bands based on logarithmic scale. Assume fft_window_size = 1024
    # Hint: start from 0-40Hz
    bands = None

    # slide a window across time axis
    # height: entire frequency range
    # width:  window_size
    for t_start in range(0, num_time_bins, window_size):
        
        # TODO: Get the window of frequencies we want to work with
        window = None

        peak_candidates = []


        # TODO: Find local maxima within the frequency bands of each window
        for f_start, f_end in bands:
            # TODO: Get the frequency band for this window
            freq_square = None

            # TODO: Find the indices of the top `candidates_per_band` peaks in the freq_square
            # Hint: Flatten the 2D freq_square to 1D using np.argpartition
            flat_indices = None

            # 
            for idx in flat_indices:
                # TODO: calculate the original time and frequency indices from the flattened candidate indices
                # Hint: use np.unravel_index and .shape of freq_square to go from 1D index to 2D index
                t_idx = None
                f_idx = None
                mag = None
                
                # Append the original time index (t_idx), frequency index (f_idx), and magnitude (mag)
                peak_candidates.append((t_idx, f_idx, mag))

        # Keep top peaks per time window (sorted by magnitude)
        proportion_keep = 0.95
        
        # TODO: Sort the peak candidates by magnitude, descending
        pass
        
        # TODO: Keep the top proportion_keep of peak candidates and 
        # append the time index and frequency to the constellation map
        pass

    # Remove peaks that are too close to each other (treated as duplicates)
    return remove_duplicate_peaks(constellation_map)


def create_constellation_map(audio, sr, hop_length=None) -> list[list[int]]:
    frequencies, times, magnitude = compute_fft(audio, sr, hop_length=hop_length)
    constellation_map = find_peaks(frequencies, times, magnitude)
    return constellation_map


def preprocess_audio(audio_path, sr = 11_025):
    """
    returns `(audio, sr)`

    11025 Hz
    44100 Hz

    Note: using mp3 prevents reading file blob directly
          using BytesIO stream, we have to save it to a
          temp file first (audio_path = BytesIO(...wavfile...)
          does work though)
    """
    # resample to 11 kHz (11,025 Hz)
    # uses a low pass filter to filter the higher frequencies to avoid aliasing (Nyquist-Shannon)
    # then takes sequential samples of size 4 and keeps the first of each ("decimate")
    audio, sr = librosa.load(audio_path, sr=sr)

    ## equivalent to:
    #max_freq_cutoff = 5512 # Hz
    ## Calculate the new sampling rate (at least twice the cutoff frequency)
    #new_sr = max_freq_cutoff * 2
    #new_sr += 1  # = 11025 to match librosa documentation / Chigozirim vid
    ## Resample the audio, which implicitly applies a low-pass filter
    #y_filtered = librosa.resample(y=audio, orig_sr=Fs, target_sr=new_sr, res_type='kaiser_best')

    return audio, sr

def compute_source_hashes(song_ids: list[int] = None, resample_rate: None|int = 11025):
    """
    `song_ids=None` (default) use all song_ids from database

    `resample_rate=None` to use original sampling rate from file

    Assumes all songs are the same sampling rate
    """
    if song_ids is None:
        song_ids = retrieve_song_ids()
    
    for song_id in song_ids:
        print(f"{song_id:03} ================================================")
        song = retrieve_song(song_id)
        print(f"{song['title']} by {song['artist']}")
        duration_s = song["duration_s"]
        audio_path = song["audio_path"]

        #waveform = song["waveform"]
        #audio_path = "temp_audio.mp3"
        #with open(audio_path, 'wb') as f:
            #f.write(waveform)
        #print(audio_path)

        audio, sr = preprocess_audio(audio_path, sr=resample_rate)
        constellation_map = create_constellation_map(audio, sr)
        hashes = create_hashes(constellation_map, song_id, sr)
        add_hashes(hashes)
    
    create_hash_index()
    return sr

def create_samples(track_info: dict, sr: int = None, n_samples: int = 5, n_seconds: int = 5, seed=1):
    audio, sr = preprocess_audio(track_info["audio_path"], sr)
    samples = []
    window_size = n_seconds * sr
    if len(audio) < window_size:
        raise ValueError(f"{track_info['title']}: could not create samples of length {n_seconds} sec")
    max_start_idx = len(audio) - window_size - 1

    np.random.seed(seed)
    start_indices = np.random.randint(0, max_start_idx, size=n_samples)
    for start_idx in start_indices:
        sample = audio[start_idx:start_idx + window_size]
        samples.append(sample)
    return samples

def add_noise(audio, noise_weight: float = 0.5):

    # BONUS: add noise to a file
    # brownian noise: x(n+1) = x(n) + w(n)
    #                 w(n) = N(0,1)

    #audio, sr = librosa.load(audio_path, sr=None) 
    def peak_normalize(x):
        # Normalize the audio to be within the range [-1, 1]
        return x / np.max(np.abs(x))

    noise = np.random.normal(0, 1, audio.shape[0])
    noise = np.cumsum(noise)
    noise = peak_normalize(noise)

    # 16-bit integer: [-32768, 32767]
    # (2**15 - 1) = 32767
    #scaled = np.int16(peak_normalize(audio_with_noise) * 32767)
    #scipy.io.wavfile.write('audio_with_noise.wav', sr, scaled)
    #ipd.Audio("audio_with_noise.wav")

    audio_with_noise = (audio + noise*noise_weight)
    return peak_normalize(audio_with_noise)


    # YOUR ANSWER HERE

