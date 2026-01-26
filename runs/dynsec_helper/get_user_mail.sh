#!/bin/bash
client_id="${1}"

# exit if no client_id provided
if [ -z "$client_id" ]; then
	exit 1
fi

# read contents of /var/lib/mosquitto/dynamic-security.json with sudo
# {
# 	"clients": [
# 		{
# 			"username": "admin",
# 			"textname": "admin@email.com",
# 			"roles": [],
# 			"password": "Yy",
# 		},
# 		{
# 			"username": "user1",
# 			"textname": "user@email.com",
# 			"roles": [],
# 			],
# 			"password": "Xx",
# 		}
# 	],
# }
# parse for client_id
mail=$(sudo cat /var/lib/mosquitto/dynamic-security.json | jq -e --arg CLIENT_ID "$client_id" '.clients[] | select(.username == $CLIENT_ID)')
# exit with error if client_id not found
if [ -z "$mail" ]; then
	exit 1
fi
# output info to stdout
echo "$mail" | jq -r '.textname'
