import random

import pandas as pd
import numpy as np
import os

import subprocess

import pit_render_test as pt


def get_class_size(root_path):
    walker_obj = pt.walk(root_path,"")

def miss_PIT(path_PIT,dico):
    d={}
    #path_PIT = '/home/ise/eran/xml/02_26_13_27_45_t=30_/pit_test/ALL_FP_t=30_it=0_/commons-math3-3.5-src/csvs/class'
    list_class_csv = pt.walk(path_PIT,'.csv')
    for csv in list_class_csv:
        name = str(csv).split('/')[-1][:-4]
        if os.stat(csv).st_size == 0:
            d[name] = 0
            list_class_csv.remove(csv)
        else:
            d[name]= 1
    for ky in dico.keys():
        if ky in d:
            dico[ky]['pit']=d[ky]
        else:
            dico[ky]['pit'] = 0


def missing_class_gen(root_class,root_test,java_src,log,pit=None,name='tmp'):
    # full path for the test and the .class files
    scanner_class = pt.walk(root_class,".class")
    scanner_java = pt.walk(java_src,".java")
    scanner_tests = pt.walk(root_test, "ESTest.java")
    print "classes size ={}".format(len(scanner_class))
    print "tests size ={}".format(len(scanner_tests))
    # convert the full path to package format
    scanner_class_pak = [pt.path_to_package('org',x,-6) for x in scanner_class ]
    scanner_tests_pak = [pt.path_to_package('org',y,-12) for y in scanner_tests ]
    d = dict_diff(list_one=scanner_class_pak,list_two=scanner_tests_pak,path_root_test=root_test)
    look_at_test(scanner_java,scanner_tests,d)
    if pit is not None:
        miss_PIT(pit,d)
    dff =  make_df(d,log,name)
    return d

def dict_diff(list_one,list_two,path_root_test):
    '''see the different between two list with class as package'''

    d={}
    for item in list_one:
        if item in d:
            raise Exception("cant be two class with the same prefix package")
        else:
            if str(item).__contains__('$'):
                continue
            d[item]={'class':item, 'java(.class)':1, 'test':0 }
    for item_2 in list_two:
        if item_2 in d:
            d[item_2]['test']+=1
            if d[item_2]['test'] > 1 :
                raise Exception("cant be two class with the same prefix package")
        else:
            print "[Error] test has no matching java class "
            d[item_2] = {'class':item, 'java(.class)':0, 'test':1}
    return d



def make_df(d,log,name):
    data_df = []
    for vali in d.values():
        data_df.append(vali)
    df = pd.DataFrame(data_df)
    df.to_csv("{}{}.csv".format(log,name))
    print "Done !"
    return  df

def system_call(command):
    p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    return p.stdout.read()

def get_FP_probability():
    p_path_csv = '/home/ise/eran/repo/ATG/csv/FP_budget_time.csv'
    df = pd.read_csv(p_path_csv,header=None)
    d={}
    print list(df)
    for index, row in df.iterrows():
        d[row[0]]=row[1]
    return d

def get_LOC(p):
    c_command = "/home/ise/.cargo/bin/loc {}".format(str(p))
    string_out = system_call(c_command)
    res = str(string_out).split()
    return res[13],res[10]



def look_at_test(classes,tests,d):
    '''some info'''
    d_FP = get_FP_probability()
    for entry in d.keys():
        d[entry]['loc_TEST']=0
        d[entry]['loc_class'] = 0
    for item in classes:
        ky = pt.path_to_package('org',item,-5)
        if str(ky).__contains__('package-info'):
            continue
        if ky in d_FP:
            d[ky]['FP']=d_FP[ky]
        loc_class= get_LOC(p=item)
        if ky in d:
            d[ky]['loc_class'] = int(loc_class[0])
        else :
            print ("the .java in not in the dict .class --> {}".format(ky))
            continue
    for cut in tests:
        ky = pt.path_to_package('org',cut,-12)
        loc_class= get_LOC(p=cut)
        if ky in d:
            num_line = int(loc_class[0])
            d[ky]['loc_TEST'] = num_line
            if num_line == 12 :
                d[ky]['Empty_test_case'] = 1
                d[ky]['no_test'] = 0
            elif num_line > 12 :
                d[ky]['no_test'] = 0
                d[ky]['Empty_test_case'] = 0
            elif num_line < 12 :
                d[ky]['no_test'] = 1
                d[ky]['Empty_test_case'] = 1
        else :
            print ("the .java in not in the dict .class --> {}".format(ky))
            continue


def func_start(main_root):
    scan_obj = pt.walk(main_root,"t=",False,0)
    li=[]
    for x in scan_obj:
        print x
        li.append(time_budget_analysis(x))
    df = pd.DataFrame(li)
    if main_root[-1] !='/':
        main_root = main_root+'/'
    df.to_csv(main_root+"class_analysis.csv")
