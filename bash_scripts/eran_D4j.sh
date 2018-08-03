#!/usr/bin/env bash

ATG="/home/ise/eran/repo/ATG/"

python ${ATG}defects_lib.py -p Lang -o /home/ise/eran/eran_D4j/Lang_t=2 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 2 -l 1 -u 100 -t project -c F -k U -r 1-2 -M U -f F

python ${ATG}defects_lib.py -p Lang -o /home/ise/eran/eran_D4j/Lang_t=5 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 5 -l 1 -u 100 -t project -c F -k U -r 1-2 -M U -f F

python ${ATG}defects_lib.py -p Lang -o /home/ise/eran/eran_D4j/Lang_t=10 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 10 -l 1 -u 100 -t project -c F -k U -r 1-2 -M U -f F

python ${ATG}defects_lib.py -p Lang -o /home/ise/eran/eran_D4j/Lang_t=20 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 20 -l 1 -u 100 -t project -c F -k U -r 1-2 -M U -f F

python ${ATG}defects_lib.py -p Lang -o /home/ise/eran/eran_D4j/Lang_t=50 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 50 -l 1 -u 100 -t project -c F -k U -r 1-2 -M U -f F

python ${ATG}defects_lib.py -p Lang -o /home/ise/eran/eran_D4j/Lang_t=90 -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 90 -l 1 -u 100 -t project -c F -k U -r 1-2 -M U -f F

