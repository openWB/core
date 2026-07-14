#!/bin/bash

OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON_VERSION_FILE="${OPENWBBASEDIR}/data/config/python_runtime_version.txt"
VENV_DIR="${OPENWBBASEDIR}/.venv"
REQ_FILE="${OPENWBBASEDIR}/requirements.txt"
MARKER_FILE="${VENV_DIR}/.requirements_installed"
PYVENV_CFG="${VENV_DIR}/pyvenv.cfg"
PYENV_ROOT="${OPENWBBASEDIR}/.pyenv"
PYENV_BIN="${PYENV_ROOT}/bin/pyenv"
PYTHON_VERSION=""
PYTHON_MAJOR_MINOR=""
PYTHON_RELEASE_TAG=""
PYTHON_BINARIES_BASE_URL=""
OPENWB_USER="openwb"
LOG_FILE="${OPENWBBASEDIR}/data/log/python-bootstrap.log"

log() {
	echo "[bootstrap_venv] $*" >&2
}

init_logging() {
	local log_dir
	log_dir=$(dirname "${LOG_FILE}")

	mkdir -p "${log_dir}" || return 1
	touch "${LOG_FILE}" || return 1
	exec > >(tee -a "${LOG_FILE}") 2>&1
	log "----- bootstrap start $(date '+%Y-%m-%d %H:%M:%S') -----"
}

init_python_config() {
	local version_from_file=""

	if [[ -n "${OPENWB_PYTHON_VERSION:-}" ]]; then
		log "Nutze OPENWB_PYTHON_VERSION aus Umgebung: ${OPENWB_PYTHON_VERSION}"
		PYTHON_VERSION="${OPENWB_PYTHON_VERSION}"
	elif [[ -f "${PYTHON_VERSION_FILE}" ]]; then
		version_from_file=$(head -n 1 "${PYTHON_VERSION_FILE}" | tr -d '[:space:]')
		if [[ -n "${version_from_file}" ]]; then
			log "Nutze Python-Version aus ${PYTHON_VERSION_FILE}: ${version_from_file}"
			PYTHON_VERSION="${version_from_file}"
		fi
	fi

	if [[ -z "${PYTHON_VERSION}" ]]; then
		log "Keine Python-Version konfiguriert, verwende Standardwert 3.9.21"
		PYTHON_VERSION="3.9.21"
	fi

	if [[ ! "${PYTHON_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
		log "ERROR: ungueltige Python-Version '${PYTHON_VERSION}'"
		return 1
	fi

	PYTHON_MAJOR_MINOR="${PYTHON_VERSION%.*}"
	PYTHON_RELEASE_TAG="${OPENWB_PYTHON_RELEASE_TAG:-python-runtime-${PYTHON_VERSION}}"
	PYTHON_BINARIES_BASE_URL="${OPENWB_PYTHON_BINARIES_BASE_URL:-https://github.com/benderl/python-runtime/releases/download/${PYTHON_RELEASE_TAG}}"
	log "Python-Zielversion: ${PYTHON_VERSION}"
	log "Release-Tag fuer Binaries: ${PYTHON_RELEASE_TAG}"
	log "Binary-Basis-URL: ${PYTHON_BINARIES_BASE_URL}"
}

is_required_python() {
	local python_cmd="$1"
	"${python_cmd}" -c "import sys; raise SystemExit(0 if sys.version_info[:3] == tuple(map(int, '${PYTHON_VERSION}'.split('.'))) else 1)" >/dev/null 2>&1
}

managed_python_path() {
	echo "${PYENV_ROOT}/versions/${PYTHON_VERSION}/bin/python${PYTHON_MAJOR_MINOR}"
}

detect_arch() {
	case "$(uname -m)" in
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
			echo "$(uname -m)"
			;;
	esac
}

detect_os_variant() {
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

extract_archive() {
	local archive="$1"
	local destination="$2"

	case "${archive}" in
		*.tar.xz)
			tar -xJf "${archive}" -C "${destination}" >/dev/null 2>&1
			;;
		*)
			return 1
			;;
	esac
}

install_prebuilt_python() {
	local py_path
	local arch
	local os_variant=""
	local debian_major=""
	local temp_dir
	local archive
	local extract_dir
	local candidate
	local url
	local found_bin
	local prefix_dir
	local target_dir
	local candidates=()
	local python_bin_name="python${PYTHON_MAJOR_MINOR}"

	if [[ -z "${PYTHON_BINARIES_BASE_URL}" ]]; then
		log "WARN: Keine Binary-Basis-URL gesetzt, ueberspringe Prebuilt-Download."
		return 1
	fi

	arch=$(detect_arch)
	if os_variant=$(detect_os_variant); then
		case "${os_variant}" in
			debian*)
				debian_major="${os_variant#debian}"
				;;
			rpios*)
				debian_major="${os_variant#rpios}"
				;;
		esac
	fi
	log "Suche vorkompilierte Runtime fuer arch=${arch}, os_variant=${os_variant:-unknown}"
	temp_dir=$(mktemp -d)
	archive="${temp_dir}/python.tar.xz"
	extract_dir="${temp_dir}/extract"
	target_dir="${PYENV_ROOT}/versions/${PYTHON_VERSION}"
	mkdir -p "${extract_dir}"

	if [[ -n "${os_variant}" ]]; then
		candidates+=("python-${PYTHON_VERSION}-linux-${arch}-${os_variant}.tar.xz")
	fi

	# In CI werden Artefakte immer als
	# python-<version>-linux-<arch>-<os_variant>.tar.xz erzeugt.
	# Auf Raspberry Pi OS nutzen wir als Fallback debian<major>, da kein rpios-Label gebaut wird.
	if [[ -n "${debian_major}" && "${os_variant}" != "debian${debian_major}" ]]; then
		candidates+=("python-${PYTHON_VERSION}-linux-${arch}-debian${debian_major}.tar.xz")
	fi

	for candidate in "${candidates[@]}"; do
		url="${PYTHON_BINARIES_BASE_URL}/${candidate}"
		log "Versuche vorkompiliertes Python herunterzuladen: ${url}"
		if ! curl -fL --connect-timeout 10 --retry 2 --retry-delay 2 -o "${archive}" "${url}" >/dev/null 2>&1; then
			log "Kein Treffer: ${candidate}"
			continue
		fi
		log "Download erfolgreich: ${candidate}"

		find "${extract_dir}" -mindepth 1 -delete >/dev/null 2>&1
		if ! extract_archive "${archive}" "${extract_dir}"; then
			log "WARN: Archiv konnte nicht entpackt werden: ${candidate}"
			continue
		fi

		found_bin=$(find "${extract_dir}" -type f -path "*/bin/${python_bin_name}" | head -n 1)
		if [[ -z "${found_bin}" ]]; then
			log "WARN: Kein ${python_bin_name} im Archiv gefunden: ${candidate}"
			continue
		fi

		prefix_dir=$(dirname "$(dirname "${found_bin}")")
		rm -rf "${target_dir}"
		mkdir -p "$(dirname "${target_dir}")"
		cp -a "${prefix_dir}" "${target_dir}" || continue

		py_path=$(managed_python_path)
		if [[ -x "${py_path}" ]] && is_required_python "${py_path}"; then
			log "Vorkompiliertes Python erfolgreich installiert: ${py_path}"
			rm -rf "${temp_dir}"
			echo "${py_path}"
			return 0
		fi
		log "WARN: Installierte Runtime aus ${candidate} ist nicht verwendbar."
		# Ungueltige Runtime wieder entfernen, damit der lokale Fallback sauber bauen kann.
		rm -rf "${target_dir}"
	done

	log "Kein passendes vorkompiliertes Python gefunden."
	rm -rf "${temp_dir}"
	return 1
}

