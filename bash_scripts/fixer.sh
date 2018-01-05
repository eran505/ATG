#!/usr/bin/env bash

ATG="/home/ise/eran/repo/ATG/"

arg_package=${1}


father_dir=${PWD}
for D in `find ${PWD}  -maxdepth 1  -type d  `
do

    dir_name=${D##*/}
    if [[ $dir_name == *"_t="* ]]; then

            ##echo ${D}"/pit_test/"
	    string=${D}
	    array+=(${D}"/pit_test/")
	fi

done

str_data=$(date +'%m_%d__%H_%M_%S')
file_log="log_fix_${str_data}_.txt"
if [ ! -d "${PWD}/logs" ]; then
  mkdir "${PWD}/logs"
fi

touch "${PWD}/logs/"${file_log}

file_log=${PWD}"/logs/"${file_log}

cnt=${#array[@]}
for ((i=0;i<cnt;i++)); do
	path_dir=${array[i]}
	if [ ! -d "${path_dir}" ]; then
  		echo "No pit_test in ${path_dir}" >> ${file_log}
		echo "" >> ${file_log}
		continue
	fi

	for Dir in `find ${path_dir}  -maxdepth 1  -type d  `
		do
    		dir_n=${Dir##*/}
    		if [[ $dir_n == *"ALL"* ]]; then

			echo ${Dir}"/"
			if [ ! -d ${Dir}"/commons-math3-3.5-src" ]; then
		  		echo "No commons-math3-3.5-src in ${Dir}" >> ${file_log}
				echo "" >> ${file_log}
				continue
			fi
			array_all+=(${Dir}"/commons-math3-3.5-src/")
		fi

	done
done

# go over all the ALL_U dir

size=${#array_all[@]}
for ((i=0;i<size;i++)); do
	dir_i=${array_all[i]}
	if [ ! -d ${dir_i}"/target" ]; then
		echo "Need to compile the path no target dir ${dir_i} \n" >> ${file_log}
		echo "" >> ${file_log}
		continue
	fi
	# if pti_init is in the dir so del
	file_pit=${dir_i}"pti_init.py"
	if [ -f "$file_pit" ]
	then
		rm "$file_pit"
	fi
	#copy the pti_init for ATG
	cp ${ATG}"pti_init.py" ${dir_i}
	if [ -z "$arg_package" ]; then
		python ${dir_i}"pti_init.py"

	else
		python ${dir_i}"pti_init.py" ${arg_package}
	fi


done

echo "END !!"