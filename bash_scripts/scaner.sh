#!/usr/bin/env bash

print_something () {
path=$1
log_file=$2
for D in `find ${path}  -maxdepth 1  -type d  `
do

    dir_name=${D##*/}
    if [[ $dir_name == *"_t="* ]]; then

            ##echo ${D}"/pit_test/"
	    string=${D}
	    array+=(${D})

	fi

done
empty_ctr=0
full_ctr=0
cnt=${#array[@]}
for ((i=0;i<cnt;i++)); do
   	path_dir=${array[i]}
    if [ -z "$(ls -A ${path_dir})" ]; then
        empty_ctr=$((empty_ctr+1))
    else
        full_ctr=$((full_ctr+1))
fi
done

echo "all:${cnt}, full:${full_ctr}, empty:${empty_ctr}, PATH:${path_dir}" >> ${log_file}
echo "" >> ${log_file}

}


arg_package=${1}


father_dir=${arg_package}
for D in `find ${father_dir}  -maxdepth 1  -type d  `
do

    dir_name=${D##*/}
    if [[ $dir_name == *"_t="* ]]; then

            ##echo ${D}"/pit_test/"
	    string=${D}
	    array+=(${D}"/pit_test/")

	fi

done

str_data=$(date +'%m_%d__%H_%M_%S')
file_log="log_scan_${str_data}_.txt"
if [ ! -d "${father_dir}/logs" ]; then
  mkdir "${father_dir}/logs"
fi

touch "${father_dir}/logs/"${file_log}

file_log=${father_dir}"/logs/"${file_log}

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

pit_ctr=0


size=${#array_all[@]}
all_ctr=${size}
for ((i=0;i<size;i++)); do
	dir_i=${array_all[i]}
	if [ ! -d ${dir_i}"/target" ]; then
		echo "Need to compile the path no target dir ${dir_i} " >> ${file_log}
		echo "" >> ${file_log}
		continue
	fi
	# if pti_init is in the dir so del
	if [ ! -d ${dir_i}"/target/pit-reports" ]; then
		echo "No PIT outputs ${dir_i} " >> ${file_log}
		echo "" >> ${file_log}
		continue
	fi
	p_path=${dir_i}"/target/pit-reports"
	cd ${dir_i}"/target/pit-reports"
	pit_ctr=$((pit_ctr+1))
	num_dir=$(ls -1 | wc -l)
	echo " ${num_dir} : ${dir_i} " >> ${file_log}
	echo "" >> ${file_log}
	print_something ${p_path} ${file_log}

done

echo " results =  ${pit_ctr} : ${all_ctr} " >> ${file_log}
echo "" >> ${file_log}

echo "END !!"