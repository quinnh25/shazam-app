import numpy as np
import plotly.graph_objects as go

from cm_helper import compute_stft, preprocess_audio
from const_map import find_peaks


def convert_to_decibel(magnitude: np.array):
    """
    returns spectrogram's amplitude at each freq/time bin, measured in dB
    """
    return 20*np.log10(magnitude + 1e-6)

def visualize_map_interactive(audio_path):
    audio, sr = preprocess_audio(audio_path)
    frequencies, times, magnitudes = compute_stft(audio, sr)
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

    # fig.show()
    
    # This line is needed to save the interactive plot as an HTML file when working on WSL
    # Use this command in the terminal to open:  explorer.exe my_spectrogram.html
    fig.write_html("my_spectrogram.html")
    
if __name__ == "__main__":
    
    # TODO: replace the path below with an audio file from audio samples folder
    audio_path = "audio_samples/pb_recording_short.wav"
    visualize_map_interactive(audio_path)