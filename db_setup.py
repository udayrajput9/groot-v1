import sqlite3
import os

def init_db(db_path=None):
    if db_path is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path  = os.path.join(BASE_DIR, 'users.db')

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email    TEXT NOT NULL
        )
    ''')

    # Favorites table
    c.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL,
            asteroid_name TEXT NOT NULL
        )
    ''')

    # ── NEW: Local Asteroid Knowledge Base ────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS asteroid_kb (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            neo_id           TEXT UNIQUE,
            name             TEXT NOT NULL,
            name_aliases     TEXT,          -- comma-separated alternate names
            diameter_min_km  REAL,
            diameter_max_km  REAL,
            is_hazardous     INTEGER DEFAULT 0,
            absolute_mag     REAL,
            orbital_period_d REAL,
            eccentricity     REAL,
            inclination_deg  REAL,
            semi_major_au    REAL,
            spectral_type    TEXT,
            discovery_year   INTEGER,
            discovered_by    TEXT,
            mission          TEXT,          -- spacecraft missions if any
            fun_fact         TEXT,
            close_approach_json TEXT,       -- latest known close approach JSON
            nasa_url         TEXT,
            fetched_at       TEXT,
            source           TEXT DEFAULT 'seeded'
        )
    ''')

    # ── Daily Email Subscriptions ──────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS email_subscriptions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT NOT NULL UNIQUE,
            email          TEXT NOT NULL,
            subscribed     INTEGER DEFAULT 1,
            subscribed_at  TEXT DEFAULT (datetime('now')),
            last_sent_at   TEXT
        )
    ''')

    # ── Blockchain Wallet Auth ─────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS wallet_nonces (
            wallet_address TEXT PRIMARY KEY,
            nonce          TEXT NOT NULL,
            created_at     TEXT DEFAULT (datetime('now'))
        )
    ''')

    # ── Blockchain Login Audit Log ─────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS blockchain_audit_log (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT,
            wallet_address TEXT,
            action         TEXT NOT NULL,
            tx_hash        TEXT,
            block_data     TEXT,
            ip_hash        TEXT,
            timestamp      TEXT DEFAULT (datetime('now'))
        )
    ''')

    # ── Token-Gated Premium ────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS premium_wallets (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT NOT NULL,
            wallet_address TEXT NOT NULL UNIQUE,
            is_premium     INTEGER DEFAULT 0,
            verified_at    TEXT DEFAULT (datetime('now'))
        )
    ''')

    conn.commit()
    conn.close()
