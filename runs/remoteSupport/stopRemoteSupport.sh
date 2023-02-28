#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
RAMDISKDIR="$OPENWBBASEDIR/ramdisk"
LOG_FILE="$RAMDISKDIR/remote_support.log"
PID_FILE="$RAMDISKDIR/remote_support.pid"
PATTERN="^sshpass .*@remotesupport.openwb.de$"

{
	if [ ! -f "$PID_FILE" ]; then
		echo "pid file '$PID_FILE' missing"
	else
		echo "pid file '$PID_FILE' found"
		pid=$(<"$PID_FILE")
		echo "remote support pid: $pid"
		if ! pgrep -F "$PID_FILE" >/dev/null; then
			echo "no process with pid found"
		else
			echo "process is running"
			if ! pgrep -F "$PID_FILE" -a -f "$PATTERN"; then
				echo "process does not match pattern"
			else
				if pkill -F "$PID_FILE" -f "$PATTERN"; then
					echo "process killed"
				else
					echo "error killing process"
				fi
			fi
		fi
		rm "$PID_FILE"
	fi
} >>"$LOG_FILE"