ensure_pyenv() {
	if [[ -x "${PYENV_BIN}" ]]; then
		log "pyenv bereits vorhanden: ${PYENV_BIN}"
		return 0
	fi

	if ! command -v git >/dev/null 2>&1; then
		log "ERROR: git ist nicht verfuegbar, pyenv kann nicht installiert werden."
		return 1
	fi

	log "Installiere pyenv lokal nach ${PYENV_ROOT}."
	rm -rf "${PYENV_ROOT}"
	git clone --depth 1 https://github.com/pyenv/pyenv.git "${PYENV_ROOT}" >/dev/null 2>&1 || {
		log "ERROR: pyenv konnte nicht installiert werden."
		return 1
	}
	log "pyenv erfolgreich installiert."

	[[ -x "${PYENV_BIN}" ]]
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
	)
	local pkg
	local -a missing_packages=()

	for pkg in "${required_packages[@]}"; do
		if ! dpkg -s "${pkg}" >/dev/null 2>&1; then
			missing_packages+=("${pkg}")
		fi
	done

	if (( ${#missing_packages[@]} > 0 )); then
		log "Fehlende Build-Abhaengigkeiten fuer pyenv erkannt: ${missing_packages[*]}"
		log "Installiere fehlende Pakete automatisch via sudo apt-get."

		if ! sudo DEBIAN_FRONTEND=noninteractive apt-get -q update; then
			log "ERROR: apt-get update fehlgeschlagen."
			return 1
		fi

		if ! sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install "${missing_packages[@]}"; then
			log "ERROR: Installation fehlgeschlagener Pakete: ${missing_packages[*]}"
			return 1
		fi

		log "Build-Abhaengigkeiten erfolgreich nachinstalliert."
	fi

	return 0
}

ensure_managed_python() {
	local py_path
	py_path=$(managed_python_path)
	log "Prüfe Managed-Python unter ${py_path}"

	ensure_pyenv || return 1

	if [[ -d "${PYENV_ROOT}" && ! -w "${PYENV_ROOT}" ]]; then
		log "ERROR: ${PYENV_ROOT} ist nicht schreibbar fuer Benutzer $(id -un)."
		ls -ld "${PYENV_ROOT}" >&2 || true
		return 1
	fi

	if ! mkdir -p "${PYENV_ROOT}/versions"; then
		log "ERROR: ${PYENV_ROOT}/versions konnte nicht angelegt werden."
		return 1
	fi

	export PYENV_ROOT
	export PATH="${PYENV_ROOT}/bin:${PATH}"

	if [[ -x "${py_path}" ]] && is_required_python "${py_path}"; then
		log "Vorhandenes Managed-Python ist gueltig."
		echo "${py_path}"
		return 0
	fi
	log "Managed-Python fehlt oder passt nicht zur Zielversion."

	if py_path=$(install_prebuilt_python); then
		log "Managed-Python aus vorkompiliertem Artefakt bereitgestellt."
		echo "${py_path}"
		return 0
	fi
	py_path=$(managed_python_path)
	log "Kein vorkompiliertes Python gefunden, falle auf lokalen Build zurueck."
	# Falls ein ungueltiges Runtime-Verzeichnis existiert, pyenv-Install nicht ueberspringen.
	rm -rf "${PYENV_ROOT}/versions/${PYTHON_VERSION}"
	check_build_dependencies || return 1

	log "Installiere CPython ${PYTHON_VERSION} via pyenv (kann einige Minuten dauern)."
	"${PYENV_BIN}" install -s "${PYTHON_VERSION}" || {
		log "ERROR: Python ${PYTHON_VERSION} konnte nicht via pyenv installiert werden."
		return 1
	}

	if [[ -x "${py_path}" ]] && is_required_python "${py_path}"; then
		log "Managed-Python erfolgreich lokal gebaut."
		echo "${py_path}"
		return 0
	fi

	log "ERROR: installierter Interpreter ist nicht verwendbar (${py_path})."
	return 1
}

ensure_permissions() {
	if id -u "${OPENWB_USER}" >/dev/null 2>&1; then
		if (( $(id -u) == 0 )); then
			[[ -d "${VENV_DIR}" ]] && chown -R "${OPENWB_USER}:${OPENWB_USER}" "${VENV_DIR}" || true
			[[ -d "${PYENV_ROOT}" ]] && chown -R "${OPENWB_USER}:${OPENWB_USER}" "${PYENV_ROOT}" || true
		fi
	fi
}

is_system_site_packages_enabled() {
	if [[ ! -f "${PYVENV_CFG}" ]]; then
		return 1
	fi
	grep -Eqi '^include-system-site-packages\s*=\s*true\s*$' "${PYVENV_CFG}"
}

prepare_venv_libpython() {
	local managed_lib_dir="${PYENV_ROOT}/versions/${PYTHON_VERSION}/lib"
	local source_lib="${managed_lib_dir}/libpython${PYTHON_MAJOR_MINOR}.so.1.0"
	local target_lib_dir="${VENV_DIR}/lib"

	if [[ ! -f "${source_lib}" ]]; then
		log "ERROR: Managed libpython fehlt (${source_lib})."
		return 1
	fi

	mkdir -p "${target_lib_dir}" || return 1
	cp -af "${source_lib}" "${target_lib_dir}/" || return 1
	ln -sfn "libpython${PYTHON_MAJOR_MINOR}.so.1.0" "${target_lib_dir}/libpython${PYTHON_MAJOR_MINOR}.so"
}

resolve_venv_libpython() {
	local venv_python="${VENV_DIR}/bin/python3"

	if ! command -v ldd >/dev/null 2>&1 || [[ ! -x "${venv_python}" ]]; then
		return 1
	fi

	ldd "${venv_python}" | awk '/libpython3\.[0-9]+\.so\.1\.0/{print $3; exit}'
}

is_venv_bound_to_managed_python() {
	local resolved_libpython=""
	local resolved_real=""
	local managed_lib_real=""
	local venv_lib_real=""

	resolved_libpython=$(resolve_venv_libpython || true)
	if [[ -z "${resolved_libpython}" ]]; then
		return 1
	fi
	resolved_real=$(readlink -f "${resolved_libpython}" 2>/dev/null || true)
	managed_lib_real=$(readlink -f "${PYENV_ROOT}/versions/${PYTHON_VERSION}/lib/libpython${PYTHON_MAJOR_MINOR}.so.1.0" 2>/dev/null || true)
	venv_lib_real=$(readlink -f "${VENV_DIR}/lib/libpython${PYTHON_MAJOR_MINOR}.so.1.0" 2>/dev/null || true)

	if [[ -z "${resolved_real}" ]]; then
		return 1
	fi

	case "${resolved_real}" in
		"${managed_lib_real}"|"${venv_lib_real}")
			return 0
			;;
		*)
			return 1
			;;
	esac
}

