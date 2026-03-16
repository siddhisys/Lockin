import psycopg2
import psycopg2.extras
import json

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
    except Exception as e:
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
    except Exception as e:
        return False

def get_user_profile(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    profile = cur.fetchone()
    cur.close()
    conn.close()
    return dict(profile) if profile else None

if __name__ == "__main__":
    init_db()