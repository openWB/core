#!/usr/bin/env python3
# auth_server.py — Flask Auth-Service mit JWT, Refresh-Rotation, DynSec-Integration, SQlite
# Python 3.11

from datetime import datetime, timedelta
from typing import Optional, Union
from flask import Flask, request, jsonify, make_response, Response
import os
import sqlite3
from passlib.hash import bcrypt
from secrets import token_urlsafe
# import secrets
import requests
# import time

# ----------------------
# Konfiguration via ENV
# ----------------------
DB_PATH = os.environ.get("AUTH_DB", "./auth.db")
MOSQUITTO_API = os.environ.get("MOSQUITTO_API", "http://localhost:8080/dynamic-security/v1")
MOSQ_ADMIN_USER = os.environ.get("MOSQ_ADMIN_USER", "admin")
MOSQ_ADMIN_PASS = os.environ.get("MOSQ_ADMIN_PASS", "changeme")
MOSQ_ROLE = os.environ.get("MOSQ_ROLE", "user")
TLS_ONLY = os.environ.get("TLS_ONLY", "1") == "1"  # wenn True cookies mit Secure setzen
COOKIE_NAME = "openwb_auth"
TOKEN_SERVER_URL = os.environ.get("TOKEN_SERVER_URL", "https://openwb.de/forgotpassword/send_token.php")

# ----------------------
# Flask App
# ----------------------
app = Flask(__name__)


# ----------------------
# DB Hilfsfunktionen
# ----------------------
def db_connect() -> sqlite3.Connection:
    db_connection = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    db_connection.row_factory = sqlite3.Row
    return db_connection


def db_timestamp_to_epoch_seconds(ts: Optional[datetime]) -> Optional[int]:
    if ts is None:
        return None
    return int(ts.timestamp())


# ----------------------
# Nutzer-Logik
# ----------------------
def get_user(email: str) -> Optional[sqlite3.Row]:
    db_connection = db_connect()
    cur = db_connection.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )
    row = cur.fetchone()
    db_connection.close()
    return row


def verify_user_password(email: str, password: str) -> bool:
    row = get_user(email)
    return row and not row["disabled"] and bcrypt.verify(password, row["password_hash"])


def verify_user_token(email: str, token: str) -> bool:
    row = get_user(email)
    return row and not row["disabled"] and bcrypt.verify(token, row["password_token_hash"]) and \
        row["password_token_expires_at"] and row["password_token_expires_at"] > datetime.now()


def verify_user_role(email: str, role: str = "admin") -> bool:
    row = get_user(email)
    return row and not row["disabled"] and row["role"] == role


# ----------------------
# Auth-Hilfsfunktion
# ----------------------
def get_authenticated_email(
        required_role: Optional[str] = None) -> tuple[Optional[str], Optional[tuple[Response, int]]]:
    """
    Prüft das Auth-Cookie und optional die Rolle.
    Rückgabe: (email, None) bei Erfolg oder (None, (jsonify..., status)) bei Fehler.
    """
    auth_data = request.cookies.get(COOKIE_NAME)
    email, password = (auth_data or ":").split(":", 1)
    if not verify_user_password(email, password):
        return None, (jsonify(error="Not Authenticated"), 401)
    if required_role and not verify_user_role(email, role=required_role):
        return None, (jsonify(error="Forbidden"), 403)
    return email, None


