#!/usr/bin/env bash

p_path=${1}

if [ -z "$p_path" ]; then
echo "missing path value p_path"
exit
fi
cd ${p_path}
ant compile
echo 'Done !'