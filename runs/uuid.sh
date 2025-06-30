#!/bin/bash

# $Id$

## this script generates a log file for unique hardware and software id's on an
## openWB charging station based on unix timestamp, serial openWB, processor name,
## processor id, mac, ip, openWB Software Version, serial of memory card (mmc) and
## kernel version

## define vars first
OPENWBBASEDIR=$(cd "$(dirname "$0")/../" && pwd)
LOGFILE="$OPENWBBASEDIR/data/log/uuid"
MMCPATH="/sys/block/mmcblk0/device"
HOMEPATH="/home/$(whoami)"
MAXTIMEDIFF=$((7 * 24 * 60 * 60)) # one week

if [ ! -e "$LOGFILE" ]; then
	# create log file and header
	echo "Date Time;Timestamp;openWB Serial Number;processor name;processor id;mac addr;ip addr;openWB Version;mmc serial number;mmc manufacturing date;Kernel;FS" >"$LOGFILE"
else
	# check file size and truncate
	lines=$(wc -l "$LOGFILE" | cut -d " " -f 1)
	if ((lines > 500)); then
		head -n 1 "$LOGFILE" >"${LOGFILE}.tmp"
		tail -n 400 "$LOGFILE" >>"${LOGFILE}.tmp"
		mv "${LOGFILE}.tmp" "$LOGFILE"
	fi
fi

# generate unix time stamp and human readable date time
dateTime=$(date +"%Y-%m-%d %H:%M:%S")
now=$(date +%s)

# try to read serial
owbSerial="-"
if [ -f "$HOMEPATH/snnumber" ]; then
	serialNumber=$(grep "snnumber" "$HOMEPATH/snnumber")
	if [ -n "$serialNumber" ]; then
		# if not empty, get serial value
		owbSerial=$(echo "$serialNumber" | cut -d "=" -f 2)
	fi
fi

# get cpu model
cpuName=$(grep -i "model name" "/proc/cpuinfo" | head -1 | cut -d ":" -f 2 | xargs)
# get processor id on arm
cpuId="-"
if cpuSerial=$(grep -i "serial" "/proc/cpuinfo"); then
	cpuId=$(echo "$cpuSerial" | awk '{print $3}')
fi

# get mac addr
ethMac=$(ip addr show | grep "ether" | cut -d " " -f 6 | head -1)

# get ip
ipAddresses=$(ip addr show | grep -E -v "inet6|127.0.0.1" | grep "inet" | awk '{print $2}' | tr '\n' ':')

# get openWB software version
owbVersion=$(<"$OPENWBBASEDIR/web/version")

mmcSerial="-"
mmcManufacturing="-"
if [ -e "$MMCPATH" ]; then
	# get serial number from mmc
	mmcSerial=$(mmc cid read "$MMCPATH" | grep -i "serial" | awk '{print $2}')

	# get manufacturing (typo: manfacturing) date from mmc
	mmcManufacturing=$(mmc cid read "$MMCPATH" | grep -E -i "manu?facturing" | awk '{print $3 "\\" $4}')
fi

# kernel revision
kernel=$(uname -r)

# filesystem dirtyflag
fs="-"
if (sudo dmesg | grep -i "recovery required on readonly filesystem"); then
	fs=$(echo "dirty")
else
	fs=$(echo "clean")
fi

# check for changes and time since last entry
newData="$owbSerial;$cpuName;$cpuId;$ethMac;$ipAddresses;$owbVersion;$mmcSerial;$mmcManufacturing;$kernel;$fs"
oldData=$(tail -n 1 "$LOGFILE" | cut -d ";" -f 3-)
oldTimestamp=$(tail -n 1 "$LOGFILE" | cut -d ";" -f 2)
if [[ $newData != "$oldData" ]] || ((now - oldTimestamp > MAXTIMEDIFF)); then
	# store collected data in log file
	echo "$dateTime;$now;$newData" >>"$LOGFILE"
fi
