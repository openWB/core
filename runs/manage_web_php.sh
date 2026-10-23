#!/bin/bash
set -Eeuo pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
for variable in ${!APACHE_@}; do unset "$variable"; done
BASE=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
APACHE=/etc/apache2
STATE=/var/lib/openwb-web-php-bash
GUARD=disable-web-php

usage() {
	echo "Usage: sudo $0 [--debug] disable|enable"
	echo "--debug: show troubleshooting stages and module-detection diagnostics."
	echo "Standard openWB Debian mod_php only; custom Apache/FPM/CGI setups need administrator review."
	echo "PHP CLI and charging services are unchanged. Recheck after updates; no startup/UI integration."
	echo "Enable restores saved modules/API state."
	echo "Power loss/SIGKILL during enable is not crash-atomic; rerun disable before restarting Apache."
}
die() { echo "ERROR: $* Result NOT confirmed." >&2; exit 1; }
debug_enabled=0
mode=
debug() { if (( debug_enabled )); then echo "INFO: $*"; fi; }
step() { stage=$*; debug "$stage"; }
for argument in "$@"; do
	case $argument in
		--debug) debug_enabled=1 ;;
		--help|-h) usage; exit 0 ;;
		enable|disable)
			[[ -z $mode ]] || { usage; exit 1; }
			mode=$argument ;;
		*) usage; exit 1 ;;
	esac
done
[[ -n $mode ]] || { usage; exit 1; }
[[ $EUID == 0 ]] || die "Run with sudo."
echo "Standard openWB mod_php only; custom Apache/FPM/CGI setups require administrator review."

