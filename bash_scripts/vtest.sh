#!/usr/bin/env bash

path=${1}
if [ -z "$path" ]; then
echo "full"
cd ..
path csv_handler.py
exit
fi


python csv_handler.py