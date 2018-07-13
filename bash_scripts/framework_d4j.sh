#!/usr/bin/env bash


proj=${1}

python /home/ise/eran/repo/ATG/defects_lib.py -d /home/ise/programs/defects4j/framework/bin -b 1 -r 1-400 -o /home/ise/Desktop/d4j_framework/out/ -t all -p ${proj}-k U

python /home/ise/eran/repo/ATG/defects_lib.py -d /home/ise/programs/defects4j/framework/bin -b 5 -r 1-400 -o /home/ise/Desktop/d4j_framework/out/ -t all -p ${proj} -k U

python /home/ise/eran/repo/ATG/defects_lib.py -d /home/ise/programs/defects4j/framework/bin -b 10 -r 1-400 -o /home/ise/Desktop/d4j_framework/out/ -t all -p ${proj} -k U

python /home/ise/eran/repo/ATG/defects_lib.py -d /home/ise/programs/defects4j/framework/bin -b 15 -r 1-400 -o /home/ise/Desktop/d4j_framework/out/ -t all -p ${proj} -k U

python /home/ise/eran/repo/ATG/defects_lib.py -d /home/ise/programs/defects4j/framework/bin -b 25 -r 1-400 -o /home/ise/Desktop/d4j_framework/out/ -t all -p ${proj} -k U

python /home/ise/eran/repo/ATG/defects_lib.py -d /home/ise/programs/defects4j/framework/bin -b 35 -r 1-400 -o /home/ise/Desktop/d4j_framework/out/ -t all -p ${proj} -k U

python /home/ise/eran/repo/ATG/defects_lib.py -d /home/ise/programs/defects4j/framework/bin -b 50 -r 1-400 -o /home/ise/Desktop/d4j_framework/out/ -t all -p ${proj} -k U

python /home/ise/eran/repo/ATG/defects_lib.py -d /home/ise/programs/defects4j/framework/bin -b 100 -r 1-400 -o /home/ise/Desktop/d4j_framework/out/ -t class -p ${proj} -k U