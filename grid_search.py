import numpy as np
import pandas as pd
from itertools import product

from cm_visualizations import visualize_map_interactive
from cm_helper import create_samples, add_noise
from DBcontrol import init_db, connect, retrieve_song

from const_map import create_constellation_map
from hasher import create_hashes
from search import score_hashes

from parameters import set_parameters, read_parameters
from pathlib import Path

#
# 1 / 3: list samples to use to evaluate recognition performance
#

microphone_sample_list = [
    ("Plastic Beach (feat. Mick Jones and Paul Simonon)", "Gorillaz", "audio_samples/plastic_beach_microphone_recording.wav"),
    #("DOGTOOTH", "Tyler, The Creator", "tracks/audio/TylerTheCreator_DOGTOOTH_QdkbuXIJHfk.flac")
    # ...
]

microphone_sample_list = [
    {"title": v[0], "artist": v[1], "audio_path": v[2]} 
    for v in microphone_sample_list
    ]

def augment_samples(sr, noise_weight):
    con = connect()
    cur = con.cursor()
    samples = []
    # TODO for members: Write this SQL query
    for sample in microphone_sample_list:
        cur.execute(
            "SELECT id AS song_id "
            "FROM songs "
            "WHERE title LIKE ? "
            "AND artist = ?",
            (sample["title"], sample["artist"])
        )

        res = cur.fetchone()
        if res: 
            song_id = res[0]
        else:
            raise ValueError(f'\'{sample["title"]}\' by \'{sample["artist"]}\' not found.\nSpelling of name/artist might be different from the spelling in tracks/audio/tracks.csv?')
        
        sample_slices = create_samples(sample["audio_path"], sr, n_samples = 20)
        sample_slices_noisy = [add_noise(audio, noise_weight) for audio in sample_slices]
        samples.extend([
            {"song_id": song_id,
             "microphone": s[0],
             #"mic_noisy": s[1]
             } for s in zip(sample_slices, sample_slices_noisy)
        ])
    return samples



#
# 2 / 3: Compute some metrics using output of search.py
#

def std_of_deltaT(song_id, time_pair_bins, sr=11025):
    """
    heuristic that measures the distribution of deltaT values

    results in standard deviation between 0 ms and 1000 ms

    lower is better - suggests that the time offsets are behaving consistently
    """
    time_pair_bin = time_pair_bins[song_id]

    # 1) take the difference in time between sourceT and sampleT
    #    values represent the offset suggested by the presence of the 
    # respective hash match
    # ex: offset = 40
    # data might look like [-4, 5, 8, 40, 40, 40, ..., 40, 40, 40, 56, 68, 80]
    deltaT_vals = sorted([sourceT-sampleT for (sourceT, sampleT) in time_pair_bin])

    #    Potential idea: then, take the difference between adjacent deltaT values
    #    removes influence of offset / outlier offset values
    #    values are close to zero for consistent time offsets
    # ex: [9, 3, 0, 0, 0, ..., 0, 0, 16, 12, 12]
    #second_order_differences = [deltaT_vals[i] - deltaT_vals[i-1] 
                                #for i in range(1, len(deltaT_vals))]
    # not doing this step makes the metric more interpretable
                                

    # 3) compute the standard deviation of these differences, measured in seconds
    #    return a metric between 0 and 1000
    #    (stddev between 0 and 1000 milliseconds, 0 and 1 seconds)
    #
    # T is in units of STFT bins, 
    # multiply by 1000*(hop_length / sr) to get in units of milliseconds
    #
    # Unit conversion:
    # bins * ((n_samples_to_jump/bin) / (samples/second)) = bins * (seconds / bin) = seconds
    # seconds * (1000 ms / second) = milliseconds
    # std(x * v) = x * std(v)
    hop_length = 1024 // 2  # sidenote: not 1024 + (1024 // 2) as in cm_helper.py

    return min(np.std(deltaT_vals) * (hop_length/sr), 1000)


def count_hash_matches(song_id, time_pair_bins, n_sample_hashes):
    """
    naive heuristic that counts the number of hash matches between sample and source
    
    note: there can be repeated matches for a single hash value present in sample

    higher is better - suggests that many hashes show up in both sample and source
    """
    n_matches = len(time_pair_bins[song_id]) 
    return n_matches


