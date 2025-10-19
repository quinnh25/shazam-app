import os
from search import search_song_in_db


def initialise_db(db_path: str = "sql/library.db"):
    """
    Initialise the database connection

    If the database does not exist at `db_path`, create it
    """
    if not os.path.exists(db_path):
        from DBcontrol import create_tables
        create_tables(db_path)
    
    return

# Add 5 songs to our database for testing
songs = []

