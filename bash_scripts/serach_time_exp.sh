#!/usr/bin/env bash

newdir=$1
t=$2
ATG=$3

if [ -z "$ATG" ]; then
echo "missing path value ATG repo"
exit
fi

if [ ! -d "$newdir" ]; then
	mkdir "$newdir"
fi


if [ -z "$t" ]; then
echo "missing path value time budget"
exit
fi


python ${ATG}budget_generation.py /home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/apache/commons/math3/fraction/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ ${newdir} U 5 600 ${t}
