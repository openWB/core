#!/bin/bash

fetchVersionRefs() {
	local baseDir=$1
	local remote=$2
	git -C "$baseDir" fetch --verbose --prune --tags --prune-tags --force "$remote"
}

remoteBranchExists() {
	local baseDir=$1
	local remote=$2
	local branch=$3
	git -C "$baseDir" show-ref --verify --quiet "refs/remotes/$remote/$branch"
}

setLogicalUpdateBranch() {
	local baseDir=$1
	local train=$2
	case "$train" in
	"Release"|"Beta")
		git -C "$baseDir" config --local openwb.updateBranch "$train"
		;;
	"")
		local configStatus=0
		git -C "$baseDir" config --local --unset-all openwb.updateBranch || configStatus=$?
		if [[ $configStatus -eq 5 ]]; then
			return 0
		fi
		return "$configStatus"
		;;
	*)
		return 1
		;;
	esac
}

validateRestoreGitMetadata() {
	local branch=$1
	local train=$2
	case "$train" in
	"Release"|"Beta"|"") ;;
	*) return 1 ;;
	esac
	if [[ -n $branch && -n $train ]]; then
		return 2
	fi
	return 0
}

getTrainTagPattern() {
	local branch=$1
	case "$branch" in
	"Release")
		echo '^([2-9]|[1-9][0-9]+)\.[0-9]+\.[0-9]+(-Patch\.[0-9]+)?$'
		;;
	"Beta")
		echo '^([2-9]|[1-9][0-9]+)\.[0-9]+\.[0-9]+(-Patch\.[0-9]+|-Beta\.[0-9]+|-[Rr][Cc]\.[0-9]+)?$'
		;;
	*)
		return 1
		;;
	esac
}

tagMatchesTrain() {
	local branch=$1
	local tag=$2
	local pattern
	pattern=$(getTrainTagPattern "$branch") || return 1
	[[ $tag =~ $pattern ]]
}

latestTagByPattern() {
	local pattern=$1
	git -C "$OPENWB_BASE_DIR" tag --sort=-version:refname | grep -E -m1 "$pattern"
}

extractBaseVersion() {
	local tag=$1
	echo "$tag" | sed -E 's/-Patch\.[0-9]+$//; s/-Beta\.[0-9]+$//; s/-[Rr][Cc]\.[0-9]+$//'
}

highestBaseByPattern() {
	local pattern=$1
	local tag
	tag=$(latestTagByPattern "$pattern") || return 1
	extractBaseVersion "$tag"
}

selectLatestTrainTag() {
	local branch=$1
	local baseVersion
	local basePattern
	local trainPattern
	trainPattern=$(getTrainTagPattern "$branch") || return 1
	baseVersion=$(highestBaseByPattern "$trainPattern") || return 1
	basePattern=${baseVersion//./\\.}

	case "$branch" in
	"Release")
		latestTagByPattern "^${basePattern}-Patch\\.[0-9]+$" ||
			latestTagByPattern "^${basePattern}$"
		;;
	"Beta")
		latestTagByPattern "^${basePattern}-Patch\\.[0-9]+$" ||
			latestTagByPattern "^${basePattern}$" ||
			latestTagByPattern "^${basePattern}-[Rr][Cc]\\.[0-9]+$" ||
			latestTagByPattern "^${basePattern}-Beta\\.[0-9]+$"
		;;
	*)
		return 1
		;;
	esac
}
