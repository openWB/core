#!/usr/bin/env python3
"""
Einfacher Token-Client für das Forgot-Password-System.
Sendet E-Mail und Token an den Server.
"""

import argparse
import json
import sys

try:
    import requests
except ImportError:
    print("Bitte zuerst installieren: pip install requests", file=sys.stderr)
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser(
        description="Token-Client: sendet E-Mail und Token an den Server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python3 token_client.py --email user@example.com --token "mein-geheimes-token"
  python3 token_client.py -e user@example.com -t "token123" --debug
  python3 token_client.py -e user@example.com -t "token123" --url https://openwb.de/forgotpassword/send_token.php
        """
    )

    parser.add_argument("-e", "--email", required=True, help="E-Mail-Adresse")
    parser.add_argument("-t", "--token", required=True, help="Token zum Übertragen")
    parser.add_argument("--url", default="https://openwb.de/forgotpassword/send_token.php",
                        help="Server-URL (Default: https://openwb.de/forgotpassword/send_token.php)")
    parser.add_argument("--timeout", type=int, default=15,
                        help="HTTP-Timeout in Sekunden (Default: 15)")
    parser.add_argument("--debug", action="store_true",
                        help="Debug-Ausgaben aktivieren")

    args = parser.parse_args()

    # Validierung
    if "@" not in args.email:
        print("Fehler: Ungültige E-Mail-Adresse", file=sys.stderr)
        sys.exit(1)

    if not args.token.strip():
        print("Fehler: Token darf nicht leer sein", file=sys.stderr)
        sys.exit(1)

    payload = {
        "email": args.email,
        "token": args.token,
    }

    if args.debug:
        print(f"DEBUG: URL: {args.url}")
        print(f"DEBUG: Payload: {json.dumps(payload, indent=2)}")
        print(f"DEBUG: Timeout: {args.timeout}s")
        print("DEBUG: Sende Request...")

    try:
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Token-Client/1.0'
        }

        resp = requests.post(
            args.url,
            json=payload,
            headers=headers,
            timeout=args.timeout
        )

    except requests.exceptions.Timeout:
        print(f"Fehler: Timeout nach {args.timeout} Sekunden", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"Fehler: Kann keine Verbindung zu {args.url} herstellen", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"HTTP-Fehler: {e}", file=sys.stderr)
        sys.exit(1)

    # Response anzeigen
    print(f"✓ POST {args.url}")
    print(f"✓ Status: {resp.status_code}")

    if args.debug:
        print(f"DEBUG: Response Headers: {dict(resp.headers)}")

    # Content anzeigen
    content_type = resp.headers.get("Content-Type", "").lower()
    if "application/json" in content_type:
        try:
            data = resp.json()
            print("Response:")
            print(json.dumps(data, ensure_ascii=False, indent=2))

            # Status auswerten
            if resp.status_code == 200 and data.get('ok'):
                print("\n✓ Erfolgreich! Prüfen Sie Ihr E-Mail-Postfach.")
            elif data.get('error'):
                print(f"\n✗ Fehler: {data['error']}", file=sys.stderr)
                sys.exit(1)

        except json.JSONDecodeError:
            print("Response (kein gültiges JSON):")
            print(resp.text)
    else:
        print("Response:")
        print(resp.text)

    if resp.status_code >= 400:
        sys.exit(1)


if __name__ == "__main__":
    main()