def compute_performance_metrics(song_id, time_pair_bins, n_sample_hashes, sr=11025):
    """
    given the output from search.py:score_hashes(), computes metrics that
    evaluate how close a given song_id matches the sample audio

    returns a dictionary containing metrics

    ## Metrics:
     
    - `std_of_deltaT`: less is better, (0-1000 ms)
    - `n_hash_matches`: more is better
    - `prop_hash_matches`: `min(cout_hash_matches / n_sample_hashes, 1)
    
    """
    metrics = {
        "std_of_deltaT": std_of_deltaT(song_id, time_pair_bins, sr),
        "n_hash_matches": count_hash_matches(song_id, time_pair_bins, n_sample_hashes),
        "n_sample_hashes": n_sample_hashes
    }
    metrics["prop_hash_matches"] = min(metrics["n_hash_matches"] / metrics["n_sample_hashes"], 1)
    return metrics




def perform_recognition_test(n_songs=None):
    """
    returns a tuple:
    `(n_correct / n_samples, performance results for each sample)`

    first value is the proportion of correct recognitions

    samples specified based on slicing of samples in `microphone_sample_list`
    using `grid_search.py:augment_samples()`
    """
    #init_db()
    sr = 11025
    init_db(n_songs=n_songs)
    results = []
    samples = augment_samples(sr=sr, noise_weight=0.3)
    for sample in samples:
        result = {}
        ground_truth_song_id = sample["song_id"]

        # peaks -> hashes
        constellation_map = create_constellation_map(sample["microphone"], sr=sr)
        hashes = create_hashes(constellation_map, None, sr)

        # hashes -> metrics
        scores, time_pair_bins = score_hashes(hashes)
        n_sample_hashes = len(hashes)
        n_potential_matches = min(len(scores), 5)
        metrics_per_potential_match = {}
        for potential_song_id, potential_score in scores[:n_potential_matches]:
            metrics_per_potential_match[potential_song_id] = compute_performance_metrics(
                potential_song_id, time_pair_bins, n_sample_hashes, sr
            )
            metrics_per_potential_match[potential_song_id]["histogram_max_height"] = potential_score
        

        # store metrics for each sample
        result = {
            "ground_truth": ground_truth_song_id,
            "prediction": scores[0][0],
            "correct": ground_truth_song_id == scores[0][0],
            "metrics": metrics_per_potential_match,
            "microphone_audio": sample["microphone"]
        }

        results.append(result)

    return sum(r["correct"] for r in results) / len(samples), results

def run_grid_search(n_songs=None):
    max_proportion_correct = 0
    max_params = 0
    max_results = {}
    proportion_correct = 0
    results = {}

    grid_cmws = [4,5,10]
    grid_cpb = [5,7]
    grid_bands = [[(0,20), (20, 40), (40,80), (80,160), (160, 320), (320,512)]]

    for (
        cm_window_size, candidates_per_band, bands
        ) in list(product(grid_cmws, grid_cpb, grid_bands)):
        parameters = {
            "cm_window_size": cm_window_size,
            "candidates_per_band": candidates_per_band,
            "bands": bands
            # ...
        }

        # unspecified parameters are set to their defaults
        #
        # **dict notation:
        # converts {"key1": value1, "key2": value2}
        #          -> key1=value1, key2=value2
        set_parameters(**parameters)
        proportion_correct, results = perform_recognition_test(n_songs)
        if proportion_correct > max_proportion_correct:
            max_proportion_correct = proportion_correct
            max_params = read_parameters("all_parameters")
            max_results = results

    return max_results, max_params
    


if __name__ == "__main__":
    max_results, max_params = run_grid_search(n_songs=2)
    print("=============")
    print("max parameters:")
    print("=============")

    print(max_params)

    print("=============")
    print("results:")
    print("=============")

    #print(max_results)
    max_results_df = pd.DataFrame(max_results)
    max_results_df.to_pickle("max_results.pkl")
    print("saved results to pkl file")

    plastic_beach = retrieve_song(1)["audio_path"]
    visualize_map_interactive(plastic_beach)