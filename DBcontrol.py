import os
from xmlrpc import server

import sqlite3
import librosa
import glob
import pandas as pd
import platform
import zipfile
from pathlib import Path

from dotenv import load_dotenv


db_name = "shazamesque"

def connect():
    con = sqlite3.connect(db_name)
    return con


def create_hash_index():
    with connect() as con:
        cur = con.cursor()
        #cur.execute("CREATE INDEX IF NOT EXISTS idx_hash_val ON hashes(hash_val);")
        cur.execute("ALTER TABLE hashes ADD INDEX (hash_val);")
        con.commit()

def add_song(track_data: dict) -> str:
    """
    track_data = {
        "youtube_url": https://youtube.com/watch?v=video_id
        "title": name of track, or youtube video title
        "artist": name of artist, or youtube video author
        "artwork_url": url to spotify album art, or youtube thumbnail
        "audio_path": local path to mp3 file
    }

    returns corresponding song id via SELECT last_insert_rowid();
    """

    #https://img.youtube.com/vi/_r-nPqWGG6c/0.jpg


    with connect() as con:
        cur = con.cursor()

        audio_path = track_data["audio_path"]
        duration_s = librosa.get_duration(path=audio_path)


        try:
            cur.execute("""
                INSERT INTO songs 
                        (youtube_url, title, artist, artwork_url, audio_path, duration_s)
                        VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    track_data["youtube_url"],
                    track_data["title"],
                    track_data["artist"],
                    track_data["artwork_url"],
                    track_data["audio_path"],
                    duration_s,
                )
            )
            con.commit()
        except sqlite3.IntegrityError:
            cur.execute("""
            SELECT id FROM songs WHERE youtube_url = %s
                        """, (track_data["youtube_url"],))
            song_id = cur.fetchone()[0]
            return song_id
        # sqlite:
        #cur.execute("SELECT last_insert_rowid()")
        cur.execute("SELECT last_insert_id()")
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
        df = pd.read_sql_query("SELECT * FROM songs WHERE id = %s", con, params=(song_id,))
        if df.empty:
            return None
        row = df.iloc[0].to_dict()
        return row

def retrieve_song_id(youtube_url: str) -> int:
    with connect() as con:
        cur = con.cursor()
        cur.execute("SELECT id FROM songs WHERE youtube_url = %s", (youtube_url,))
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
      
def add_hash(hash_val: int, time_stamp: float, song_id: int, cur: "mysqlcursor") -> None:
    cur.execute("""INSERT INTO hashes 
                    (hash_val, time_stamp, song_id) 
                    VALUES (%s, %s, %s)""", 
                    (hash_val, time_stamp, song_id))
    
def add_hashes(hashes: dict[int, tuple[int, int]]):
    with connect() as con:
        cur = con.cursor()
        for address, (anchorT, song_id) in hashes.items():
            add_hash(address, anchorT, song_id, cur)
        con.commit()

def retrieve_hashes(hash_val: int, cursor) -> tuple[int, int, int]|None:
    cursor.execute("SELECT hash_val, time_stamp, song_id FROM hashes WHERE hash_val = %s", (hash_val,))
    result = cursor.fetchall()
    return result

def create_tables():
    # if system == "Darwin" or system == "Linux":
    #     con = mysql.connector.connect(
    #         host="localhost",
    #         user="root",
    #         password="password"
    #     )
    # else:
    #     #load_dotenv(dotenv_path='/home/evanteal15/F25-Shazam-Clone/env/.env')
        
    #     #server = 'tcp:shazesq.database.windows.net,1433'
    #     #database = 'shazamesque'
    #     #username = os.getenv('USER_NAME')
    #     #password = os.getenv('THE_PASSWORD')
    #     #driver = '{ODBC Driver 18 for SQL Server}'
    #     #connection_string = f"DRIVER={driver};SERVER={server};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    #     ## Driver={ODBC Driver 18 for SQL Server};Server=tcp:shazesq.database.windows.net,1433;Database=shazamesque;Uid=CloudSAce2ffd30;Pwd={your_password_here};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
    #     #con = pyodbc.connect(connection_string)
    #     print("========================================================")
    #     print("Windows: `CREATE DATABASE shazamesque;` and run sql/schema.sql manually")
    #     raise OSError
    
    

    cur = con.cursor()
    with open("sql/schema.sql", "r") as f:
        schema_sql = f.read()

    try:
        cur.execute(f"CREATE DATABASE {db_name};")
        con.commit()
    except mysql.connector.errors.DatabaseError:
        # db exists
        pass
    try:
        cur.execute(f"USE {db_name};")
        cur.execute(schema_sql)
    except mysql.connector.errors.ProgrammingError:
        # tables exist
        pass

    con.close()

