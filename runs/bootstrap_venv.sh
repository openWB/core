#!/bin/bash

OPENWB_BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON_VERSION_FILE="${OPENWB_BASE_DIR}/data/config/python_runtime_version.txt"
VENV_DIR="${OPENWB_BASE_DIR}/.venv"
REQ_FILE="${OPENWB_BASE_DIR}/requirements.txt"
MARKER_FILE="${VENV_DIR}/.requirements_installed"
PYVENV_CFG="${VENV_DIR}/pyvenv.cfg"
PYENV_ROOT="${OPENWB_BASE_DIR}/.pyenv"
PYENV_BIN="${PYENV_ROOT}/bin/pyenv"
PYTHON_VERSION=""
PYTHON_MAJOR_MINOR=""
PYTHON_RELEASE_TAG=""
PYTHON_BINARIES_BASE_URL=""
PYTHON_WHEELHOUSE_RELEASE_TAG=""
PYTHON_WHEELHOUSE_BASE_URL=""
PYTHON_REPO_OWNER="openWB"
PYTHON_REPO_NAME="python-runtime"
OPENWB_USER="openwb"
LOG_FILE="${OPENWB_BASE_DIR}/data/log/python-bootstrap.log"

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
		log "Using OPENWB_PYTHON_VERSION from environment: ${OPENWB_PYTHON_VERSION}"
		PYTHON_VERSION="${OPENWB_PYTHON_VERSION}"
	elif [[ -f "${PYTHON_VERSION_FILE}" ]]; then
		version_from_file=$(head -n 1 "${PYTHON_VERSION_FILE}" | tr -d '[:space:]')
		if [[ -n "${version_from_file}" ]]; then
			log "Using Python version from ${PYTHON_VERSION_FILE}: ${version_from_file}"
			PYTHON_VERSION="${version_from_file}"
		fi
	fi

	if [[ -z "${PYTHON_VERSION}" ]]; then
		log "No Python version configured, using default 3.9.25"
		PYTHON_VERSION="3.9.25"
	fi

	if [[ ! "${PYTHON_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
		log "ERROR: invalid Python version '${PYTHON_VERSION}'"
		return 1
	fi

	PYTHON_MAJOR_MINOR="${PYTHON_VERSION%.*}"
	PYTHON_RELEASE_TAG="${OPENWB_PYTHON_RELEASE_TAG:-python-runtime-${PYTHON_VERSION}}"
	PYTHON_BINARIES_BASE_URL="${OPENWB_PYTHON_BINARIES_BASE_URL:-https://github.com/${PYTHON_REPO_OWNER}/${PYTHON_REPO_NAME}/releases/download/${PYTHON_RELEASE_TAG}}"
	PYTHON_WHEELHOUSE_RELEASE_TAG="${OPENWB_PYTHON_WHEELHOUSE_RELEASE_TAG:-python-wheels-${PYTHON_VERSION}}"
	PYTHON_WHEELHOUSE_BASE_URL="${OPENWB_PYTHON_WHEELHOUSE_BASE_URL:-https://github.com/${PYTHON_REPO_OWNER}/${PYTHON_REPO_NAME}/releases/download/${PYTHON_WHEELHOUSE_RELEASE_TAG}}"
	log "Python target version: ${PYTHON_VERSION}"
	log "Release tag for binaries: ${PYTHON_RELEASE_TAG}"
	log "Binary base URL: ${PYTHON_BINARIES_BASE_URL}"
	log "Release tag for wheelhouse: ${PYTHON_WHEELHOUSE_RELEASE_TAG}"
	log "Wheelhouse base URL: ${PYTHON_WHEELHOUSE_BASE_URL}"
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

resolve_platform_target() {
	local arch
	local os_variant=""
	local debian_major=""

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

	echo "${arch};${os_variant};${debian_major}"
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
		log "WARN: No binary base URL set, skipping prebuilt download."
		return 1
	fi

	IFS=';' read -r arch os_variant debian_major <<< "$(resolve_platform_target)"
	log "Searching compiled Python runtime for arch=${arch}, os_variant=${os_variant:-unknown}"
	temp_dir=$(mktemp -d)
	archive="${temp_dir}/python.tar.xz"
	extract_dir="${temp_dir}/extract"
	target_dir="${PYENV_ROOT}/versions/${PYTHON_VERSION}"
	mkdir -p "${extract_dir}"

	if [[ -n "${os_variant}" ]]; then
		candidates+=("python-${PYTHON_VERSION}-linux-${arch}-${os_variant}.tar.xz")
	fi

	# In CI, artifacts are always produced as
	# python-<version>-linux-<arch>-<os_variant>.tar.xz.
	# On Raspberry Pi OS, use debian<major> as a fallback because no rpios label is built.
	if [[ -n "${debian_major}" && "${os_variant}" != "debian${debian_major}" ]]; then
		candidates+=("python-${PYTHON_VERSION}-linux-${arch}-debian${debian_major}.tar.xz")
	fi

	for candidate in "${candidates[@]}"; do
		url="${PYTHON_BINARIES_BASE_URL}/${candidate}"
		log "Trying to download compiled Python runtime: ${url}"
		if ! curl -fL --connect-timeout 10 --retry 2 --retry-delay 2 -o "${archive}" "${url}" >/dev/null 2>&1; then
			log "No match found: ${candidate}"
			continue
		fi
		log "Download successful: ${candidate}"

		find "${extract_dir}" -mindepth 1 -delete >/dev/null 2>&1
		if ! extract_archive "${archive}" "${extract_dir}"; then
			log "WARN: Could not extract archive: ${candidate}"
			continue
		fi

		found_bin=$(find "${extract_dir}" -type f -path "*/bin/${python_bin_name}" | head -n 1)
		if [[ -z "${found_bin}" ]]; then
			log "WARN: No ${python_bin_name} found in archive: ${candidate}"
			continue
		fi

		prefix_dir=$(dirname "$(dirname "${found_bin}")")
		rm -rf "${target_dir}"
		mkdir -p "$(dirname "${target_dir}")"
		cp -a "${prefix_dir}" "${target_dir}" || continue

		py_path=$(managed_python_path)
		if [[ -x "${py_path}" ]] && is_required_python "${py_path}"; then
			log "Compiled Python runtime installed successfully: ${py_path}"
			rm -rf "${temp_dir}"
			echo "${py_path}"
			return 0
		fi
		log "WARN: Installed runtime from ${candidate} is not usable."
		# Remove invalid runtime so the local fallback can build cleanly.
		rm -rf "${target_dir}"
	done

	log "No matching compiled Python runtime found."
	rm -rf "${temp_dir}"
	return 1
}

prepare_wheelhouse_source() {
	local arch
	local os_variant=""
	local debian_major=""
	local temp_dir
	local archive
	local wheelhouse_dir
	local candidate
	local url
	local wheel_count
	local candidates=()

	if [[ -z "${PYTHON_WHEELHOUSE_BASE_URL}" ]]; then
		log "WARN: No wheelhouse base URL set, skipping wheelhouse download."
		return 1
	fi

	IFS=';' read -r arch os_variant debian_major <<< "$(resolve_platform_target)"

	temp_dir=$(mktemp -d)
	archive="${temp_dir}/wheelhouse.tar.xz"
	wheelhouse_dir="${temp_dir}/wheelhouse"
	mkdir -p "${wheelhouse_dir}"

	if [[ -n "${os_variant}" ]]; then
		candidates+=("python-wheelhouse-${PYTHON_VERSION}-linux-${arch}-${os_variant}.tar.xz")
	fi

	# On Raspberry Pi OS, fall back to debian<major> because CI artifacts are built on Debian.
	if [[ -n "${debian_major}" && "${os_variant}" != "debian${debian_major}" ]]; then
		candidates+=("python-wheelhouse-${PYTHON_VERSION}-linux-${arch}-debian${debian_major}.tar.xz")
	fi

	for candidate in "${candidates[@]}"; do
		url="${PYTHON_WHEELHOUSE_BASE_URL}/${candidate}"
		log "Trying to download wheelhouse artifact: ${url}"
		if ! curl -fL --connect-timeout 10 --retry 2 --retry-delay 2 -o "${archive}" "${url}" >/dev/null 2>&1; then
			log "No wheelhouse match found: ${candidate}"
			continue
		fi

		find "${wheelhouse_dir}" -mindepth 1 -delete >/dev/null 2>&1
		if ! extract_archive "${archive}" "${wheelhouse_dir}"; then
			log "WARN: Could not extract wheelhouse archive: ${candidate}"
			continue
		fi

		wheel_count=$(find "${wheelhouse_dir}" -type f -name '*.whl' | wc -l)
		if (( wheel_count > 0 )); then
			log "Wheelhouse artifact ready with ${wheel_count} wheels: ${candidate}"
			echo "${wheelhouse_dir}"
			return 0
		fi

		log "WARN: Wheelhouse archive contains no wheels: ${candidate}"
	done

	rm -rf "${temp_dir}"
	log "No matching wheelhouse artifact available."
	return 1
}

ensure_pyenv() {
	local attempt
	local max_attempts=5
	local retry_delay=3
	local clone_log

	if [[ -x "${PYENV_BIN}" ]]; then
		log "pyenv already present: ${PYENV_BIN}"
		return 0
	fi

	if ! command -v git >/dev/null 2>&1; then
		log "ERROR: git is not available, pyenv cannot be installed."
		return 1
	fi

	log "Installing local pyenv to ${PYENV_ROOT}."
	rm -rf "${PYENV_ROOT}"
	clone_log=$(mktemp)
	for attempt in $(seq 1 "${max_attempts}"); do
		if git clone --depth 1 https://github.com/pyenv/pyenv.git "${PYENV_ROOT}" >"${clone_log}" 2>&1; then
			rm -f "${clone_log}"
			log "pyenv installed successfully."
			[[ -x "${PYENV_BIN}" ]]
			return 0
		fi

		log "WARN: pyenv clone attempt ${attempt}/${max_attempts} failed."
		if [[ -s "${clone_log}" ]]; then
			log "pyenv clone error output:"
			tail -n 20 "${clone_log}" | while IFS= read -r line; do
				log "  ${line}"
			done
		fi

		rm -rf "${PYENV_ROOT}"
		if (( attempt < max_attempts )); then
			log "Retrying pyenv clone in ${retry_delay}s."
			sleep "${retry_delay}"
		fi
	done

	rm -f "${clone_log}"
	log "ERROR: pyenv could not be installed after ${max_attempts} attempts."
	return 1
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
		log "Missing build dependencies for pyenv detected: ${missing_packages[*]}"
		log "Installing missing packages automatically via sudo apt-get."

		if ! sudo DEBIAN_FRONTEND=noninteractive apt-get -q update; then
			log "ERROR: apt-get update failed."
			return 1
		fi

		if ! sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install "${missing_packages[@]}"; then
			log "ERROR: Failed to install packages: ${missing_packages[*]}"
			return 1
		fi

		log "Build dependencies installed successfully."
	fi

	return 0
}

ensure_managed_python() {
	local py_path
	py_path=$(managed_python_path)
	log "Checking managed Python at ${py_path}"

	ensure_pyenv || return 1

	if [[ -d "${PYENV_ROOT}" && ! -w "${PYENV_ROOT}" ]]; then
		log "ERROR: ${PYENV_ROOT} is not writable for user $(id -un)."
		ls -ld "${PYENV_ROOT}" >&2 || true
		return 1
	fi

	if ! mkdir -p "${PYENV_ROOT}/versions"; then
		log "ERROR: Could not create ${PYENV_ROOT}/versions."
		return 1
	fi

	export PYENV_ROOT
	export PATH="${PYENV_ROOT}/bin:${PATH}"

	if [[ -x "${py_path}" ]] && is_required_python "${py_path}"; then
		log "Existing managed Python is valid."
		echo "${py_path}"
		return 0
	fi
	log "Managed Python is missing or does not match the target version."

	if py_path=$(install_prebuilt_python); then
		log "Managed Python provided from compiled artifact."
		echo "${py_path}"
		return 0
	fi
	py_path=$(managed_python_path)
	log "No compiled Python runtime found, falling back to local build."
	# If an invalid runtime directory exists, do not let pyenv skip installation.
	rm -rf "${PYENV_ROOT}/versions/${PYTHON_VERSION}"
	check_build_dependencies || return 1

	log "Installing CPython ${PYTHON_VERSION} via pyenv (this may take several minutes)."
	"${PYENV_BIN}" install -s "${PYTHON_VERSION}" || {
		log "ERROR: Python ${PYTHON_VERSION} could not be installed via pyenv."
		return 1
	}

	if [[ -x "${py_path}" ]] && is_required_python "${py_path}"; then
		log "Managed Python built locally successfully."
		echo "${py_path}"
		return 0
	fi

	log "ERROR: Installed interpreter is not usable (${py_path})."
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
		log "ERROR: Managed libpython is missing (${source_lib})."
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
	log "Creating venv with ${py_cmd} (isolated, symlinked to managed runtime)."
	"${py_cmd}" -m venv "${VENV_DIR}" || {
		log "ERROR: Could not create venv."
		return 1
	}
	if ! prepare_venv_libpython; then
		log "ERROR: Could not prepare venv libpython."
		return 1
	fi
	if ! is_required_python "${VENV_DIR}/bin/python3"; then
		log "ERROR: venv Python does not match expected version ${PYTHON_VERSION}."
		return 1
	fi
	if ! is_venv_bound_to_managed_python; then
		log "ERROR: venv is not bound to the managed runtime."
		return 1
	fi
	if is_system_site_packages_enabled; then
		log "ERROR: venv was created with system site-packages enabled."
		return 1
	fi
	return 0
}

install_requirements() {
	local py_cmd="${VENV_DIR}/bin/python3"
	local pip_cmd=("${VENV_DIR}/bin/python3" -m pip)
	local uv_bin="${VENV_DIR}/bin/uv"
	local uv_cmd=("${VENV_DIR}/bin/python3" -m uv)
	local wheelhouse_dir=""
	local wheelhouse_temp_dir=""
	log "Installing Python dependencies from ${REQ_FILE}."

	if ! "${pip_cmd[@]}" install --upgrade pip setuptools wheel; then
		log "WARN: Could not upgrade pip/setuptools/wheel."
	fi

	if ! "${pip_cmd[@]}" install --upgrade uv; then
		log "WARN: Could not install uv, using pip fallback where needed."
	fi

	if wheelhouse_dir=$(prepare_wheelhouse_source); then
		wheelhouse_temp_dir=$(dirname "${wheelhouse_dir}")
		log "Using wheelhouse as preferred source: ${wheelhouse_dir}"

		if [[ -x "${uv_bin}" ]]; then
			if "${uv_cmd[@]}" pip install --python "${py_cmd}" --no-index --find-links "${wheelhouse_dir}" -r "${REQ_FILE}"; then
				log "Requirements installed successfully from wheelhouse with uv."
				touch "${MARKER_FILE}"
				rm -rf "${wheelhouse_temp_dir}"
				return 0
			fi
			log "WARN: uv wheelhouse installation failed, trying pip with wheelhouse."
		fi

		if "${pip_cmd[@]}" install --no-index --find-links "${wheelhouse_dir}" -r "${REQ_FILE}"; then
			log "Requirements installed successfully from wheelhouse with pip."
			touch "${MARKER_FILE}"
			rm -rf "${wheelhouse_temp_dir}"
			return 0
		fi

		log "WARN: Wheelhouse installation failed, falling back to remote installation."
		rm -rf "${wheelhouse_temp_dir}"
	fi

	if [[ -x "${uv_bin}" ]]; then
		log "Using uv for faster requirements installation."

		if "${uv_cmd[@]}" pip install --python "${py_cmd}" --only-binary :all: -r "${REQ_FILE}"; then
			log "Requirements installed successfully with uv."
			touch "${MARKER_FILE}"
			return 0
		fi
		log "WARN: uv wheel-only installation failed, retrying with source distributions."

		if "${uv_cmd[@]}" pip install --python "${py_cmd}" -r "${REQ_FILE}"; then
			log "Requirements installed successfully with uv (including source distributions)."
			touch "${MARKER_FILE}"
			return 0
		fi

		log "WARN: uv installation failed, falling back to pip."
	else
		log "WARN: uv binary was not found (${uv_bin}), using pip fallback."
	fi

	if "${pip_cmd[@]}" install --only-binary :all: -r "${REQ_FILE}"; then
		log "Requirements installed successfully."
		touch "${MARKER_FILE}"
		return 0
	fi
	log "WARN: Wheel-only installation failed, retrying with source distributions."

	if "${pip_cmd[@]}" install -r "${REQ_FILE}"; then
		log "Requirements installed successfully (including source distributions)."
		touch "${MARKER_FILE}"
		return 0
	fi

	if [[ -f "${MARKER_FILE}" ]]; then
		log "WARN: Could not update requirements, using existing installation."
		return 0
	fi

	log "ERROR: Could not install requirements and no existing installation was found."
	return 1
}

main() {
	local py_cmd

	init_logging || {
		echo "[bootstrap_venv] ERROR: Could not initialize log file (${LOG_FILE})."
		exit 1
	}

	init_python_config || exit 1
	log "Starting bootstrap for venv at ${VENV_DIR}."

	if [[ -d "${VENV_DIR}" ]]; then
		log "Existing venv found, checking compatibility."
		if ! is_required_python "${VENV_DIR}/bin/python3" || is_system_site_packages_enabled || ! is_venv_bound_to_managed_python; then
			log "Existing venv is incompatible or not properly bound to managed Python."
			py_cmd=$(ensure_managed_python) || {
				log "ERROR: Could not provision Python ${PYTHON_VERSION}."
				exit 1
			}
			log "Existing venv is incompatible or not properly bound, rebuilding it."
			rm -rf "${VENV_DIR}"
			create_venv "${py_cmd}" || exit 1
		else
			log "venv already exists (${VENV_DIR})."
		fi
	else
		log "No venv found, initializing a new one."
		py_cmd=$(ensure_managed_python) || {
			log "ERROR: Could not provision Python ${PYTHON_VERSION}."
			exit 1
		}
		create_venv "${py_cmd}" || exit 1
	fi

	ensure_permissions

	if [[ ! -f "${REQ_FILE}" ]]; then
		log "ERROR: requirements file not found (${REQ_FILE})."
		exit 1
	fi

	install_requirements || exit 1
	ensure_permissions
	log "venv ready (${VENV_DIR})."
}

main "$@"