create_venv() {
	local py_cmd="$1"
	log "Erzeuge venv mit ${py_cmd} (isoliert, Symlink auf Managed-Runtime)."
	"${py_cmd}" -m venv "${VENV_DIR}" || {
		log "ERROR: venv konnte nicht erzeugt werden."
		return 1
	}
	if ! prepare_venv_libpython; then
		log "ERROR: venv-libpython konnte nicht vorbereitet werden."
		return 1
	fi
	if ! is_required_python "${VENV_DIR}/bin/python3"; then
		log "ERROR: venv-Python hat nicht die erwartete Version ${PYTHON_VERSION}."
		return 1
	fi
	if ! is_venv_bound_to_managed_python; then
		log "ERROR: venv ist nicht an die Managed-Runtime gebunden."
		return 1
	fi
	if is_system_site_packages_enabled; then
		log "ERROR: venv wurde mit System-Site-Packages erstellt."
		return 1
	fi
	return 0
}

install_requirements() {
	local pip_cmd=("${VENV_DIR}/bin/python3" -m pip)
	log "Installiere Python-Abhaengigkeiten aus ${REQ_FILE}."

	if ! "${pip_cmd[@]}" install --upgrade pip setuptools wheel; then
		log "WARN: pip/setuptools/wheel konnten nicht aktualisiert werden."
	fi

	if "${pip_cmd[@]}" install --only-binary :all: -r "${REQ_FILE}"; then
		log "Requirements erfolgreich installiert."
		touch "${MARKER_FILE}"
		return 0
	fi
	log "WARN: Installation nur mit Wheels fehlgeschlagen, versuche Installation mit Source-Distributionen."

	if "${pip_cmd[@]}" install -r "${REQ_FILE}"; then
		log "Requirements erfolgreich installiert (inkl. Source-Distributionen)."
		touch "${MARKER_FILE}"
		return 0
	fi

	if [[ -f "${MARKER_FILE}" ]]; then
		log "WARN: requirements konnten nicht aktualisiert werden, nutze vorhandene Installation."
		return 0
	fi

	log "ERROR: requirements konnten nicht installiert werden und keine bestehende Installation gefunden."
	return 1
}

