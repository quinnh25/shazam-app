import os

import sqlite3
import librosa
import glob
import pandas as pd
import platform
import zipfile
from pathlib import Path

from dotenv import load_dotenv


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
    if n_songs == 0:
        return
    
        
    df = pd.read_csv(os.path.join(audio_directory, "tracks.csv"))
    # set audio_path to a relative path originating from current directory
    df["audio_path"] = df["audio_path"].apply(lambda x: str(Path(audio_directory)/x))

    if n_songs is not None:
        df = df.head(n_songs)

    for row in df.to_dict(orient="records"):
        if specific_songs is not None: 
            if row["title"] in specific_songs:
                add_song(row)
        else:
            add_song(row)

def retrieve_song(song_id) -> dict|None:
    with connect() as con:
        # TODO SQLAlchemy error (consider using SQLAlchemy) - just do a normal cur.fetchall()
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
    cursor.execute("SELECT hash_val, time_stamp, song_id FROM hashes WHERE hash_val = ?", (hash_val,))
    result = cursor.fetchall()
    return result

def create_tables():
    if os.path.exists(library):
        os.remove(library)
    with sqlite3.connect(library) as con:
        cur = con.cursor()
        with open("sql/schema.sql", "r") as f:
            schema_sql = f.read()
        cur.executescript(schema_sql)
        con.commit()

