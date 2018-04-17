import random

import pandas as pd
import numpy as np
import os

import subprocess

import pit_render_test as pt



def get_class_size(root_path):
    walker_obj = pt.walk(root_path,"")


def miss_target_pit(path_PIT,dico):
    d={}
    list_class_dir = pt.walk(path_PIT, '',False)
    for dir in list_class_dir:
        empty = 0
        name = str(dir).split('/')[-1]
        files = pt.walk(dir,'mutations')
        if len(files)==1:
            if os.stat(files[0]).st_size < 1:
                empty=1
            suffix = files[0][-3:]
            if suffix == 'xml':
                d[name]= {'xml':1,'csv':0,'empty':empty}
            elif suffix =='csv':
                d[name] = {'xml': 0, 'csv': 1,'empty':empty}
            else:
                raise Exception('unreconzie suffix: (path)= {}'.format(files[0]))
        elif len(files)>1:
            raise Exception('more than on Mutations.xml/Mutations.csv in dir: {}'.format(dir))
        else:
            d[name] = {'xml': 0, 'csv': 0,'empty':empty}
    for ky in dico.keys():
        if ky in d:
            dico[ky]['pit_xml']=d[ky]['xml']
            dico[ky]['pit_csv'] = d[ky]['csv']
            dico[ky]['pit_empty_file'] = d[ky]['empty']
        else:
            print 'in'
            dico[ky]['pit_xml'] = 0
            dico[ky]['pit_csv'] = 0
            dico[ky]['pit_empty_file'] = 0


def miss_PIT(path_PIT,dico):
    d={}
    if os.path.isdir(path_PIT) is False:
        return
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


def missing_class_gen(root_class,root_test,java_src,log,pit=None,name='tmp',pit2=None):
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
    if pit2 is not None:
        miss_target_pit(pit2,d)
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


def func_start(main_root,mode='reg'):
    scan_obj = pt.walk(main_root,"t=",False,0)
    li=[]
    for x in scan_obj:
        print x
        li.append(time_budget_analysis(x,mode))
    df = pd.DataFrame(li)
    if main_root[-1] !='/':
        main_root = main_root+'/'
    df.to_csv(main_root+"class_analysis.csv")
def time_budget_analysis(path_root,mode):
    list_fp = []
    list_u =[]
    res_scanner = pt.walk_rec(path_root, [],"commons-", False,-3)
    #res_scanner = pt.walk(path_root, "commons-math3-3.5-src", False)
    p_path = path_root
    if p_path[-1] != '/':
        p_path= p_path+'/'
    if os.path.isdir("{}stat_r/".format(p_path)):
        os.system("rm -r {}".format(p_path + "stat_r/"))
    os.system("mkdir {}".format(p_path + "stat_r/"))
    log_path = "{}stat_r/".format(p_path)
    for i_path in res_scanner:
        #if str(i_path).__contains__("ALL_U") is False:
        #    continue
        name_i = get_name_path(i_path,-2)
        allocation_mode = str(name_i).split('_')[1]
        time_budget = str(name_i).split('_')[2][2:]

        javas_path="{}/src/main/java/org/".format(i_path)
        classes_path = "{}/target/classes/org/".format(i_path)
        tests_path = "{}/src/test/java/org/".format(i_path)
        pit_path2=None
        pit_path=None
        if mode == 'rev':
            pit_path = "{}/csvs/class".format(i_path)
        else:
            pit_path2 = "{}/target/pit-reports/".format(i_path)
        df_i = missing_class_gen(root_class=classes_path, root_test=tests_path, java_src=javas_path,log=log_path,name=name_i,pit=pit_path,pit2=pit_path2)
        if allocation_mode =='FP':
            list_fp.append(df_i)
        elif allocation_mode == 'U':
            list_u.append(df_i)
        else:
            raise Exception('No allocation mode is known in name:{} \n path:{}'.format(name_i,i_path))
    if len(list_u) > 0:
        merge_df(list_u,log_path,'u')
    if len(list_fp) > 0:
        merge_df(list_fp, log_path,'fp')
    return None


