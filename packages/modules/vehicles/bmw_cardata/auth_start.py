#!/usr/bin/env python3
import json
import subprocess
import sys


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"connected": False, "error": "Client ID fehlt."}))
        sys.exit(1)

    client_id = sys.argv[1]

    result = subprocess.run(
        ["python3", "/var/www/html/openWB/packages/modules/vehicles/bmw_cardata/auth.py", "start", client_id],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(json.dumps({"connected": False, "error": result.stderr.strip() or result.stdout.strip()}))
        sys.exit(1)

    try:
        print(result.stdout.strip())
    except Exception:
        print(json.dumps({"connected": False, "error": "Auth konnte nicht gestartet werden."}))
        sys.exit(1)


if __name__ == "__main__":
    main()