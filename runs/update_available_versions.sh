#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOG_FILE="${OPENWB_BASE_DIR}/ramdisk/versions.log"
GIT_REMOTE="origin"
YOUR_CHARGE_PREFIX="yc/"
DRY_RUN=0 # set to 1 for testing without writing to files or publishing to MQTT

source "$OPENWB_BASE_DIR/runs/update_version_helpers.sh"

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
	currentCommit=$(git -C "$OPENWB_BASE_DIR" log --pretty='format:%ci [%h]' -n1)
	echo "current commit: $currentCommit"
	mqttPublish "openWB/system/current_commit" "\"$currentCommit\""
	writeFile "$OPENWB_BASE_DIR/web/lastcommit" "$currentCommit"

	# fetch data from git
	echo "fetching latest data from '$GIT_REMOTE'..."
	git -C "$OPENWB_BASE_DIR" fetch --verbose --prune --tags --prune-tags --force "$GIT_REMOTE" && echo "done"

	# update branches from $GIT_REMOTE
	echo "branches:"
	IFS=$'\n'
	read -r -d '' -a branches < <(git -C "$OPENWB_BASE_DIR" branch -r --list "$GIT_REMOTE/*")
	declare -A availableBranches
	declare -A tagsJson
	for index in "${!branches[@]}"; do
		if [[ ${branches[$index]} == *"HEAD"* ]]; then
			unset 'branches[$index]'
		else
			branches[index]="${branches[$index]//*$GIT_REMOTE\//}" # remove leading whitespace and $GIT_REMOTE/
			if [[ ${branches[$index]} == *"$YOUR_CHARGE_PREFIX"* ]]; then
				echo "skipping branch '${branches[$index]}'"
				unset 'branches[$index]'
			else
				echo -n "checking commit for '$GIT_REMOTE/${branches[$index]}'..."
				availableBranches[${branches[$index]}]=$(git -C "$OPENWB_BASE_DIR" log --pretty='format:%ci [%h]' -n1 "$GIT_REMOTE/${branches[$index]}")
				echo "${availableBranches[${branches[$index]}]}"
				if [[ ${branches[$index]} == "master" ]]; then
					echo "tags in branch:"
					read -r -d '' -a tags < <(git -C "$OPENWB_BASE_DIR" tag -n --format "%(refname:short): %(subject)" --merged "$GIT_REMOTE/${branches[$index]}" && printf '\0')
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
	read -r -d '' -a allTags < <(git -C "$OPENWB_BASE_DIR" tag -n --format "%(refname:short): %(subject)" && printf '\0')
	declare -a releaseTags
	declare -a betaTags
	for tagLine in "${allTags[@]}"; do
		tagName="${tagLine%%: *}"
		if [[ $tagName =~ ^([2-9]|[1-9][0-9]+)\.[0-9]+\.[0-9]+(-Patch\.[0-9]+)?$ ]]; then
			releaseTags+=("$tagLine")
			betaTags+=("$tagLine")
		
		elif [[ $tagName =~ ^([2-9]|[1-9][0-9]+)\.[0-9]+\.[0-9]+(-Patch\.[0-9]+|-Beta\.[0-9]+|-[Rr][Cc]\.[0-9]+)?$ ]]; then
			betaTags+=("$tagLine")
		fi
	done

	tagsJson["Release"]=$(buildTagJson false "${releaseTags[@]}")
	tagsJson["Beta"]=$(buildTagJson false "${betaTags[@]}")

	latestReleaseTag=$(selectLatestTrainTag "Release")
	if [[ -n $latestReleaseTag ]]; then
		availableBranches["Release"]=$(git -C "$OPENWB_BASE_DIR" log --pretty='format:%ci [%h]' -n1 "$latestReleaseTag")
	else
		availableBranches["Release"]=${availableBranches["master"]}
	fi

	latestBetaTag=$(selectLatestTrainTag "Beta")
	if [[ -n $latestBetaTag ]]; then
		availableBranches["Beta"]=$(git -C "$OPENWB_BASE_DIR" log --pretty='format:%ci [%h]' -n1 "$latestBetaTag")
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
	currentBranch=$(git -C "$OPENWB_BASE_DIR" branch --no-color --show-current)
	if [[ -z $currentBranch ]]; then
		logicalBranch=$(git -C "$OPENWB_BASE_DIR" config --local --get openwb.updateBranch)
		if [[ -z $logicalBranch ]]; then
			local -a headTags
			local train headTag
			read -r -d '' -a headTags < <(git -C "$OPENWB_BASE_DIR" tag --points-at HEAD && printf '\0')
			for train in Release Beta; do
				for headTag in "${headTags[@]}"; do
					if jq -e --arg tag "$headTag" 'has($tag)' <<<"${tagsJson[$train]}" >/dev/null; then
						logicalBranch="$train"
						break 2
					fi
				done
			done
			if [[ -n $logicalBranch ]]; then
				echo "inferred update branch '$logicalBranch' from tags at HEAD"
				if [[ $DRY_RUN -eq 0 ]]; then
					git -C "$OPENWB_BASE_DIR" config --local openwb.updateBranch "$logicalBranch" || return 1
				else
					echo "DRY RUN: would persist update branch '$logicalBranch'"
				fi
			fi
		fi
		if [[ $logicalBranch == "Release" || $logicalBranch == "Beta" ]]; then
			currentBranch="$logicalBranch"
		fi
	fi
	echo "currently selected branch: $currentBranch"
	mqttPublish "openWB/system/current_branch" "\"$currentBranch\""

	# update $currentBranch commit and list missing commits
	remoteCurrentBranch="$GIT_REMOTE/$currentBranch"
	echo "changes:"
	latestTrainTag=""
	case "$currentBranch" in
	"Release") latestTrainTag="$latestReleaseTag" ;;
	"Beta") latestTrainTag="$latestBetaTag" ;;
	esac
	if [[ -n $latestTrainTag ]]; then
		currentBranchCommit=$(git -C "$OPENWB_BASE_DIR" log --pretty='format:%ci [%h]' -n1 "refs/tags/$latestTrainTag")
		echo "last commit in '$currentBranch' train: $currentBranchCommit"
		mqttPublish "openWB/system/current_branch_commit" "\"$currentBranchCommit\""
		IFS=$'\n'
		read -r -d '' -a commitDiff < <(git -C "$OPENWB_BASE_DIR" log --pretty='format:%ci [%h] - %s' "HEAD..refs/tags/$latestTrainTag" && printf '\0')
	elif [[ -n $currentBranch ]] && git -C "$OPENWB_BASE_DIR" show-ref --verify --quiet "refs/remotes/$remoteCurrentBranch"; then
		currentBranchCommit=$(git -C "$OPENWB_BASE_DIR" log --pretty='format:%ci [%h]' -n1 "$remoteCurrentBranch")
		echo "last commit in '$currentBranch' branch: $currentBranchCommit"
		mqttPublish "openWB/system/current_branch_commit" "\"$currentBranchCommit\""
		IFS=$'\n'
		read -r -d '' -a commitDiff < <(git -C "$OPENWB_BASE_DIR" log --pretty='format:%ci [%h] - %s' "$currentBranch..$remoteCurrentBranch" && printf '\0')
	else
		currentBranchCommit=$(git -C "$OPENWB_BASE_DIR" log --pretty='format:%ci [%h]' -n1)
		echo "no remote branch '$remoteCurrentBranch' found, using local HEAD commit"
		echo "last commit in '$currentBranch' branch: $currentBranchCommit"
		mqttPublish "openWB/system/current_branch_commit" "\"$currentBranchCommit\""
		commitDiff=()
	fi
	printf "* %s\n" "${commitDiff[@]}"
	commitDiffMessage=$(jq --compact-output --null-input '$ARGS.positional' --args -- "${commitDiff[@]}")
	mqttPublish "openWB/system/current_missing_commits" "$commitDiffMessage"
}

runUpdate >"$LOG_FILE" 2>&1
