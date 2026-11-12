#!/bin/bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
workdir=$(mktemp -d)
trap 'rm -rf -- "$workdir"' EXIT
mkdir -p "$workdir/openwb/runs" "$workdir/bin"
cp "$script_dir/run_python.sh" "$workdir/openwb/runs/"
printf 'example==1\n' > "$workdir/openwb/requirements.txt"

cat > "$workdir/bin/python" <<'EOF'
#!/bin/bash
set -e
if [[ "$1" == -c ]]; then
	echo 'mock Python 3.9'
elif [[ "$1 $2" == '-m venv' ]]; then
	mkdir -p "$3/bin"
	cat > "$3/bin/python" <<'PYTHON'
#!/bin/bash
if [[ "${1:-}" == --probe ]]; then
	printf '%s\n' "$0"
	exit 0
fi
if [[ "${1:-}" == --show-python-path ]]; then
	command -v python3
	exit 0
fi
if [[ "${1:-}" == --hold ]]; then
	printf 'ready\n'
	read -r
	exit 0
fi
if [[ -n "${MOCK_PYTHON_LOG:-}" ]]; then
	printf '%s\n' "$*" >> "$MOCK_PYTHON_LOG"
fi
if [[ "$*" == '-m pip check' ]]; then
	[[ ${PIP_CHECK_RESULT:-0} == 0 ]]
	exit $?
fi
if [[ "$1" == -c && "$2" == 'import aiohttp, evdev, grpc, jq, lxml, paho.mqtt.client, pymodbus, telnetlib3' ]]; then
	[[ ${IMPORT_PROBE_RESULT:-0} == 0 ]]
	exit $?
fi
if [[ "${1:-}" == -c && "${2:-}" == *sysconfig* ]]; then
	mkdir -p "$(dirname "$0")/../site-packages"
	cd "$(dirname "$0")/../site-packages" && pwd
	exit 0
fi
if [[ "$*" == '-m pip install '* ]]; then
	[[ -z "${PIP_TARGET:-}${PIP_PREFIX:-}${PIP_ROOT:-}${PIP_USER:-}" ]] || exit 1
	if [[ -n "${PIP_CAPTURE:-}" ]]; then
		printf '%s\n' "$*" >> "$PIP_CAPTURE"
	fi
fi
if [[ "${FAIL_INSTALL:-0}" == 1 && "$*" == '-m pip install '* ]]; then
	exit 1
fi
exit 0
PYTHON
	chmod +x "$3/bin/python"
	ln -s python "$3/bin/python3"
else
	exit 1
fi
EOF
chmod +x "$workdir/bin/python"
export OPENWB_PYTHON="$workdir/bin/python"
export PIP_TARGET=/unexpected PIP_PREFIX=/unexpected PIP_ROOT=/unexpected PIP_USER=1
cat > "$workdir/bin/legacy-python" <<'EOF'
#!/bin/bash
if [[ "$1" == -c && "$2" == *find_spec* ]]; then
	[[ ${LEGACY_TELNET_AVAILABLE:-0} == 1 ]]
	exit $?
fi
printf 'legacy interpreter: %s\n' "$*"
EOF
chmod +x "$workdir/bin/legacy-python"
export OPENWB_LEGACY_PYTHON="$workdir/bin/legacy-python"

status=0
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 1 || status=$?
[[ "$status" == 10 ]]
first_env=$(readlink -f "$workdir/openwb/.venv")
[[ -f "$first_env/.openwb-ready" ]]
[[ $(stat -c '%a' "$first_env") == 755 ]]
[[ -f "$workdir/openwb/.venvs/.migrated" ]]
[[ $(bash "$workdir/openwb/runs/run_python.sh" --probe) == "$first_env/bin/python" ]]
[[ $(bash "$workdir/openwb/runs/run_python.sh" --show-python-path) == "$first_env/bin/python3" ]]
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0 --boot-cleanup boot-one
coproc HOLDER { bash "$workdir/openwb/runs/run_python.sh" --hold; }
holder_pid=$HOLDER_PID
read -r holder_ready <&"${HOLDER[0]}"
[[ "$holder_ready" == ready ]]
touch "$workdir/openwb/.venvs/.legacy"
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0
[[ ! -e "$workdir/openwb/.venvs/.legacy" ]]

