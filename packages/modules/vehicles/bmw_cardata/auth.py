#!/usr/bin/env python3
"""
BMW CarData – Device Code Flow für openWB
"""

import base64
import hashlib
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BMW_AUTH_URL = "https://customer.bmwgroup.com/gcdm/oauth"
TOKEN_FILE = "/var/www/html/openWB/data/bmw_cardata_tokens.json"
STATUS_FILE = "/var/www/html/openWB/data/bmw_cardata_auth_status.json"
SCOPE = "authenticate_user openid cardata:api:read cardata:streaming:read"


def http_post(url: str, data: dict) -> dict:
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=encoded, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def generate_pkce():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def write_status(data: dict):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(STATUS_FILE, 0o600)


def read_status() -> dict:
    if not os.path.exists(STATUS_FILE):
        return {}
    with open(STATUS_FILE) as f:
        return json.load(f)


def save_tokens(tokens: dict):
    data = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "id_token": tokens.get("id_token"),
        "expires_at": time.time() + tokens.get("expires_in", 3600) - 60,
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)


def start_auth(client_id: str):
    verifier, challenge = generate_pkce()

    response = http_post(
        f"{BMW_AUTH_URL}/device/code",
        {
            "client_id": client_id,
            "response_type": "device_code",
            "scope": SCOPE,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )

    status = {
        "connected": False,
        "client_id": client_id,
        "device_code": response["device_code"],
        "user_code": response["user_code"],
        "verification_uri": response.get("verification_uri_complete", response.get("verification_uri", "")),
        "interval": response.get("interval", 5),
        "expires_at": time.time() + response.get("expires_in", 300),
        "code_verifier": verifier,
        "message": "BMW Auth gestartet. Bitte BMW-Seite öffnen und Code eingeben.",
        "error": "",
    }
    write_status(status)
    return status


def poll_auth():
    status = read_status()
    if not status:
        return {
            "connected": False,
            "message": "Noch keine BMW Auth gestartet.",
            "error": "",
        }

    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE) as f:
                tokens = json.load(f)
            if tokens.get("access_token") and tokens.get("refresh_token"):
                status["connected"] = True
                status["message"] = "BMW verbunden."
                status["error"] = ""
                write_status(status)
                return status
        except Exception:
            pass

    if time.time() > status.get("expires_at", 0):
        status["connected"] = False
        status["error"] = "BMW Auth ist abgelaufen. Bitte erneut starten."
        status["message"] = ""
        write_status(status)
        return status

    try:
        tokens = http_post(
            f"{BMW_AUTH_URL}/token",
            {
                "client_id": status["client_id"],
                "device_code": status["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "code_verifier": status["code_verifier"],
            },
        )
        save_tokens(tokens)

        status["connected"] = True
        status["message"] = "BMW Auth erfolgreich abgeschlossen."
        status["error"] = ""
        status["user_code"] = ""
        status["verification_uri"] = ""
        status["device_code"] = ""
        status["code_verifier"] = ""

        write_status(status)
        return status

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass

        err = ""
        try:
            err = json.loads(body).get("error", "")
        except Exception:
            pass

        if err == "authorization_pending":
            status["connected"] = False
            status["message"] = "Warte auf BMW-Bestätigung..."
            status["error"] = ""
            write_status(status)
            return status

        if err == "slow_down":
            status["connected"] = False
            status["message"] = "BMW fordert langsameres Polling."
            status["error"] = ""
            write_status(status)
            return status

        if err == "authorization_declined":
            status["connected"] = False
            status["message"] = ""
            status["error"] = "BMW Auth wurde abgelehnt."
            write_status(status)
            return status

        status["connected"] = False
        status["error"] = body[:300] or f"HTTP {e.code}"
        status["message"] = ""
        write_status(status)
        return status


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python3 auth.py start <client_id>")
        print("  python3 auth.py poll")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        if len(sys.argv) != 3:
            print("Verwendung: python3 auth.py start <client_id>")
            sys.exit(1)
        result = start_auth(sys.argv[2])
        print(json.dumps(result, indent=2))
    elif command == "poll":
        result = poll_auth()
        print(json.dumps(result, indent=2))
    else:
        print("Unbekannter Befehl.")
        sys.exit(1)