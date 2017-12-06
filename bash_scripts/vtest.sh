#!/usr/bin/env bash

echo -e 'bo\nhello'

arr=[]
counter=1
while [ $counter -le 106 ]
do
echo $counter
A=$(/home/eran/programs/Defects4j/defects4j/framework/bin/defects4j info -p Math -b $counter)
regex='^20[0-9][0-9][-][0-9][0-9][-][0-9][0-9]$'
B=$(awk 'f {print; exit} /Revision date/ {f=1}' <<<"$A")
for word in $B
do
    arr+=$word'\n'
    break
done

((counter++))

done

echo -e $arr >> ~/Desktop/data_dj.txt
#bash init_exp.sh ~/eran/repo/ATG/ 60 exp

#bash init_exp.sh ~/eran/repo/ATG/ 90 exp

#bash init_exp.sh ~/eran/repo/ATG/ 120 exp