printf 'example==2\n' > "$workdir/openwb/requirements.txt"
if bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0; then
	exit 1
fi
if FAIL_INSTALL=1 bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 1; then
	exit 1
fi
[[ $(readlink -f "$workdir/openwb/.venv") == "$first_env" ]]
[[ $(find "$workdir/openwb/.venvs" -maxdepth 1 -type d -name 'env.*' | wc -l) == 1 ]]

for validation in pip-check import-probe; do
	validation_root="$workdir/failed-$validation"
	mkdir "$validation_root"
	cp "$workdir/openwb/requirements.txt" "$validation_root/requirements.txt"
	status=0
	if [[ "$validation" == pip-check ]]; then
		PIP_CHECK_RESULT=1 MOCK_PYTHON_LOG="$validation_root/python.log" \
			bash "$script_dir/setup_python_venv.sh" "$validation_root" 1 > "$validation_root/setup.log" 2>&1 || status=$?
		grep -q '^-m pip check$' "$validation_root/python.log"
	else
		IMPORT_PROBE_RESULT=1 MOCK_PYTHON_LOG="$validation_root/python.log" \
			bash "$script_dir/setup_python_venv.sh" "$validation_root" 1 > "$validation_root/setup.log" 2>&1 || status=$?
		grep -q '^-c import aiohttp, evdev, grpc, jq, lxml, paho.mqtt.client, pymodbus, telnetlib3$' "$validation_root/python.log"
	fi
	[[ "$status" != 0 ]]
	[[ ! -e "$validation_root/.venv" && ! -L "$validation_root/.venv" ]]
	[[ $(find "$validation_root/.venvs" -maxdepth 1 -type d -name 'env.*' | wc -l) == 0 ]]
done

status=0
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 1 || status=$?
[[ "$status" == 10 ]]
second_env=$(readlink -f "$workdir/openwb/.venv")
[[ "$second_env" != "$first_env" && -d "$first_env" ]]
[[ $(bash "$workdir/openwb/runs/run_python.sh" --probe) == "$second_env/bin/python" ]]
mkdir -p "$workdir/openwb/.venvs/env.OLD00001" "$workdir/openwb/.venvs/env.OLD00002"
touch "$workdir/openwb/.venvs/env.OLD00001/.openwb-ready"
touch "$workdir/openwb/.venvs/env.OLD00002/.openwb-ready" "$workdir/openwb/.venvs/env.OLD00002/.openwb-lock" "$workdir/openwb/.venvs/env.OLD00002/.openwb-unprotected"
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0
[[ -d "$first_env" && -d "$second_env" ]]
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0 --boot-cleanup boot-one
[[ -d "$first_env" ]]
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0 --boot-cleanup boot-two
[[ -d "$first_env" ]]
printf 'stop\n' >&"${HOLDER[1]}"
wait "$holder_pid"
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0
[[ -d "$first_env" ]]
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0 --boot-cleanup boot-two
[[ -d "$first_env" ]]
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0 --boot-cleanup boot-three
[[ ! -e "$first_env" && -d "$second_env" ]]
[[ -d "$workdir/openwb/.venvs/env.OLD00001" && -d "$workdir/openwb/.venvs/env.OLD00002" ]]

mkdir -p "$workdir/legacy/.venvs/env.LEGACY01/bin"
cp "$second_env/bin/python" "$workdir/legacy/.venvs/env.LEGACY01/bin/python"
cp "$workdir/openwb/requirements.txt" "$workdir/legacy/requirements.txt"
printf 'old fingerprint\n' > "$workdir/legacy/.venvs/env.LEGACY01/.openwb-ready"
ln -s "$workdir/legacy/.venvs/env.LEGACY01" "$workdir/legacy/.venv"
status=0
bash "$script_dir/setup_python_venv.sh" "$workdir/legacy" 1 || status=$?
[[ "$status" == 10 ]]
[[ -f "$workdir/legacy/.venvs/env.LEGACY01/.openwb-unprotected" ]]
bash "$script_dir/setup_python_venv.sh" "$workdir/legacy" 0 --boot-cleanup boot-one
bash "$script_dir/setup_python_venv.sh" "$workdir/legacy" 0 --boot-cleanup boot-two
[[ -d "$workdir/legacy/.venvs/env.LEGACY01" ]]