# ----------------------
# Mosquitto Dynamic Security helpers
# ----------------------
# def create_temp_mqtt_user(username_hint: str, ttl_seconds: int = 3600) -> dict:
#     """
#     Legt einen temporären Mosquitto-Client (User) an via Dynamic Security API.
#     Rückgabe: { "tempUser": "...", "tempPass": "...", "expires_at": epoch_sec }
#     """
#     temp_user = f"sess_{secrets.token_hex(6)}"
#     temp_pass = secrets.token_urlsafe(12)
#     payload = {
#         "username": temp_user,
#         "password": temp_pass,
#         "roles": [MOSQ_ROLE]
#     }
#     url = f"{MOSQUITTO_API}/client"
#     try:
#         r = requests.post(url, auth=(MOSQ_ADMIN_USER, MOSQ_ADMIN_PASS), json=payload, timeout=5)
#     except Exception as e:
#         raise RuntimeError(f"Mosquitto API nicht erreichbar: {e}")
#     if r.status_code not in (200, 201):
#         raise RuntimeError(f"Mosquitto-API Fehler ({r.status_code}): {r.text}")
#     expires_at = int(time.time()) + ttl_seconds
#     return {"tempUser": temp_user, "tempPass": temp_pass, "expires_at": expires_at}


# def delete_mqtt_user(username: str):
#     url = f"{MOSQUITTO_API}/client/{username}"
#     try:
#         r = requests.delete(url, auth=(MOSQ_ADMIN_USER, MOSQ_ADMIN_PASS), timeout=5)
#         return r.status_code in (200, 204)
#     except Exception:
#         return False


# ----------------------
# Routes: Auth-Plugin kompatible Endpoints
# ----------------------
# @app.post("/auth")
# def auth_check():
#     """
#     Erwartet form-encoded oder JSON:
#     - username
#     - password
#     Antwort:
#     - 200 OK -> erlaubt
#     - 401/403 -> abgelehnt
#     """
#     data = request.form.to_dict() or request.get_json(silent=True) or {}
#     email = data.get("username", "")
#     password = data.get("password", "")

#     # klassische Nutzer/Passwort-Prüfung
#     if verify_user_password(email, password):
#         return ("OK", 200)

#     return ("Unauthorized", 401)


# @app.post("/acl")
# def acl_check():
#     """
#     Erwartet (form oder json):
#     - username
#     - topic
#     - acc (1=sub, 2=pub; je nach Plugin)
#     - clientid (optional)
#     Antwort:
#     - 200 OK -> erlaubt
#     - 403 -> verweigert
#     """
#     data = request.form.to_dict() or request.get_json(silent=True) or {}
#     email = data.get("username", "")
#     topic = data.get("topic", "")
#     acc = int(data.get("acc", 0))

#     row = get_user(email)
#     if not row or row["disabled"]:
#         return ("Forbidden", 403)

#     role = row["role"]
#     # Beispiel-ACLs — bitte an deine Anforderungen anpassen:
#     if role == "admin":
#         return ("OK", 200)
#     if role == "viewer" and acc == 1:
#         # nur lesen, zusätzlich Topic-Filter möglich
#         if topic.startswith("sensors/") or topic.startswith("status/"):
#             return ("OK", 200)
#     if role == "operator":
#         # operator darf lesen und schreiben auf device-Tops
#         if topic.startswith("devices/") or topic.startswith("commands/"):
#             return ("OK", 200)
#     # Standard: verweigern
#     return ("Forbidden", 403)


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
def web_login() -> Response:
    data: dict = request.get_json(force=True)
    email: Optional[str] = data.get("email")
    password: Optional[str] = data.get("password")
    if email is None or password is None:
        return jsonify(error="email/password required"), 400
    if not verify_user_password(email, password):
        return jsonify(error="invalid credentials"), 401

    resp = make_response(jsonify(success=True))
    # Cookie setzen
    set_cookie(resp, COOKIE_NAME, f"{email}:{password}", expires=None)
    return resp


@app.post("/api/logout")
def logout() -> Response:
    resp = make_response(jsonify(success=True))
    # Cookie löschen
    set_cookie(resp, COOKIE_NAME, "", expires=0)
    return resp


@app.get("/api/health")
def health() -> Response:
    return jsonify(status="ok")


# ----------------------
# User Endpoints
# ----------------------


