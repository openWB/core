#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

while IFS= read -r -d '' d; do
	entries=("$d/"*)
	if ((${#entries[@]} == 1)); then
		# echo "folder: " "${entries[0]}"
		if [[ "${entries[0]}" =~ /__pycache__$ ]]; then
			echo "$d: containing only cache without sources -> will be removed"
			rm -fr "$d"
		fi
	fi
done < <(find "$OPENWBBASEDIR" -type d ! -name "__pycache__" -print0)
echo "python cache cleanup done"
