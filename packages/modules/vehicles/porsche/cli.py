#!/usr/bin/env python3
"""Kleines CLI zum Live-Test des Porsche-Connect-Moduls.

Testet den echten Login und SoC-Abruf mit deinen My-Porsche-Zugangsdaten,
bevor das Modul auf der openWB konfiguriert wird.

Beispiele:
    python cli.py soc  --email you@example.com --password 'geheim'
    python cli.py soc  --email you@example.com --password 'geheim' --vin WP0ZZZ...
    python cli.py list --email you@example.com --password 'geheim'
    python cli.py charge on  --email ... --password ... --vin WP0ZZZ...

Zugangsdaten koennen auch per Umgebungsvariablen PORSCHE_EMAIL / PORSCHE_PASSWORD
gesetzt werden (dann muessen --email/--password nicht angegeben werden).
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

# api.py als Nachbar-Modul importierbar machen (standalone lauffaehig)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import api  # noqa: E402


def build_client(args) -> "api.PorscheConnectApi":
    email = args.email or os.environ.get("PORSCHE_EMAIL")
    password = args.password or os.environ.get("PORSCHE_PASSWORD")
    if not email or not password:
        sys.exit("Bitte --email/--password angeben (oder PORSCHE_EMAIL/PORSCHE_PASSWORD setzen).")
    # Lokaler Token-Cache NUR fuer dieses CLI - das Modul selbst speichert keine Dateien.
    token_file = Path(__file__).resolve().parent / f".token_{args.vehicle_id}.json"
    token = {}
    try:
        token = json.loads(token_file.read_text())
    except (FileNotFoundError, ValueError):
        pass

    def persist(tok):
        try:
            token_file.write_text(json.dumps(tok))
        except OSError:
            pass

    return api.PorscheConnectApi(email, password, vehicle_id=args.vehicle_id,
                                 token=token, persist_cb=persist)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Porsche-Connect-Modul Live-Test")
    parser.add_argument("--email")
    parser.add_argument("--password")
    parser.add_argument("--vin", default=None)
    parser.add_argument("--vehicle-id", type=int, default=0, help="openWB-Fahrzeug-ID fuer den Token-Cache")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug-Logging")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("soc", help="SoC/Reichweite/Kilometerstand abrufen")
    sub.add_parser("list", help="Fahrzeuge im Konto auflisten")
    charge = sub.add_parser("charge", help="Sofortladen starten/stoppen")
    charge.add_argument("state", choices=["on", "off"])
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    client = build_client(args)
    try:
        if args.cmd == "list":
            print(json.dumps(client.list_vehicles(), indent=2, ensure_ascii=False))
        elif args.cmd == "soc":
            soc, range_km, ts, odometer = client.fetch_soc(args.vin)
            print(f"SoC:            {soc} %")
            print(f"Reichweite:     {range_km} km")
            print(f"Kilometerstand: {odometer} km")
            print(f"Zeitstempel:    {ts}")
        elif args.cmd == "charge":
            result = client.direct_charge(args.vin, args.state == "on")
            print(f"Direct Charging {args.state}: {result}")
    except api.PorscheCaptchaRequired as e:
        sys.exit(f"CAPTCHA erforderlich: {e}")
    except api.PorscheWrongCredentials as e:
        sys.exit(f"Zugangsdaten falsch: {e}")
    except api.PorscheApiError as e:
        sys.exit(f"Fehler: {e}")


if __name__ == "__main__":
    main()
