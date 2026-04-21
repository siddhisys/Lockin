import psycopg2
import psycopg2.extras
import json
import hashlib

# PostgreSQL database connection configuration
DB_CONFIG = {
    "host": "localhost",      # Database server address
    "port": 5432,             # Default PostgreSQL port
    "dbname": "lockin",       # Database name
    "user": "postgres",       # Database username
    "password": "siddhi123"   # Database password
}

def get_connection():
    """Create and return a database connection using the configured parameters."""
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    """
    Initialize the database by creating all necessary tables if they don't exist.
    
    Tables created:
    - users: Stores user account information
    - user_profiles: Stores user preferences and knowledge state (JSONB)
    - scrape_cache: Caches scraped PDFs and their chunk previews
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Users table - core authentication and user info
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # User profiles table - stores JSON preferences and knowledge state
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            preferences JSONB,   -- User's learning preferences
            knowledge JSONB,     -- User's knowledge/learning state
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # Scrape cache table - stores scraped PDF data and chunk previews
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scrape_cache (
            id SERIAL PRIMARY KEY,
            cache_key VARCHAR(255) UNIQUE NOT NULL,  -- MD5 hash of domain+subdomain
            domain VARCHAR(255),
            subdomain VARCHAR(255),
            pdf_bytes BYTEA,      -- Binary PDF data
            chunks_json JSONB,    -- Preview chunks for display
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # Add chunks_json column if table already existed without it (migration)
    cur.execute("""
        ALTER TABLE scrape_cache ADD COLUMN IF NOT EXISTS chunks_json JSONB;
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def create_user(email, password_hash, full_name):
    """
    Create a new user account in the database.
    
    Args:
        email: User's email address (must be unique)
        password_hash: SHA-256 hashed password
        full_name: User's full name
        
    Returns:
        User dict with id, email, full_name on success
        "duplicate" if email already exists
        None if other error occurs
    """
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
        return "duplicate"  # Email already exists
    except Exception:
        return None  # Other error occurred

def get_user_by_email(email):
    """
    Retrieve a user record by email address.
    
    Args:
        email: User's email address
        
    Returns:
        User dict if found, None otherwise
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return dict(user) if user else None

def save_user_profile(user_id, preferences, knowledge):
    """
    Save or update a user's profile data.
    
    Deletes existing profile first (if any) then inserts new one.
    
    Args:
        user_id: User's ID from users table
        preferences: Dictionary of user preferences
        knowledge: Dictionary of user's knowledge state
        
    Returns:
        True on success, False on failure
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Delete existing profile to avoid conflicts
        cur.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
        # Insert new profile
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
    """
    Retrieve a user's profile data.
    
    Args:
        user_id: User's ID from users table
        
    Returns:
        Profile dict if found, None otherwise
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    profile = cur.fetchone()
    cur.close()
    conn.close()
    return dict(profile) if profile else None

# -------- Scrape cache helpers ----------------------------

def make_cache_key(domain: str, subdomain: str) -> str:
    """
    Generate a unique cache key from domain and subdomain.
    
    Args:
        domain: Website domain (e.g., "example.com")
        subdomain: Subdomain path (e.g., "/docs/page")
        
    Returns:
        MD5 hash string to use as cache key
    """
    raw = f"{domain}::{subdomain}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()

def get_cached_scrape(domain: str, subdomain: str):
    """
    Retrieve cached PDF bytes for a given domain and subdomain.
    
    Args:
        domain: Website domain
        subdomain: Subdomain path
        
    Returns:
        PDF bytes if cached, None otherwise
    """
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
    """
    Save scraped PDF data to cache.
    
    Uses UPSERT (INSERT ... ON CONFLICT DO UPDATE) to handle existing entries.
    
    Args:
        domain: Website domain
        subdomain: Subdomain path
        pdf_bytes: Binary PDF data to cache
        
    Returns:
        True on success, False on failure
    """
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
    """
    Save chunk preview data as JSON alongside the cached PDF.
    
    Args:
        domain: Website domain
        subdomain: Subdomain path
        display_results: List of {source, url, chunks} dicts for display
        
    Returns:
        True on success, False on failure
    """
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
    """
    Retrieve cached chunk preview data.
    
    Args:
        domain: Website domain
        subdomain: Subdomain path
        
    Returns:
        List of {source, url, chunks} dicts if cached, None otherwise
    """
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
    # Run database initialization when script is executed directly
    init_db()