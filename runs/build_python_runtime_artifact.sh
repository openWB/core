#!/bin/bash

set -euo pipefail

BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON_VERSION_FILE="${BASE_DIR}/data/config/python_runtime_version.txt"
PYTHON_VERSION="${PYTHON_VERSION:-}"
PYTHON_MAJOR_MINOR=""
TARGET_ARCH="${1:-${TARGET_ARCH:-}}"
TARGET_OS_VARIANT="${2:-${TARGET_OS_VARIANT:-}}"
ALLOW_CROSS_TARGET_BUILD="${ALLOW_CROSS_TARGET_BUILD:-0}"
PYENV_ROOT="${PYENV_ROOT:-${BASE_DIR}/.pyenv-build}"
PYENV_BIN="${PYENV_ROOT}/bin/pyenv"
OUTPUT_DIR="${OUTPUT_DIR:-${BASE_DIR}/dist/python-runtime}"
PACKAGED_ARTIFACT_PATH=""

log() {
	echo "[build_python_runtime] $*"
}

init_python_version() {
	if [[ -z "${PYTHON_VERSION}" && -f "${PYTHON_VERSION_FILE}" ]]; then
		PYTHON_VERSION=$(head -n 1 "${PYTHON_VERSION_FILE}" | tr -d '[:space:]')
	fi

	if [[ -z "${PYTHON_VERSION}" ]]; then
		PYTHON_VERSION="3.9.21"
	fi

	if [[ ! "${PYTHON_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
		log "ERROR: ungueltige Python-Version '${PYTHON_VERSION}'"
		return 1
	fi

	PYTHON_MAJOR_MINOR="${PYTHON_VERSION%.*}"
}

normalize_arch() {
	local raw_arch="$1"
	case "${raw_arch}" in
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
			log "ERROR: nicht unterstuetzte Architektur '${raw_arch}'"
			return 1
			;;
	esac
}

normalize_os_variant() {
	local raw_os="$1"
	case "${raw_os}" in
		debian11|debian12|debian13|rpios11|rpios12|rpios13)
			echo "${raw_os}"
			;;
		11|12|13)
			echo "debian${raw_os}"
			;;
		*)
			log "ERROR: nicht unterstuetzte OS-Variante '${raw_os}'"
			return 1
			;;
	esac
}

detect_host_os_variant() {
	local os_id=""
	local version_id=""
	local version_major=""

	if [[ -f /etc/os-release ]]; then
		# shellcheck disable=SC1091
		source /etc/os-release
		os_id="${ID:-}"
		version_id="${VERSION_ID:-}"
	fi

	version_major="${version_id%%.*}"
	if [[ -z "${version_major}" ]]; then
		return 1
	fi

	case "${os_id}" in
		raspbian)
			echo "rpios${version_major}"
			;;
		debian)
			echo "debian${version_major}"
			;;
		*)
			return 1
			;;
	esac
}

ensure_target_arch() {
	if [[ -z "${TARGET_ARCH}" ]]; then
		TARGET_ARCH=$(uname -m)
	fi
	TARGET_ARCH=$(normalize_arch "${TARGET_ARCH}")
}

ensure_target_os_variant() {
	local host_os_variant=""

	if [[ -z "${TARGET_OS_VARIANT}" ]]; then
		host_os_variant=$(detect_host_os_variant || true)
		TARGET_OS_VARIANT="${host_os_variant}"
	fi

	if [[ -z "${TARGET_OS_VARIANT}" ]]; then
		log "ERROR: OS-Variante konnte nicht ermittelt werden. Bitte TARGET_OS_VARIANT setzen."
		return 1
	fi

	TARGET_OS_VARIANT=$(normalize_os_variant "${TARGET_OS_VARIANT}")
}

