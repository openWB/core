#!/bin/bash

set -euo pipefail

BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON_VERSION_FILE="${BASE_DIR}/data/config/python_runtime_version.txt"
PYTHON_VERSION="${PYTHON_VERSION:-}"
PYTHON_MAJOR_MINOR=""
TARGET_ARCH="${1:-${TARGET_ARCH:-}}"
TARGET_OS_VARIANT="${2:-${TARGET_OS_VARIANT:-}}"
OUTPUT_DIR="${OUTPUT_DIR:-${BASE_DIR}/dist/python-wheelhouse}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-${BASE_DIR}/requirements.txt}"
PYTHON_RUNTIME_REPO_OWNER="${PYTHON_RUNTIME_REPO_OWNER:-openWB}"
PYTHON_RUNTIME_REPO_NAME="${PYTHON_RUNTIME_REPO_NAME:-python-runtime}"
PYTHON_RUNTIME_TAG=""
PYTHON_RUNTIME_BASE_URL="${PYTHON_RUNTIME_BASE_URL:-}"
PYTHON_RUNTIME_ARTIFACT_PATH="${PYTHON_RUNTIME_ARTIFACT_PATH:-}"

log() {
	echo "[build_python_wheelhouse] $*"
}

init_python_version() {
	if [[ -z "${PYTHON_VERSION}" && -f "${PYTHON_VERSION_FILE}" ]]; then
		PYTHON_VERSION=$(head -n 1 "${PYTHON_VERSION_FILE}" | tr -d '[:space:]')
	fi

	if [[ -z "${PYTHON_VERSION}" ]]; then
		log "ERROR: No Python version configured."
		return 1
	fi

	if [[ ! "${PYTHON_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
		log "ERROR: Invalid Python version '${PYTHON_VERSION}'."
		return 1
	fi

	PYTHON_MAJOR_MINOR="${PYTHON_VERSION%.*}"
	PYTHON_RUNTIME_TAG="python-runtime-${PYTHON_VERSION}"

	if [[ -z "${PYTHON_RUNTIME_BASE_URL}" ]]; then
		PYTHON_RUNTIME_BASE_URL="https://github.com/${PYTHON_RUNTIME_REPO_OWNER}/${PYTHON_RUNTIME_REPO_NAME}/releases/download/${PYTHON_RUNTIME_TAG}"
	fi
}

normalize_arch() {
	case "$1" in
		x86_64)
			echo "x86_64"
			;;
		aarch64|arm64)
			echo "aarch64"
			;;
		armv7l|armv7)
			echo "armv7l"
			;;
		*)
			log "ERROR: Unsupported architecture '$1'."
			return 1
			;;
	esac
}

normalize_os_variant() {
	case "$1" in
		debian11|debian12|debian13|rpios11|rpios12|rpios13)
			echo "$1"
			;;
		11|12|13)
			echo "debian$1"
			;;
		*)
			log "ERROR: Unsupported OS variant '$1'."
			return 1
			;;
	esac
}

init_target() {
	if [[ -z "${TARGET_ARCH}" ]]; then
		TARGET_ARCH=$(uname -m)
	fi

	if [[ -z "${TARGET_OS_VARIANT}" ]]; then
		log "ERROR: TARGET_OS_VARIANT must be provided."
		return 1
	fi

	TARGET_ARCH=$(normalize_arch "${TARGET_ARCH}")
	TARGET_OS_VARIANT=$(normalize_os_variant "${TARGET_OS_VARIANT}")
}

ensure_requirements_file() {
	if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
		log "ERROR: Requirements file not found: ${REQUIREMENTS_FILE}"
		return 1
	fi
}

validate_wheelhouse_glibcxx_compatibility() {
	local python_bin="$1"
	local wheelhouse_dir="$2"
	local max_glibcxx_version="${3:-3.4.28}"

	log "Validating wheelhouse GLIBCXX compatibility (max ${max_glibcxx_version})"
	if ! "${python_bin}" - "${wheelhouse_dir}" "${max_glibcxx_version}" <<'PY'
import os
import re
import sys
import zipfile

wheelhouse_dir = sys.argv[1]
max_version_raw = sys.argv[2]
max_version = tuple(int(part) for part in max_version_raw.split('.'))

def parse_version(token: bytes):
	match = re.match(rb"GLIBCXX_(\d+)\.(\d+)(?:\.(\d+))?", token)
	if not match:
		return None
	major = int(match.group(1))
	minor = int(match.group(2))
	patch = int(match.group(3) or 0)
	return (major, minor, patch)

offenders = []

for entry in sorted(os.listdir(wheelhouse_dir)):
	if not entry.endswith('.whl'):
		continue
	wheel_path = os.path.join(wheelhouse_dir, entry)
	with zipfile.ZipFile(wheel_path, 'r') as archive:
		so_members = [name for name in archive.namelist() if name.endswith('.so')]
		for name in so_members:
			data = archive.read(name)
			symbols = set(re.findall(rb"GLIBCXX_[0-9]+\.[0-9]+(?:\.[0-9]+)?", data))
			for symbol in symbols:
				version = parse_version(symbol)
				if version and version > max_version:
					offenders.append((entry, name, symbol.decode()))

if offenders:
	print("Found incompatible GLIBCXX symbols in wheelhouse:", file=sys.stderr)
	for wheel, member, symbol in offenders:
		print(f"  {wheel}: {member} requires {symbol}", file=sys.stderr)
	sys.exit(2)

sys.exit(0)
PY
	then
		log "ERROR: Wheelhouse contains native wheels incompatible with target libstdc++."
		return 1
	fi
}

