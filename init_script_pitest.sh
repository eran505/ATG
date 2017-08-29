#!/bin/bash


path_arg=${1}
if [ -z "$path_arg" ]; then
echo "missing path value "
exit
fi

string_dir="V_"${RANDOM}

mkdir ${string_dir}
tar -xzvf /home/ise/eran/repo/common_math/jars/commons-math3-3.5-src.tar.gz -C /home/ise/eran/exp/${string_dir}
relative_path=/home/ise/eran/exp/${string_dir}/commons-math3-3.5-src
rm -r /home/ise/eran/exp/${string_dir}/commons-math3-3.5-src/src/test/java/org
rm /home/ise/eran/exp/${string_dir}/commons-math3-3.5-src/pom.xml
cp -avr ${path_arg} ${relative_path}/src/test/java/
cp -avr /home/ise/eran/repo/ATG/pom.xml /home/ise/eran/exp/${string_dir}/commons-math3-3.5-src/
cd ${relative_path}
mvn install
mvn org.pitest:pitest-maven:mutationCoverage
DIRECTORY_path=/home/ise/eran/exp/output/${string_dir}
if [ ! -d "${DIRECTORY_path}" ]; then
	mkdir  ${DIRECTORY_path}
fi

mv ${relative_path}/target/pit-reports/* "$DIRECTORY_path"

echo "done"
