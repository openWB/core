#!/usr/bin/env python3
# auth_server.py — Flask Auth-Service with DynSec-Integration, SQlite
# Python 3.11

from datetime import datetime, timedelta
from random import randrange
from time import sleep
from typing import Optional, Union
from flask import Flask, request, jsonify, make_response, Response
import os
import sqlite3
from passlib.hash import bcrypt
from secrets import token_urlsafe, token_hex
import requests
from time import time
from inspect import currentframe

# ----------------------
# Configuration via ENV
# ----------------------
DB_PATH = os.environ.get("AUTH_DB", "/home/openwb/auth.db")
MOSQUITTO_API = os.environ.get("MOSQUITTO_API", "http://localhost:8080/dynamic-security/v1")
MOSQ_ADMIN_USER = os.environ.get("MOSQ_ADMIN_USER", "admin")
MOSQ_ADMIN_PASS = os.environ.get("MOSQ_ADMIN_PASS", "changeme")
MOSQ_ROLE = os.environ.get("MOSQ_ROLE", "user")
TLS_ONLY = os.environ.get("TLS_ONLY", "1") == "1"  # if True set cookies with Secure flag
COOKIE_NAME = "openwb_auth"
TOKEN_SERVER_URL = os.environ.get("TOKEN_SERVER_URL", "https://openwb.de/forgotpassword/send_token.php")
DEFAULT_ADMIN_USER = {"username": "admin", "email": "admin@localhost", "password": "openWB#Admin"}

host = os.environ.get("LISTEN_HOST", "127.0.0.1")
port = int(os.environ.get("LISTEN_PORT", "3000"))
debug = os.environ.get("AUTH_DEBUG", "0") == "1"

# ----------------------
# Flask App
# ----------------------
app = Flask(__name__)


# ----------------------
# DB Helpers
# ----------------------
def db_connect() -> sqlite3.Connection:
    """Creates a connection to the SQLite database."""
    db_connection = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    db_connection.row_factory = sqlite3.Row
    print_debug("Connected to DB")
    return db_connection


def db_timestamp_to_epoch_seconds(timestamp: Optional[datetime]) -> Optional[int]:
    """Translates a DB TIMESTAMP to epoch seconds."""
    if timestamp is None:
        return None
    return int(timestamp.timestamp())


def init_db():
    """Initializes the database and creates the initial admin user."""
    db_connection = db_connect()
    db_cursor = db_connection.cursor()
    # All TIMESTAMP are stored as ISO8601 strings in UTC
    db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        role TEXT NOT NULL DEFAULT 'viewer',
        disabled INTEGER NOT NULL DEFAULT 0,
        comment TEXT,
        password_token_hash TEXT,
        password_token_expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    db_connection.commit()
    print("DB initialisiert:", DB_PATH)
    pw_hash = bcrypt.hash(DEFAULT_ADMIN_USER["password"])
    db_cursor.execute(
        "INSERT OR REPLACE INTO users (username, email, password_hash, role, comment) "
        "VALUES (?, ?, ?, ?, ?);",
        (DEFAULT_ADMIN_USER["username"], DEFAULT_ADMIN_USER["email"], pw_hash, "admin", "Initialer Admin-Benutzer")
    )
    db_connection.commit()
    print(f"Initialen Admin-Benutzer angelegt: {DEFAULT_ADMIN_USER['username']} / "
          f"{DEFAULT_ADMIN_USER['email']} / {DEFAULT_ADMIN_USER['password']}")
    print("Bitte Passwort nach dem ersten Login ändern!")
    db_connection.close()
    # set file permissions to owner read/write only
    os.chmod(DB_PATH, 0o600)


def check_default_admin_user_exists():
    """Checks if the default admin user exists."""
    pw_hash = bcrypt.hash(DEFAULT_ADMIN_USER["password"])
    db_connection = db_connect()
    db_cursor = db_connection.execute(
        "SELECT COUNT(*) AS count FROM users WHERE username = ? and password_hash = ?",
        (DEFAULT_ADMIN_USER["username"], pw_hash)
    )
    row = db_cursor.fetchone()
    db_connection.close()
    return row["count"] > 0


