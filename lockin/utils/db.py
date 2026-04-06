import psycopg2
import psycopg2.extras
import json
import hashlib

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "lockin",
    "user": "postgres",
    "password": "siddhi123"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            preferences JSONB,
            knowledge JSONB,
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scrape_cache (
            id SERIAL PRIMARY KEY,
            cache_key VARCHAR(255) UNIQUE NOT NULL,
            domain VARCHAR(255),
            subdomain VARCHAR(255),
            pdf_bytes BYTEA,
            chunks_json JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    # Add chunks_json column if table already existed without it
    cur.execute("""
        ALTER TABLE scrape_cache ADD COLUMN IF NOT EXISTS chunks_json JSONB;
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_user(email, password_hash, full_name):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s) RETURNING id, email, full_name",
            (email, password_hash, full_name)
        )
        user = dict(cur.fetchone())
        conn.commit()
        cur.close()
        conn.close()
        return user
    except psycopg2.errors.UniqueViolation:
        return "duplicate"
    except Exception:
        return None

def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return dict(user) if user else None

def save_user_profile(user_id, preferences, knowledge):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
        cur.execute(
            "INSERT INTO user_profiles (user_id, preferences, knowledge) VALUES (%s, %s, %s)",
            (user_id, json.dumps(preferences), json.dumps(knowledge))
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False

def get_user_profile(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    profile = cur.fetchone()
    cur.close()
    conn.close()
    return dict(profile) if profile else None

# -------- Scrape cache helpers ----------------------------

def make_cache_key(domain: str, subdomain: str) -> str:
    raw = f"{domain}::{subdomain}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()

def get_cached_scrape(domain: str, subdomain: str):
    """Returns PDF bytes if cached, else None."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        key = make_cache_key(domain, subdomain)
        cur.execute(
            "SELECT pdf_bytes FROM scrape_cache WHERE cache_key = %s", (key,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return bytes(row[0]) if row else None
    except Exception:
        return None

def save_scrape_cache(domain: str, subdomain: str, pdf_bytes: bytes):
    """Saves scraped PDF to DB cache."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        key = make_cache_key(domain, subdomain)
        cur.execute("""
            INSERT INTO scrape_cache (cache_key, domain, subdomain, pdf_bytes)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cache_key) DO UPDATE
            SET pdf_bytes = EXCLUDED.pdf_bytes,
                created_at = NOW()
        """, (key, domain, subdomain, psycopg2.Binary(pdf_bytes)))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False

def save_display_cache(domain: str, subdomain: str, display_results: list):
    """Saves chunk preview data as JSON alongside the PDF cache row."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        key = make_cache_key(domain, subdomain)
        cur.execute("""
            UPDATE scrape_cache SET chunks_json = %s WHERE cache_key = %s
        """, (json.dumps(display_results), key))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False

def get_cached_display(domain: str, subdomain: str):
    """Returns the list of {source, url, chunks} dicts from DB, or None."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        key = make_cache_key(domain, subdomain)
        cur.execute(
            "SELECT chunks_json FROM scrape_cache WHERE cache_key = %s", (key,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception:
        return None

if __name__ == "__main__":
    init_db()