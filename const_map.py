import numpy as np

from cm_helper import compute_stft

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
    peaksc=peaks.copy()
    
    # TODO: sort peaks by time
    peaksc.sort(key=lambda x: x[0])

    # TODO: for each peak, search for duplicates within the next 15 peaks (ordered by time)
    for i in range(len(peaks)):
        for j in range(len(peaks[i:min(i+15, len(peaks)-1)])):
            j = j+i+1
            if peaks_are_duplicate(peaks[i], peaks[j]):
                peaks[j] = None
    return [peak for peak in peaks if peak is not None]
            
    # return unique_peaks


def find_peaks(frequencies, times, magnitude,
                             window_size=10,
                             candidates_per_band=6):

    return find_peaks_windowed(frequencies, times, magnitude, window_size, candidates_per_band)

def find_peaks_windowed(frequencies, times, magnitude,
                             window_size=10,
                             candidates_per_band=6):
    """
    find the peaks in the spectrum using a sliding window

    within each window spanning the entire frequency range, find the local maxima within sub tiles of the window, with sub tile height defined by a list of `bands`

    windowing across both frequency and time is used since low frequencies are amplified (equal-loudness contour), and different track sections (bridge, chorus, ..) have different average intensities;
    we don't want areas of the spectrogram with 'high activity' to have all of the peaks while neglecting areas with low but still important activity.

    deduplication and "proportion_keep" are just extras to help avoid peaks from being clustered too close together
    """
    constellation_map = []
        
    # sliding window across time, extract top peaks from each window after
    # computing local maxima within frequency bands
    num_freq_bins, num_time_bins = magnitude.shape
    constellation_map = []

    # assuming fft_window_size = 1024
    #bands = [(0, 512)]
    #bands = [(0, 40), (40, 80), (80, 160), (160, 240), (240, 512)]
    bands = [(0, 10), (10, 20), (20, 40), (40, 80), (80, 160), (160, 512)]
    #bands = [(0, 30), (30, 60), (60, 90), (90, 120), (120, 160), (160, 330), (330, 512)]

    # slide a window across time axis
    # height: entire frequency range
    # width:  window_size
    for t_start in range(0, num_time_bins, window_size):
        t_end = min(t_start + window_size, num_time_bins)
        window = magnitude[:, t_start:t_end]

        peak_candidates = []

        # find local maxima within bands of the window
        # height: variable based on current band
        # width:  window_size
        #for f_start in range(0, num_freq_bins, sub_tile_height):
            #f_end = min(f_start + sub_tile_height, num_freq_bins)
        for f_start, f_end in bands:
            sub_tile = window[f_start:f_end, :]

            # Flatten and get indices of top candidates in this frequency band
            flat_indices = np.argpartition(sub_tile.ravel(), -candidates_per_band)[-candidates_per_band:]

            for idx in flat_indices:
                f_local, t_local = np.unravel_index(idx, sub_tile.shape)
                f_idx = f_start + f_local
                t_idx = t_start + t_local
                mag = magnitude[f_idx, t_idx]
                peak_candidates.append((t_idx, f_idx, mag))

        # Keep top peaks per time window (sorted by magnitude)
        proportion_keep = 0.95
        peak_candidates.sort(key=lambda x: x[2], reverse=True)
        for t_idx, f_idx, _ in peak_candidates[0:int(np.floor(proportion_keep*len(peak_candidates)))]:
            freq = frequencies[f_idx]
            peak = (t_idx, freq)
            constellation_map.append(peak)

    return remove_duplicate_peaks(constellation_map)


def create_constellation_map(audio, sr, hop_length=None) -> list[list[int]]:
    frequencies, times, magnitude = compute_stft(audio, sr, hop_length=hop_length)
    constellation_map = find_peaks(frequencies, times, magnitude)
    return constellation_map
