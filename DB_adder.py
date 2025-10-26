from DBcontrol import connect
import sqlite3
import pandas as pd
from cm_helper import preprocess_audio
from hasher import create_hashes
from const_map import create_constellation_map
import librosa

# TODO: Implement this function to check if a song with the given YouTube URL already exists in the database
def check_if_song_exists(youtube_url: str) -> bool:
    with connect() as con:
        cur = con.cursor()
        
        # TODO: Write a SQL query to count how many songs have the given YouTube URL
        query = None
        cur.execute(query, (youtube_url,))
        count = cur.fetchone()[0]
        return count > 0
    
def add_song(track_info: dict, resample_rate: None|int = 11025) -> int:
    with connect() as con:
        cur = con.cursor()

        # get the duration of the audio file
        audio_path = track_info["audio_path"]
        duration_s = librosa.get_duration(path=audio_path)
        
        # TODO: Insert the song metadata into the songs table
        query = None
        data = None
        cur.execute(query, data)
        con.commit()

        # select the last inserted song id
        cur.execute("SELECT last_insert_rowid()")
        song_id = cur.fetchone()[0]
        
        # get the hashes for this song
        audio, sr = preprocess_audio(track_info["audio_path"], sr=resample_rate)
        constellation_map = create_constellation_map(audio, sr)
        hashes = create_hashes(constellation_map, song_id, sr)
        
        # TODO: Insert the hashes into the fingerprints table
        # HINT: can use the same query string 
        #       as DBcontrol.py:add_hash()
        for address, (anchorT, song_id) in hashes.items():
            query = None
            data = None
            cur.execute(query, data)
        con.commit()
        
        return song_id
        