#!/usr/bin/env python3
"""simpleAPI regression harness: diffs the old PHP endpoint against the new
Python endpoint for every parameter in the whitelist, so the HTTP-contract
port can be verified parameter-by-parameter against a real device instead of
by inspection.

Parameter names are imported directly from src/parameter_handler.py (the
single source of truth for the whitelist) rather than hand-copied here, so
the two can't drift apart silently.

Typical usage, before Apache's ProxyPass for /openWB/simpleAPI/ is deployed
(hits the old PHP file through Apache as today, and the new daemon directly
on its local port):

    python3 simpleAPI/regression_check.py \\
        --old-base-url "https://<host>/openWB/simpleAPI/simpleapi.php" \\
        --new-base-url "http://127.0.0.1:8099/"

Once the ProxyPass is live, the public URL serves the NEW backend for both
"old" and "new" - at that point this script can only confirm the new backend
answers consistently, not provide an old-vs-new diff anymore. Do the real
old-vs-new comparison beforehand (e.g. via an SSH tunnel to the new backend's
local port, or by temporarily pointing --old-base-url at a second device still
running the PHP version).

Write parameters are skipped by default - see --include-writes.
"""
import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.parameter_handler import (  # noqa: E402
    READ_PARAMETER_ORDER,
    WRITE_PARAMETER_ORDER,
    is_chargepoint_parameter,
    is_io_parameter,
)

# Fields whose name marks them as point-in-time event/publish data rather than
# live telemetry - these are expected to legitimately differ between two
# separate HTTP requests (even back-to-back, even against the same backend)
# and are excluded from the diff. Everything else (power, voltages, soc,
# fault_state, ...) is compared exactly, since both endpoints read the same
# retained MQTT state and should agree.
TIMESTAMP_FIELD_NAMES = {'timestamp', 'time'}
TIMESTAMP_FIELD_SUFFIX = '_timestamp'

# Conservative values for write parameters under --include-writes: chosen to
# be a no-op-ish or easily-reversible state change, not a disruptive one
# (e.g. chargepoint_lock=false rather than true, bat_power_reserve=0 rather
# than some nonzero reservation). 'vehicle' and 'set_io_output' are left out
# deliberately - see --vehicle-id/--io-output-name.
DEFAULT_WRITE_VALUES = {
    'set_chargemode': 'pv',
    'chargecurrent': '6',
    'minimal_pv_soc': '50',
    'minimal_permanent_current': '6',
    'max_price_eco': '10',
    'chargepoint_lock': 'false',
    'bat_mode': 'bat_mode',
    'bat_power_reserve': '0',
    'instant_charging_limit': 'none',
    'instant_charging_amount': '10',
    'instant_charging_soc': '80',
    'pv_charging_limit': 'none',
    'pv_charging_amount': '10',
    'pv_charging_soc': '80',
    'manual_soc': '50',
}


def is_timestamp_field(key: str) -> bool:
    return key in TIMESTAMP_FIELD_NAMES or key.endswith(TIMESTAMP_FIELD_SUFFIX)


def deep_diff(old: Any, new: Any, path: str, float_tolerance: float, diffs: List[str]) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            if is_timestamp_field(key):
                continue
            if key not in old:
                diffs.append(f"{path}.{key}: missing in OLD, NEW={new[key]!r}")
            elif key not in new:
                diffs.append(f"{path}.{key}: OLD={old[key]!r}, missing in NEW")
            else:
                deep_diff(old[key], new[key], f"{path}.{key}", float_tolerance, diffs)
        return

    if isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            diffs.append(f"{path}: length OLD={len(old)} NEW={len(new)}")
        for i, (o, n) in enumerate(zip(old, new)):
            deep_diff(o, n, f"{path}[{i}]", float_tolerance, diffs)
        return

    is_old_num = isinstance(old, (int, float)) and not isinstance(old, bool)
    is_new_num = isinstance(new, (int, float)) and not isinstance(new, bool)
    if is_old_num and is_new_num:
        if abs(float(old) - float(new)) > float_tolerance:
            diffs.append(f"{path}: OLD={old!r} NEW={new!r}")
        return

    if old != new:
        diffs.append(f"{path}: OLD={old!r} NEW={new!r}")


