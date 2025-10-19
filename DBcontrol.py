import os

import sqlite3
import librosa
import pandas as pd
from pathlib import Path
from dataloader import load

from cm_helper import preprocess_audio
from hasher import create_hashes
from const_map import create_constellation_map



library = "sql/library.db"

def connect() -> tuple[sqlite3.Connection]:
    con = sqlite3.connect(library)
    return con

def create_hash_index():
    with connect() as con:
        cur = con.cursor()
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hash_val ON hashes(hash_val)")
        con.commit()

def add_song(track_info: dict) -> str:
    """
    track_info = {
        "youtube_url": https://youtube.com/watch?v=video_id
        "title": name of track, or youtube video title
        "artist": name of artist, or youtube video author
        "artwork_url": url to spotify album art, or youtube thumbnail
        "audio_path": local path to mp3 file
    }

    returns corresponding song id via SELECT last_insert_rowid();
    """


    with connect() as con:
        cur = con.cursor()

        audio_path = track_info["audio_path"]
        duration_s = librosa.get_duration(path=audio_path)


        try:
            cur.execute("""
                INSERT INTO songs 
                        (youtube_url, title, artist, artwork_url, audio_path, duration_s)
                        VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    track_info["youtube_url"],
                    track_info["title"],
                    track_info["artist"],
                    track_info["artwork_url"],
                    track_info["audio_path"],
                    duration_s,
                )
            )
            con.commit()
        except sqlite3.IntegrityError:
            cur.execute("""
            SELECT id FROM songs WHERE youtube_url = ?
                        """, (track_info["youtube_url"],))
            song_id = cur.fetchone()[0]
            return song_id
        # sqlite:
        cur.execute("SELECT last_insert_rowid()")
        song_id = cur.fetchone()[0]
        return song_id


def add_songs(audio_directory: str = "./tracks", n_songs: int = None, specific_songs: list[str] = None) -> None:
    
    tracks_info = load(audio_directory)
    print(tracks_info)

    if n_songs is not None:
        tracks_info = tracks_info[:min(n_songs, len(tracks_info))]

    print(tracks_info)
    for track_info in tracks_info:
        print("Adding:", track_info["title"])
        if specific_songs is not None: 
            if track_info["title"] in specific_songs:
                add_song(track_info)
        else:
            add_song(track_info)

def retrieve_song(song_id) -> dict|None:
    with connect() as con:
        df = pd.read_sql_query("SELECT * FROM songs WHERE id = ?", con, params=(song_id,))
        if df.empty:
            return None
        row = df.iloc[0].to_dict()
        return row

def retrieve_song_id(youtube_url: str) -> int:
    with connect() as con:
        cur = con.cursor()
        cur.execute("SELECT id FROM songs WHERE youtube_url = ?", (youtube_url,))
        song_id = cur.fetchone()[0]
        try:
            return int(song_id)
        except:
            return None

    
def retrieve_song_ids() -> list[int]:
    with connect() as con:
        cur = con.cursor()
        cur.execute("SELECT id FROM songs ORDER BY id ASC")
        ids = [row[0] for row in cur.fetchall()]
    return ids
      
def add_hash(hash_val: int, time_stamp: float, song_id: int, cur: sqlite3.Cursor) -> None:
    """
    uses a db cursor for efficiency 
    (avoid creating new cursor repeatedly over many queries)
    ```
    con = DBcontrol.connect()
    cur = con.cursor()
    add_hash(hash_val, time_stamp, song_id, cur)
    ```
    """
    cur.execute("""INSERT INTO hashes 
                    (hash_val, time_stamp, song_id) 
                    VALUES (?, ?, ?)""", 
                    (hash_val, time_stamp, song_id))
    
def add_hashes(hashes: dict[int, tuple[int, int]]):
    """
    uses a db cursor for efficiency 
    (avoid creating new cursor repeatedly over many queries)
    ```
    con = DBcontrol.connect()
    cur = con.cursor()
    add_hash(hash_val, time_stamp, song_id, cur)
    ```
    """
    with connect() as con:
        cur = con.cursor()
        for address, (anchorT, song_id) in hashes.items():
            add_hash(address, anchorT, song_id, cur)
        con.commit()

def retrieve_hashes(hash_val: int, cursor: sqlite3.Cursor) -> tuple[int, int, int]|None:
    """
    returns list of (hash_val, time_stamp, song_id) tuples matching given hash_val
    
    Input: hash_val: hash value we are searching for
    
    Output: list of (hash_val, time_stamp, song_id) tuples
    
    """
    cursor.execute("SELECT hash_val, time_stamp, song_id FROM hashes WHERE hash_val = ?", (hash_val,))
    result = cursor.fetchall()
    return result


def create_tables():
    """
    Creates necessary tables in the database
    """
    if os.path.exists(library):
        os.remove(library)
    with sqlite3.connect(library) as con:
        cur = con.cursor()
        with open("sql/schema.sql", "r") as f:
            schema_sql = f.read()
        cur.executescript(schema_sql)
        con.commit()
        
def init_db(tracks_dir: str = None, n_songs: int = None, specific_songs: list[str] = None):
    """
    tracks_dir:
        Path to the audio dataset downloaded by `musicdl`. 
        Default is to look for a folder or zip archive matching the pattern "`tracks*`"
    n_songs:
        Take a sample from the top of the tracks dataset. Default is to read all songs

    """
    create_tables()
    add_songs("./tracks", n_songs, specific_songs)
    compute_source_hashes()

def compute_source_hashes(song_ids: list[int] = None, resample_rate: None|int = 11025):
    """
    `song_ids=None` (default) use all song_ids from database

    `resample_rate=None` to use original sampling rate from file

    Assumes all songs are the same sampling rate
    """
    if song_ids is None:
        song_ids = retrieve_song_ids()
    
    for song_id in song_ids:
        print(f"{song_id:03} ================================================")
        song = retrieve_song(song_id)
        print(f"{song['title']} by {song['artist']}")
        #duration_s = song["duration_s"]
        audio_path = song["audio_path"]

        #waveform = song["waveform"]
        #audio_path = "temp_audio.mp3"
        #with open(audio_path, 'wb') as f:
            #f.write(waveform)
        #print(audio_path)

        audio, sr = preprocess_audio(audio_path, sr=resample_rate)
        constellation_map = create_constellation_map(audio, sr)
        hashes = create_hashes(constellation_map, song_id, sr)
        add_hashes(hashes)
    
    create_hash_index()
    return
