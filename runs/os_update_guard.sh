#!/bin/bash

# Return 0 only for the explicitly incompatible operating systems. Future
# Debian versions must not accidentally trigger a downgrade through this guard.
requiresSystemUpdate() {
	local VERSION_CODENAME=""
	[[ -r /etc/os-release ]] || return 2
	source /etc/os-release || return 2
	[[ -n $VERSION_CODENAME ]] || return 2
	case "$VERSION_CODENAME" in
		bullseye|bookworm) return 0 ;;
		*) return 1 ;;
	esac
}

# Also used by main.py, since old installed service units ignore failures in
# ExecStartPre. This mode checks only; it must never launch another update.
if [[ ${BASH_SOURCE[0]} == "$0" && ${1:-} == "--check-start" ]]; then
	requiresSystemUpdate
	case "$?" in
		1) exit 0 ;;
		*) exit 1 ;;
	esac
fi

selectLegacyReleaseTag() {
	# 2.5 requires the new OS. Never let the regular Release selector choose
	# 2.5 (or a later major version) when recovering an older installation.
	latestTagByPattern '^2\.[0-4]\.[0-9]+(-Patch\.[0-9]+)?$'
}

publishSystemUpdateMessage() {
	# Use the system Python, not the incompatible application's virtualenv.
	# Fixed text only. Missing MQTT must not prevent recovery to Release.
	python3 - <<'PY'
import json
import subprocess
import time

message = (
    "openWB 2.5.x benötigt ein Systemupdate. "
    "Bitte zuerst das OS-Update durchführen. "
    "Neustart auf das aktuelle Release wird durchgeführt."
)
try:
    subprocess.run(
        ["mosquitto_pub", "-h", "127.0.0.1", "-p", "1886",
         "-t", "openWB/system/messages/" + str(int(time.time() * 1000)),
         "-q", "1", "-r", "-s"],
        input=json.dumps({"source": "command", "type": "warning",
                          "message": message, "timestamp": int(time.time())}),
        universal_newlines=True, timeout=3, check=True,
    )
except Exception:
    pass
PY
}
