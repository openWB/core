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

	runtime_stage=$(mktemp -d)
	runtime_archive="${runtime_stage}/python-runtime.tar.xz"
	runtime_extract_dir="${runtime_stage}/runtime"
	wheelhouse_dir="${runtime_stage}/wheelhouse"
	artifact_path="${OUTPUT_DIR}/${artifact_name}"

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
	"${python_bin}" -m pip install --upgrade pip wheel uv

	log "Building wheels with uv."
	if ! "${python_bin}" -m uv pip wheel --python "${python_bin}" --wheel-dir "${wheelhouse_dir}" -r "${REQUIREMENTS_FILE}"; then
		log "WARN: uv wheel build failed, falling back to pip wheel."
		"${python_bin}" -m pip wheel --wheel-dir "${wheelhouse_dir}" -r "${REQUIREMENTS_FILE}"
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
