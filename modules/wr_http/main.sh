#!/bin/bash


power=$(curl --connect-timeout 10 -s $1)

re='^-?[0-9]+$'

if ! [[ $power =~ $re ]] ; then
	   wattwr="0"
fi
if (( power > 3 )); then
	power=$(( power * -1 ))
fi
echo $power

if [[ $2 != "none" ]]; then
	echo $(curl --connect-timeout 5 -s $2)
fi


