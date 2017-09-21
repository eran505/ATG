#!/usr/bin/env bash

#!/usr/bin/env bash

ATG=${1}
t=${2}
if [ -z "$ATG" ]; then
echo "missing path value ATG repo"
exit
fi

if [ -z "$t" ]; then
echo "missing path value time budget"
exit
fi

curdir=${PWD}
echo "curdir="${curdir}

time_dir=$(date +"%m_%d_%H_%M_%S")_t=${t}_

newdir=${curdir}/${time_dir}/
if [ ! -d "$newdir" ]; then
	mkdir "$newdir"
fi

cd "$newdir"
mkdir csv
cp -avr ${ATG}csv/Most_out_files.csv ./csv/
if [[ ${curdir} == *"ise"* ]]; then
	python ${ATG}budget_generation.py /home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/apache/commons/math3/distribution/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ ${newdir} exp 30 180 ${t}
else
	python  ${ATG}budget_generation.py  /home/eran/thesis/test_gen/poc/commons-math3-3.5-src/target/classes/org/apache/commons/math3/fraction/ evosuite-1.0.5.jar /home/eran/programs/EVOSUITE/jar/ ${newdir} exp 30 180 ${t}
fi
python ${ATG}pit_render_test.py ${newdir}
mkdir "pit_test"
for D in `find ${PWD}  -maxdepth 1  -type d  `
do

	string=${D}

	if [[ ${string} == *"exp"* ]]; then
		array+=(${D}"/")

	fi
done

pitest=${newdir}pit_test/

#cp ${ATG}init_script_pitest.sh ${pit_dir}

cd ${pitest}
cp ${ATG}init_script_pitest.sh .
cnt=${#array[@]}
for ((i=0;i<cnt;i++)); do
    path_arg=${array[i]}org/
    echo ${path_arg}
    bash init_script_pitest.sh  ${path_arg}
done

echo "making dir  ${pitest}report_pit "
if [  -d "${pitest}report_pit" ]; then
	rm -r ${pitest}report_pit
fi
mkdir "report_pit"

for D in `find ${pitest}  -maxdepth 1  -type d  `
do
	if [[ ${D} == *"ALL"* ]]; then
		echo "python ${ATG}csv_PIT.py all ${D}/ ${pitest}report_pit/"
                python ${ATG}csv_PIT.py all ${D}/ ${pitest}report_pit/
	fi
done
cp ${newdir}pit_test/FP_budget_time.csv ${pitest}report_pit/
echo "python ${ATG}csv_PIT.py fin ${pitest}report_pit/ ${pitest}report_pit/FP_budget_time.csv ${2}"
python ${ATG}csv_PIT.py fin ${pitest}report_pit/ ${pitest}report_pit/FP_budget_time.csv ${2}
echo ${PWD}
cd ".."
cd ".."


exit