"""Run manually in a private local terminal, never through a cloud agent tool.

No credentials as command-line arguments, no files, no wallbox access.
The output is private and must not be copied into an issue or cloud chat.
"""
from datetime import datetime, timezone
from getpass import getpass, GetPassWarning
import logging
import os
import sys
import warnings

if __package__:
    from ..src.api import NissanClient, NissanError
else:
    # Isolated/embedded Python needs the module root to find the internal src package.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.api import NissanClient, NissanError


AGENT_ENVIRONMENT_VARIABLES = ("CODEX_THREAD_ID", "CODEX_SANDBOX", "CODEX_CI")
EXIT_SUCCESS = 0
EXIT_QUERY_FAILED = 1
EXIT_UNSAFE_TERMINAL = 2
EXIT_INTERRUPTED = 130


def main():
    if any(os.environ.get(name) for name in AGENT_ENVIRONMENT_VARIABLES):
        print("Aborted: Please run in a private terminal outside a Codex or agent session.")
        return EXIT_UNSAFE_TERMINAL
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Aborted: An interactive local terminal is required; no redirection or pipes.")
        return EXIT_UNSAFE_TERMINAL
    print("Local MyNISSAN test: This request sends credentials directly to Nissan.")
    print("No wallbox connection. No files are written. The result is confidential.")
    print("Only use outside cloud agents, terminal recording and screen sharing.")
    print("The environment check is a precaution, not a complete technical safeguard.")
    if input("Query cached battery and odometer data now? [y/N] ").strip().lower() != "y":
        return EXIT_SUCCESS
    try:
        with warnings.catch_warnings():
            # getpass must abort instead of falling back to an echoed input.
            warnings.simplefilter("error", GetPassWarning)
            user = getpass("MyNISSAN email (hidden): ")
            password = getpass("MyNISSAN password (hidden): ")
            vin = getpass("VIN (hidden; leave blank for a single vehicle): ")
        # This separate process owns logging; never expose dependency debug output.
        logging.disable(logging.CRITICAL)
        status = NissanClient(user, password, vin).fetch_battery(include_odometer=True)
        measured = datetime.fromtimestamp(status.measurement_unix_seconds, tz=timezone.utc).astimezone()
        print("SoC: {:g} %".format(status.soc_percent))
        print("Measurement time: " + measured.isoformat())
        if status.range_km is not None:
            print("Range: {:g} km".format(status.range_km))
        if status.odometer_km is not None:
            print("Odometer: {:g} km (measurement time unavailable)".format(status.odometer_km))
        else:
            print("Odometer: Not available; battery query succeeded.")
        print("Compare with MyNISSAN. Do not copy values, screenshots or credentials into a cloud chat.")
        return EXIT_SUCCESS
    except GetPassWarning:
        print("Hidden input is unavailable in this terminal. Aborted.")
        return EXIT_UNSAFE_TERMINAL
    except NissanError as error:
        print("Query failed: " + str(error))
        return EXIT_QUERY_FAILED
    except (KeyboardInterrupt, EOFError):
        print("Aborted.")
        return EXIT_INTERRUPTED
    except Exception:
        # Never print an unexpected exception/traceback with potentially private data.
        print("Unexpected local error; no confidential details were displayed.")
        return EXIT_QUERY_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
