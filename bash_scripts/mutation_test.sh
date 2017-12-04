#!/usr/bin/env bash

ATG=${1}

newdir=${PWD}/

if [ -z "$ATG" ]; then
echo "missing path value ATG repo"
exit
fi

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