mkdir -p "$workdir/real/runs" "$workdir/real/.venvs/env.REAL0001/bin"
cp "$script_dir/run_python.sh" "$workdir/real/runs/"
ln -s /usr/bin/python3 "$workdir/real/.venvs/env.REAL0001/bin/python"
touch "$workdir/real/.venvs/.lock" "$workdir/real/.venvs/env.REAL0001/.openwb-lock" "$workdir/real/.venvs/env.REAL0001/.openwb-ready"
ln -s "$workdir/real/.venvs/env.REAL0001" "$workdir/real/.venv"
coproc REAL_HOLDER { bash "$workdir/real/runs/run_python.sh" -u -c 'import sys; print("ready", flush=True); sys.stdin.readline()'; }
real_holder_pid=$REAL_HOLDER_PID
read -r real_holder_ready <&"${REAL_HOLDER[0]}"
[[ "$real_holder_ready" == ready ]]
if flock -n -x "$workdir/real/.venvs/env.REAL0001/.openwb-lock" true; then
	exit 1
fi
printf 'stop\n' >&"${REAL_HOLDER[1]}"
wait "$real_holder_pid"
flock -n -x "$workdir/real/.venvs/env.REAL0001/.openwb-lock" true

mkdir "$workdir/concurrent"
cp "$workdir/openwb/requirements.txt" "$workdir/concurrent/requirements.txt"
bash "$script_dir/setup_python_venv.sh" "$workdir/concurrent" 1 > "$workdir/first.log" 2>&1 &
first_pid=$!
bash "$script_dir/setup_python_venv.sh" "$workdir/concurrent" 1 > "$workdir/second.log" 2>&1 &
second_pid=$!
first_status=0
second_status=0
wait "$first_pid" || first_status=$?
wait "$second_pid" || second_status=$?
[[ $((first_status + second_status)) == 10 ]]
[[ $(find "$workdir/concurrent/.venvs" -maxdepth 1 -type d -name 'env.*' | wc -l) == 1 ]]

mkdir "$workdir/activation-bin" "$workdir/activation"
cp "$workdir/openwb/requirements.txt" "$workdir/activation/requirements.txt"
cat > "$workdir/activation-bin/mv" <<'EOF'
#!/bin/bash
/bin/mv "$@"
status=$?
target=
for argument in "$@"; do target=$argument; done
if [[ $status == 0 && "$target" == */.venv ]]; then
	kill -TERM "$PPID"
fi
exit "$status"
EOF
chmod +x "$workdir/activation-bin/mv"
activation_status=0
PATH="$workdir/activation-bin:$PATH" bash "$script_dir/setup_python_venv.sh" "$workdir/activation" 1 > "$workdir/activation.log" 2>&1 || activation_status=$?
[[ "$activation_status" != 0 ]]
[[ -L "$workdir/activation/.venv" ]]
activated_env=$(readlink -f "$workdir/activation/.venv")
[[ -d "$activated_env" && -f "$activated_env/.openwb-ready" ]]

mkdir "$workdir/arch-bin"
mkdir -p "$workdir/system-evdev/evdev" "$workdir/system-evdev/evdev-1.9.1.dist-info"
cat > "$workdir/arch-bin/dpkg" <<'EOF'
#!/bin/bash
printf '%s\n' "$TEST_ARCH"
EOF
chmod +x "$workdir/arch-bin/dpkg"
for architecture in armhf arm64 amd64; do
	mkdir "$workdir/$architecture"
	cp "$workdir/openwb/requirements.txt" "$workdir/$architecture/requirements.txt"
	status=0
	PATH="$workdir/arch-bin:$PATH" TEST_ARCH="$architecture" PIP_CAPTURE="$workdir/$architecture/pip.log" \
		OPENWB_EVDEV_SOURCE="$workdir/system-evdev" \
		bash "$script_dir/setup_python_venv.sh" "$workdir/$architecture" 1 || status=$?
	[[ "$status" == 10 ]]
	grep -q -- '--only-binary=:all:' "$workdir/$architecture/pip.log"
	if [[ "$architecture" == amd64 ]]; then
		grep -q -- '--no-binary=evdev' "$workdir/$architecture/pip.log"
	else
		! grep -q -- '--no-binary' "$workdir/$architecture/pip.log"
	fi
	if [[ "$architecture" == arm64 ]]; then
		[[ -d "$workdir/$architecture/.venv/site-packages/evdev-1.9.1.dist-info" ]]
	fi
