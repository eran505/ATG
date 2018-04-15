#!/usr/bin/env bash

ATG=${1}
t=${2}
m=${3}
project=${4}
main_dir=${PWD}


if [ -z "$ATG" ]; then
echo "missing path value ATG repo"
exit
fi


if [ -z "$project" ]; then
echo "missing path value time budget"
exit
fi

if [ -z "$t" ]; then
echo "missing path value time budget"
exit
fi

if [ -z "$m" ]; then
echo "missing path value time budget"
exit
fi


curdir=${PWD}
echo "curdir="${curdir}

time_dir=$(date +"%m_%d_%H_%M_%S")_t=${t}_

newdir=${curdir}/${time_dir}/
if [ ! -d "$newdir" ]; then
	mkdir "$newdir"
fi

cd "$newdir"
mkdir csv
cp -avr ${ATG}csv/Most_out_files.csv ./csv/

if [[ $project == *"math"* ]]; then
python ${ATG}budget_generation.py /home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/apache/commons/math3/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ ${newdir} ${m} 1 240 ${t}
fi

if [[ $project == *"lang"* ]]; then
python ${ATG}budget_generation.py /home/ise/eran/repo/lang/commons-lang3-3.5-src/target/classes/org/apache/commons/lang3/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ ${newdir} ${m} 1 240 ${t} 2 U
fi

python ${ATG}pit_render_test.py ${newdir}

cd ${main_dir}

bash fix_newer.sh


exit
