import sqlite3
import pandas as pd
import os

def export_to_csv():
    # Connect to the SQLite database
    conn = sqlite3.connect('videoLogs.db')
    print("Database connected successfully!")

    # Query data from the database into a pandas DataFrame
    query = "SELECT * FROM VideoLogs"
    df = pd.read_sql_query(query, conn)

    # Add a new column for the full video path
    df['full_video_path'] = './savedRecordings/' + df['saved_clip_location']

    # Export the DataFrame to a CSV file
    admin_panel_path = os.path.join("admin-panel", "dataset.csv")
    df.to_csv(admin_panel_path, index=False)

    # Close the connection
    conn.close()

if __name__ == "__main__":
    export_to_csv()
