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
    for index, peak in enumerate(peaksc):
        i = 0
        size = min(15, len(peaksc) - index - 1)
        while (i < size):
            #i goes from 0 to 14
            if (peaks_are_duplicate(peaksc[index], peaks[index + i + 1])):
                peaksc[index + i + 1] = None
            i += 1

    return [peak for peak in peaksc if peak is not None]


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
    bands = [(0, 10), (10, 20), (20, 40), (40, 80), (80, 160), (160, 512)]
    #bands = [(0, 40), (40, 80), (80, 160), (160, 240), (240, 512)]

    # slide a window across time axis
    # height: entire frequency range
    # width:  window_size
    for t_start in range(0, num_time_bins, window_size):
        # TODO: Get the window of frequencies we want to work with
        t_end = min(t_start + window_size, num_time_bins)
        window_mag = magnitude[:, t_start:t_end]

        peak_candidates = []

        # TODO: Find local maxima within the frequency bands of each window
        for f_start, f_end in bands:
            # TODO: Get the frequency band for this window
            freq_square = window_mag[f_start:f_end,:]

            # TODO: Find the indices of the top `candidates_per_band` peaks in the freq_square
            # Hint: Flatten the 2D freq_square to 1D using np.argpartition
            #np.ravel(freq_square)
            flat_indices = np.argpartition(freq_square.ravel(), -candidates_per_band) #len(freq_square)

            # 
            for idx in flat_indices[-candidates_per_band:]:
                # TODO: calculate the original time and frequency indices from the flattened candidate indices
                # Hint: use np.unravel_index and .shape of freq_square to go from 1D index to 2D index
                f_local, t_local = np.unravel_index(idx, freq_square.shape)
                f_idx = f_start + f_local
                t_idx = t_start + t_local
                mag = magnitude[f_idx, t_idx]
                
                # Append the original time index (t_idx), frequency index (f_idx), and magnitude (mag)
                peak_candidates.append((t_idx, f_idx, mag))

        # Keep top peaks per time window (sorted by magnitude)
        proportion_keep = 0.95
        
        # TODO: Sort the peak candidates by magnitude, descending
        peak_candidates.sort(key=lambda x: x[2], reverse=True)
        
        # TODO: Keep the top proportion_keep of peak candidates and 
        # append the time index and frequency to the constellation map
        stell_cutoff = proportion_keep * len(peak_candidates)

        for star in range(int(stell_cutoff)):
            #extract freq and the time before appending
            frequency = frequencies[peak_candidates[star][1]]
            time = peak_candidates[star][0]
            constellation_map.append((time, frequency))

    # Remove peaks that are too close to each other (treated as duplicates)
    return remove_duplicate_peaks(constellation_map)


def create_constellation_map(audio, sr, hop_length=None) -> list[list[int]]:
    frequencies, times, magnitude = compute_stft(audio, sr, hop_length=hop_length)
    constellation_map = find_peaks(frequencies, times, magnitude)
    return constellation_map