def merge_df(list_d,log_path_dir,allocation_mode):
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
                    if filed_i in d_big[ky]:
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
    df.to_csv("{}FinStat_{}_Size_{}_.csv".format(log_path_dir,allocation_mode,size))
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
            return df
        try:
            values = random.sample(range(1, size), k)
            df_cut = df.iloc[values,:]
        except ValueError:
            print('Sample size exceeded population size.')
            exit(-1)
    if df_cut is None:
        raise Exception("the df cut is None")
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
    d_fp = load__data(root_path_project) # load all the package of the prefix packages
    name_project =  project_name(root_path_project)  # get the project name
    out_path = pt.mkdir_system(out,name_project,False) # create dir for the output
    df_stat = pd.read_csv(root_stat)  # load the stat DataFrame
    diced_to_prefix(df_stat,d_fp) # make packages stat dict
    for ky in d_fp.keys():
        print '--------------------------on={}---------------------------'.format(on)
        print "name----->name_project: {}".format(name_project)
        print "KEY : {}".format(ky)
        df_filter = df_stat.loc[df_stat['prefix'] == ky]
        package_size = len(df_filter)
        df_filter = df_filter.loc[df_filter['test'] == 1]
        package_size_actual_test = len(df_filter)
        df_filter = df_filter.loc[df_filter['pit'] == 1]
        package_size_actual_pit = len(df_filter)
        print list(df_filter)
        loc = df_filter['loc_TEST'].sum()
        if len(df_filter) > k:
            #print "ky: {} len: {}".format(ky,len(df_filter))
            df_cut = get_top_k(df_filter,on,k)
        else:
            df_cut = df_filter
        target_list=['ID']
        if df_cut is None: #TODO:FIX IT !!!!!
            raise Exception("[Error] the df cut is empty == None")
        target_list.extend(df_cut['class'].tolist())
        print "df_CUT\n\t{}".format(list(df_cut))
        package_df = d_fp[ky]
        print list(package_df)
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
        tmp_d[ky]['Test_LOC'] = loc
        tmp_d[ky]['all_mutation'] = size_bug
        tmp_d[ky]['package_class_size'] = package_size
        tmp_d[ky]['package_size_actual_test'] = package_size_actual_test
        tmp_d[ky]['package_size_actual_pit'] = package_size_actual_pit
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
        sum_kill = df['KILLED'].sum()
        sum_all = df['all_mutation'].sum()
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


def statistic_by_packaging(p_path):
    '''
    make a static over all packages in the given project

    :param p_path:
    :return:
    '''
    new_df_list=[]
    all_dir = pt.walk(p_path,'stat_r',False)
    for dir in all_dir:
        pass

def sum_all_stat_dir(p_path,mod='fp'):

    new_df_list=[]
    list_col=['Empty_test_case','FP','empty_test','java(.class)','no_test','pit','test','no_test_Avg']
    all_dir = pt.walk(p_path,'stat_r',False)
    for dir in all_dir:
        name = str(dir).split('/')[-2]
        print 'name=',name
        if len(name.split('_') ) < 5 :
            continue
        time = name.split('_')[5]
        time = time[2:]
        all_csvs = pt.walk(dir,'Fin')
        all_csvs = [x for x in all_csvs if str(x).split('/')[-1].__contains__('_{}_'.format(mod))]
        if len(all_csvs) > 1:
            raise Exception("Two file Fin in dir:{} mode allocation={}".format(dir,mod))
        for csv_item in all_csvs:
            name_file = str(csv_item).split('/')[-1][:-4]
            mode = name_file.split('_')[1]
            size_dirs =name_file.split('_')[3]
            size_project =int(size_dirs)
            d = {}
            df = pd.read_csv(csv_item,index_col=0)
            df['avg__empty'] = df['empty_test']/size_project
            list_col.extend(['avg__empty'])
            list_numric = list(df._get_numeric_data())
            list_numric = [x for x in list_numric if x in list_col]
            d['dirs']=size_dirs
            d['time']=time
            d['allocation_mode'] = mode
            d['name']=name
            d['size_project']=size_project
            d['size'] = len(df)
            for x in list_numric:
                d[x]=df[x].sum()
            new_df_list.append(d)
    df = pd.DataFrame(new_df_list)
    df['time']=df['time'].apply(int)
    df = df.set_index(df['time'])
    df.drop('time', axis=1, inplace=True)
    df.sort_index(inplace=True)
    if p_path[-1] == '/':
        df.to_csv("{}fin_{}_stat.csv".format(p_path,mod))
    else:
        df.to_csv("{}/fin_{}_stat.csv".format(p_path,mod))


def merge_by_packages_Roni(dir_root,out_path):
    '''
    this function output a matrix with the columns target_col for each file configurations in the time_FP and time_U
    :param dir_root:
    :param out_path:
    :return:
    '''
    print ""
    d = []
    name = dir_root.split('/')[-1]
    target_cols = ['KILLED', 'all_mutation', 'package','Test_LOC', 'package_class_size', 'package_size_actual_pit','package_size_actual_test','criterion','allocation_mode','K','time_budget']
    list_files = pt.walk(dir_root, '.csv')
    all_dfs = None
    for file_i in list_files:
        name_file = str(file_i).split('/')[-1][:-4]
        arr = name_file.split('_')
        k=arr[2]
        criterion =arr[-1]
        if str(name_file).__contains__('sum'):
            continue
        dir_name = str(file_i).split('/')[-2]
        arr = dir_name.split('_')
        allocation_mode = arr[1]
        time_budget = arr[2][2:]
        df = pd.read_csv(file_i, index_col=0)
        df['K']=k
        df['criterion'] = criterion
        df['time_budget']=time_budget
        df['allocation_mode'] = allocation_mode
        df = df[target_cols]
        #df[target_cols].to_csv("/home/ise/eran/bbb.csv", index=False)
        if all_dfs is None:
            all_dfs = df
            #print "len: {}".format(len(all_dfs))
            continue
        else:
            size_df=len(df)
            size_all_df = len(all_dfs)
            print "df:",size_df
            print "all_dfs:", size_all_df
            all_dfs = all_dfs.append(df)
            print "mereg: {}".format(len(all_dfs))
            if len(all_dfs)-size_all_df != 73:
                print "-------Error--------"
    if out_path[-1] == '/':
        all_dfs.to_csv("{}by_package_{}.csv".format(out_path, name), index=False)
    else:
        all_dfs.to_csv("{}/by_package_{}.csv".format(out_path, name), index=False)
    exit()


