#!/bin/bash
set -euo pipefail

base_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
venv="$base_dir/.venv"

if [[ -f "$base_dir/.venvs/.lock" ]]; then
	exec 9<"$base_dir/.venvs/.lock"
	flock -s 9
	if [[ -L "$venv" && -f "$venv/.openwb-ready" && -f "$venv/.openwb-lock" && -x "$venv/bin/python" ]]; then
		venv=$(readlink -f "$venv")
		case "$venv" in
			"$base_dir"/.venvs/env.*)
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
	exec /usr/bin/python3 "$@"
fi

echo "No usable openWB Python environment is available" >&2
exit 1