sudo_lock=/run/openwb-apache
install -d -m 755 "$sudo_lock"
touch "$sudo_lock/configuration.lock"
chmod 644 "$sudo_lock/configuration.lock"
exec 9<"$sudo_lock/configuration.lock"
flock --exclusive 9
[[ ! -L $STATE ]] || die "State directory must not be a symlink."
install -d -m 700 "$STATE"
[[ $(stat -c %u "$STATE") == 0 ]] || die "State directory must be root-owned."
umask 077
probe=
transition=0
stage=preflight
guard() {
	local file="$APACHE/conf-available/$GUARD.conf"
	# Never overwrite a custom deny rule.
	[[ ! -L $file ]] || return 1
	cat >"$STATE/guard.tmp" <<'EOF' || return 1
# Managed by openWB runs/manage_web_php.sh
<FilesMatch "(?i)\.(php[0-9]*|phtml|phar|phps)(\.|$)">
    Require all denied
</FilesMatch>
<LocationMatch "(?i)\.(php[0-9]*|phtml|phar|phps)([./]|$)">
    Require all denied
</LocationMatch>
EOF
	if [[ -e $file ]]; then cmp -s "$STATE/guard.tmp" "$file" || return 1; fi
	install -m 644 "$STATE/guard.tmp" "$file" || return 1
	a2enconf "$GUARD"
}
cleanup() {
	local status=$? failed=0 active
	trap - EXIT INT TERM
	(( status == 0 )) || echo "ERROR: failed during $stage; requested result NOT confirmed." >&2
	if (( status != 0 && ! transition )); then echo "INFO: Apache/PHP configuration was not changed by this run." >&2; fi
	if (( status != 0 && transition )); then
		guard || failed=1
		timeout 60 systemctl stop apache2.service || failed=1
		active=$(timeout 60 systemctl show --property=ActiveState --value apache2.service) || failed=1
		[[ $active == inactive || $active == failed ]] || failed=1
		if (( failed )); then
			echo "FAILED: cleanup unconfirmed; Apache may still expose PHP!" >&2
		else
			echo "FAILED: Apache stopped with PHP deny guard enabled." >&2
		fi
		echo "Rollback state retained. Correct the error and rerun." >&2
	fi
	[[ -z $probe ]] || rm -f "$probe"
	rm -f "$STATE/guard.tmp" "$STATE/state.tmp"
	exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
enabled() { [[ -e $APACHE/sites-enabled/$1.conf ]]; }
modules() {
	local file name
	for file in "$APACHE"/mods-enabled/php*.load; do
		[[ -e $file ]] || continue
		name=${file##*/}; name=${name%.load}
		[[ $name =~ ^php[0-9]+(\.[0-9]+)?$ ]] || continue
		echo "$name"
	done
}
module_diagnostics() {
	local directory loaded
	if (( ! debug_enabled )); then
		echo "Rerun with --debug for PHP module-detection diagnostics." >&2
		return 0
	fi
	echo "DIAGNOSTIC: recognized enabled PHP modules: ${saved[*]:-(none)}" >&2
	echo "DIAGNOSTIC: looking for php<number>[.<number>].load; symlinks must resolve." >&2
	for directory in mods-enabled mods-available; do
		echo "DIAGNOSTIC: $APACHE/$directory PHP entries (name -> symlink target):" >&2
		find "$APACHE/$directory" -maxdepth 1 -iname '*php*' -printf '  %f -> %l\n' >&2 || true
	done
	echo "DIAGNOSTIC: Apache PHP/CGI module report:" >&2
	if loaded=$(apache2ctl -M); then
		grep -Ei 'php|cgi|actions' <<<"$loaded" >&2 || echo "  (no PHP/CGI modules reported)" >&2
	else
		echo "  Unable to query Apache modules." >&2
	fi
	echo "DIAGNOSTIC: HTTP 403 alone does not prove mod_php is unloaded; no module will be guessed." >&2
}
check_modules() {
	local loaded
	loaded=$(apache2ctl -M)
	! grep -Eq '^[[:space:]]*(cgi|cgid|fcgid|fastcgi|proxy_fcgi|proxy_scgi|actions)_module' <<<"$loaded" ||
		die "Alternate CGI/FastCGI handler found; administrator review required."
	if [[ $mode == disable ]]; then
		! grep -Eq '^[[:space:]]*php[^[:space:]]*_module' <<<"$loaded" || die "PHP module is still loaded."
	else
		grep -Eq '^[[:space:]]*php[^[:space:]]*_module' <<<"$loaded" || die "No PHP module is loaded."
	fi
}
step "checking Apache configuration and validation endpoints"
apache2ctl configtest
urls=()
if enabled localhost; then urls+=(http://127.0.0.1:81); fi
if enabled 000-default; then urls+=(http://127.0.0.1); fi
if enabled apache-openwb-ssl; then urls+=(https://127.0.0.1); fi
(( ${#urls[@]} )) || die "No standard openWB website enabled for HTTP validation (localhost, 000-default or apache-openwb-ssl)."
debug "validation endpoints: ${urls[*]}"
[[ $(systemctl is-enabled apache2.service || true) != masked* ]] || die "Apache is masked."
systemctl is-active --quiet apache2.service || die "Apache is stopped; start it explicitly before live validation."
step "detecting PHP modules and rollback state"
if [[ -e $APACHE/conf-enabled/$GUARD.conf ]]; then
	debug "PHP deny guard is already enabled; HTTP 403 may be due to this existing rule."
else
	debug "PHP deny guard is not enabled."
fi
mapfile -t saved < <(modules)
debug "recognized enabled PHP modules: ${saved[*]:-(none)}"
api=false
enabled http-api-ssl && api=true
if [[ -e $STATE/state ]]; then
	debug "reading saved module/API state from $STATE/state"
	mapfile -t saved <"$STATE/state"
	api=${saved[0]:-invalid}; saved=("${saved[@]:1}")
	[[ $api == true || $api == false ]] || die "Invalid saved API state."
else
	if [[ $mode == enable ]]; then
		[[ ! -e $APACHE/conf-enabled/$GUARD.conf ]] || die "No Bash rollback state; guard retained."
	fi
	if (( ! ${#saved[@]} )); then
		module_diagnostics
		die "No enabled Debian mod_php module found. PHP may already be disabled or use a different handler/name."
	fi
	printf '%s\n' "$api" "${saved[@]}" >"$STATE/state.tmp"
	mv "$STATE/state.tmp" "$STATE/state"
fi
(( ${#saved[@]} )) || die "No PHP module to restore or validate."
for module in "${saved[@]}"; do
	[[ $module =~ ^php[0-9]+(\.[0-9]+)?$ ]] || die "Invalid saved PHP module."
	[[ -f $APACHE/mods-available/$module.load ]] || die "PHP module $module is no longer installed."
	dpkg-query -W '-f=${Package} ${Version}\n' "libapache2-mod-$module" 2>/dev/null || true
done
php -n -v 2>/dev/null | head -n 1 || true
echo "PHP2Shell patch status: UNKNOWN; check your vendor advisory for backports."
[[ $mode != enable ]] || echo "WARNING: enabling web PHP restores its attack surface; this is not a security patch."
transition=1
step "stopping Apache and applying PHP $mode"
timeout 60 systemctl stop apache2.service
if [[ $mode == disable ]]; then
	guard
	mapfile -t current < <(modules)
	for module in "${current[@]}"; do a2dismod "$module"; done
	if enabled http-api-ssl; then a2dissite http-api-ssl; fi
else
	for module in "${saved[@]}"; do a2enmod "$module"; done
	if [[ -e $STATE/state ]]; then a2disconf "$GUARD"; fi
	if [[ $api == true ]]; then a2ensite http-api-ssl
	elif enabled http-api-ssl; then a2dissite http-api-ssl; fi
fi
step "checking changed configuration before starting Apache"
apache2ctl configtest
check_modules
timeout 60 systemctl start apache2.service
step "validating running Apache and PHP $mode"
systemctl is-active --quiet apache2.service
check_modules
if [[ $mode == disable ]]; then
	if enabled http-api-ssl; then die "PHP API site is still enabled."; fi
else
	if [[ $api == true ]]; then enabled http-api-ssl || die "PHP API site was not restored."
	elif enabled http-api-ssl; then die "PHP API site should be disabled."; fi
fi
curl_local() { curl -ksS --noproxy '*' --connect-timeout 5 --max-time 10 "$@"; }
if [[ $mode == enable ]]; then
	probe=$(mktemp "$BASE/web/openwb-php-check-XXXXXX.php")
	token=$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')
	printf "<?php echo '%s';" "$token" >"$probe"
	chmod 644 "$probe"
fi
for url in "${urls[@]}"; do
	step "checking static website and PHP response at $url"
	[[ $(curl_local -o /dev/null -w '%{http_code}' "$url/openWB/index.html") == 200 ]] ||
		die "Static website check failed at $url."
	if [[ $mode == disable ]]; then
		[[ $(curl_local -o /dev/null -w '%{http_code}' "$url/openWB/web/settings/uploadFile.php") == 403 ]] ||
			die "PHP denial check failed at $url; expected HTTP 403."
	else
		[[ $(curl_local -w '%{http_code}' "$url/openWB/web/${probe##*/}") == "${token}200" ]] ||
			die "PHP execution check failed at $url."
	fi
	echo "CHECK $url: static HTTP 200; PHP $mode verified."
done
if [[ $mode == enable ]]; then rm -f "$STATE/state"; fi
transition=0
echo "CONFIRMED: web PHP $mode verified on standard openWB endpoints; PHP CLI unchanged."
if [[ $mode == disable ]]; then
	echo "Disabled to contain PHP2Shell: web PHP modules and optional HTTPS API (port 8443)."
	echo "Unavailable: restore/migration uploads, PHP CSV export, Tesla/Mercedes authorization,"
	echo "legacy SmartHome settings and PHP firmware-update buttons. Static UI and /ws remain configured."
fi
echo "Verify dashboard updates, primary/secondary communication and charging manually."
echo "Recheck after updates/startup setup, which may re-enable the API site; the deny guard persists when disabled."
