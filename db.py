import sqlite3
from flask import g

DB = "database.db"

def get_connection():
    con = sqlite3.connect(DB, timeout=10)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def execute(sql, params=None):
    if params is None:
        params = []
    con = get_connection()
    cur = con.execute(sql, params)
    con.commit()
    last_id = cur.lastrowid
    con.close()
    try:
        g.last_insert_id = last_id
    except Exception:
        pass
    return last_id

def last_insert_id():
    return getattr(g, "last_insert_id", None)

def query(sql, params=None):
    if params is None:
        params = []
    con = get_connection()
    result = con.execute(sql, params).fetchall()
    con.close()
    return result