ensure_target_matches_host() {
	local host_arch
	local host_os_variant

	host_arch=$(normalize_arch "$(uname -m)")
	host_os_variant=$(detect_host_os_variant || true)

	if [[ "${ALLOW_CROSS_TARGET_BUILD}" == "1" ]]; then
		log "WARN: Cross-Target-Build explizit aktiviert (ALLOW_CROSS_TARGET_BUILD=1)."
		return 0
	fi

	if [[ "${TARGET_ARCH}" != "${host_arch}" ]]; then
		log "ERROR: TARGET_ARCH=${TARGET_ARCH} passt nicht zum Host (${host_arch})."
		log "ERROR: Fuer echtes Cross-Build CI/Emulation nutzen oder ALLOW_CROSS_TARGET_BUILD=1 setzen."
		return 1
	fi

	if [[ -n "${host_os_variant}" && "${TARGET_OS_VARIANT}" != "${host_os_variant}" ]]; then
		log "ERROR: TARGET_OS_VARIANT=${TARGET_OS_VARIANT} passt nicht zum Host (${host_os_variant})."
		log "ERROR: Fuer echtes Cross-Build CI/Emulation nutzen oder ALLOW_CROSS_TARGET_BUILD=1 setzen."
		return 1
	fi
}

ensure_pyenv() {
	if [[ -x "${PYENV_BIN}" ]]; then
		return 0
	fi

	if ! command -v git >/dev/null 2>&1; then
		log "ERROR: git ist erforderlich, um pyenv zu installieren."
		return 1
	fi

	log "Installiere pyenv nach ${PYENV_ROOT}."
	rm -rf "${PYENV_ROOT}"
	git clone --depth 1 https://github.com/pyenv/pyenv.git "${PYENV_ROOT}" >/dev/null 2>&1
}

