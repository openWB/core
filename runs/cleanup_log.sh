#!/bin/bash
echo "$(tail -10000 $1)" > $1
