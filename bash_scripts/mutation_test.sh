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

	if [[ ${string} == *"t="* ]]; then
		array+=(${D}"/")
	fi
done

pit_dir=${newdir}pit_test/


cd ${pit_dir}
cp ${ATG}init_script_pitest.sh .
cnt=${#array[@]}
for ((i=0;i<cnt;i++)); do
    path_arg=${array[i]}org/
    bash init_script_pitest.sh  ${path_arg}
done


if [  -d "${pitest}report_pit" ]; then
	rm -r ${pitest}report_pit
fi
mkdir ${pit_dir}"report_pit"
mv ${pit_dir}FP_budget_time.csv ${pitest}report_pit/
for D in `find ${pitest}  -maxdepth 1  -type d  `
do
	if [[ ${D} == *"ALL"* ]]; then
		echo "python ${ATG}csv_PIT.py all ${D}/ ${pitest}report_pit/"
                python ${ATG}csv_PIT.py all ${D}/ ${pitest}report_pit/
	fi
done

echo "python ${ATG}csv_PIT.py fin ${pitest}report_pit/ ${pitest}report_pit/FP_budget_time.csv ${2}"
python ${ATG}csv_PIT.py fin ${pitest}report_pit/ ${pitest}report_pit/FP_budget_time.csv ${2}


echo ""

exit
