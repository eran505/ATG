#!/bin/bash 

if [ -z "$1" ]; then
echo "not time insert"
exit
fi 

dir=${1}_sec

python evo_call.py /home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ /home/ise/eran/out/${dir}/ ${1}
