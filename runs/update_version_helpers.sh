#!/bin/bash

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