done
mkdir -p "$workdir/system-evdev-egg/evdev" "$workdir/system-evdev-egg/evdev-1.9.1.egg-info" "$workdir/arm64-egg"
cp "$workdir/openwb/requirements.txt" "$workdir/arm64-egg/requirements.txt"
status=0
PATH="$workdir/arch-bin:$PATH" TEST_ARCH=arm64 PIP_CAPTURE="$workdir/arm64-egg/pip.log" \
	OPENWB_EVDEV_SOURCE="$workdir/system-evdev-egg" \
	bash "$script_dir/setup_python_venv.sh" "$workdir/arm64-egg" 1 || status=$?
[[ "$status" == 10 ]]
egg_env=$(readlink -f "$workdir/arm64-egg/.venv")
[[ -d "$egg_env/site-packages/evdev-1.9.1.egg-info" ]]
[[ ! -e "$egg_env/site-packages/evdev-1.9.1.dist-info" ]]

mkdir -p "$workdir/missing-deb" "$workdir/wrong-evdev/evdev" "$workdir/wrong-evdev/evdev-1.6.1.dist-info"
cp "$workdir/openwb/requirements.txt" "$workdir/missing-deb/requirements.txt"
if PATH="$workdir/arch-bin:$PATH" TEST_ARCH=arm64 OPENWB_EVDEV_SOURCE="$workdir/wrong-evdev" \
	bash "$script_dir/setup_python_venv.sh" "$workdir/missing-deb" 1; then
	exit 1
fi
[[ ! -e "$workdir/missing-deb/.venv" ]]
[[ $(find "$workdir/missing-deb/.venvs" -maxdepth 1 -type d -name 'env.*' | wc -l) == 0 ]]
arm64_env=$(readlink -f "$workdir/arm64/.venv")
printf 'example==3\n' > "$workdir/arm64/requirements.txt"
if PATH="$workdir/arch-bin:$PATH" TEST_ARCH=arm64 OPENWB_EVDEV_SOURCE="$workdir/wrong-evdev" \
	bash "$script_dir/setup_python_venv.sh" "$workdir/arm64" 1; then
	exit 1
fi
[[ $(readlink -f "$workdir/arm64/.venv") == "$arm64_env" ]]

rm "$workdir/openwb/.venv"
bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 0 --boot-cleanup boot-four
touch "$workdir/openwb/.venvs/.legacy"
if bash "$workdir/openwb/runs/run_python.sh" -c 'pass'; then
	exit 1
fi
rm "$workdir/openwb/.venvs/.migrated"
if bash "$workdir/openwb/runs/run_python.sh" --probe > "$workdir/legacy.out" 2> "$workdir/legacy.err"; then
	exit 1
fi
[[ ! -s "$workdir/legacy.out" ]]
grep -q 'neither telnetlib3 nor telnetlib is available' "$workdir/legacy.err"
LEGACY_TELNET_AVAILABLE=1 bash "$workdir/openwb/runs/run_python.sh" --probe > "$workdir/legacy.out"
grep -q 'legacy interpreter: --probe' "$workdir/legacy.out"

mkdir "$workdir/openwb/.venv"
if bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 1; then
	exit 1
fi
[[ -d "$workdir/openwb/.venv" ]]
rmdir "$workdir/openwb/.venv"
mkdir -p "$workdir/foreign/bin"
cp "$second_env/bin/python" "$workdir/foreign/bin/python"
touch "$workdir/foreign/.openwb-ready" "$workdir/openwb/.venvs/.migrated"
ln -s "$workdir/foreign" "$workdir/openwb/.venv"
if bash "$script_dir/setup_python_venv.sh" "$workdir/openwb" 1; then
	exit 1
