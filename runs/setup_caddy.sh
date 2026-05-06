#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

detectPhpFpmSocket() {
	local sock
	sock=$(ls /run/php/php*fpm*.sock 2>/dev/null | head -1)
	if [ -n "$sock" ] && [ -S "$sock" ]; then
		echo "$sock"
		return 0
	fi
	return 1
}

PHP_SOCK=$(detectPhpFpmSocket)
if [ -z "$PHP_SOCK" ]; then
	echo "WARNING: No PHP-FPM socket found, attempting to start PHP-FPM..."
	sudo systemctl start php*-fpm 2>/dev/null || true
	PHP_SOCK=$(detectPhpFpmSocket)
fi

if [ -z "$PHP_SOCK" ]; then
	echo "ERROR: PHP-FPM is not running and no socket found. Aborting Caddy setup."
	exit 1
fi
echo "PHP-FPM socket: $PHP_SOCK"

CADDYFILE_SRC="${OPENWBBASEDIR}/data/config/caddy/Caddyfile"
CADDYFILE_DST="/etc/caddy/Caddyfile"
CADDYFILE_TMP="${CADDYFILE_DST}.tmp"

if [ ! -f "$CADDYFILE_SRC" ]; then
	echo "ERROR: Caddyfile template not found at $CADDYFILE_SRC"
	exit 1
fi

if allowUnencryptedAccess=$(mosquitto_sub -t "openWB/general/allow_unencrypted_access" -p 1886 -C 1 -W 1 --quiet); then
	echo "got 'allow unencrypted access' setting: '$allowUnencryptedAccess'"
else
	echo "failed getting 'allow unencrypted access' setting! assuming 'true'"
	allowUnencryptedAccess="true"
fi

if httpApiEnabled=$(mosquitto_sub -t "openWB/general/http_api" -p 1886 -C 1 -W 1 --quiet); then
	echo "got 'http api enabled' setting: '$httpApiEnabled'"
else
	echo "failed getting 'http api enabled' setting! assuming 'false'"
	httpApiEnabled="false"
fi

generate_site_block() {
	local block_name="$1"
	echo "${block_name} {"
	if [[ "$block_name" == ":81" ]]; then
		echo '	bind 127.0.0.1'
	fi
	echo '	root * /var/www/html'
	if [[ "$block_name" == ":443" || "$block_name" == ":8443" ]]; then
		echo '	tls /etc/ssl/certs/ssl-cert-snakeoil.pem /etc/ssl/private/ssl-cert-snakeoil.key'
	fi
	echo "	php_fastcgi unix/${PHP_SOCK}"
	echo '	file_server {'
	echo '		index index.php index.html'
	echo '	}'
	echo '	handle_path /openWB/ramdisk/* {'
	echo '		root * /var/www/html'
	echo '		file_server browse'
	echo '	}'
	echo '	handle_path /openWB/data/backup/* {'
	echo '		root * /var/www/html'
	echo '		file_server browse'
	echo '	}'
	echo '	handle /ws* {'
	echo '		reverse_proxy 127.0.0.1:9003'
	echo '	}'
	echo '	handle /mqtt* {'
	echo '		reverse_proxy 127.0.0.1:9003'
	echo '	}'
	echo '	header {'
	echo '		Cache-Control "no-cache, no-store, must-revalidate"'
	echo '		Pragma "no-cache"'
	echo '		Expires 0'
	echo '	}'
	echo '	@blocked {'
	echo '		path *.conf'
	echo '		path *.ini'
	echo '		path *.py'
	echo '		path *.sh'
	echo '	}'
	echo '	respond @blocked 404'
	echo '	@clientJson path /openWB/data/clients/*.json'
	echo '	respond @clientJson 403'
	echo '	handle_errors {'
	echo '		@404 expression {http.error.status_code} == 404'
	echo '		handle @404 {'
	echo '			rewrite * /openWB/web/error.html'
	echo '			file_server'
	echo '		}'
	echo '	}'
	if [[ "$block_name" != ":81" ]]; then
		local logname
		case "$block_name" in
			":80") logname="access" ;;
			":443") logname="ssl-access" ;;
			*) logname="access" ;;
		esac
		echo "	log {"
		echo "		output file /var/log/caddy/${logname}.log"
		echo "	}"
	fi
	echo '}'
}

