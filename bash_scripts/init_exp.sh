#!/usr/bin/env bash

ATG=${1}
t=${2}
m=${3}
if [ -z "$ATG" ]; then
echo "missing path value ATG repo"
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
python ${ATG}budget_generation.py /home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/apache/commons/math3/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ ${newdir} ${m} 1 300 ${t}
python ${ATG}pit_render_test.py ${newdir}

#if [[ $cur_dir == l*"ise"* ]]; then
#	python ${ATG}budget_generation.py /home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/apache/commons/math3/linear/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ ${newdir} ${m} 30 180 ${t}
#else
#	python  ${ATG}budget_generation.py  /home/eran/thesis/test_gen/poc/commons-math3-3.5-src/target/classes/org/apache/commons/math3/fraction/ evosuite-1.0.5.jar /home/eran/programs/EVOSUITE/jar/ ${newdir} ${m} 30 180 ${t}
#fi


echo "pwd="${newdir}


python ${ATG}pit_render_test.py ${newdir}
mkdir "pit_test"


cp ${newdir}FP_budget_time.csv ${newdir}pit_test/
for D in `find ${newdir}  -maxdepth 1  -type d  `
do

	string=${D}

	if [[ ${string} == *"it="* ]]; then
		array+=(${D}"/")
		echo ${D}"/"
	fi
done

pit_dir=${newdir}pit_test/
echo ${pit_dir}
cd ${pit_dir}
cp ${ATG}init_script_pitest.sh .
cnt=${#array[@]}
for ((i=0;i<cnt;i++)); do
    path_arg=${array[i]}org/
    bash init_script_pitest.sh  ${path_arg}
done



exit