# ----------------------
# User-Me Endpoint
# ----------------------
@app.get("/user/me")
def user_me() -> Response:
    email, err = get_authenticated_email()
    if err:
        return err
    row = get_user(email)
    if not row or row["disabled"]:
        return jsonify(error="user not found"), 404
    user_info = {
        "email": row["email"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "role": row["role"],
        "comment": row["comment"],
        "created_at": db_timestamp_to_epoch_seconds(row["created_at"]),
        "token_expires_at": db_timestamp_to_epoch_seconds(row["password_token_expires_at"])
    }
    return jsonify(user=user_info)


# ----------------------
# User-Update-Password Endpoint
# ----------------------
@app.post("/user/update_password")
def user_update_password() -> Response:
    data: dict = request.get_json(force=True)
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    email = data.get("email")
    token_used = False
    if old_password is None or new_password is None:
        return jsonify(error="old_password and new_password required"), 400
    # check for passwort token
    if not verify_user_token(email, old_password):
        email, err = get_authenticated_email()
        if err:
            return err
        if not verify_user_password(email, old_password):
            return jsonify(error="invalid old_password or token"), 401
    else:
        token_used = True
    pw_hash = bcrypt.hash(new_password)
    conn = db_connect()
    conn.execute(
        "UPDATE users SET password_hash = ?, password_token_hash = NULL, password_token_expires_at = NULL "
        "WHERE email = ?",
        (pw_hash, email)
    )
    conn.commit()
    conn.close()

    resp = make_response(jsonify(success=True, token_used=token_used))
    # Cookie setzen
    set_cookie(resp, COOKIE_NAME, f"{email}:{new_password}", expires=None)
    return resp


# ----------------------
# User-Create-Password-Token Endpoint
# ----------------------
@app.post("/user/create_password_token")
def user_generate_token() -> Response:
    timeout = 10  # seconds
    data: dict = request.get_json(force=True)
    email = data.get("email")
    # create random token
    token = token_urlsafe(6)
    token_hash = bcrypt.hash(token)
    expires_at = datetime.now() + timedelta(hours=1)
    conn = db_connect()
    conn.execute(
        "UPDATE users SET password_token_hash = ?, password_token_expires_at = ? "
        "WHERE email = ?",
        (token_hash, expires_at, email)
    )
    conn.commit()
    conn.close()
    # send token to user via email gateway
    error = None
    try:
        payload = {"email": email, "token": token}
        print(f"Sending token to {TOKEN_SERVER_URL}: {payload}")
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Token-Client/1.0',
            'charset': 'utf-8'
        }
        resp = requests.post(
            url=TOKEN_SERVER_URL,
            json=payload,
            headers=headers,
            timeout=timeout
        )
    except requests.exceptions.Timeout:
        error = f"Error: request timed out after {timeout}s"
    except requests.exceptions.ConnectionError:
        error = f"Error: connection to {TOKEN_SERVER_URL} failed"
    except requests.RequestException as e:
        error = f"HTTP-Error: {e}"
    print(f"{resp.status_code}: {resp.text}")
    if resp.status_code != 200:
        error = f"Error: server returned status {resp.status_code}"
    if error is not None:
        return jsonify(error=error), 500
    return jsonify(success=True, token=token, expires_at=expires_at.isoformat())


# ----------------------
# User-Update Endpoint
# ----------------------
@app.post("/user/update")
def user_update() -> Response:
    email, err = get_authenticated_email()
    if err:
        return err
    data: dict = request.get_json(force=True)
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    comment = data.get("comment")
    conn = db_connect()
    conn.execute(
        "UPDATE users SET first_name = ?, last_name = ?, comment = ? "
        "WHERE email = ?",
        (first_name, last_name, comment, email)
    )
    conn.commit()
    conn.close()
    return jsonify(success=True)

# ----------------------
# Admin Endpoints
# ----------------------