def time_budget_analysis(path_root):
    list_d = []
    res_scanner = pt.walk(path_root, "commons-math3-3.5-src", False)
    p_path = path_root
    if p_path[-1] != '/':
        p_path= p_path+'/'
    if os.path.isdir("{}stat/".format(p_path)) is False :
        os.system("mkdir {}".format(p_path+"stat/"))
    log_path = "{}stat/".format(p_path)
    for i_path in res_scanner:
        #if str(i_path).__contains__("ALL_U") is False:
        #    continue
        name_i = get_name_path(i_path,-2)
        javas_path="{}/src/main/java/org/".format(i_path)
        classes_path = "{}/target/classes/org/".format(i_path)
        tests_path = "{}/src/test/java/org/".format(i_path)
        pit_path = "{}/csvs/class".format(i_path)
        df_i = missing_class_gen(root_class=classes_path, root_test=tests_path, java_src=javas_path,log=log_path,name=name_i,pit=pit_path)
        list_d.append(df_i)
    if len(list_d) == 0:
        return {}
    res = merge_df(list_d,log_path)
    return res




def merge_df(list_d,log_path_dir):
    size = len(list_d)
    d_big ={}
    for dico in list_d:
        for ky in dico.keys():
            if ky in d_big:
                #print "d_big[ky]:: ",d_big[ky]
                #print "dico[ky]:: ",dico[ky]
                d_big[ky]['arr'] = str(d_big[ky]['arr']) + "," + str(dico[ky]['loc_TEST'])
                if dico[ky]['loc_TEST'] == 12:
                    d_big[ky]['empty_test'] += 1
                if dico[ky]['loc_TEST'] == 0:
                    d_big[ky]['no_test'] += 1
                for filed_i in dico[ky]:
                    if filed_i == 'class' or filed_i=='FP':
                        continue
                    if filed_i in d_big:
                        d_big[ky][filed_i]+=dico[ky][filed_i]
                    else:
                        d_big[ky][filed_i] = dico[ky][filed_i]
            else:
                d_big[ky] = {'empty_test':0,'no_test':0,'arr':""}
                d_big[ky]['arr'] =  str(dico[ky]['loc_TEST'])
                if dico[ky]['loc_TEST'] == 12:
                    d_big[ky]['empty_test'] += 1
                if dico[ky]['loc_TEST'] == 0:
                    d_big[ky]['no_test'] += 1
                for filed_i in dico[ky]:
                    d_big[ky][filed_i]=dico[ky][filed_i]

    for entry in d_big.keys():
        arr_str = d_big[entry]['arr']
        arr_str = str(arr_str).split(',')
        arr=[]
        for x in arr_str:
            arr.append(int(x))
        d_big[entry]['var'] = np.var(arr)
        d_big[entry]['mean'] = np.mean(arr)
    df = pd.DataFrame(d_big.values())
    df['empty_Avg_OutOfGenerated'] = df['empty_test']/df['test']
    df['no_test_Avg'] = df['no_test']/(df['test']+df['no_test'])
    good_bye_list = ['arr']
    df.drop(good_bye_list, axis=1, inplace=True)
    df.to_csv("{}FinStat_Size_{}_.csv".format(log_path_dir,size))
    numeric_clmns = df.dtypes[df.dtypes != "object"].index
    d_sum_fin={"num_classes":df['class'].count(),'size_dir':size,'time_budget':extract_time(log_path_dir)}
    for col in numeric_clmns :
        d_sum_fin[col]=df[col].sum()
    return d_sum_fin

###############################################################################################################################
## matrix analysis
###############################################################################################################################
def extract_time(string_path):
    arr_tmp = str(string_path).split('_t=')
    time = str(arr_tmp[1]).split('_')[0]
    print "T={} P={}".format(time,string_path)
    return time

def get_name_path(v_path,index):
    arr = str(v_path).split('/')
    return arr[index]

def load__data(root_data):
    print ""
    list_files = pt.walk(root_data,'.csv')
    d_dico={}
    for item_csv in list_files:
        prefix_name = str(item_csv).split('/')[-1][:-4]
        d_dico[prefix_name]=pd.read_csv(item_csv)
    return d_dico



def get_top_k(df,col_name,k=5):

    df_cut = None
    if col_name in df:
        df_cut = df.nlargest(k,col_name)
    if col_name == 'random':
        size = len(df)
        if k >= size:
            return df_cut
        try:
            values = random.sample(range(1, size), k)
            df_cut = df.iloc[values,:]
        except ValueError:
            print('Sample size exceeded population size.')
            exit(-1)
    return df_cut

def main_loader(fp_path,info_path,uni_path):
    print ""