# ----------------------
# User Helpers
# ----------------------
def get_user(username: str) -> Optional[sqlite3.Row]:
    """Fetches a user row by username."""
    db_connection = db_connect()
    db_cursor = db_connection.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    )
    row = db_cursor.fetchone()
    db_connection.close()
    print_debug(f"Fetched user '{username}': {'found' if row else 'not found'}")
    return row


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    """Fetches a user row by email."""
    db_connection = db_connect()
    db_cursor = db_connection.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )
    row = db_cursor.fetchone()
    db_connection.close()
    print_debug(f"Fetched user by email '{email}': {'found' if row else 'not found'}")
    return row


def verify_user_password(username: str, password: str) -> bool:
    """Verifies a user's password. Returns (is_valid, actual_username).
    Parameter 'username' can be either the username or the email.
    """
    row = get_user(username)
    if not row:
        # try email as username
        row = get_user_by_email(username)
    user_valid = row and not row["disabled"] and bcrypt.verify(password, row["password_hash"])
    print_debug(f"Password verification for user '{username}': {'valid' if user_valid else 'invalid'}")
    return (user_valid, row["username"] if row else None)


def verify_user_token(username: str, token: str) -> bool:
    """Verifies a user's password reset token.
    Parameter 'username' can be either the username or the email.
    """
    print_debug(f"Verifying token for user '{username}'")
    row = get_user(username)
    if not row:
        # try email as username
        row = get_user_by_email(username)
    token_valid = (
        row
        and not row["disabled"]
        and row["password_token_hash"]
        and bcrypt.verify(token, row["password_token_hash"])
        and row["password_token_expires_at"]
        and row["password_token_expires_at"] > datetime.now()
    )
    print_debug(f"Token verification for user '{username}': {'valid' if token_valid else 'invalid'}")
    return token_valid


def verify_user_role(username: str, role: str = "admin") -> bool:
    """Verifies a user's role."""
    row = get_user(username)
    role_valid = row and not row["disabled"] and row["role"] == role
    print_debug(f"Role verification for user '{username}': {'valid' if role_valid else 'invalid'}")
    return role_valid


# ----------------------
# Auth Helpers
# ----------------------
def get_authenticated_username(
        required_role: Optional[str] = None) -> tuple[Optional[str], Optional[tuple[Response, int]]]:
    """Verifies the authentication cookie and optional role.
    Returns (username, None) if authenticated, otherwise (None, (Response, status_code))
    """
    auth_data = request.cookies.get(COOKIE_NAME)
    username, password = (auth_data or ":").split(":", 1)
    result = username, None
    user_valid, _ = verify_user_password(username, password)
    if not user_valid:
        result = None, (jsonify(error="Not Authenticated"), 401)
    if required_role and not verify_user_role(username, role=required_role):
        result = None, (jsonify(error="Forbidden"), 403)
    print_debug(f"Authenticated user: '{username}' -> {'success' if result[0] else 'failure'}")
    return result


# ----------------------
# General Helpers
# ----------------------
def print_debug(msg: str) -> None:
    """Prints a debug message if AUTH_DEBUG is enabled.
    """
    if debug:
        frame = currentframe().f_back
        lineno = frame.f_lineno
        filename = frame.f_code.co_filename
        print(f"[DEBUG][{filename}]:{lineno} {msg}")


# ----------------------
# Mosquitto Dynamic Security helpers
# ----------------------
def create_temp_mqtt_user(username_hint: str, ttl_seconds: int = 3600) -> dict:
    """Creates a temporary MQTT user via Mosquitto Dynamic Security API.
    The user will have the role defined in MOSQ_ROLE.
    The user will expire after ttl_seconds.
    Returns: { "tempUser": "...", "tempPass": "...", "expires_at": epoch_sec }
    """
    temp_user = f"sess_{token_hex(6)}"
    temp_pass = token_urlsafe(12)
    payload = {
        "username": temp_user,
        "password": temp_pass,
        "roles": [MOSQ_ROLE]
    }
    url = f"{MOSQUITTO_API}/client"
    try:
        result = requests.post(url, auth=(MOSQ_ADMIN_USER, MOSQ_ADMIN_PASS), json=payload, timeout=5)
    except Exception as e:
        raise RuntimeError(f"Unable to connect to Mosquitto API: {e}")
    if result.status_code not in (200, 201):
        raise RuntimeError(f"Mosquitto-API Error ({result.status_code}): {result.text}")
    expires_at = int(time()) + ttl_seconds
    return {"tempUser": temp_user, "tempPass": temp_pass, "expires_at": expires_at}


