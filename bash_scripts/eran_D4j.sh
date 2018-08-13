#!/usr/bin/env bash

ATG="/home/ise/eran/repo/ATG/"
p_name='Lang'

sudo chmod -R 777 /home/ise/eran/eran_D4j/

python ${ATG}defects_lib.py -p ${p_name} -F fix -o /home/ise/eran/eran_D4j/${p_name}_t=2 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 2 -l 1 -u 100 -t package -c F -k U -r 2-400 -M U -f F

python ${ATG}defects_lib.py -p ${p_name} -F fix -o /home/ise/eran/eran_D4j/${p_name}_t=5 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 5 -l 1 -u 100 -t package -c F -k U -r 2-400 -M U -f F

python ${ATG}defects_lib.py -p ${p_name} -F fix -o /home/ise/eran/eran_D4j/${p_name}_t=10 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 10 -l 1 -u 100 -t package -c F -k U -r 2-400 -M U -f F

python ${ATG}defects_lib.py -p ${p_name} -F fix -o /home/ise/eran/eran_D4j/${p_name}_t=20 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 20 -l 1 -u 100 -t package -c F -k U -r 2-400 -M U -f F

python ${ATG}defects_lib.py -p ${p_name} -F fix -o /home/ise/eran/eran_D4j/${p_name}_t=50 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 50 -l 1 -u 100 -t package -c F -k U -r 2-400 -M U -f F

python ${ATG}defects_lib.py -p ${p_name} -F fix -o /home/ise/eran/eran_D4j/${p_name}_t=90 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 90 -l 1 -u 100 -t package -c F -k U -r 2-400 -M U -f F

