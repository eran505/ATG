#!/usr/bin/env bash

location_dir=$1

ctr=10

while [ $ctr -le 300 ]
    do
        echo "generate testing with time budget= $ctr"
        des_dir=${location_dir}/T_${ctr}/
        mkdir ${location_dir}/T_${ctr}/
        bash serach_time_exp.sh ${des_dir} ${ctr} ~/eran/repo/ATG/
        ((ctr=ctr+10))
    done