def delete_mqtt_user(username: str):
    """Deletes a MQTT user via Mosquitto Dynamic Security API.
    Returns True on success, False otherwise.
    """
    url = f"{MOSQUITTO_API}/client/{username}"
    try:
        result = requests.delete(url, auth=(MOSQ_ADMIN_USER, MOSQ_ADMIN_PASS), timeout=5)
        return result.status_code in (200, 204)
    except Exception:
        return False


# ----------------------
# Web API Endpoints (Login / Refresh / MQTT credentials / Logout / Health)
# ----------------------
def set_cookie(resp: Response, key: str, value, expires: Optional[Union[str, datetime, int, float]] = None) -> None:
    resp.set_cookie(
        key,
        value,
        httponly=True,
        secure=TLS_ONLY,
        samesite="Strict",
        expires=expires
    )


@app.post("/api/login")
def login() -> Response:
    data: dict = request.get_json(force=True)
    username: Optional[str] = data.get("username")
    password: Optional[str] = data.get("password")
    if username is None or password is None:
        return jsonify(error="username/password required"), 400
    user_valid, actual_username = verify_user_password(username, password)
    if not user_valid:
        return jsonify(error="invalid credentials"), 401

    response = make_response(jsonify(success=True))
    # set Cookie
    set_cookie(response, COOKIE_NAME, f"{actual_username}:{password}", expires=None)
    print_debug(f"User '{actual_username}' logged in.")
    return response


@app.post("/api/logout")
def logout() -> Response:
    if debug:
        username, _ = get_authenticated_username()  # just for logging
    resp = make_response(jsonify(success=True))
    # delete Cookie
    set_cookie(resp, COOKIE_NAME, "", expires=0)
    print_debug(f"User '{username}' logged out.")
    return resp


@app.get("/api/health")
def health() -> Response:
    print_debug("Health check")
    return jsonify(status="ok")


# ----------------------
# User Endpoints
# ----------------------


