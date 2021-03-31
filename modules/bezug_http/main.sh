#!/bin/bash


power=$(curl --connect-timeout 10 -s $1)

re='^-?[0-9]+$'

if ! [[ $power =~ $re ]] ; then
	   wattbezug="0"
fi
echo $power

if [[ $2 != "none" ]]; then
	echo $(curl --connect-timeout 5 -s $2)
fi
if [[ $3 != "none" ]]; then
	echo $(curl --connect-timeout 5 -s $3)
fi
if [[ $4 != "none" ]]; then
	echo $(curl --connect-timeout 5 -s $4)
fi
if [[ $5 != "none" ]]; then
	echo $(curl --connect-timeout 5 -s $5)
fi
if [[ $6 != "none" ]]; then
	echo $(curl --connect-timeout 5 -s $6)
fi




