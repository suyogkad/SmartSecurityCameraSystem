import sqlite3
import datetime

def create_database():
    conn = sqlite3.connect('videoLogs.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS VideoLogs 
                 (id INTEGER PRIMARY KEY,
                  title TEXT, 
                  url TEXT, 
                  detection_timestamp TEXT, 
                  annotated_info TEXT, 
                  saved_clip_location TEXT,
                  recorded_date TEXT)''')  # added recorded_date column

    conn.commit()
    conn.close()

create_database()
