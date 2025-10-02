import numpy as np
from scipy import signal

# TODO: Finish this function to compute the hash of two peaks
def create_address(anchor: tuple[int, int], target: tuple[int, int], sr: int) -> int:
    # get relevant information from the anchor and target points
    anchor_freq = anchor[1]
    target_freq = target[1]
    deltaT = target[0] - anchor[0]

    ##############################################
    # Creating a 32 bit hash f1:f2:dt (2002 paper)
    ##############################################

    # MP3 files are downloaded at 48 kHz sampling rate
    # preprocess_audio() resamples to 11 kHz
    # => max frequency is sr/2 = 5512.5
    # (by the Nyquist–Shannon sampling theorem)
    # use a value slightly higher than this
    max_frequency = np.ceil(sr / 2) + 10

    # transform frequencies to fit in 10 bits (0-1023)
    # results in some loss of information (int -> smaller float -> int)
    n_bits = 10
    anchor_freq = (anchor_freq / max_frequency) * (2 ** n_bits)
    target_freq = (target_freq / max_frequency) * (2 ** n_bits)
    
    # bit shifting to obtain 32 bit hash
    # int(anchor_freq)         occupies bits 0-9,    anchor_freq <= 1023
    # int(target_freq) << 10   occupies bits 10-19,  target_freq <= 1023
    # int(deltaT) << 20        occupies bits 20-31,  deltaT <= 4095
    hash = int(anchor_freq) | (int(target_freq) << 10) | (int(deltaT) << 20)
    return hash

def create_hashes(peaks, song_id: int = None, sr: int = None, fanout_t=100, fanout_f=3000):
    """
    fanout:
        specify the fan-out factor used for determining the target zone

        = number of timesteps forward from anchor to use for target points
    """
    fingerprints = {}
    
    # iterate through each anchor point in the constellation map
    for i, anchor in enumerate(peaks):
        # iterate through each point in target zone for that anchor point
        for j in range(i+1, len(peaks)):
            # select targets from a zone in front of the anchor point
            target = peaks[j]
            time_diff = target[0] - anchor[0]
            freq_diff = target[1] - anchor[1]

            # determine if peak is within target zone
            if time_diff <= 1:
                continue
            if np.abs(freq_diff) >= fanout_f:
                continue
            if time_diff > fanout_t:
                # constellation points are sorted by time
                # => no need to check more potential targets
                break
            
            address = create_address(anchor, target, sr)
            anchorT = anchor[0]

            fingerprints[address] = (int(anchorT), song_id)
            
    return fingerprints