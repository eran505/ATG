#!/usr/bin/env bash





root_dir=${PWD}
arg_package=${1}

ATG="/home/ise/eran/repo/ATG/"
Mathjar="/home/ise/eran/repo/common_math/jars/commons-math3-3.5-src.tar.gz"
father_dir=${PWD}
${ATG}python pit_render_test.py ${PWD}
for D in `find ${PWD}  -maxdepth 1  -type d  `
do

    dir_name=${D##*/}
    if [[ $dir_name == *"_t="* ]]; then

            ##echo ${D}"/pit_test/"
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
for ((i=0;i<cnt;i++)); do
	array_sub=()
	father_dir=${array[i]}
	if [ ! -d "${father_dir}/pit_test" ]; then
		mkdir "${father_dir}/pit_test"
	fi
	for D in `find ${father_dir}  -maxdepth 1  -type d  `
	do
		currnet_dir=${D##*/}
		if [[ $currnet_dir == *"exp"* ]]; then
	    	string=${D}
	    	array_sub+=(${D})
		fi
	done
	#suffix_name=${path_dir##*/}
	#echo "path_dir"$path_dir
	#echo "path_dir="$suffix_name
	cnt=${#array_sub[@]}
	for ((k=0;k<cnt;k++)); do
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
		mkdir $cut_dir
		tar -xzf ${Mathjar} -C $cut_dir
		relative_path=${cut_dir}/commons-math3-3.5-src/
		rm -r ${cut_dir}/commons-math3-3.5-src/src/test/java/org
		rm ${cut_dir}/commons-math3-3.5-src/pom.xml
		cp -ar ${now_dir}/org/ ${relative_path}src/test/java/
		cp -ar ${ATG}pom.xml ${relative_path}
		cp -ar ${ATG}pti_init.py ${relative_path}
		cd ${relative_path}
		mvn -fn install

	done

done

##########################3

python ${ATG}pit_render_test.py ${root_dir}
python ${ATG}fail_cleaner.py ${root_dir}
cd ${root_dir}
bash fixer.sh
python ${ATG}pit_dir_fix.py ${root_dir}
python ${ATG}csv_PIT.py arg ${root_dir}
echo "END !!"