#!/usr/bin/env bash

root_dir=${PWD}
arg_package=${2}

project_name=${1}
if [ -z "${project_name}" ]; then
    echo "[Error] no project arg -- math or lang"
    exit
fi



ATG="/home/ise/eran/repo/ATG/"
python ${ATG}pit_render_test.py ${root_dir}
Mathjar="/home/ise/eran/repo/common_math/jars/commons-math3-3.5-src.tar.gz"
Langjar="/home/ise/eran/repo/lang/jars/commons-lang3-3.5-src.tar.gz"

father_dir=${PWD}
for D in `find ${PWD}  -maxdepth 1  -type d  `
do

    dir_name=${D##*/}
    if [[ $dir_name == *"_t="* ]]; then
	    string=${D}
	    array+=(${D})
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
echo "_____${cnt}________"
for ((i=0;i<cnt;i++)); do
	father_dir=${array[i]}
	array_sub=()
	echo "f dir ="${father_dir}
	if [ ! -d "${father_dir}/pit_test" ]; then
		mkdir "${father_dir}/pit_test"
	fi
	for D in `find ${father_dir}  -maxdepth 1  -type d  `
	do
		currnet_dir=${D##*/}
		echo "currnet_dir= "${currnet_dir}
		if [[ $currnet_dir == *"exp"* ]]; then
			echo ${D}
	    	string=${D}
	    	array_sub+=(${D})
		fi
	done
	#suffix_name=${path_dir##*/}
	#echo "path_dir"$path_dir
	#echo "path_dir="$suffix_name
	inner_loop=${#array_sub[@]}
	for ((k=0;k<inner_loop;k++)); do
		now_dir=${array_sub[k]}
		echo "now="$now_dir
		suffix_name=${now_dir##*/}
		echo "suffix_name="$suffix_name
		mod=$(echo $suffix_name| cut -d'_' -f 1)
		echo "mod="$mod
		time=$(echo $suffix_name| cut -d'_' -f 8)
		echo "time="$time
		it=$(echo $suffix_name| cut -d'_' -f 9)
		echo "it="$it
		string_dir="ALL_"${mod}"_${time}_"${it}"_"
		echo $string_dir
		cut_dir=${father_dir}/"pit_test"/${string_dir}
		if [ -d "${cut_dir}" ]; then
			rm -r ${cut_dir}
		fi
		mkdir $cut_dir

		if [[ ${project_name} == "math" ]]; then

		    tar -xzf ${Mathjar} -C $cut_dir
		    relative_path=${cut_dir}/commons-math3-3.5-src/
		    rm -r ${cut_dir}/commons-math3-3.5-src/src/test/java/org
		    rm ${cut_dir}/commons-math3-3.5-src/pom.xml
		    cp -ar ${ATG}"pom/"${project_name}"/"pom.xml ${relative_path}

		fi

		if [[ ${project_name} == "lang" ]]; then

		    tar -xzf ${Langjar} -C $cut_dir
		    relative_path=${cut_dir}/commons-lang3-3.5-src/
		    rm -r ${cut_dir}/commons-lang3-3.5-src/src/test/java/org
		    rm ${cut_dir}/commons-lang3-3.5-src/pom.xml
       		cp -ar ${ATG}"pom/"${project_name}"/"pom.xml ${relative_path}
		fi

		cp -ar ${now_dir}/org/ ${relative_path}src/test/java/
		cp -ar ${ATG}pti_init.py ${relative_path}
		cd ${relative_path}
		mvn -fn install
	done

done

echo ''
echo "---- Done building the environments-----"
echo ''
#############################python##################################

python ${ATG}fail_cleaner.py ${root_dir}
cd ${root_dir}
echo "----done with the fixing----"

############################fixer##############################


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
            res=$(find ${Dir} -mindepth 1 -maxdepth 1 -type d  \(  -iname "common*" \))
            if [[ ! -z "${res// }" ]]; then
                array_all+=(${res}"/")
            else
                echo "No commons-math3-3.5-src in ${Dir}" >> ${file_log}
			    echo "" >> ${file_log}
			    continue
            fi

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

	#crate dir for pit logs
	if [ ! -d ${dir_i}"/target/log_pit" ]; then
		mkdir
	fi

	#start the pit program
	echo "starting PIT on ${dir_i}"
	if [ -z "$arg_package" ]; then
		cd ${dir_i}
		python ${dir_i}"pti_init.py"

	else
		cd ${dir_i}
		python ${dir_i}"pti_init.py" ${arg_package}
	fi

done

echo "END !!"