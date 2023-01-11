#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOGFILE="${OPENWBBASEDIR}/data/log/update.log"
GITREMOTE="origin"

if [ "$(id -u -n)" != "openwb" ]; then
	echo "this script has to be run as user openwb"
	exit 1
fi

{
	echo "#### updating available version info ####"

	# update our local version
	currentCommit=$(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h]' -n1)
	echo "current commit: $currentCommit"
	mosquitto_pub -p 1886 -t "openWB/set/system/current_commit" -r -m "\"$currentCommit\""
	echo "$currentCommit" >"$OPENWBBASEDIR/web/lastcommit"

	# fetch data from git
	echo "fetching latest data from $GITREMOTE..."
	git -C "$OPENWBBASEDIR" fetch --verbose --prune --tags --prune-tags --force "$GITREMOTE" && echo "done"

	# update branches from $GITREMOTE
	echo "branches:"
	IFS=$'\n'
	read -r -d '' -a branches < <(git -C "$OPENWBBASEDIR" branch -r --list "$GITREMOTE/*")
	declare -A availableBranches
	declare -A tagsJson
	for index in "${!branches[@]}"; do
		if [[ ${branches[$index]} == *"HEAD"* ]]; then
			unset 'branches[$index]'
		else
			branches[index]="${branches[$index]//*\//}" # remove leading $GITREMOTE/ and whitespaces
			echo -n "checking commit for $GITREMOTE/${branches[$index]}..."
			availableBranches[${branches[$index]}]=$(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h]' -n1 "$GITREMOTE/${branches[$index]}")
			echo "${availableBranches[${branches[$index]}]}"
			echo "tags in branch:"
			read -r -d '' -a tags < <(git -C "$OPENWBBASEDIR" tag -n --format "%(refname:short): %(subject)" --merged "$GITREMOTE/${branches[$index]}")
			echo "${tags[*]}"
			tagsJson[${branches[$index]}]=$(
				for key in "${!tags[@]}"; do
					echo "${tags[${key}]//: */}"
					echo "${tags[${key}]}"
				done |
					jq -n -R -c 'reduce inputs as $key ({}; . + { ($key): (input) })'
			)
			echo "${branches[$index]}: ${tagsJson[${branches[$index]}]}"
		fi
	done
	branchJson=$(
		for key in "${!availableBranches[@]}"; do
			echo "$key"
			echo "${availableBranches[$key]}"
			echo "${tagsJson[$key]}"
		done |
			jq -n -R 'reduce inputs as $key ({}; . + { ($key): { commit: (input), tags: (input|fromjson) } })'
	)
	echo "$branchJson"
	mosquitto_pub -p 1886 -t "openWB/set/system/available_branches" -r -m "$branchJson"

	# update current branch
	currentBranch=$(git -C "$OPENWBBASEDIR" branch --no-color --show-current)
	echo "currently selected branch: $currentBranch"
	mosquitto_pub -p 1886 -t "openWB/set/system/current_branch" -r -m "\"$currentBranch\""

	# update $currentBranch commit
	currentBranchCommit=$(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h]' -n1 "$GITREMOTE/$currentBranch")
	echo "last commit to $currentBranch branch: $currentBranchCommit"
	mosquitto_pub -p 1886 -t "openWB/set/system/current_branch_commit" -r -m "\"$currentBranchCommit\""

	# list missing commits
	echo "changes:"
	IFS=$'\n'
	read -r -d '' -a commitDiff < <(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h] - %s' "$currentBranch..$GITREMOTE/$currentBranch")
	printf "* %s\n" "${commitDiff[@]}"
	commitDiffMessage=$(jq --compact-output --null-input '$ARGS.positional' --args -- "${commitDiff[@]}")
	mosquitto_pub -p 1886 -t "openWB/set/system/current_missing_commits" -r -m "$commitDiffMessage"
} >"$LOGFILE" 2>&1
