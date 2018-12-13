#!/usr/bin/env bash

ATG="/home/ise/eran/repo/ATG/"

#   project    num_bugs
#   -------    -------
#   Lang          65
#   Chart         26
#   Closure       133
#   Math          106
#   Mockito       38
#   Time          27



sudo env "PATH=$PATH" python ${ATG}defects_lib.py d4j -i /home/ise/eran/D4J/info/ -M U -C 0 -d /home/ise/programs/defects4j/framework/bin -b 65 -r 36-60 -o /home/ise/eran/D4j/out/ -t package_only -p Math -k U



#    usage='-p project name\n' \
#          '-o out dir\n' \
#          '-e Evosuite path\n' \
#          '-b time budget\n' \
#          '-l Lower bound time budget\n' \
#          '-u Upper bound time budget\n' \
#         '-t target class/package/all\n' \
#          '-c clean flaky test [T/F]\n' \
#          '-d use defect4j framework\n' \
#          '-k the csv fp file or U for uniform' \
#          '-r range for bug ids e.g. x-y | x<=y and x,y int' \
#          '-z to what time budgets to make a predection CSV e.g. 4;5;6' \
#          '-i dir folder where the FP CSV' \
#          '-C crate the info dir or not e.g. 1/0' \
#          '-M mode of the allocation [FP/U]'
#
