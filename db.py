# db.py
import psycopg2
from psycopg2 import sql

def get_db_connection():
    return psycopg2.connect(
        dbname="neondb",
        user="neondb_owner",
        password="npg_xgumJZ2hq4CE",
        host="ep-bitter-salad-a1zshodz-pooler.ap-southeast-1.aws.neon.tech",
        port="5432",
        sslmode="require"
    )

def fetch_data(query, params=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, params or ())
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def execute_query(query, params=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    cur.close()
    conn.close()
