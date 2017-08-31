#!/bin/bash


path_arg=${1}
name_arg=${2}
if [ -z "$path_arg" ]; then
echo "missing path value "
exit
fi

if [ -z "$name_arg" ]; then
echo "missing path value name  "
exit
fi

string_dir="ALL_"${name_arg}

mkdir ${string_dir}
tar -xzvf /home/ise/eran/repo/common_math/jars/commons-math3-3.5-src.tar.gz -C /home/ise/eran/exp_all/${string_dir}
relative_path=/home/ise/eran/exp_all/${string_dir}/commons-math3-3.5-src
rm -r /home/ise/eran/exp_all/${string_dir}/commons-math3-3.5-src/src/test/java/org
rm /home/ise/eran/exp_all/${string_dir}/commons-math3-3.5-src/pom.xml
cp -avr ${path_arg} ${relative_path}/src/test/java/
cp -avr /home/ise/eran/repo/ATG/pom.xml /home/ise/eran/exp_all/${string_dir}/commons-math3-3.5-src/
cp -avr /home/ise/eran/repo/ATG/pti_init.py /home/ise/eran/exp_all/${string_dir}/commons-math3-3.5-src/
cd ${relative_path}
mvn install
python pti_init.py


echo "done"
