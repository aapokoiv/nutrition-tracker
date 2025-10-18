import sqlite3
from flask import g, flash

DB = "database.db"

def get_connection():
    """Get a SQLite connection with foreign keys and Row factory enabled."""
    try:
        con = sqlite3.connect(DB, timeout=10)
        con.execute("PRAGMA foreign_keys = ON")
        con.row_factory = sqlite3.Row  # rows behave like dicts
        return con
    except sqlite3.Error:
        flash("Database connection failed. Please try again later.")
        return None


def execute(sql, params=None):
    """Execute INSERT/UPDATE/DELETE and return last inserted ID (or None)."""
    params = params or []
    con = get_connection()
    if con is None:
        return None

    try:
        cur = con.execute(sql, params)
        con.commit()
        last_id = cur.lastrowid
        g.last_insert_id = last_id  # store like original
        return last_id
    except sqlite3.Error:
        flash("A database error occurred. Please try again later.")
        return None
    finally:
        con.close()


def query(sql, params=None):
    """Run SELECT queries and return all rows as list[sqlite3.Row]."""
    params = params or []
    con = get_connection()
    if con is None:
        return []

    try:
        result = con.execute(sql, params).fetchall()
        return result
    except sqlite3.Error:
        flash("A database query error occurred. Please try again later.")
        return []
    finally:
        con.close()


def last_insert_id():
    """Return the last insert ID stored in flask.g."""
    return getattr(g, "last_insert_id", None)