{
	echo '# openwb-version:'"$(grep -o 'openwb-version:[0-9]\+' "$CADDYFILE_SRC" | head -1 | grep -o '[0-9]\+$')"
	echo '{'
	echo '	auto_https off'
	echo '}'
	echo ''

	if [[ "$allowUnencryptedAccess" == "true" ]]; then
		echo "WARNING: unencrypted access is enabled!" >&2
		generate_site_block ":80"
	else
		echo "unencrypted access is disabled" >&2
		echo ':80 {'
		echo '	redir https://{host}{uri} permanent'
		echo '}'
	fi
	echo ''

	generate_site_block ":443"
	echo ''

	generate_site_block ":81"
	echo ''

	if [[ "$httpApiEnabled" == "true" ]]; then
		echo "http api is enabled" >&2
		echo ':8443 {'
		echo '	root * /var/www/html/openWB/runs/http-api'
		echo '	tls /etc/ssl/certs/ssl-cert-snakeoil.pem /etc/ssl/private/ssl-cert-snakeoil.key'
		echo "	php_fastcgi unix/${PHP_SOCK}"
		echo '	file_server {'
		echo '		index index.php index.html'
		echo '	}'
		echo '	log {'
		echo '		output file /var/log/caddy/api-access.log'
		echo '	}'
		echo '}'
	else
		echo "http api is disabled" >&2
	fi
	echo ''

	if lsusb 2>/dev/null | grep -qE 'RTL8153|AX88179'; then
		echo "second network for pro plus detected" >&2
		echo ':8080 {'
		echo '	reverse_proxy 192.168.192.50:80'
		echo '}'
	else
		echo "no second network for pro plus detected" >&2
	fi
} | sudo tee "$CADDYFILE_TMP" > /dev/null

NEEDS_RESTART=0
if [ ! -f "$CADDYFILE_DST" ] || ! diff -q "$CADDYFILE_TMP" "$CADDYFILE_DST" > /dev/null 2>&1; then
	echo "Caddyfile changed, updating..."
	sudo mv "$CADDYFILE_TMP" "$CADDYFILE_DST"
	NEEDS_RESTART=1
else
	echo "Caddyfile is up to date"
	sudo rm -f "$CADDYFILE_TMP"
fi

echo "checking PHP-FPM upload limit..."
php_dir=""
for dir in /etc/php/*/fpm/conf.d; do
	if [ -d "$dir" ]; then
		php_dir="$dir"
		break
	fi
done
if [ -n "$php_dir" ]; then
	if [ ! -f "${php_dir}/20-uploadlimit.ini" ] || ! diff -q "${OPENWBBASEDIR}/data/config/php/fpm/20-uploadlimit.ini" "${php_dir}/20-uploadlimit.ini" > /dev/null 2>&1; then
		echo "updating PHP upload limit..."
		sudo cp "${OPENWBBASEDIR}/data/config/php/fpm/20-uploadlimit.ini" "${php_dir}/20-uploadlimit.ini"
		sudo systemctl restart php*-fpm 2>/dev/null
	else
		echo "PHP upload limit already up to date"
	fi
else
	echo "no PHP-FPM config directory found, skipping"
fi

sudo usermod -aG ssl-cert caddy 2>/dev/null
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy

sudo chmod -R a+rX /var/www/html 2>/dev/null

if [[ "$NEEDS_RESTART" == "1" ]]; then
	echo -n "validating Caddyfile..."
	if sudo caddy validate --config "$CADDYFILE_DST" --adapter caddyfile 2>&1; then
		echo -n "restarting caddy..."
		sudo systemctl restart caddy
		echo "done"
	else
		echo "ERROR: Caddyfile validation failed, not restarting!"
	fi
else
	echo "caddy configuration is already up to date"
fi