# ----------------------
# User-Me Endpoint
# ----------------------
@app.get("/user/me")
def user_me() -> Response:
    username, error = get_authenticated_username()
    if error:
        return error
    row = get_user(username)
    if not row or row["disabled"]:
        return jsonify(error="user not found"), 404
    user_info = {
        "username": row["username"],
        "email": row["email"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "role": row["role"],
        "comment": row["comment"],
        "created_at": db_timestamp_to_epoch_seconds(row["created_at"]),
        "token_expires_at": db_timestamp_to_epoch_seconds(row["password_token_expires_at"])
    }
    print_debug(f"User-Me for '{username}'")
    return jsonify(user=user_info)


# ----------------------
# User-Update-Password Endpoint
# ----------------------
@app.post("/user/update_password")
def user_update_password() -> Response:
    data: dict = request.get_json(force=True)
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    if old_password is None or new_password is None:
        return jsonify(error="old_password and new_password required"), 400
    username, error = get_authenticated_username()
    if error:
        return error
    user_valid, _ = verify_user_password(username, old_password)
    if not user_valid:
        return jsonify(error="invalid old_password"), 401
    pw_hash = bcrypt.hash(new_password)
    db_connection = db_connect()
    db_connection.execute(
        "UPDATE users SET password_hash = ?, password_token_hash = NULL, password_token_expires_at = NULL "
        "WHERE username = ?",
        (pw_hash, username)
    )
    db_connection.commit()
    db_connection.close()

    response = make_response(jsonify(success=True))
    # set Cookie
    set_cookie(response, COOKIE_NAME, f"{username}:{new_password}", expires=None)
    print_debug(f"User '{username}' updated password.")
    return response


# ----------------------
# User-Reset-Password Endpoint
# ----------------------
@app.post("/user/reset_password")
def user_reset_password() -> Response:
    data: dict = request.get_json(force=True)
    email = data.get("email")
    new_password = data.get("new_password")
    token = data.get("token")
    if email is None or new_password is None or token is None:
        return jsonify(error="email, new_password and token required"), 400
    row = get_user_by_email(email)
    if not row:
        return jsonify(error="invalid email or token"), 401
    username = row["username"]
    if not verify_user_token(username, token):
        return jsonify(error="invalid email or token"), 401
    pw_hash = bcrypt.hash(new_password)
    db_connection = db_connect()
    db_connection.execute(
        "UPDATE users SET password_hash = ?, password_token_hash = NULL, password_token_expires_at = NULL "
        "WHERE username = ?",
        (pw_hash, username)
    )
    db_connection.commit()
    db_connection.close()

    response = make_response(jsonify(success=True))
    # set Cookie
    set_cookie(response, COOKIE_NAME, f"{username}:{new_password}", expires=None)
    print_debug(f"User '{username}' reset password via token.")
    return response


# ----------------------
# User-Create-Password-Token Endpoint
# ----------------------
@app.post("/user/create_password_token")
def user_generate_token() -> Response:
    timeout = 10  # seconds
    data: dict = request.get_json(force=True)
    email = data.get("email")
    if not email:
        return jsonify(error="email required"), 400
    token = token_urlsafe(6)
    token_hash = bcrypt.hash(token)
    expires_at = datetime.now() + timedelta(hours=1)

    db_connection = db_connect()
    db_cursor = db_connection.execute(
        "UPDATE users SET password_token_hash = ?, password_token_expires_at = ? "
        "WHERE email = ?",
        (token_hash, expires_at, email)
    )
    affected_rows = db_cursor.rowcount
    db_connection.commit()
    db_connection.close()

    if affected_rows == 0:
        print(f"Password token requested for unknown email: {email}")
        # report success even if email not found to avoid user enumeration
        sleep(randrange(5, 25) * 0.1)  # artificial delay to mitigate user enumeration
        return jsonify(success=True,)

    # send token to user via email gateway
    error = None
    try:
        payload = {
            "email": email,
            "subject": "openWB Passwort-Reset",
            "message": "Hallo,\n\n"
                       "Du hast in einer openWB ein Passwort-Reset angefordert.\n"
                       "Bitte verwende den folgenden Token, um Dein Passwort zurückzusetzen:\n\n"
                       f"Token: {token}\n\n"
                       "Dieser Token ist 1 Stunde gültig.\n\n"
                       "Falls Du kein Passwort-Reset angefordert hast, kannst Du diese Nachricht ignorieren."
        }
        print(f"Sending token to {TOKEN_SERVER_URL}: {payload}")
        response = requests.post(
            url=TOKEN_SERVER_URL,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Token-Client/1.0',
                'charset': 'utf-8'
            },
            timeout=timeout
        )
    except requests.exceptions.Timeout:
        error = f"Error: request timed out after {timeout}s"
    except requests.exceptions.ConnectionError:
        error = f"Error: connection to {TOKEN_SERVER_URL} failed"
    except requests.RequestException as e:
        error = f"HTTP-Error: {e}"
    print(f"{response.status_code}: {response.text}")
    if error is not None or response.status_code != 200:
        return jsonify(error=error or f"Error: server returned status {response.status_code}"), 500
    return jsonify(success=True,)


# ----------------------
# User-Update Endpoint
# ----------------------
@app.post("/user/update")
def user_update() -> Response:
    username, error = get_authenticated_username()
    if error:
        return error
    data: dict = request.get_json(force=True)
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    comment = data.get("comment")
    db_connection = db_connect()
    db_connection.execute(
        "UPDATE users SET first_name = ?, last_name = ?, comment = ? "
        "WHERE username = ?",
        (first_name, last_name, comment, username)
    )
    db_connection.commit()
    db_connection.close()
    return jsonify(success=True)


# ----------------------
# Admin Endpoints
# ----------------------


# ----------------------
# Admin Create-User Endpoint
# ----------------------
@app.post("/admin/create_user")
def admin_create_user() -> Response:
    # validate Auth
    _, error = get_authenticated_username(required_role="admin")
    if error:
        return error
    data: dict = request.get_json(force=True)
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    role = data.get("role", "viewer")
    comment = data.get("comment")
    if not email or not password:
        return jsonify(error="email and password required"), 400
    pw_hash = bcrypt.hash(password)
    db_connection = db_connect()
    try:
        db_connection.execute(
            "INSERT INTO users (username, email, password_hash, first_name, last_name, role, disabled, comment) "
            "VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
            (username, email, pw_hash, first_name, last_name, role, comment)
        )
        db_connection.commit()
    except sqlite3.IntegrityError:
        return jsonify(error=f"user '{username}' already exists"), 409
    finally:
        db_connection.close()
    return jsonify(success=True, email=email)


