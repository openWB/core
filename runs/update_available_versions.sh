#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOGFILE="${OPENWBBASEDIR}/data/log/update.log"

if [ "$(id -u -n)" != "openwb" ]; then
	echo "this script has to be run as user openwb"
	exit 1
fi

{
	echo "#### updating available version info ####"
	cd "$OPENWBBASEDIR" || exit 1

	# update our local version
	currentCommit=$(git log --pretty='format:%ci [%h]' -n1)
	echo "current commit: $currentCommit"
	mosquitto_pub -p 1886 -t openWB/system/current_commit -r -m "\"$currentCommit\""

	# fetch data from git
	echo "fetching latest data from origin..."
	git fetch -v origin && echo "done"

	# update current master commit
	currentMasterCommit=$(git log --pretty='format:%ci [%h]' -n1 origin/master)
	echo "last commit to master branch: $currentMasterCommit"
	mosquitto_pub -p 1886 -t openWB/system/current_master_commit -r -m "\"$currentMasterCommit\""

	# list missing commits
	echo "changes:"
	IFS=$'\n'
	read -r -d '' -a commitDiff < <( git log --pretty='format:%ci [%h] - %s' master..origin/master )
	printf "* %s\n" "${commitDiff[@]}"
	commitDiffMessage=$(jq --compact-output --null-input '$ARGS.positional' --args -- "${commitDiff[@]}")
	mosquitto_pub -p 1886 -t openWB/system/current_missing_commits -r -m "$commitDiffMessage"
} >> "$LOGFILE" 2>&1
