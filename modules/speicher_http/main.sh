#!/bin/bash

soc=$(curl --connect-timeout 10 -s $1 |sed 's/\..*$//')

re='^-?[0-9]+$'

echo $soc 
power=$(curl --connect-timeout 10 -s $2 )

echo $power 

if [[ speicherikwh != "none" ]]; then
echo $(curl --connect-timeout 10 -s $3)
fi

if [[ speicherekwh != "none" ]]; then
echo $(curl --connect-timeout 10 -s $3)
fi
