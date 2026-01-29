#!/bin/bash
client_id="${1}"

# exit if no client_id provided
if [ -z "$client_id" ]; then
	exit 1
fi

# read contents of /var/lib/mosquitto/dynamic-security.json with sudo and parse with jq
# {
# 	"clients": [
# 		{
# 			"username": "admin",
# 			"textname": "admin@email.com",
# 			...
# 		},
# 		{
# 			"username": "user1",
# 			"textname": "user@email.com",
# 			...
# 		},
# 		...
# 	],
# 	...
# }

client=$(sudo cat /var/lib/mosquitto/dynamic-security.json | jq -e --arg CLIENT_ID "$client_id" '.clients[] | select(.username == $CLIENT_ID)')
if [ -z "$client" ]; then
	# exit with error if client_id not found
	exit 1
fi

mail=$(echo "$client" | jq -e '.textname')
if [ -z "$mail" ]; then
	# exit with error if textname not found
	exit 1
fi

# output info to stdout without quotes
echo "$mail" | tr -d '"'
