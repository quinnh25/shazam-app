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

    #######################################################################
    # Week 5: October 26th
    # Visualize parameters of recognition model
    # insert after fig.write_html("my_spectrogram.html")

    from parameters import read_parameters
    parameters = read_parameters("all_parameters")
    cm_window_size = parameters["constellation_mapping"]["cm_window_size"]
    fanout_t = parameters["hashing"]["fanout_t"]
    fanout_f = parameters["hashing"]["fanout_f"]
    bands = parameters["constellation_mapping"]["bands"]

    # draw cm window (vertically spanning rectangle)
    fig.add_vrect(x0=0, x1=cm_window_size, line={"color":"white"})

    # draw frequency bands within cm window
    for (b0, b1) in bands:
        fig.add_shape(type="line", x0=0, x1=cm_window_size,
                      y0=frequencies[b1], y1=frequencies[b1], line={"color":"white"})
    
    # draw fan-out factor visualization
    idx = 0
    for i, (t,f) in enumerate(constellation_map):
        # pick a peak after the cm window overlay
        # somewhere in the upper 2/3rds of the frequency range
        if times[t] > cm_window_size + 5 and f >= frequencies[len(frequencies) // 3]:
            idx = i
            break

    # draw lines between anchor point and target points
    # target points are green squares
    peak_anchor = constellation_map[idx]

    # draw target zone
    fig.add_shape(type="rect",
        x0=times[peak_anchor[0] + 1], x1=times[peak_anchor[0] + fanout_t],
        y0=peak_anchor[1] - fanout_f, y1=peak_anchor[1] + fanout_f,
        line=dict(
            color="#39FF14",
            width=3,), 
        showlegend=False)

    # highlight anchor point
    fig.add_scatter(x=(times[peak_anchor[0]],), y=(peak_anchor[1],),
                    marker={"size": 20, "color": "#39FF14", "symbol":"square-open"},
                    showlegend=False)
    
    target_zone_peaks = [(times[peak_target[0]], peak_target[1])
                            for peak_target in constellation_map#[idx+1:] 
                            if (peak_target[0] - peak_anchor[0]) > 1
                            and (peak_target[0] - peak_anchor[0]) < fanout_t
                            and (np.abs(peak_target[1] - peak_anchor[1]) < fanout_f)
                            and (peak_anchor[0] < peak_target[0])]

    for peak_target in target_zone_peaks:
        # draw a line between anchor and target
        fig.add_shape(type="line",
                      x0=times[peak_anchor[0]], x1 = peak_target[0],
                      y0=peak_anchor[1], y1 = peak_target[1], 
                      line=dict(
                          color="#39FF14",
                          width=0.5,),
                      showlegend=False)

        # replace white squares with green squares for target peaks
        fig.add_scatter(x=(peak_target[0],), y=(peak_target[1],),
                        mode='markers',
                        marker={"size": 7, "color": "#39FF14", "symbol":"square-open"},
                        showlegend=False)

    fig.write_html("parameters.html")
    #######################################################################

    
if __name__ == "__main__":
    
    # TODO: replace the path below with an audio file from audio samples folder
    audio_path = "audio_samples/pb_recording_short.wav"
    visualize_map_interactive(audio_path)