#!/bin/bash
set -euo pipefail

base_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
venv="$base_dir/.venv"

if [[ -f "$base_dir/.venvs/.lock" ]]; then
	exec 9<"$base_dir/.venvs/.lock"
	flock -s 9
	base_python=${OPENWB_PYTHON:-/usr/bin/python3}
	expected_fingerprint=$({
		sha256sum "$base_dir/requirements.txt"
		"$base_python" -c 'import os, sys; print(os.path.realpath(sys.executable), sys.version)'
	} | sha256sum | cut -d ' ' -f 1)
	if [[ -L "$venv" && -f "$venv/.openwb-ready" && -f "$venv/.openwb-lock" && -x "$venv/bin/python" ]]; then
		venv=$(readlink -f "$venv")
		case "$venv" in
			"$base_dir"/.venvs/env.*)
				if [[ $(<"$venv/.openwb-ready") != "$expected_fingerprint" ]]; then
					echo "The active Python environment does not match the current requirements; refusing to start" >&2
					exit 1
				fi
				exec 8<"$venv/.openwb-lock"
				flock -s 8
				exec 9<&-
				export PATH="$venv/bin:$PATH"
				exec "$venv/bin/python" "$@"
				;;
		esac
	fi
	exec 9<&-
fi
if [[ -f "$base_dir/.venvs/.legacy" && ! -e "$base_dir/.venvs/.migrated" ]]; then
	legacy_python=${OPENWB_LEGACY_PYTHON:-/usr/bin/python3}
	if [[ -x "$legacy_python" ]] && "$legacy_python" -c 'import importlib.util,sys; sys.exit(0 if importlib.util.find_spec("telnetlib3") is not None or importlib.util.find_spec("telnetlib") is not None else 1)' >/dev/null 2>&1; then
		exec "$legacy_python" "$@"
	fi
	echo "Cannot use the legacy Python interpreter: neither telnetlib3 nor telnetlib is available" >&2
	exit 1
fi

echo "No usable openWB Python environment is available" >&2
exit 1
