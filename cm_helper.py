import numpy as np
from scipy import signal

def compute_fft(audio, sr, n_fft: int = None, hop_length: int = None):
    """
    compute a fast fourier transform on the audio data to get the frequency spectrum

    turns raw audio data into a "spectrogram"

    n_fft (int): FFT size; number of samples used to calculate each FFT

    hop_length (int): number of samples the window slides over each time (step size)
    
    """
    if n_fft is None:
        #window_len_s = 0.5
        #window_samples = int(window_len_s * sr)
        fft_window_size = 1024
    else:
        fft_window_size=n_fft

    if hop_length is None:
        hop_length = fft_window_size + (fft_window_size // 2)

    
    ##########################
    # params of signal.stft():
    ##########################
    # window: used to avoid the spread of strong true frequencies to their neighbors
    # https://en.wikipedia.org/wiki/Spectral_leakage
    # https://dsp.stackexchange.com/questions/63405/spectral-leakage-in-laymans-terms
    # signal.windows.hann  # default
    # signal.windows.hamming
    #https://docs.scipy.org/doc/scipy/tutorial/signal.html#comparison-with-legacy-implementation
    ##########################

    # fft is used for its O(nlog(n)) time complexity, vs dft's O(n^2) complexity
    # TODO: this could be done manually for understanding, then later on in the project
    #       signal.stft could be introduced for speed and versatility
    frequencies, times, stft = signal.stft(audio, fs=sr, 
                                           window="hamming",
                                           nperseg=fft_window_size,
                                           noverlap=fft_window_size - hop_length,
                                           padded=True,
                                           return_onesided=True
                                           #noverlap=window_size // 2,
                                           )


    # stft is a 2D complex array of shape (len(frequencies), len(times))
    # complex values of stft encode amplitude and phase offset of each sine wave component
    # We're interested in just the magnitude / strength of the frequency components
    # (phase offset information is useful though for time-stretching/pitch-shifting, or 
    # reconstructing signal via inverse STFT)
    magnitude = np.abs(stft)

    # frequencies is an array of frequency bin centers (in Hz)
    # times is an array of time bin centers (in seconds)
    # magnitude is a 2D real array of shape (len(frequencies), len(times))
    #           that for each time step gives a spectrum: an array of frequency bins
    return frequencies, times, magnitude
