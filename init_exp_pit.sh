#!/usr/bin/env bash

ATG=${1}
t=${2}
if [ -z "$ATG" ]; then
echo "missing path value ATG repo"
exit
fi

if [ -z "$t" ]; then
echo "missing path value ATG repo"
exit
fi
echo ""
curdir=${PWD}
echo "curdir="${curdir}

time_dir=$(date +"%m_%d_%H_%M_%S")

newdir=${curdir}/${time_dir}/
if [ ! -d "$newdir" ]; then
	mkdir "$newdir"
fi

cd "$newdir"
mkdir csv
cp -avr ${ATG}csv/Most_out_files.csv ./csv/
#python  ${ATG}budget_generation.py  /home/eran/thesis/test_gen/poc/commons-math3-3.5-src/target/classes/org/apache/commons/math3/distribution/ evosuite-1.0.5.jar /home/eran/programs/EVOSUITE/jar/ ${newdir} exp ${t}
python ${ATG}budget_generation.py /home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/apache/commons/math3/distribution/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ ${newdir} exp ${t}
python ${ATG}pit_render_test.py ${newdir}
mkdir "pit"
for D in `find ${PWD}  -maxdepth 1  -type d  `
do

	string=${D}

	if [[ ${string} == *"exp"* ]]; then
		array+=(${D}"/")

	fi
done

pit_dir=${newdir}pit/

#cp ${ATG}init_script_pitest.sh ${pit_dir}

cd ${pit_dir}
cp ${ATG}init_script_pitest.sh .
cnt=${#array[@]}
for ((i=0;i<cnt;i++)); do
    path_arg=${array[i]}org/
    echo ${path_arg}
    #screen -d -m -t ${RANDOM} sh init_script_pitest.sh  ${path_arg}
    bash init_script_pitest.sh  ${path_arg}
done




exit