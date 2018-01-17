#!/usr/bin/env bash


ATG="/home/ise/eran/repo/ATG/"

path_dir_root=${1}


father_dir=${path_dir_root}
for D in `find ${father_dir}  -maxdepth 1  -type d  `
do

    dir_name=${D##*/}
    if [[ $dir_name == *"_t="* ]]; then

            ##echo ${D}"/pit_test/"
	    string=${D}
	    array+=(${D}"/pit_test/")
	fi

done

cnt=${#array[@]}
echo "found: "${cnt}
for ((i=0;i<cnt;i++)); do
	path_dir=${array[i]}
	cp ${ATG}bash_scripts/mutation_test.sh ${path_dir}
	bash ${path_dir}/mutation_test.sh
done