def fetch(base_url: str, query: Dict[str, Any], timeout: float,
          verify: bool) -> Tuple[Optional[int], Any, Optional[str]]:
    try:
        resp = requests.get(base_url, params=query, timeout=timeout, verify=verify)
    except requests.RequestException as exc:
        return None, None, str(exc)
    try:
        return resp.status_code, resp.json(), None
    except ValueError:
        return resp.status_code, resp.text, None


def compare(old_base: str, new_base: str, query: Dict[str, Any], path: str,
            float_tolerance: float, timeout: float, verify: bool) -> Tuple[Optional[bool], List[str]]:
    old_status, old_body, old_err = fetch(old_base, query, timeout, verify)
    new_status, new_body, new_err = fetch(new_base, query, timeout, verify)

    if old_err or new_err:
        return False, [f"request failed: OLD error={old_err!r} NEW error={new_err!r}"]
    if old_status != new_status:
        return False, [f"HTTP status: OLD={old_status} NEW={new_status}"]

    diffs: List[str] = []
    deep_diff(old_body, new_body, path, float_tolerance, diffs)
    return (len(diffs) == 0), diffs


def selected(param: str, only: Optional[List[str]], skip: List[str]) -> bool:
    if skip and param in skip:
        return False
    if only:
        return param in only
    return True


def build_common_params(args: argparse.Namespace) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    for item in args.param:
        key, _, value = item.partition('=')
        params[key] = value
    if args.token:
        params['token'] = args.token
    if args.username is not None:
        params['username'] = args.username
    if args.password is not None:
        params['password'] = args.password
    return params


def check_read_param(param: str, args: argparse.Namespace, common: Dict[str, Any]) -> Tuple[Optional[bool], List[str]]:
    query = {**common, param: args.id}
    return compare(args.old_base_url, args.new_base_url, query, param,
                   args.float_tolerance, args.timeout, not args.insecure)


def check_list_components(args: argparse.Namespace, common: Dict[str, Any]) -> Tuple[Optional[bool], List[str]]:
    query = {**common, 'list_components': 'true'}
    return compare(args.old_base_url, args.new_base_url, query, 'list_components',
                   args.float_tolerance, args.timeout, not args.insecure)