build_wheelhouse() {
	local runtime_asset="python-${PYTHON_VERSION}-linux-${TARGET_ARCH}-${TARGET_OS_VARIANT}.tar.xz"
	local runtime_url="${PYTHON_RUNTIME_BASE_URL}/${runtime_asset}"
	local runtime_stage=""
	local runtime_archive=""
	local runtime_extract_dir=""
	local python_bin=""
	local wheelhouse_dir=""
	local artifact_path=""
	local artifact_name="python-wheelhouse-${PYTHON_VERSION}-linux-${TARGET_ARCH}-${TARGET_OS_VARIANT}.tar.xz"
	local -a pip_wheel_args=()
	local compatibility_mode="false"
	local requests_requirement=""

	runtime_stage=$(mktemp -d)
	runtime_archive="${runtime_stage}/python-runtime.tar.xz"
	runtime_extract_dir="${runtime_stage}/runtime"
	wheelhouse_dir="${runtime_stage}/wheelhouse"
	artifact_path="${OUTPUT_DIR}/${artifact_name}"
	pip_wheel_args=("--wheel-dir" "${wheelhouse_dir}" "-r" "${REQUIREMENTS_FILE}")

	mkdir -p "${runtime_extract_dir}" "${wheelhouse_dir}" "${OUTPUT_DIR}"

	if [[ -n "${PYTHON_RUNTIME_ARTIFACT_PATH}" ]]; then
		if [[ ! -f "${PYTHON_RUNTIME_ARTIFACT_PATH}" ]]; then
			log "ERROR: Local runtime artifact does not exist: ${PYTHON_RUNTIME_ARTIFACT_PATH}"
			rm -rf "${runtime_stage}"
			return 1
		fi
		log "Using local runtime artifact: ${PYTHON_RUNTIME_ARTIFACT_PATH}"
		cp "${PYTHON_RUNTIME_ARTIFACT_PATH}" "${runtime_archive}"
	else
		log "Downloading runtime artifact: ${runtime_url}"
		if ! curl -fL --connect-timeout 20 --retry 3 --retry-delay 2 -o "${runtime_archive}" "${runtime_url}" >/dev/null 2>&1; then
			log "ERROR: Could not download runtime artifact: ${runtime_url}"
			rm -rf "${runtime_stage}"
			return 1
		fi
	fi

	log "Extracting runtime artifact."
	tar -xJf "${runtime_archive}" -C "${runtime_extract_dir}"

	python_bin=$(find "${runtime_extract_dir}" -type f -path "*/bin/python${PYTHON_MAJOR_MINOR}" | head -n 1)
	if [[ -z "${python_bin}" || ! -x "${python_bin}" ]]; then
		log "ERROR: Could not locate runtime python binary python${PYTHON_MAJOR_MINOR}."
		rm -rf "${runtime_stage}"
		return 1
	fi

	log "Using runtime python: ${python_bin}"
	"${python_bin}" -m pip install --upgrade pip setuptools wheel

	if [[ "${TARGET_ARCH}" == "armv7l" && ("${TARGET_OS_VARIANT}" == "debian11" || "${TARGET_OS_VARIANT}" == "rpios11") ]]; then
		log "Compatibility mode enabled: forcing grpcio source build for ${TARGET_ARCH}/${TARGET_OS_VARIANT}."
		compatibility_mode="true"
		if grep -Eq '^[[:space:]]*jq([<>=!~].*)?$' "${REQUIREMENTS_FILE}"; then
			requests_requirement=$(grep -E '^[[:space:]]*requests([<>=!~].*)?$' "${REQUIREMENTS_FILE}" | head -n 1 | tr -d '[:space:]')
			if [[ -z "${requests_requirement}" ]]; then
				requests_requirement="requests"
			fi
			log "Compatibility mode: pre-installing ${requests_requirement} for jq metadata build."
			"${python_bin}" -m pip install "${requests_requirement}"
		fi
		# grpcio may fail in an isolated build env when legacy setup.py expects pkg_resources.
		pip_wheel_args=("--no-binary" "grpcio" "--no-build-isolation" "${pip_wheel_args[@]}")
	fi

	log "Building wheels with pip."
	"${python_bin}" -m pip wheel "${pip_wheel_args[@]}"

	if [[ "${compatibility_mode}" == "true" ]]; then
		if ! validate_wheelhouse_glibcxx_compatibility "${python_bin}" "${wheelhouse_dir}" "3.4.28"; then
			rm -rf "${runtime_stage}"
			return 1
		fi
	fi

	cp "${REQUIREMENTS_FILE}" "${wheelhouse_dir}/requirements.txt"

	log "Packaging wheelhouse artifact: ${artifact_path}"
	tar -C "${wheelhouse_dir}" -cJf "${artifact_path}" .
	sha256sum "${artifact_path}" > "${artifact_path}.sha256"

	rm -rf "${runtime_stage}"
	log "Wheelhouse build completed: ${artifact_path}"
}

main() {
	init_python_version
	init_target
	ensure_requirements_file
	build_wheelhouse
}

main "$@"
