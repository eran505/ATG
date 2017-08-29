#!/bin/bash


path_arg=${1}

if [ -z "$path_arg" ]; then
echo "missing path value "
exit
fi
now_time=$(date +%T)
string_dir="$now_time" | tr : _
string_dir=${string_dir}"_V"${RANDOM}
mkdir $string_dir
tar -xzvf /home/ise/eran/repo/common_math/jar/commons-math3-3.5-src.tar.gz -C /home/ise/eran/exp/${$string_dir}
relativ_path=/home/ise/eran/exp/${$string_dir}/commons-math3-3.5-src/
rm -r /home/ise/eran/exp/${$string_dir}/commons-math3-3.5-src/src/test/java/org
cp -avr ${path_arg} ${relativ_path}/src/test/java/
cd ${relativ_path}
mvn install 
mvn org.pitest:pitest-maven:mutationCoverage
DIRECTORY_path="/home/ise/eran/exp/output/${string_dir}
if [ ! -d "$DIRECTORY_path" ]; then
	mkdir "$DIRECTORY_path"
fi

mv ${relativ_path}/target/pit-reports/* "$DIRECTORY_path"


echo "Done !! "

exit
