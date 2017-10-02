#!/usr/bin/env bash

ATG=${1}

if [ -z "$ATG" ]; then
echo "missing path value ATG repo"
exit
fi
father_dir=${PWD}
for D in `find ${PWD}  -maxdepth 1  -type d  `
do

	string=${D}
	array+=(${D}"/")

done



cnt=${#array[@]}
for ((i=0;i<cnt;i++)); do
    path_dir=${array[i]}
    #echo ${path_dir}
    pitest=${path_dir}pit_test/
    if [ ! -d "$pitest" ]; then
    	mkdir ${path_dir}pit_test/
	#echo "dir made"
    fi
   #mv ${path_dir}FP_budget_time.csv ${path_dir}pit_test/
   #cp ${ATG}init_script_pitest.sh ${path_dir}pit_test/
    #echo " -------------------------------------------------- "
    #echo "cding into ${pitest} dir.. the  cur dir = ${PWD}/ "
    cd "${pitest}"
    str_time="null"
    for D in `find ${path_dir}  -maxdepth 1  -type d  `
	do
		string=${D}
		if [[ ${string} == *"FP"* ]]; then
			#bash ${path_dir}pit_test/init_script_pitest.sh ${D}/org/
			#echo "piting..."
            str_time=${string}

		fi
	done
    #echo "making dir  ${pitest}report_pit "
        if [  -d "${pitest}report_pit" ]; then
     		rm -r ${pitest}report_pit
         fi
    mkdir "report_pit"
    for D in `find ${pitest}  -maxdepth 1  -type d  `
	do
		if [[ ${D} == *"ALL"* ]]; then
                   echo "" >> ${father_dir}/info.txt
                   echo "python ${ATG}csv_PIT.py all ${D}/ ${pitest}report_pit/" >> ${father_dir}/info.txt
                   echo "">> ${father_dir}/info.txt
		   #echo ".....sleeping_10_sec.."
		   #sleep 10
                  # python ${ATG}csv_PIT.py all ${D}/ ${pitest}report_pit/
		fi
        done
    cp ${path_dir}FP_budget_time.csv ${pitest}report_pit/
    if [[  ${str_time} == *"exp"* ]]; then
    	str_time=${str_time##*_t=}
    	str_time=${str_time%%_*}
    	echo"">> ${father_dir}/info.txt
    	echo "python ${ATG}csv_PIT.py fin ${pitest}report_pit/ ${pitest}report_pit/FP_budget_time.csv ${str_time}">> ${father_dir}/info.txt
    	echo "">> ${father_dir}/info.txt
    	#python ${ATG}csv_PIT.py fin ${pitest}report_pit/ ${pitest}report_pit/FP_budget_time.csv ${str_time}
    fi
    #echo ${PWD}
    cd ".."
    cd ".."

done