fi
if bash "$workdir/openwb/runs/run_python.sh" --probe; then
	exit 1
fi
[[ $(readlink "$workdir/openwb/.venv") == "$workdir/foreign" ]]
mkdir "$workdir/apt-bin"
mkdir -p "$workdir/apt/sources.list.d"
cat > "$workdir/apt/sources.list" <<'EOF'
deb http://security.debian.org/debian-security bullseye-security main
deb-src https://security.debian.org/debian-security/ bullseye-security main
deb http://deb.debian.org/debian bullseye main
deb http://security.debian.org/debian-security trixie-security main
# deb http://security.debian.org/debian-security bullseye-security main
EOF
cat > "$workdir/apt/sources.list.d/security.sources" <<'EOF'
Types: deb deb-src
URIs: http://security.debian.org/debian-security
Suites: bullseye-security
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://security.debian.org/debian-security
Suites: trixie-security
Components: main
EOF
cat > "$workdir/apt-bin/sudo" <<'EOF'
#!/bin/bash
if [[ "$1" == apt-get && " $* " == *" ${FAIL_APT_STEP} "* ]]; then
	exit 42
fi
if [[ "$1" == mv && ${FAIL_SOURCE_RENAME:-0} == 1 ]]; then
	exit 42
fi
exec "$@"
EOF
chmod +x "$workdir/apt-bin/sudo"
for step in update install; do
	status=0
	PATH="$workdir/apt-bin:$PATH" FAIL_APT_STEP="$step" OPENWB_APT_DIR="$workdir/apt" \
		bash "$script_dir/install_packages.sh" > "$workdir/apt-$step.log" 2>&1 || status=$?
	[[ "$status" == 1 ]]
	grep -q 'Failed to' "$workdir/apt-$step.log"
	! grep -q 'PHP 7.4 package fix' "$workdir/apt-$step.log"
done
if [[ $(. /etc/os-release; printf '%s' "${VERSION_CODENAME:-}") == bullseye ]]; then
	[[ $(grep -c '^deb.*https://archive.debian.org/debian-security bullseye-security' "$workdir/apt/sources.list") == 2 ]]
	grep -q '^deb http://deb.debian.org/debian bullseye main$' "$workdir/apt/sources.list"
	grep -q '^deb http://security.debian.org/debian-security trixie-security main$' "$workdir/apt/sources.list"
	grep -q '^# deb http://security.debian.org/debian-security bullseye-security main$' "$workdir/apt/sources.list"
	grep -q '^URIs: https://archive.debian.org/debian-security$' "$workdir/apt/sources.list.d/security.sources"
	grep -q '^URIs: http://security.debian.org/debian-security$' "$workdir/apt/sources.list.d/security.sources"
	grep -q '^Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg$' "$workdir/apt/sources.list.d/security.sources"
	grep -q '^deb http://security.debian.org/debian-security bullseye-security main$' "$workdir/apt/sources.list.openwb-backup"
	! grep -q 'Updated Bullseye security source' "$workdir/apt-install.log"
fi
mkdir -p "$workdir/apt-rename-failure/sources.list.d"
cat > "$workdir/apt-rename-failure/sources.list" <<'EOF'
deb http://security.debian.org/debian-security bullseye-security main
EOF
cp "$workdir/apt/sources.list.d/security.sources" "$workdir/apt-rename-failure/sources.list.d/security.sources"
if PATH="$workdir/apt-bin:$PATH" OPENWB_APT_DIR="$workdir/apt-rename-failure" FAIL_SOURCE_RENAME=1 \
	bash "$script_dir/install_packages.sh" > "$workdir/apt-rename-failure.log" 2>&1; then
	exit 1
fi
grep -q '^deb http://security.debian.org/debian-security bullseye-security main$' "$workdir/apt-rename-failure/sources.list"
[[ $(find "$workdir/apt-rename-failure" -maxdepth 1 -name 'sources.list.openwb.*' | wc -l) == 0 ]]
echo 'Python environment bootstrap tests passed'
