import sqlite3
import requests
from datetime import datetime

NASA_API_KEY = "2UeThfszIbfRy83QPwhZRpGAPzPu4FNIiGEJzDUY"

def init_asteroid_db():
    conn = sqlite3.connect('asteroids.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS asteroid_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            neo_reference_id TEXT,
            name TEXT,
            data_json TEXT,
            fetched_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def fetch_and_store_asteroids():
    url = f"https://api.nasa.gov/neo/rest/v1/neo/browse?api_key={NASA_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        asteroids = data.get('near_earth_objects', [])
        conn = sqlite3.connect('asteroids.db')
        c = conn.cursor()
        for asteroid in asteroids:
            c.execute('''
                INSERT OR REPLACE INTO asteroid_data
                (neo_reference_id, name, data_json, fetched_at)
                VALUES (?, ?, ?, ?)
            ''', (
                asteroid['neo_reference_id'],
                asteroid['name'],
                str(asteroid),
                datetime.utcnow().isoformat()
            ))
        conn.commit()
        conn.close()
