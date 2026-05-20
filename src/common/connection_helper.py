import sqlite3
from contextlib import contextmanager

@contextmanager
def db_connection(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()