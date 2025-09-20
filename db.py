import sqlite3
from flask import g

DB = "database.db"

def get_connection():
    con = sqlite3.connect(DB, timeout=10)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con

def execute(sql, params=[]):
    with get_connection() as con:
        cur = con.execute(sql, params)
        con.commit()
        g.last_insert_id = cur.lastrowid
        return cur

def last_insert_id():
    return g.last_insert_id

def query(sql, params=[]):
    with get_connection() as con:
        return con.execute(sql, params).fetchall()