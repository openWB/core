#!/usr/bin/env python3
# init_db.py
import sqlite3
from passlib.hash import bcrypt
import os
import getpass

DB_PATH = os.environ.get("AUTH_DB", "./auth.db")


def init_db():
    db_connection = sqlite3.connect(DB_PATH)
    db_cursor = db_connection.cursor()
    db_cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        role TEXT NOT NULL DEFAULT 'viewer',
        disabled INTEGER NOT NULL DEFAULT 0,
        comment TEXT,
        password_token TEXT,
        password_token_expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    db_connection.commit()
    db_connection.close()
    print("DB initialisiert:", DB_PATH)


def create_user(email, password, first_name=None, last_name=None, role="viewer", comment=None):
    db_connection = sqlite3.connect(DB_PATH)
    db_cursor = db_connection.cursor()
    pw_hash = bcrypt.hash(password)
    db_cursor.execute(
        "INSERT OR REPLACE INTO users (email, password_hash, first_name, last_name, role, disabled, comment) "
        "VALUES (?, ?, ?, ?, ?, 0, ?);",
        (email, pw_hash, first_name, last_name, role, comment)
    )
    db_connection.commit()
    db_connection.close()
    print(f"Benutzer '{username}' angelegt (Rolle={role})")


if __name__ == "__main__":
    init_db()
    username = input("Admin-E-Mail [admin@localhost]: ") or "admin@localhost"
    password = getpass.getpass("Passwort: ")
    password_2 = getpass.getpass("Passwort wiederholen: ")
    if password != password_2:
        print("Passwörter stimmen nicht überein.")
        raise SystemExit(1)
    create_user(username, password, role="admin", comment="Initialer Admin-Benutzer")
    print("Datenbankinitialisierung abgeschlossen.")
