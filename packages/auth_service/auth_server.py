#!/usr/bin/env python3
# auth_server.py — Flask Auth-Service mit JWT, Refresh-Rotation, DynSec-Integration, SQlite
# Python 3.11

from typing import Optional
from flask import Flask, request, jsonify, make_response
import os
import sqlite3
from passlib.hash import bcrypt
# import secrets
# import requests
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
COOKIE_NAME = "mqtt_auth"

# ----------------------
# Flask App
# ----------------------
app = Flask(__name__)


# ----------------------
# DB Hilfsfunktionen
# ----------------------
def db_connect():
    db_connection = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    db_connection.row_factory = sqlite3.Row
    return db_connection


# ----------------------
# Nutzer-Logik
# ----------------------
def get_user(email):
    db_connection = db_connect()
    cur = db_connection.execute(
        "SELECT email, password_hash, first_name, last_name, role, disabled, comment FROM users WHERE email = ?",
        (email,)
    )
    row = cur.fetchone()
    db_connection.close()
    return row


def verify_user_password(email, password):
    row = get_user(email)
    if not row or row["disabled"]:
        return False
    try:
        return bcrypt.verify(password, row["password_hash"])
    except Exception:
        return False


def verify_user_role(email, role="admin"):
    row = get_user(email)
    if row and not row["disabled"] and row["role"] == role:
        return True
    return False


# ----------------------
# Auth-Hilfsfunktion
# ----------------------
def get_authenticated_email(required_role: Optional[str] = None):
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
def set_cookie(resp, name, value, expires=None):
    resp.set_cookie(
        name,
        value,
        httponly=False,
        secure=TLS_ONLY,
        samesite="Strict",
        expires=expires
    )


@app.post("/api/login")
def web_login():
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
def logout():
    resp = make_response(jsonify(success=True))
    # Cookie löschen
    set_cookie(resp, COOKIE_NAME, "", expires=0)
    return resp


@app.get("/api/health")
def health():
    return jsonify(status="ok")


# ----------------------
# Admin Endpoints
# ----------------------


# ----------------------
# User-Create Endpoint
# ----------------------
@app.post("/admin/create_user")
def admin_create_user():
    # Auth prüfen
    _, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    data = request.get_json(force=True)
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
def admin_update_user():
    # Auth prüfen
    _, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    data = request.get_json(force=True)
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
def admin_delete_user():
    # Auth prüfen
    _, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    data = request.get_json(force=True)
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
def admin_update_password():
    # Auth prüfen
    _, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    data = request.get_json(force=True)
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
    return jsonify(success=True, email=email)


# ----------------------
# Get-Users Endpoint
# ----------------------
@app.get("/admin/get_users")
def admin_get_users():
    # Auth prüfen
    email, err = get_authenticated_email(required_role="admin")
    if err:
        return err
    conn = db_connect()
    cur = conn.execute("SELECT email, first_name, last_name, comment, role, disabled, created_at FROM users")
    users = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(users=users, requested_by=email)


# ----------------------
# Start App
# ----------------------
if __name__ == "__main__":
    # Hinweis: Für Prod: WSGI-Server wie gunicorn + HTTPS-Frontend (z. B. nginx) verwenden
    host = os.environ.get("LISTEN_HOST", "127.0.0.1")
    port = int(os.environ.get("LISTEN_PORT", "3000"))
    debug = os.environ.get("AUTH_DEBUG", "0") == "1"
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
