#!/bin/bash
OPENWBBASEDIR="/var/www/html/openWB"

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$IP" ]; then
	IP="unknown"
fi

# Get openWB version
OWB_VERSION="unknown"
OWB_GIT="unknown"
if [ -d "$OPENWBBASEDIR/.git" ]; then
	OWB_GIT=$(cd "$OPENWBBASEDIR" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")
	OWB_BRANCH=$(cd "$OPENWBBASEDIR" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
fi

# Check service status
OWB_STATUS=$(systemctl is-active openwb2.service 2>/dev/null || echo "unknown")

# Get Debian version
. /etc/os-release 2>/dev/null
DEBIAN_VER="${PRETTY_NAME:-unknown}"

# Get uptime
UPTIME=$(uptime -p 2>/dev/null || echo "unknown")

# Get memory
MEM=$(free -h 2>/dev/null | awk '/^Mem:/{print $3 "/" $2}' || echo "unknown")

# Get load
LOAD=$(cat /proc/loadavg 2>/dev/null | awk '{print $1 " " $2 " " $3}' || echo "unknown")

printf "${GREEN}╔══════════════════════════════════════════════════════════╗
║                    openWB 2.0                            ║
╚══════════════════════════════════════════════════════════╝${RESET}
  Web UI:      ${BOLD}http://${IP}/openWB/${RESET}
  Status:      $([ "$OWB_STATUS" = "active" ] && echo "$GREEN" || echo "$RED")${OWB_STATUS}${RESET}
  Git:         ${OWB_BRANCH} @ ${OWB_GIT}
  OS:          ${DEBIAN_VER}
  Uptime:      ${UPTIME}
  Load:        ${LOAD}
  Memory:      ${MEM}

  ${DIM}Logs: journalctl -u openwb2 -f${RESET}
"
