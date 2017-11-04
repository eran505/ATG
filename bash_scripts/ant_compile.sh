#!/usr/bin/env bash

p_path=${1}
flg=0
if [ -z "$p_path" ]; then
echo "missing path value p_path"
exit
fi
cd ${p_path}

ant compile > ant_out.txt 2 > ant_err.txt
if [ "$?" -ne 0 ]; then
	echo "ant compile Unsuccessful!"
	flg=1
	echo  "---> $?"
fi

if [ "${flg}" == "0" ];then
	exit 0
fi

ant clean

mvn compile > mvn_out.txt 2 > mvn_err.txt

if [ "$?" -ne 0 ]; then
	echo "[E]--------mvn install Unsuccessful -------"
	echo "===========${?}=================="
	exit 1
fi

exit 0