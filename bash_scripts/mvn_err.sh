#!/usr/bin/env bash



father_dir=${PWD}
for D in `find ${PWD}  -maxdepth 1  -type d  `
do

    if echo "${D}" | grep -q "0"
    then


	    array+=(${D}"/")
	fi

done


cnt=${#array[@]}
for ((i=0;i<cnt;i++)); do
    path_dir=${array[i]}
    pitest=${path_dir}pit_test/
    if [ ! -d "$pitest" ]; then
    	mkdir ${path_dir}pit_test/
    fi
    cd "${pitest}"
	echo "${pitest}"
    for D in `find ${pitest}  -maxdepth 1  -type d  `
	do
        if echo "${D}" | grep -q "ALL"
        then

		cd "${D}"/commons-math3-3.5-src/
		mvn test
	fi
	done
done