def merge_by_packages(dir_root,out_path):
    print ""
    d = []
    name = dir_root.split('/')[-1]
    target_cols = ['KILLED','all_mutation','package','package_class_size','package_size_actual_pit','package_size_actual_test']
    list_files = pt.walk(dir_root, '.csv')
    all_dfs = None
    for file_i in list_files:
        name_file = str(file_i).split('/')[-1][:-4]
        if str(name_file).__contains__('sum'):
            continue
        dir_name = str(file_i).split('/')[-2]
        arr = str(name_file).split('_')
        k_num = arr[2]
        criterion = arr[4]
        df = pd.read_csv(file_i, index_col=0)
        col_list = list(df)
        name_col = "K_{}_mode_{}_dir_{}".format(k_num,criterion,dir_name)
        print list(df)
        df = df[target_cols]
        df.rename(columns={'KILLED': '{}_{}'.format(name_col,'kill')}, inplace=True)
        #df.rename(columns={'all_mutation': '{}_{}'.format(name_col,'all_bug')}, inplace=True)
        if all_dfs is None:
            all_dfs = df
            print "len: {}".format(len(all_dfs))
            continue
        else:

            all_dfs=pd.merge(all_dfs,df,on=['package','package_class_size','package_size_actual_pit','package_size_actual_test','all_mutation'])
            print "len: {}".format(len(all_dfs))
    if out_path[-1]=='/':
        all_dfs.to_csv("{}by_package_{}.csv".format(out_path,name), index=False)
    else:
        all_dfs.to_csv("{}/by_package_{}.csv".format(out_path,name), index=False)
    #df_all = pd.DataFrame(d)
    #df_all.sort_values(by=['K'], inplace=True)
    #df_all.to_csv("{}/sum.csv".format(dir_root), index=False)

import sys

if __name__ == "__main__":


    #merge_by_packages_Roni('/home/ise/eran/oout/data','/home/ise/eran/oout/')
#    exit()
    #sum_all_stat_dir('/home/ise/eran/exp_all/')
    sys.argv=['','/home/ise/tran','reg'] #'/home/ise/tran'
    if len(sys.argv)>1:
        pp=sys.argv[1]
        func_start(pp,sys.argv[2])
        sum_all_stat_dir(pp, 'fp')
        sum_all_stat_dir(pp,'u')

    #fraggregation_res_matrix('/home/ise/eran/oout')
    exit()

    p_stat_U ='/home/ise/eran/xml/02_26_13_27_45_t=30_/stat_r/ALL_U_t=30_it=0_.csv'
    p_stat_FP='/home/ise/eran/xml/02_26_13_27_45_t=30_/stat_r/ALL_FP_t=30_it=0_.csv'
    p_prefix_csv_Fp = '/home/ise/eran/xml/02_26_13_27_45_t=30_/pit_test/ALL_FP_t=30_it=0_/commons-math3-3.5-src/csvs/package'
    p_prefix_csv_U = '/home/ise/eran/xml/02_26_13_27_45_t=30_/pit_test/ALL_U_t=30_it=0_/commons-math3-3.5-src/csvs/package'

    p_stat_U = '/home/ise/eran/xml/02_23_17_34_26_t=60_/stat_r/ALL_U_t=60_it=0_.csv'
    p_stat_FP = '/home/ise/eran/xml/02_23_17_34_26_t=60_/stat_r/ALL_FP_t=60_it=0_.csv'
    p_prefix_csv_Fp = '/home/ise/eran/xml/02_23_17_34_26_t=60_/pit_test/ALL_FP_t=60_it=0_/commons-math3-3.5-src/csvs/package'
    p_prefix_csv_U = '/home/ise/eran/xml/02_23_17_34_26_t=60_/pit_test/ALL_U_t=60_it=0_/commons-math3-3.5-src/csvs/package'


#    aggregation_res_matrix('/home/ise/eran/oout')
#    merge_by_packages('/home/ise/eran/oout/ALL_FP_t=60_it=0_','/home/ise/eran/oout/')

    exit()
    arr_on=['loc_class','random','FP']
    for x in arr_on:
        for k_val in [1,2,3,5,8,10,30,100]:
            print "config: k={} on={}".format(k_val,x)
            matrix_analysis(p_prefix_csv_U,p_stat_U,on=x,k=k_val)
            matrix_analysis(p_prefix_csv_Fp, p_stat_FP, on=x, k=k_val)
    #aggregation_res_matrix('/home/ise/eran/oout')

    #args = sys.argv
    #func_start(args[1])