def matrix_get_class_by_name(name):
    print ""

def _get_prefix(name):
    arr = str(name).split('.')[:-1]
    return '.'.join(arr)

def diced_to_prefix(df,dico_prefix):
    df_prefix={}
    df['prefix']=df.apply(lambda x: _get_prefix(x['class']), axis=1)
    for key in dico_prefix.keys():
        df_prefix[key] = df.loc[df['prefix'] == key]
    return df_prefix

def project_name(path):
    arr= str(path).split('/')
    for x in arr:
        if str(x).startswith('ALL'):
            return x

def matrix_analysis(root_path_project, root_stat,k=3,on='FP',out='/home/ise/eran/oout'):
    df_sum=[]
    d_fp = load__data(root_path_project)
    name_project =  project_name(root_path_project)
    out_path = pt.mkdir_system(out,name_project,False)
    df_stat = pd.read_csv(root_stat)
    diced_to_prefix(df_stat,d_fp)
    for ky in d_fp.keys():
        df_filter = df_stat.loc[df_stat['prefix'] == ky]
        if len(df_filter) > k:
            #print "ky: {} len: {}".format(ky,len(df_filter))
            df_cut = get_top_k(df_filter,on,k)
        else:
            df_cut = df_filter
        target_list=['ID']
        target_list.extend(df_cut['class'].tolist())
        package_df = d_fp[ky]
        res_package_df = package_df[target_list]
        size_bug = len(res_package_df)
        print 'size_bug: ',size_bug
        tmp_d = {}
        for x in target_list:
            if x == 'ID':
                continue
            out_pit =  res_package_df[x].value_counts()
            out_pit = out_pit.to_dict()
            if ky not in tmp_d:
                tmp_d[ky]=out_pit
            else:
                d=tmp_d[ky]
                d_res = mereg_dico(d,out_pit)
                tmp_d[ky] = d_res
        tmp_d[ky]['package']=ky
        df_sum.append(tmp_d[ky])
        del tmp_d[ky]
    df = pd.DataFrame(df_sum)
    name = "k_{}_on_{}".format(k,on)
    df.to_csv("{}/res_{}.csv".format(out_path,name))

def aggregation_res_matrix(path_dir):
    print ""
    d=[]
    list_files = pt.walk(path_dir,'.csv')
    for file_i in list_files:

        name_file = str(file_i).split('/')[-1][:-4]
        if str(name_file).__contains__('sum'):
            continue
        dir_name = str(file_i).split('/')[-2]
        arr =str(name_file).split('_')
        k_num = arr[2]
        criterion = arr[4]
        df = pd.read_csv(file_i,index_col=0)
        col_list = list(df)
        col_list.remove('package')
        df['sum_all'] = df[col_list].sum(axis=1)
        sum_kill = df['KILLED'].sum()
        sum_all = df['sum_all'].sum()
        d.append({'criterion':criterion,'dir':dir_name,'K':k_num,'kill':sum_kill,'all_bug':sum_all})
    df_all = pd.DataFrame(d)
    df_all.sort_values(by=['K'],inplace=True)
    df_all.to_csv("{}/sum.csv".format(path_dir),index=False)
def mereg_dico(d1,d2):
    print type(d1)
    print 'd1: ',d1
    print 'd2: ',d2
    d3 = {}
    for x in d1.keys():
        if x in d2:
            d3[x] = d1[x] + d2[x]
        else:
            d3[x] = d1[x]
    for y in d2.keys():
        if y not in d1:
            d3[y] = d2[y]
    print 'd3: ',d3
    return d3


import sys
if __name__ == "__main__":
    #func_start('/home/ise/eran/xml/')
    aggregation_res_matrix('/home/ise/eran/oout')
    exit()
    p_stat_U ='/home/ise/eran/xml/02_26_13_27_45_t=30_/stat/ALL_U_t=30_it=0_.csv'
    p_stat_FP='/home/ise/eran/xml/02_26_13_27_45_t=30_/stat/ALL_FP_t=30_it=0_.csv'
    p_prefix_csv_Fp = '/home/ise/eran/xml/02_26_13_27_45_t=30_/pit_test/ALL_FP_t=30_it=0_/commons-math3-3.5-src/csvs/package'
    p_prefix_csv_U = '/home/ise/eran/xml/02_26_13_27_45_t=30_/pit_test/ALL_U_t=30_it=0_/commons-math3-3.5-src/csvs/package'


    arr_on=['random','loc_class','FP']
    for x in arr_on:
        matrix_analysis(p_prefix_csv_U,p_stat_U,on=x,k=6)
        matrix_analysis(p_prefix_csv_Fp, p_stat_FP, on=x, k=6)
    #args = sys.argv
    #func_start(args[1])