def check_write_param(param: str, args: argparse.Namespace, common: Dict[str, Any]) -> Tuple[Optional[bool], List[str]]:
    if param == 'vehicle':
        if not args.vehicle_id:
            return None, ["skipped: pass --vehicle-id to exercise this parameter"]
        value: Any = args.vehicle_id
    elif param == 'set_io_output':
        if not args.io_output_name:
            return None, ["skipped: pass --io-output-name (and --io-output-value) to exercise this parameter"]
        value = args.io_output_value
    else:
        value = DEFAULT_WRITE_VALUES[param]

    query = {**common, param: value}
    if is_chargepoint_parameter(param):
        query['chargepoint_nr'] = args.chargepoint_nr
    if is_io_parameter(param):
        query['io_nr'] = args.io_nr
        if param == 'set_io_output':
            query['io_output'] = args.io_output_name

    return compare(args.old_base_url, args.new_base_url, query, param,
                   args.float_tolerance, args.timeout, not args.insecure)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--old-base-url', required=True,
        help="old PHP simpleAPI endpoint, e.g. https://<host>/openWB/simpleAPI/simpleapi.php")
    parser.add_argument(
        '--new-base-url', required=True,
        help="new Python endpoint, e.g. http://127.0.0.1:8099/ "
             "(or the public URL once Apache's ProxyPass is live)")
    parser.add_argument(
        '--id', default='auto',
        help="device id used for every read parameter (default: 'auto', resolves to the lowest known id "
             "of the matching component type on each side)")
    parser.add_argument('--token', help="bare 'token' auth parameter sent with every request")
    parser.add_argument('--username')
    parser.add_argument('--password')
    parser.add_argument(
        '--param', action='append', default=[], metavar='KEY=VALUE',
        help="extra query parameter sent with every request (repeatable), e.g. --param debug=true")
    parser.add_argument('--only', nargs='+', metavar='PARAM', help="only check these exact parameter names")
    parser.add_argument('--skip', nargs='+', metavar='PARAM', default=[], help="skip these parameter names")
    parser.add_argument(
        '--include-writes', action='store_true',
        help="also exercise write parameters - performs REAL write operations against whatever device "
             "--old-base-url/--new-base-url point at")
    parser.add_argument('--chargepoint-nr', default='auto', help="chargepoint_nr for write-parameter checks")
    parser.add_argument('--io-nr', default='auto', help="io_nr for write-parameter checks")
    parser.add_argument(
        '--io-output-name',
        help="io_output name required to exercise set_io_output under --include-writes; omitted -> "
             "set_io_output is skipped even with --include-writes")
    parser.add_argument('--io-output-value', default='0', help="value to write for set_io_output (default: 0)")
    parser.add_argument(
        '--vehicle-id',
        help="vehicle id required to exercise the 'vehicle' write parameter under --include-writes; "
             "omitted -> 'vehicle' is skipped even with --include-writes")
    parser.add_argument(
        '--float-tolerance', type=float, default=0.0,
        help="allowed absolute difference for numeric leaves, to absorb live power/voltage jitter between "
             "the two near-simultaneous requests (default: 0.0, exact match)")
    parser.add_argument('--timeout', type=float, default=10.0, help="per-request HTTP timeout in seconds")
    parser.add_argument('--max-diff-lines', type=int, default=20, help="diff lines printed per failing parameter")
    parser.add_argument(
        '-k', '--insecure', action='store_true',
        help="don't verify TLS certificates (e.g. for a device's self-signed HTTPS cert)")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    common = build_common_params(args)

    if args.insecure:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    read_params = [p for p in READ_PARAMETER_ORDER if selected(p, args.only, args.skip)]
    write_params = [p for p in WRITE_PARAMETER_ORDER if selected(p, args.only, args.skip)]
    checks = (['list_components'] if selected('list_components', args.only, args.skip) else []) + read_params
    if args.include_writes:
        checks += write_params

    print("simpleAPI regression check")
    print(f"  OLD (PHP):    {args.old_base_url}")
    print(f"  NEW (Python): {args.new_base_url}")
    print(f"  read parameters: {len(read_params)}")

    if args.include_writes:
        print()
        print("WARNING: --include-writes performs REAL write operations (chargemode, chargecurrent,")
        print("bat_mode, lock state, io outputs, ...) against whatever device both base URLs point at.")
        print("Only run this against a non-production test device. Starting in 3 seconds...")
        print(f"  write parameters: {len(write_params)}")
        time.sleep(3)
    print()

    name_width = max((len(name) for name in checks), default=10) + 2
    print(f"{'PARAMETER':<{name_width}}RESULT")
    print('-' * (name_width + 6))

    results: List[Tuple[str, Optional[bool], List[str]]] = []
    for name in checks:
        if name == 'list_components':
            ok, diffs = check_list_components(args, common)
        elif name in write_params:
            ok, diffs = check_write_param(name, args, common)
        else:
            ok, diffs = check_read_param(name, args, common)
        results.append((name, ok, diffs))

        status = 'PASS' if ok is True else 'SKIP' if ok is None else 'FAIL'
        print(f"{name:<{name_width}}{status}", flush=True)
        if ok is False:
            for line in diffs[:args.max_diff_lines]:
                print(f"    {line}")
            if len(diffs) > args.max_diff_lines:
                print(f"    ... {len(diffs) - args.max_diff_lines} more diff line(s)")

    passed = sum(1 for _, ok, _ in results if ok is True)
    failed = sum(1 for _, ok, _ in results if ok is False)
    skipped = sum(1 for _, ok, _ in results if ok is None)
    print()
    print(f"{passed} passed, {failed} failed, {skipped} skipped (of {len(results)} checked)")

    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
