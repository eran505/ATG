import os ,sys,re
import pandas as pd
import numpy as np
import csv

from scipy.io.matlab.miobase import arr_dtype_number

import pit_render_test

arr_sign = [ 'KILLED' , 'NO_COVERAGE' ,'SURVIVED' ,'TIMED_OUT' , 'RUN_ERROR' ]

def get_csv_summary(root_p):
    walker=pit_render_test.walker(root_p)
    classes_list = walker.walk("csv")
    return classes_list


def get_all_dir(root_p):
    walker=pit_render_test.walker(root_p)
    classes_list = walker.walk("org",False,0)
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


def get_name(path):
    walker=pit_render_test.walker(path)
    name ='null'
    list_p = walker.walk("csv")
    if len(list_p)>0:
        val_s = 'ESTest'
        csv_file = csv.reader(open(path+'/mutations.csv', "rb"), delimiter=",")
        for row in csv_file:
            if str(row[6]).__contains__(val_s) is True:
                name = row[6]
                break
    return name[:len(name)/2]
def make_dcit(all_dir):
    all_data=[]
    for dir in all_dir:
        arr = str(dir).split('/')
        if len(str(arr[len(arr)-1])) < 20 :
            name_class = get_name(dir)
        else :
            name_class = arr[len(arr)-1]+"_ESTest"
       # name_class = get_name_CUT(dir)
        csv = get_csv_summary(dir)
        d={'name':name_class , 'csv':csv , 'dir':dir }
        all_data.append(d)
    print 'data_size=',len(all_data)
    return all_data


def _data_df(list_data):
    df_list=[]
    error_dir=0
    names_list=["class","method","line"]
    for item in list_data:
        csvs = item['csv']
        #print "name= ",item['name']
        names_list.append(item['name'])
        if len(csvs) > 0 :
            df = pd.read_csv(csvs[0],names = ["class-suffix", "class", "mutation-type", "method","line",item['name'],"test"])
            df.drop(df.columns[[0, 2 ,len(list(df))-1]], axis=1, inplace=True)
            #df.set_index(["class","method","line"], inplace=True)
            df.reset_index(level=['class','method','line'],inplace=True)
            if len(df) == 47163 :
                df_list.append(df)
            else:
                error_dir+=1
                print item['name']
                del_error_files(item['dir'])
    print 'error_dir=',error_dir
    result = merge_df(df_list)
    return result

def del_error_files(path_err):
    os.system('rm -r '+path_err)

def merge_df(list_df):
    df_all = list_df[0]
    ctr = 0
    while ctr<len(list_df):
        if ctr == 0 :
            ctr += 1
            continue
        df_all = pd.merge(df_all, list_df[ctr], how='inner',on=['index',"class","method","line"])
        ctr += 1
    return df_all


def merge_all_mutation_df(root):
    all_dir= get_all_dir(root)
    dict_mut=make_dcit(all_dir)
    dfs = _data_df(dict_mut)
    return  dfs


def write_to_csv(dest_path ,df):
    df.to_csv(dest_path, encoding='utf-8')

def mean_all(df):    #[ KILLED , NO_COVERAGE ,SURVIVED ,TIMED_OUT , RUN_ERROR
    list_name = list(df)[4:]
    for name  in arr_sign:
        df[name+'_sum'] = (df[list_name] == name).sum(axis=1)
    string = '_sum'
    my_new_list = [x + string for x in arr_sign]
    df['total'] = df[my_new_list].sum(axis=1)
    for it in my_new_list:
        df[it[:-3]+"mean"] = (df[it].astype(float))/df['total']
        df[it[:-3] + "mean_norm"] = (df[it].astype(float)) / df['total']


def delet_csv(root_p):
    walker=pit_render_test.walker(root_p)
    list_p = walker.walk("mutations.csv")
    for csv_f in list_p:
        if str(csv_f).__contains__('org.apache.commons') is True :
            os.system("rm "+csv_f)

def init_clac(arr_path,out):
    ctr=0
    arr_dfs = []
    for path in arr_path :
        ctr += 1
        dfs = merge_all_mutation_df(path+'commons-math3-3.5-src/target/pit-reports/')
        print dfs.shape
        size =  len(list(dfs))
        mean_all(dfs)
        arr_dfs.append({'id':ctr , 'data':dfs})
        write_to_csv(path+'commons-math3-3.5-src/target/pit-reports/'+'all_t'+str(size)+'.csv', dfs)
        #delet_csv(path)
    return arr_dfs


def fin_sum(dict_df_list):
    new_df = dict_df_list[0]['data'][['index',"class","method","line"]].copy()
    total_sum=0.0
    for item in dict_df_list :
        total_sum+= item['data']['total']
        new_df['total_sum'] = total_sum
    for label in  arr_sign :
        new_df[label+'_W_mean']=0.0
        for item in dict_df_list:
            new_df[label+'_W_mean']+=item['data'][label+'_mean']*(item['data']['total']/new_df['total_sum'])
    return new_df




if __name__ == "__main__":
    #dir_names= ['ALL_t=1' ,'ALL_t=3' ]#, 'ALL_t=4']
    #dir_names_tmp = ['pit_tmp','pit_tmp_2']
    #out = '/home/eran/thesis/test_gen/experiment/'
    #path = '/home/eran/thesis/test_gen/experiment/all_pit/'
    #arr_p = [ path+x+'/' for x in dir_names_tmp]

    arr=sys.argv
    arr = ["",'/home/eran/thesis/test_gen/experiment/all_pit/ALL_t=1/']
    arr_p=[arr[1]]
    out = arr[1]
    split_arr = str(arr[1]).split('/')
    last_name_dir = split_arr[-2]
    dico = init_clac(arr_p,out)
  #  df = fin_sum(dico)
  #  write_to_csv(out+last_name_dir+'_fin.csv',df)























