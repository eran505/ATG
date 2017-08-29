#!/usr/bin/env bash
curdir=$(pwd)
echo "curdir="$curdir
newdir=$curdir/apache_test
if [ ! -d "$newdir" ]; then
	mkdir "$newdir"
fi

out_path=/home/ise/eran/out/pit_mvn/
mv $curdir/src/test/java/org/ $newdir
cp -avr $curdir/.evosuite/best-tests/org $curdir/src/test/java/
mvn clean test
exit
mvn org.pitest:pitest-maven:mutationCoverage
mv $curdir/target/pit-reports/* "$out_path"


exit