# ----------------------
# Admin Update-User Endpoint
# ----------------------
@app.post("/admin/update_user")
def admin_update_user() -> Response:
    # validate Auth
    _, error = get_authenticated_username(required_role="admin")
    if error:
        return error
    data: dict = request.get_json(force=True)
    username = data.get("username")
    email = data.get("email")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    role = data.get("role", "viewer")
    disabled = data.get("disabled", 0)
    comment = data.get("comment")
    if not email:
        return jsonify(error="email required"), 400
    db_connection = db_connect()
    try:
        db_connection.execute(
            "UPDATE users SET email = ?, first_name = ?, last_name = ?, role = ?, disabled = ?, comment = ? "
            "WHERE username = ?",
            (email, first_name, last_name, role, disabled, comment, username)
        )
        db_connection.commit()
    except sqlite3.IntegrityError:
        return jsonify(error=f"user with email '{email}' already exists"), 409
    finally:
        db_connection.close()
    return jsonify(success=True, username=username)


# ----------------------
# Admin Delete-User Endpoint
# ----------------------
@app.post("/admin/delete_user")
def admin_delete_user() -> Response:
    # validate Auth
    _, error = get_authenticated_username(required_role="admin")
    if error:
        return error
    data: dict = request.get_json(force=True)
    username = data.get("username")
    if not username:
        return jsonify(error="email required"), 400
    db_connection = db_connect()
    db_cursor = db_connection.execute(
        "DELETE FROM users WHERE username = ?",
        (username,)
    )
    deleted_rows = db_cursor.rowcount
    db_connection.commit()
    db_connection.close()
    if deleted_rows == 0:
        return jsonify(error="user not found"), 404
    return jsonify(success=True, username=username)


# ----------------------
# Admin Update-Password Endpoint
# ----------------------
@app.post("/admin/update_password")
def admin_update_password() -> Response:
    # validate Auth
    _, error = get_authenticated_username(required_role="admin")
    if error:
        return error
    data: dict = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify(error="username and password required"), 400
    pw_hash = bcrypt.hash(password)
    db_connection = db_connect()
    db_cursor = db_connection.execute(
        "UPDATE users SET password_hash = ? "
        "WHERE username = ?",
        (pw_hash, username)
    )
    modified_rows = db_cursor.rowcount
    db_connection.commit()
    db_connection.close()
    if modified_rows == 0:
        return jsonify(error=f"user '{username}' not found"), 409
    return jsonify(success=True)


# ----------------------
# Admin Get-Users Endpoint
# ----------------------
@app.get("/admin/get_users")
def admin_get_users() -> Response:
    # validate Auth
    _, error = get_authenticated_username(required_role="admin")
    if error:
        return error
    db_connection = db_connect()
    db_cursor = db_connection.execute(
        "SELECT username, email, first_name, last_name, comment, role, disabled, created_at "
        "FROM users"
    )
    users = [dict(row) for row in db_cursor.fetchall()]
    for user in users:
        user["created_at"] = db_timestamp_to_epoch_seconds(user["created_at"])
    db_connection.close()
    return jsonify(users=users)


# ----------------------
# Start App
# ----------------------
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Datenbank nicht gefunden: {DB_PATH}")
        print("Es wird eine neue Datenbank angelegt.")
        init_db()
    elif check_default_admin_user_exists():
        print("Warnung: Der initiale Admin-Benutzer mit Standard-Passwort existiert noch!")
        print(f"Bitte ändere das Passwort des Benutzers '{DEFAULT_ADMIN_USER['username']}'!")
    # IMPORTANT: For Production use: WSGI-Server like gunicorn + HTTPS-Frontend (eg. nginx)
    print(f"Starting Auth-Service on {host}:{port} (Debug={debug})")
    # run with waitress, if present; fallback to Flask-Dev-Server
    try:
        from waitress import serve
        if debug:
            import logging
            logger = logging.getLogger('waitress')
            logger.setLevel(logging.INFO)
        serve(app, host=host, port=port)
    except Exception:
        app.run(host=host, port=port, debug=debug)
