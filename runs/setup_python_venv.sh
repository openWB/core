#!/bin/bash
set -euo pipefail

base_dir=$(cd "${1:?Missing openWB directory}" && pwd -P)
online=${2:-1}
python=${OPENWB_PYTHON:-/usr/bin/python3}
venv_link="$base_dir/.venv"
venv_dir="$base_dir/.venvs"

unset PYTHONHOME PYTHONPATH PIP_TARGET PIP_PREFIX PIP_ROOT PIP_USER
export PYTHONNOUSERSITE=1
umask 022

mkdir -p "$venv_dir"
exec 9>"$venv_dir/.lock"
flock 9

if [[ -L "$venv_link" ]]; then
	case $(readlink "$venv_link") in
		"$venv_dir"/env.*) ;;
		*) echo "Refusing to replace existing $venv_link" >&2; exit 1 ;;
	esac
elif [[ -e "$venv_link" ]]; then
	echo "Refusing to replace existing $venv_link" >&2
	exit 1
fi

if [[ -f "$venv_link/.openwb-ready" && ! -e "$venv_link/.openwb-lock" ]]; then
	touch "$venv_link/.openwb-unprotected" "$venv_link/.openwb-lock"
fi

remove_unused_envs() {
	local active_env candidate
	active_env=$(readlink -f "$venv_link" 2>/dev/null || true)
	for candidate in "$venv_dir"/env.*; do
		[[ -d "$candidate" && ! -L "$candidate" && "$candidate" != "$active_env" ]] || continue
		[[ ${candidate##*/} =~ ^env\.[a-zA-Z0-9]{8}$ ]] || continue
		if [[ ! -f "$candidate/.openwb-ready" ]]; then
			echo "Removing incomplete Python environment $candidate"
			if ! rm -rf -- "$candidate"; then
				echo "Failed to remove incomplete Python environment $candidate" >&2
			fi
			continue
		fi
		[[ -f "$candidate/.openwb-lock" && ! -e "$candidate/.openwb-unprotected" ]] || continue
		if ! exec 8<"$candidate/.openwb-lock"; then
			echo "Cannot lock Python environment $candidate" >&2
			continue
		fi
		if flock -n -x 8; then
			echo "Removing unused Python environment $candidate"
			if ! rm -rf -- "$candidate"; then
				echo "Failed to remove Python environment $candidate" >&2
			fi
		fi
		exec 8<&-
	done
}

if [[ ${3:-} == --boot-cleanup ]]; then
	boot_id=${4:?Missing system boot ID}
	previous_boot_id=
	if [[ -f "$venv_dir/.cleanup-boot-id" ]]; then
		previous_boot_id=$(<"$venv_dir/.cleanup-boot-id")
	fi
	if [[ "$boot_id" != "$previous_boot_id" ]]; then
		printf '%s\n' "$boot_id" > "$venv_dir/.cleanup-boot-id"
		if [[ -n "$previous_boot_id" ]]; then
			remove_unused_envs
		fi
	fi
	exit 0
fi

fingerprint=$({ sha256sum "$base_dir/requirements.txt"; "$python" -c 'import os, sys; print(os.path.realpath(sys.executable), sys.version)'; } | sha256sum | cut -d ' ' -f 1)
if [[ -x "$venv_link/bin/python" && -f "$venv_link/.openwb-ready" ]] &&
	[[ $(<"$venv_link/.openwb-ready") == "$fingerprint" ]] &&
	"$venv_link/bin/python" -m pip check &&
	"$venv_link/bin/python" -c 'import aiohttp, evdev, grpc, jq, lxml, paho.mqtt.client, pymodbus, telnetlib3'; then
	rm -f "$venv_link/.openwb-fallback"
	touch "$venv_dir/.migrated"
	rm -f "$venv_dir/.legacy"
	echo "Python environment is up to date"
	exit 0
fi

use_existing_environment_fallback() {
	local active_env marker_tmp
	[[ -L "$venv_link" && -f "$venv_link/.openwb-ready" && -f "$venv_link/.openwb-lock" && -x "$venv_link/bin/python" ]] || return 1
	active_env=$(readlink -f "$venv_link") || return 1
	case "$active_env" in
		"$venv_dir"/env.*) ;;
		*) return 1 ;;
	esac
	if ! rm -f "$active_env/.openwb-fallback" ||
		! "$active_env/bin/python" -m pip check ||
		! "$active_env/bin/python" -c 'import aiohttp, evdev, grpc, jq, lxml, paho.mqtt.client, pymodbus, telnetlib3'; then
		return 1
	fi
	marker_tmp="$active_env/.openwb-fallback.$$"
	if ! printf '%s\n' "$fingerprint" > "$marker_tmp" || ! mv -f -- "$marker_tmp" "$active_env/.openwb-fallback"; then
		rm -f -- "$marker_tmp"
		return 1
	fi
	echo "Python environment rebuild failed; using the verified previous environment for this requirements fingerprint" >&2
	return 0
}

fail_rebuild() {
	local message=$1
	echo "$message" >&2
	if use_existing_environment_fallback; then
		exit 0
	fi
	exit 1
}

if [[ "$online" != 1 ]]; then
	fail_rebuild "Cannot install Python dependencies without a network connection"
fi

if ! new_env=$(mktemp -d "$venv_dir/env.XXXXXXXX"); then
	fail_rebuild "Cannot create a temporary Python environment"
fi
temporary_link=
cleanup() {
	if [[ -n "$new_env" ]]; then
		active_env=$(readlink -f "$venv_link" 2>/dev/null || true)
		if [[ "$active_env" != "$new_env" ]]; then
			rm -rf -- "$new_env"
		fi
	fi
	if [[ -n "$temporary_link" ]]; then
		rm -f -- "$temporary_link"
	fi
}
trap cleanup EXIT
if ! chmod 755 "$new_env"; then
	fail_rebuild "Cannot set permissions on the temporary Python environment"
fi

if ! "$python" -m venv "$new_env"; then
	fail_rebuild "Failed to create the Python virtual environment"
fi
binary_options=(--only-binary=:all:)
case $(dpkg --print-architecture) in
	arm64)
		evdev_source=${OPENWB_EVDEV_SOURCE:-/usr/lib/python3/dist-packages}
		site_packages=$("$new_env/bin/python" -c 'import sysconfig; print(sysconfig.get_path("purelib"))')
		evdev_metadata=
		for metadata_suffix in dist-info egg-info; do
			candidate="$evdev_source/evdev-1.9.1.$metadata_suffix"
			if [[ -d "$candidate" ]]; then
				evdev_metadata=$candidate
				break
			fi
		done
		if [[ ! -d "$evdev_source/evdev" || -z "$evdev_metadata" ]]; then
			fail_rebuild "Debian python3-evdev 1.9.1 is required on ARM64"
		fi
		if ! cp -a "$evdev_source/evdev" "$evdev_metadata" "$site_packages/"; then
			fail_rebuild "Failed to copy Debian evdev into the Python environment"
		fi
		;;
	arm*) ;;
	*) binary_options+=(--no-binary=evdev) ;;
esac
if ! "$new_env/bin/python" -m pip install --no-user "${binary_options[@]}" --extra-index-url https://www.piwheels.org/simple -r "$base_dir/requirements.txt"; then
	fail_rebuild "Failed to install Python dependencies"
fi
if ! "$new_env/bin/python" -m pip check; then
	fail_rebuild "Python dependency consistency check failed"
fi
if ! "$new_env/bin/python" -c 'import aiohttp, evdev, grpc, jq, lxml, paho.mqtt.client, pymodbus, telnetlib3'; then
	fail_rebuild "Python dependency import check failed"
fi
if ! touch "$new_env/.openwb-lock" || ! printf '%s\n' "$fingerprint" > "$new_env/.openwb-ready"; then
	fail_rebuild "Failed to mark the Python environment as ready"
fi
temporary_link="$venv_dir/.venv-link.$$"
if ! ln -s "$new_env" "$temporary_link" || ! mv -Tf "$temporary_link" "$venv_link"; then
	fail_rebuild "Failed to activate the new Python environment"
fi
new_env=
touch "$venv_dir/.migrated"
rm -f "$venv_dir/.legacy"
echo "Python environment installed"
exit 10
