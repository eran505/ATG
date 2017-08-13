#!/bin/bash

read -p "Version Enter: " VAR

read -p "dir in out: " dir

read -p "Time Enter: " Time


python evo_call.py /home/ise/eran/repo/common_math/commons-math3-${VAR}-src/target/classes/org/apache/commons/math3/fraction evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ /home/ise/eran/out/${dir}/ ${Time}
