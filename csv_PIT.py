import os ,sys,re
import pandas as pd
import numpy as np
from numpy.distutils.system_info import dfftw_info

import pit_render_test

root = '~/thesis/test_gen/poc/commons-math3-3.5-src/target/pit-reports/201708310036/org.apache.commons.math3.fraction/'

def get_csv_summary(root_p):
    walker=pit_render_test.walker(root_p)
    classes_list = walker.walk("csv")
    return classes_list


def get_all_dir(root_p):
    walker=pit_render_test.walker(root_p)
    classes_list = walker.walk("",False,0)
    return classes_list

def get_name_CUT(root_p):
    walker=pit_render_test.walker(root_p)
    list_p = walker.walk("html")
    size = len('<h2>Tests examined</h2><ul>*</ul>')
    name = []
    for page in list_p:
        with open(page, 'r') as myfile:
            data = myfile.read()
            data = data.replace('\n','')
            tmp = re.findall('<h2>Tests examined</h2><ul>.*?</ul>',data)
            if tmp == None:
                continue
            if len(tmp)>0 and len(tmp[0])>size:
                name.append(tmp[0][31:-20])
                break
    if len(name) == 0:
        raise Exception("problem with the ", root_p)
    size=len(name[0])
    res_name = name[0][:size/2]
    return res_name


def make_dcit(all_dir):
    all_data=[]
    for dir in all_dir:
        name_class = get_name_CUT(dir)
        csv = get_csv_summary(dir)
        d={'name':name_class , 'csv':csv , 'dir':dir }
        all_data.append(d)
    return all_data


def _data_df(list_data):
    df_list=[]
    names_list=["class","method","line"]
    for item in list_data:
        csvs = item['csv']
        print "name= ",item['name']
        names_list.append(item['name'])
        if len(csvs) > 0 :
            df = pd.read_csv(csvs[0],names = ["class-suffix", "class", "mutation-type", "method","line",item['name'],"test"])
            df.drop(df.columns[[0, 2 ,len(list(df))-1]], axis=1, inplace=True)
            #df.set_index(["class","method","line"], inplace=True)
            df.reset_index(level=['class','method','line'],inplace=True)
            df_list.append(df)
    result = merge_df(df_list)
    return result

def merge_df(list_df):
    df_all = list_df[0]
    ctr = 0
    while ctr<len(list_df):
        if ctr == 0 :
            ctr += 1
            continue
        df_all = pd.merge(df_all, list_df[ctr], how='inner',on=['index',"class","method","line"])
        ctr+=1
    return df_all


def merge_all_mutation_df(root):
    all_dir= get_all_dir(path)
    dict_mut=make_dcit(all_dir)
    dfs = _data_df(dict_mut)
    return  dfs


def mean_all(arr_path):


if __name__ == "__main__":
    path = '/home/eran/thesis/test_gen/poc/commons-math3-3.5-src/target/pit-reports/'
    dfs = merge_all_mutation_df(path)
    print dfs.shape
    print list(dfs)

























