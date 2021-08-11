#!/bin/bash
echo "$(tail -1000 $1)" > $1
