#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOGFILE="${OPENWBBASEDIR}/data/log/update.log"
GITREMOTE="origin"
selectedBranch="master"

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
	echo "fetching latest data from $GITREMOTE..."
	git fetch -v "$GITREMOTE" && echo "done"

	# update branches from $GITREMOTE
	echo "branches:"
	IFS=$'\n'
	read -r -d '' -a branches < <(git branch -r --list "$GITREMOTE/*")
	declare -A availableBranches
	for index in "${!branches[@]}"; do
		if [[ ${branches[$index]} == *"HEAD"* ]]; then
			unset 'branches[$index]'
		else
			branches[$index]="${branches[$index]//*\//}"  # remove leading $GITREMOTE/ and whitespaces
			echo "checking commit for $GITREMOTE/${branches[$index]}..." "$(git log --pretty='format:%ci [%h]' -n1 "$GITREMOTE/${branches[$index]}")"
			availableBranches[${branches[$index]}]=$(git log --pretty='format:%ci [%h]' -n1 "$GITREMOTE/${branches[$index]}")
			echo "${availableBranches[${branches[$index]}]}"
		fi
	done
	branchJson=$(
		for key in "${!availableBranches[@]}"; do
			echo "$key"
			echo "${availableBranches[${key}]}"
		done |
		jq -n -R 'reduce inputs as $key ({}; . + { ($key): (input|(tonumber? // .)) })'
	)
	echo "$branchJson"
	mosquitto_pub -p 1886 -t openWB/system/available_branches -r -m "$branchJson"

	# update current branch
	currentBranch=$(git branch --no-color --show-current)
	echo "currently selected branch: $currentBranch"
	mosquitto_pub -p 1886 -t openWB/system/current_branch -r -m "\"$currentBranch\""

	# update $selectedBranch commit
	currentMasterCommit=$(git log --pretty='format:%ci [%h]' -n1 "$GITREMOTE/$selectedBranch")
	echo "last commit to $selectedBranch branch: $currentMasterCommit"
	mosquitto_pub -p 1886 -t openWB/system/current_master_commit -r -m "\"$currentMasterCommit\""

	# list missing commits
	echo "changes:"
	IFS=$'\n'
	read -r -d '' -a commitDiff < <( git log --pretty='format:%ci [%h] - %s' "$selectedBranch..$GITREMOTE/$selectedBranch" )
	printf "* %s\n" "${commitDiff[@]}"
	commitDiffMessage=$(jq --compact-output --null-input '$ARGS.positional' --args -- "${commitDiff[@]}")
	mosquitto_pub -p 1886 -t openWB/system/current_missing_commits -r -m "$commitDiffMessage"
} >> "$LOGFILE" 2>&1