# ----------------------
# User-Create Endpoint
# ----------------------
@app.post("/admin/create_user")
def admin_create_user() -> Response:
    # Auth prüfen
    _, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    data: dict = request.get_json(force=True)
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    role = data.get("role", "viewer")
    comment = data.get("comment")
    if not email or not password:
        return jsonify(error="email and password required"), 400
    pw_hash = bcrypt.hash(password)
    conn = db_connect()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, first_name, last_name, role, disabled, comment) "
            "VALUES (?, ?, ?, ?, ?, 0, ?)",
            (email, pw_hash, first_name, last_name, role, comment)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify(error=f"user with email '{email}' already exists"), 409
    finally:
        conn.close()
    return jsonify(success=True, email=email)


# ----------------------
# User-Update Endpoint
# ----------------------
@app.post("/admin/update_user")
def admin_update_user() -> Response:
    # Auth prüfen
    _, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    data: dict = request.get_json(force=True)
    email = data.get("email")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    role = data.get("role", "viewer")
    disabled = data.get("disabled", 0)
    comment = data.get("comment")
    if not email:
        return jsonify(error="email required"), 400
    conn = db_connect()
    try:
        conn.execute(
            "UPDATE users SET first_name = ?, last_name = ?, role = ?, disabled = ?, comment = ? "
            "WHERE email = ?",
            (first_name, last_name, role, disabled, comment, email)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify(error=f"user with email '{email}' already exists"), 409
    finally:
        conn.close()
    return jsonify(success=True, email=email)


# ----------------------
# User-Delete Endpoint
# ----------------------
@app.post("/admin/delete_user")
def admin_delete_user() -> Response:
    # Auth prüfen
    _, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    data: dict = request.get_json(force=True)
    email = data.get("email")
    if not email:
        return jsonify(error="email required"), 400
    conn = db_connect()
    cur = conn.execute(
        "DELETE FROM users WHERE email = ?",
        (email,)
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if deleted == 0:
        return jsonify(error="user not found"), 404
    return jsonify(success=True, email=email)


# ----------------------
# User-Password Endpoint
# ----------------------
@app.post("/admin/update_password")
def admin_update_password() -> Response:
    # Auth prüfen
    _, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    data: dict = request.get_json(force=True)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify(error="email and password required"), 400
    pw_hash = bcrypt.hash(password)
    conn = db_connect()
    cur = conn.execute(
        "UPDATE users SET password_hash = ? "
        "WHERE email = ?",
        (pw_hash, email)
    )
    modified = cur.rowcount
    conn.commit()
    conn.close()
    if modified == 0:
        return jsonify(error=f"user with email '{email}' not found"), 409
    return jsonify(success=True)


# ----------------------
# Get-Users Endpoint
# ----------------------
@app.get("/admin/get_users")
def admin_get_users() -> Response:
    # Auth prüfen
    _, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    conn = db_connect()
    cur = conn.execute("SELECT email, first_name, last_name, comment, role, disabled, created_at FROM users")
    users = [dict(row) for row in cur.fetchall()]
    for user in users:
        user["created_at"] = db_timestamp_to_epoch_seconds(user["created_at"])
    conn.close()
    return jsonify(users=users)


# ----------------------
# Start App
# ----------------------
if __name__ == "__main__":
    # Hinweis: Für Prod: WSGI-Server wie gunicorn + HTTPS-Frontend (z. B. nginx) verwenden
    host = os.environ.get("LISTEN_HOST", "127.0.0.1")
    port = int(os.environ.get("LISTEN_PORT", "3000"))
    debug = os.environ.get("AUTH_DEBUG", "0") == "1"
    print(f"Starting Auth-Service on {host}:{port} (Debug={debug})")
    # Starte mit waitress, falls verfügbar; sonst Fallback auf Flask-Dev-Server
    try:
        from waitress import serve
        if debug:
            import logging
            logger = logging.getLogger('waitress')
            logger.setLevel(logging.INFO)
        serve(app, host=host, port=port)
    except Exception:
        app.run(host=host, port=port, debug=debug)
