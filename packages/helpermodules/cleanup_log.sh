#!/bin/bash
echo "$(tail -25000 $1)" > $1
