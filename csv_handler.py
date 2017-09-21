

import pandas as pd
import numpy as np
import os
import csv

import pandas as pd
import sys


def get_all_csv(path):
    list_csv_path = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".csv"):
                if str(file).__contains__("statistics") is False:
                    continue
                name = str(file)
                size =len(root)
                time=''
                for w in range(size-1,0,-1):
                    if root[w] == '_':
                        list_csv_path.append([time,str(os.path.join(root, file))])
                        break
                    time=root[w]+time
    list_pd = []
    for path in list_csv_path:
        pd_tmp = pd.read_csv(path[1])
        index_time = str(path[0])
        list_name = list(pd_tmp)
        size = len(list_name)
        for i in range(1,size,1):
            pd_tmp[str(list_name[i]+'_'+index_time)]=pd_tmp[str(list_name[i])].copy()
            pd_tmp.drop(str(list_name[i]), axis=1, inplace=True)
        #print list(pd_tmp)
        list_pd.append(pd_tmp)
        pd_tmp=None
    return list_pd

def join_data_frame(list):
    if len(list)>1 :
        data_res=list[0]
        for item in list :
            if data_res.size > item.size :
                data_res = data_res.merge(item, how='left', on=' TARGET_CLASS')
            else:
                data_res = item.merge(data_res, how='left', on=' TARGET_CLASS')
    return data_res

def remove_dot_csv(path):
    list_csv_path = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".csv"):
                if str(file).__contains__("statistics") is False:
                    continue
                list_csv_path.append(str(os.path.join(root, file)))
    for file_csv in list_csv_path :
        with open(file_csv, 'r') as myfile:
            data = myfile.read().replace(';','_')
            text_file = open(file_csv, "w")
            text_file.write(" %s" % data)
            text_file.close()
    return "done"



if len(sys.argv) == 3 :
    if str(sys.argv[1]) == '-p' :
        v_path = sys.argv[2]
        print(remove_dot_csv(v_path))
else:
    print 'Usage :\n-p [path] '
    print pd



'''''''''''
list = get_all_csv(str_path)
list.sort(key=lambda x: x.size, reverse=True)
res=join_data_frame(list)
res.to_csv("/home/eran/Desktop/evo_result/res.csv", sep='\t', encoding='utf-8')
'''''