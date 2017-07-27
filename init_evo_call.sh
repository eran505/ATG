#!/bin/bash

read -p "Version Enter: " VAR



read -p "Time Enter: " time


python evo_call.py /home/ise/eran/repo/common_math/commons-math3-${VAR}-src/target/classes/org/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ /home/ise/eran/out/ ${time}
