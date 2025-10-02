import numpy as np
import librosa
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
