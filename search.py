import numpy as np
import os
from collections import defaultdict

from hasher import create_hashes
from cm_helper import preprocess_audio
from const_map import create_constellation_map
from DBcontrol import connect, retrieve_hashes

def score_hashes(hashes: dict[int, tuple[int, int]]) -> tuple[list[tuple[int, int]], dict[int, set[int, int]]]:
    """
    returns two values:

    ```
    result[0]: [(top_song_id, top_song_score), (2nd_song_id, 2nd_song_score, ...)]  # sorted
    result[1]: {song_id_1: {(sourceT, sampleT), (sourceT, sampleT), ...}, ...}
    ```
    
    """
    con = connect()
    cur = con.cursor()

    # An Industrial-Strength Audio Search Algorithm
    # 2.3: Searching and Scoring
    
    # Each hash from the sample is used to search in the 
    # database for matching hashes

    # For each matching hash found in the database, the
    # corresponding offset times from the beginning of the
    # sample and database files are associated into time pairs.

    # The time pairs are distributed into bins according to the 
    # track ID associated with the matching database hash

    # TODO: Implement the steps above, storing source and sample time pairs in a 
    # bin (dictionary) for each song.

    time_pair_bins = defaultdict(set)
    
    for address, (sampleT, _) in hashes.items():
        
        # Hint: This line retrieves matchin hashes froom the database in the format
        # (hash_val, time_stamp, song_id)
        matching_hashes = retrieve_hashes(address, cur)
        
        # TODO: Finish the loop by adding (sourceT, sampleT) pairs to the appropriate bin
            
    # After all sample hashes have been used to search in the
    # database to form matching time pairs, the bins are scanned
    # for matches. 

    #################################################
    # Histogram Method for scanning for matches     #
    # (detecting diagonal line within scatterplot)  #
    #################################################

    # Within each bin, the set of time pairs represents
    # a scatter plot of association between the sample and database
    # sound files.

    # If the files match, matching features should occur at similar
    # relative offsets from the beginning of the file, i.e. a sequence
    # of hashes in one file should also occur in the matching file with
    # the same relative time sequence.

    # The problem of deciding whether a match has been found reduces to
    # detecting a significant cluster of points forming a diagonal line
    # within the scatterplot.

    # Assume that the slope of the diagonal line is 1.0

    # Then corresponding times of matching features between matching
    # files have the relationship:
    # sourceT = sampleT + offset
    # => offset = sourceT - sampleT

    scores = {}
    for song_id, time_pair_bin in time_pair_bins.items():
        # For each (sourceT, sampleT) coordinate in the scatterplot,
        # we calculate:
        # deltaT = sourceT - sampleT
        deltaT_values = [sourceT - sampleT for (sourceT, sampleT) in time_pair_bin]

        # Then we calculate a histogram of these deltaT values
        # and scan for a peak.
        #hist = defaultdict(lambda: 0)
        #for dT in deltaT_values:
            #hist[dT] += 1
        hist, bin_edges = np.histogram(deltaT_values, bins=max(len(np.unique(deltaT_values)), 10))

        # The score of the match is the number of matching points
        # in the histogram peak
        #scores[song_id] = max(hist.values()) if hist else 0
        scores[song_id] = hist.max()

    scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    con.close()
    return scores, time_pair_bins


def recognize_music(sample_audio_path: str, sr: None|int = None, remove_sample: bool = True) -> list[tuple[int, int]]:
    """
    returns sorted list of `(song_id, score)` tuples, access top prediction with `scores[0][0]`

    ```
    # add songs to db
    DBcontrol.add_songs(...)

    # record from microphone
    sample_audio_path = "audio_samples/pb_recording_short.wav"

    # correct recognition if song_id 
    # corresponds to Gorillaz - Plastic Beach
    song_id = recognize_music(sample_audio_path)[0][0]
    ```
    """
    sample, sr = preprocess_audio(sample_audio_path, sr=sr)
    # if remove_sample:
    #     os.remove(sample_audio_path)
    constellation_map = create_constellation_map(sample, sr)
    hashes = create_hashes(constellation_map, None, sr)
    scores, time_pair_bins = score_hashes(hashes)
    return scores, time_pair_bins