check_build_dependencies() {
	local -a required_packages=(
		build-essential
		make
		libssl-dev
		zlib1g-dev
		libbz2-dev
		libreadline-dev
		libsqlite3-dev
		libffi-dev
		liblzma-dev
		xz-utils
		tk-dev
		libncursesw5-dev
		git
		patchelf
	)
	local pkg
	local -a missing_packages=()

	for pkg in "${required_packages[@]}"; do
		if ! dpkg -s "${pkg}" >/dev/null 2>&1; then
			missing_packages+=("${pkg}")
		fi
	done

	if (( ${#missing_packages[@]} > 0 )); then
		log "Fehlende Build-Abhaengigkeiten erkannt: ${missing_packages[*]}"
		log "Installiere fehlende Pakete automatisch."

		if command -v sudo >/dev/null 2>&1; then
			if ! sudo DEBIAN_FRONTEND=noninteractive apt-get -q update; then
				log "ERROR: apt-get update fehlgeschlagen."
				return 1
			fi

			if ! sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install "${missing_packages[@]}"; then
				log "ERROR: Installation fehlgeschlagener Pakete: ${missing_packages[*]}"
				return 1
			fi
		else
			if ! DEBIAN_FRONTEND=noninteractive apt-get -q update; then
				log "ERROR: apt-get update fehlgeschlagen."
				return 1
			fi

			if ! DEBIAN_FRONTEND=noninteractive apt-get -q -y install "${missing_packages[@]}"; then
				log "ERROR: Installation fehlgeschlagener Pakete: ${missing_packages[*]}"
				return 1
			fi
		fi

		log "Build-Abhaengigkeiten erfolgreich nachinstalliert."
	fi
}

build_python() {
	export PYENV_ROOT
	export PATH="${PYENV_ROOT}/bin:${PATH}"
	MAKE_OPTS="-j$(nproc)"
	export MAKE_OPTS

	log "Baue CPython ${PYTHON_VERSION} fuer ${TARGET_ARCH}."
	"${PYENV_BIN}" install -v -s "${PYTHON_VERSION}" >/dev/null
}

harden_runtime_loader() {
	local python_bin="${PYENV_ROOT}/versions/${PYTHON_VERSION}/bin/python${PYTHON_MAJOR_MINOR}"
	local target_rpath='$ORIGIN/../lib'

	if [[ ! -x "${python_bin}" ]]; then
		log "ERROR: Interpreter fuer RPATH-Haertung nicht gefunden: ${python_bin}"
		return 1
	fi

	if ! command -v patchelf >/dev/null 2>&1; then
		log "ERROR: patchelf ist erforderlich, um ein relocatable Runtime-Artefakt zu erzeugen."
		return 1
	fi

	log "Setze RUNPATH fuer ${python_bin} auf ${target_rpath}."
	patchelf --set-rpath "${target_rpath}" "${python_bin}"
}

validate_runtime() {
	local python_bin="${PYENV_ROOT}/versions/${PYTHON_VERSION}/bin/python${PYTHON_MAJOR_MINOR}"
	local runpath=""

	if [[ ! -x "${python_bin}" ]]; then
		log "ERROR: erwarteter Interpreter fehlt: ${python_bin}"
		return 1
	fi

	"${python_bin}" -c "import sys; raise SystemExit(0 if sys.version_info[:3] == tuple(map(int, '${PYTHON_VERSION}'.split('.'))) else 1)"
	"${python_bin}" -c "import ssl, bz2, ctypes, readline, lzma, sqlite3, curses"

	runpath=$(patchelf --print-rpath "${python_bin}" 2>/dev/null || true)
	if [[ "${runpath}" != '$ORIGIN/../lib' ]]; then
		log "ERROR: ungueltiger RUNPATH '${runpath}' fuer ${python_bin} (erwartet: $ORIGIN/../lib)."
		return 1
	fi
}

package_runtime() {
	local artifact_name="python-${PYTHON_VERSION}-linux-${TARGET_ARCH}-${TARGET_OS_VARIANT}.tar.xz"
	local artifact_path="${OUTPUT_DIR}/${artifact_name}"

	mkdir -p "${OUTPUT_DIR}"
	log "Packe Runtime in ${artifact_path}."
	tar -C "${PYENV_ROOT}/versions" -cJf "${artifact_path}" "${PYTHON_VERSION}"
	sha256sum "${artifact_path}" > "${artifact_path}.sha256"
	PACKAGED_ARTIFACT_PATH="${artifact_path}"

	log "Artefakt erstellt: ${artifact_path}"
	log "Pruefsumme erstellt: ${artifact_path}.sha256"
}

validate_packaged_runtime() {
	local artifact_path="${PACKAGED_ARTIFACT_PATH}"
	local test_dir=""
	local extracted_python=""
	local resolved_libpython=""

	if [[ -z "${artifact_path}" || ! -f "${artifact_path}" ]]; then
		log "ERROR: Kein Artefakt zur Endvalidierung vorhanden."
		return 1
	fi

	test_dir=$(mktemp -d)
	mkdir -p "${test_dir}/extract"

	if ! tar -xJf "${artifact_path}" -C "${test_dir}/extract"; then
		log "ERROR: Gepacktes Artefakt konnte zur Endvalidierung nicht entpackt werden."
		rm -rf "${test_dir}"
		return 1
	fi

	extracted_python=$(find "${test_dir}/extract" -type f -path "*/bin/python${PYTHON_MAJOR_MINOR}" | head -n 1)
	if [[ -z "${extracted_python}" || ! -x "${extracted_python}" ]]; then
		log "ERROR: Gepacktes Artefakt enthaelt keinen ausfuehrbaren Interpreter python${PYTHON_MAJOR_MINOR}."
		rm -rf "${test_dir}"
		return 1
	fi

	if ! "${extracted_python}" -c "import sys; raise SystemExit(0 if sys.version_info[:3] == tuple(map(int, '${PYTHON_VERSION}'.split('.'))) else 1)"; then
		log "ERROR: Gepacktes Artefakt liefert nicht die erwartete Python-Version ${PYTHON_VERSION}."
		rm -rf "${test_dir}"
		return 1
	fi

	if command -v ldd >/dev/null 2>&1; then
		resolved_libpython=$(ldd "${extracted_python}" | awk '/libpython3\.[0-9]+\.so\.1\.0/{print $3; exit}')
		if [[ -z "${resolved_libpython}" ]]; then
			log "ERROR: libpython-Aufloesung konnte fuer ${extracted_python} nicht ermittelt werden."
			rm -rf "${test_dir}"
			return 1
		fi

		case "${resolved_libpython}" in
			"${test_dir}"/*)
				;;
			*)
				log "ERROR: Gepacktes Artefakt bindet gegen System-libpython (${resolved_libpython}) statt gegen die gebuendelte Runtime."
				rm -rf "${test_dir}"
				return 1
				;;
		esac
	fi

	rm -rf "${test_dir}"
	log "Endvalidierung des gepackten Artefakts erfolgreich."
}

main() {
	init_python_version
	ensure_target_arch
	ensure_target_os_variant
	ensure_target_matches_host
	ensure_pyenv
	check_build_dependencies
	build_python
	harden_runtime_loader
	validate_runtime
	package_runtime
	validate_packaged_runtime
}

main "$@"
