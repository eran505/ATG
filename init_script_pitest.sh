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
echo "========>"${1}
suffix_name=${path_arg##*2017}  #TODO: change the suffix to "##*201"
suffix_name=${suffix_name%/org/}
prefix_name="U"

if [[ $path_arg == *"FP"* ]]; then
  prefix_name="FP"
fi

string_dir="ALL_"${prefix_name}"_"${suffix_name}
echo ${string_dir}

cur_dir=${PWD}/
echo "pwd = "${cur_dir}
#string_dir="ALL_"${name_arg}

ATG="/home/eran/thesis/repo/ATG/"
Mathjar="/home/eran/thesis/zips/commons-math3-3.5-src.tar.gz"

if [[ $cur_dir == *"ise"* ]]; then
    ATG="/home/ise/eran/repo/ATG/"
    Mathjar="/home/ise/eran/repo/common_math/jars/commons-math3-3.5-src.tar.gz"
fi



mkdir ${cur_dir}${string_dir}
tar -xzf ${Mathjar} -C ${cur_dir}${string_dir}
relative_path=${cur_dir}${string_dir}/commons-math3-3.5-src/
rm -r ${cur_dir}${string_dir}/commons-math3-3.5-src/src/test/java/org
rm ${relative_path}pom.xml
cp -ar ${path_arg} ${relative_path}src/test/java/
cp -ar ${ATG}pom.xml ${relative_path}
cp -ar ${ATG}pti_init.py ${relative_path}
cd ${relative_path}
mvn -fn install
mkdir target/log_pit/
python pti_init.py

echo "done"
