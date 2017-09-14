#!/bin/bash


path_arg=${1}
#name_arg=${2}
if [ -z "$path_arg" ]; then
echo "missing path value "
exit
fi

#if [ -z "$name_arg" ]; then
#echo "missing path value name  "
#exit
#fi

suffix_name=${path_arg##*2017}
suffix_name=${suffix_name%/org/}

prefix_name=${path_arg%%_*}

string_dir="ALL_"${prefix_name}"_"${suffix_name}

cur_dir=${PWD}/
#string_dir="ALL_"${name_arg}

ATG="/home/ise/eran/repo/ATG/"
Mathjar="/home/ise/eran/repo/common_math/jars/commons-math3-3.5-src.tar.gz"

mkdir ${string_dir}
tar -xzvf ${Mathjar} -C ${cur_dir}${string_dir}
relative_path=${cur_dir}${string_dir}/commons-math3-3.5-src/
rm -r ${cur_dir}${string_dir}/commons-math3-3.5-src/src/test/java/org
rm ${relative_path}pom.xml
cp -avr ${path_arg} ${relative_path}src/test/java/
cp -avr ${ATG}pom.xml /home/ise/eran/exp_all/${string_dir}/commons-math3-3.5-src/
cp -avr ${ATG}pti_init.py ${relative_path}
cd ${relative_path}
mvn install
python pti_init.py

echo "done"
