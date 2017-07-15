

import pandas as pd
import numpy as np
import os

import pandas as pd

str_path = "/home/eran/Desktop/evo_result/"

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
    new_names=['Covered_Goals','Total_Goals','Coverage']
    for path in list_csv_path:
        pd_tmp = pd.read_csv(path[1])
        index_time = str(path[0])
        list_name = list(pd_tmp)
        size = len(list_name)
        for i in range(len(new_names)):
            pd_tmp[new_names[i]+'_'+index_time] = pd_tmp[list_name[size - (i+1)]].copy()
            pd_tmp.drop(str(list_name[size-(i+1)]), axis=1, inplace=True)
        list_name = list(pd_tmp)
        size = len(list_name)
        fitness=''
        for i in range(1,size-3,1):
            fitness=fitness+"_"+str(pd_tmp[list_name[i]][1])
            pd_tmp.drop(str(list_name[i]), axis=1, inplace=True)
        pd_tmp['criterion_' + index_time] = fitness
        list_pd.append(pd_tmp)
        pd_tmp=None
    return list_pd

def join_data_frame(d1,d2):
    if d1.size > d2.size :
        data_res =  d1.merge(d2 ,how='left', on='TARGET_CLASS')
    else:
        data_res = d2.merge(d1, how='left', on='TARGET_CLASS')
    return data_res


list = get_all_csv(str_path)
res=join_data_frame(list[0],list[1])
res.to_csv("/home/eran/Desktop/evo_result/res.csv", sep='\t', encoding='utf-8')