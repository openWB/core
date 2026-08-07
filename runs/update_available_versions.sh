#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOGFILE="${OPENWBBASEDIR}/ramdisk/versions.log"
GITREMOTE="origin"
YOURCHARGEPREFIX="yc/"
DRY_RUN=0

if [ "$(id -u -n)" != "openwb" ]; then
	echo "this script has to be run as user openwb"
	exit 1
fi

buildTagJson() {
	includeHead=$1
	shift
	local -a inputTags=("$@")

	{
		for tagLine in "${inputTags[@]}"; do
			if [[ -z $tagLine ]]; then
				continue
			fi
			echo "${tagLine%%: *}"
			echo "$tagLine"
		done
		if [[ $includeHead == "true" ]]; then
			echo "*HEAD*"
			echo "Aktuellster Stand"
		fi
	} |
		jq -n -R -c 'reduce inputs as $key ({}; . + { ($key): (input) })'
}

mqttPublish() {
	if [[ $DRY_RUN -eq 0 ]]; then
		mosquitto_pub -p 1886 -t "$1" -r -m "$2"
	fi
}

writeFile() {
	if [[ $DRY_RUN -eq 0 ]]; then
		echo "$2" >"$1"
	fi
}

runUpdate() {
	echo "#### updating available version info ####"

	# update our local version
	currentCommit=$(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h]' -n1)
	echo "current commit: $currentCommit"
	mqttPublish "openWB/system/current_commit" "\"$currentCommit\""
	writeFile "$OPENWBBASEDIR/web/lastcommit" "$currentCommit"

	# fetch data from git
	echo "fetching latest data from '$GITREMOTE'..."
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
			branches[index]="${branches[$index]//*$GITREMOTE\//}" # remove leading whitespace and $GITREMOTE/
			if [[ ${branches[$index]} == *"$YOURCHARGEPREFIX"* ]]; then
				echo "skipping branch '${branches[$index]}'"
				unset 'branches[$index]'
			else
				echo -n "checking commit for '$GITREMOTE/${branches[$index]}'..."
				availableBranches[${branches[$index]}]=$(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h]' -n1 "$GITREMOTE/${branches[$index]}")
				echo "${availableBranches[${branches[$index]}]}"
				if [[ ${branches[$index]} == "master" ]]; then
					echo "tags in branch:"
					read -r -d '' -a tags < <(git -C "$OPENWBBASEDIR" tag -n --format "%(refname:short): %(subject)" --merged "$GITREMOTE/${branches[$index]}" && printf '\0')
					echo "${tags[*]}"
					tagsJson[${branches[$index]}]=$(buildTagJson true "${tags[@]}")
				else
					tagsJson[${branches[$index]}]='{"*HEAD*":"Aktuellster Stand"}'
				fi
				echo "${branches[$index]}: ${tagsJson[${branches[$index]}]}"
			fi
		fi
	done

	# Build virtual Release/Beta entries from repository tags
	read -r -d '' -a allTags < <(git -C "$OPENWBBASEDIR" tag -n --format "%(refname:short): %(subject)" && printf '\0')
	declare -a releaseTags
	declare -a betaTags
	for tagLine in "${allTags[@]}"; do
		tagName="${tagLine%%: *}"
		if [[ $tagName =~ ^[2-9]+\.[0-9]+\.[0-9]+(-Patch\.[0-9]+)?$ ]]; then
			releaseTags+=("$tagLine")
			betaTags+=("$tagLine")
		
		elif [[ $tagName =~ ^[2-9]+\.[0-9]+\.[0-9]+(-Patch\.[0-9]+|-Beta\.[0-9]+|-[Rr][Cc]\.[0-9]+)?$ ]]; then
			betaTags+=("$tagLine")
		fi
	done

	tagsJson["Release"]=$(buildTagJson false "${releaseTags[@]}")
	tagsJson["Beta"]=$(buildTagJson false "${betaTags[@]}")

	latestReleaseTag=$(git -C "$OPENWBBASEDIR" tag --sort=-version:refname | grep -E -m1 '^[0-9]+\.[0-9]+\.[0-9]+(-Patch\.[0-9]+)?$')
	if [[ -n $latestReleaseTag ]]; then
		availableBranches["Release"]=$(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h]' -n1 "$latestReleaseTag")
	else
		availableBranches["Release"]=${availableBranches["master"]}
	fi

	latestBetaTag=$(git -C "$OPENWBBASEDIR" tag --sort=-version:refname | grep -E -m1 '^[0-9]+\.[0-9]+\.[0-9]+(-Patch\.[0-9]+|-Beta\.[0-9]+|-[Rr][Cc]\.[0-9]+)?$')
	if [[ -n $latestBetaTag ]]; then
		availableBranches["Beta"]=$(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h]' -n1 "$latestBetaTag")
	else
		availableBranches["Beta"]=${availableBranches["master"]}
	fi
	echo "Release: ${tagsJson["Release"]}"
	echo "Beta: ${tagsJson["Beta"]}"
	branchJson=$(
		for key in "${!availableBranches[@]}"; do
			echo "$key"
			echo "${availableBranches[$key]}"
			echo "${tagsJson[$key]}"
		done |
			jq -n -R 'reduce inputs as $key ({}; . + { ($key): { commit: (input), tags: (input|fromjson) } })'
	)
	echo "$branchJson"
	mqttPublish "openWB/system/available_branches" "$branchJson"

	# update current branch
	currentBranch=$(git -C "$OPENWBBASEDIR" branch --no-color --show-current)
	echo "currently selected branch: $currentBranch"
	mqttPublish "openWB/system/current_branch" "\"$currentBranch\""

	# update $currentBranch commit and list missing commits
	remoteCurrentBranch="$GITREMOTE/$currentBranch"
	echo "changes:"
	if [[ -n $currentBranch ]] && git -C "$OPENWBBASEDIR" show-ref --verify --quiet "refs/remotes/$remoteCurrentBranch"; then
		currentBranchCommit=$(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h]' -n1 "$remoteCurrentBranch")
		echo "last commit in '$currentBranch' branch: $currentBranchCommit"
		mqttPublish "openWB/system/current_branch_commit" "\"$currentBranchCommit\""
		IFS=$'\n'
		read -r -d '' -a commitDiff < <(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h] - %s' "$currentBranch..$remoteCurrentBranch" && printf '\0')
	else
		currentBranchCommit=$(git -C "$OPENWBBASEDIR" log --pretty='format:%ci [%h]' -n1)
		echo "no remote branch '$remoteCurrentBranch' found, using local HEAD commit"
		echo "last commit in '$currentBranch' branch: $currentBranchCommit"
		mqttPublish "openWB/system/current_branch_commit" "\"$currentBranchCommit\""
		commitDiff=()
	fi
	printf "* %s\n" "${commitDiff[@]}"
	commitDiffMessage=$(jq --compact-output --null-input '$ARGS.positional' --args -- "${commitDiff[@]}")
	mqttPublish "openWB/system/current_missing_commits" "$commitDiffMessage"
}

runUpdate >"$LOGFILE" 2>&1