main() {
	local py_cmd

	init_logging || {
		echo "[bootstrap_venv] ERROR: Logdatei kann nicht initialisiert werden (${LOG_FILE})."
		exit 1
	}

	init_python_config || exit 1
	log "Starte Bootstrap fuer venv unter ${VENV_DIR}."

	if [[ -d "${VENV_DIR}" ]]; then
		log "Bestehendes venv gefunden, pruefe Kompatibilitaet."
		if ! is_required_python "${VENV_DIR}/bin/python3" || is_system_site_packages_enabled || ! is_venv_bound_to_managed_python; then
			log "Bestehendes venv ist inkompatibel oder nicht korrekt an Managed-Python gebunden."
			py_cmd=$(ensure_managed_python) || {
				log "ERROR: Python ${PYTHON_VERSION} konnte nicht bereitgestellt werden."
				exit 1
			}
			log "Vorhandenes venv ist nicht kompatibel oder nicht korrekt gebunden, baue neu auf."
			rm -rf "${VENV_DIR}"
			create_venv "${py_cmd}" || exit 1
		else
			log "venv bereits vorhanden (${VENV_DIR})."
		fi
	else
		log "Kein venv vorhanden, initialisiere neu."
		py_cmd=$(ensure_managed_python) || {
			log "ERROR: Python ${PYTHON_VERSION} konnte nicht bereitgestellt werden."
			exit 1
		}
		create_venv "${py_cmd}" || exit 1
	fi

	ensure_permissions

	if [[ ! -f "${REQ_FILE}" ]]; then
		log "ERROR: requirements-Datei nicht gefunden (${REQ_FILE})."
		exit 1
	fi

	install_requirements || exit 1
	ensure_permissions
	log "venv bereit (${VENV_DIR})."
}

main "$@"
