import pandas as pd
import numpy as np
import pit_render_test as pt
import os
from math import pow
import re
from collections import Counter
from subprocess import Popen, PIPE, check_call, check_output
import pit_render_test as pt
import subprocess
import shlex

'''
This script handel the csv operation on the D4J exp
'''



def get_faulty_comp_defe4j_dir(p_name='Math',dir_d4j='/home/ise/programs/defects4j/framework/projects'):
    faluty_comp_dir = '/home/ise/programs/defects4j/framework/projects/{}/modified_classes'.format(p_name)
    list_files_src = pt.walk_rec(faluty_comp_dir,[],'.src')
    list_bug_info=[]
    for file_i in list_files_src:
        d={}
        bug_number = str(file_i).split('/')[-1].split('.')[0]
        d['bug_ID'] = bug_number
        d['project'] = p_name
        with open(file_i,'r+') as f:
            lines = f.readlines()
        for line in lines:
            line = line.replace('\n','')
            list_bug_info.append({'bug_ID':bug_number, 'project':p_name, 'class':line})
    return list_bug_info



def get_deff(dir_path):
    '''
    getting the diff between the result of the junit, the buggy version and the fix version
    :param dir_path:
    :return:
    '''
    log_files = pt.walk_rec(dir_path, [], 'trigger.log')
    d = {}
    if len(log_files) == 2:
        for file_i in log_files:
            if str(file_i).split('.')[0].__contains__('f'):
                d['fix'] = {'path': file_i}
            elif str(file_i).split('.')[0].__contains__('b'):
                d['bug'] = {'path': file_i}
            else:
                raise Exception("[Error] the log file is not in the correct format -> {}".format(file_i))
    else:
        return d
    diff_bug, diff_fix = diff_function(d['bug']['path'], d['fix']['path'])
    d['bug']['diff'] = diff_bug
    d['fix']['diff'] = diff_fix
    d['fix']['tests'] = ':'.join(get_regex_res(diff_fix, 'test\d+'))
    d['bug']['tests'] = ':'.join(get_regex_res(diff_bug, 'test\d+'))
    d['bug']['class'] = ':'.join(get_regex_res(diff_bug,'---.+ESTest',4))
    d['fix']['class'] = ':'.join(get_regex_res(diff_fix,'^---.+ESTest',4))
    if len(d['fix']['tests']) == 0:
        d['fix']['tests']='-'
    if len(d['bug']['tests']) == 0:
        d['bug']['tests'] = '-'
    return d



def get_regex_res(string_search, pattern,cut=0):
    tmp = re.compile(r'{}'.format(pattern)).search(string_search)
    arr = []
    if tmp is not None:
        for tuple in tmp.regs:
            arr.append(string_search[tuple[0]:tuple[1]])
    if cut == 0:
        return arr
    else:
        arr = [x[cut:] for x in arr]
    if len(arr) == 0 :
        return ['-']
    return arr


def diff_function(file_one, file_two):
    '''
    This is very inefficient, especially for large files !!! FIX IT !!!
    :return:
    '''
    doc2 = open(file_two, 'r')
    doc1 = open(file_one, 'r')

    f2 = [x for x in doc2.readlines()]
    f1 = [x for x in doc1.readlines()]

    f1 = [x for x in f1 if str(x).startswith('\tat') is False]
    f2 = [x for x in f2 if str(x).startswith('\tat') is False]

    diff1 = [line for line in f1 if line not in f2]  # lines present only in f1
    diff2 = [line for line in f2 if line not in f1]  # lines present only in f2



    if len(diff1) == 0:
        diff1 = '-'
    else:
        diff1 = '\n'.join(diff1)
        diff1 = diff1.replace(',', '|')
    if len(diff2) == 0:
        diff2 = '-'
    else:
        diff2 = '\n'.join(diff2)
        diff2 = diff2.replace(',', '|')
    doc2.close()
    doc1.close()

    return diff1, diff2



def read_scope_test_gen(out_dir):
    '''
    read the scope that the test was generted in the out dir loging dir scope.txt
    '''
    lines = None
    if os.path.isfile('{}/loging/scope.txt'.format(out_dir)):
        with open('{}/loging/scope.txt'.format(out_dir), 'r+') as f:
            lines = f.readlines()
            lines = lines[0]
    if lines[-1]=='\n':
        lines=lines[:-1]
    return lines

def group_by_MVN(csv_path='/home/ise/eran/eran_D4j/results/smart/all_df_merg.csv'):

    out = '/'.join(str(csv_path).split('/')[:-2])
    df1 = pd.read_csv(csv_path,index_col=0)
    df2 = pd.read_csv('/home/ise/eran/eran_D4j/results/map/all_df_merg.csv',index_col=0)
    df = pd.concat([df1,df2])
    print list(df)
    df.drop(['buggy_class_err','buggy_class_fail','fix_class_err','time_budget','fix_class_fail','name','fix_err','buggy_err'], axis=1, inplace=True)

    df['GROUP_fix_fail'] = df.groupby(['project','bug_ID'])['fix_fail'].transform('sum')
    df['GROUP_buggy_fail'] = df.groupby([ 'project', 'bug_ID'])['buggy_fail'].transform('sum')
    df.drop(['buggy_fail','fix_fail'], axis=1, inplace=True)
    df.drop_duplicates(inplace=True)

    #df.to_csv('{}/grouped.csv'.format(out))
    df = df.loc[df['GROUP_fix_fail'] == 0]
    df  = df.loc[df['GROUP_buggy_fail'] == 0]

    df.to_csv('{}/un_killable_LANG_ID.csv'.format(out))


def group_by_unkillabe(p_name='Math'):
    csv_path = '/home/ise/eran/out_csvs_D4j/project/{0}/{0}_GroupBy.csv'.format(p_name)
    out = '/'.join(csv_path.split('/')[:-1])
    out ='/home/ise/Desktop/rui_folder'
    df = pd.read_csv(csv_path,index_col=0)
    print list(df)

    df_bug_ID_scop_unkillabe = df[['bug_id','project_id','rep_avg','time_budget']]
    df_bug_ID_scop_unkillabe['sum_GROUP'] = df_bug_ID_scop_unkillabe.groupby(['bug_id', 'project_id'])['rep_avg'].transform('sum')
    df_bug_ID_scop_unkillabe['MAX_search_time'] = df_bug_ID_scop_unkillabe.groupby(['bug_id', 'project_id'])['time_budget'].transform('max')
    df_bug_ID_scop_unkillabe = df_bug_ID_scop_unkillabe.loc[df_bug_ID_scop_unkillabe['sum_GROUP']==0]
    df_bug_ID_scop_unkillabe.drop(['time_budget','sum_GROUP','rep_avg'], axis=1, inplace=True)

    df_bug_ID_scop_unkillabe.drop_duplicates(inplace=True)
    df_bug_ID_scop_unkillabe.to_csv('{}/{}_unkillable_ID'.format(out,p_name))




def replication_experiment(csv_path):
    '''
    package vs target, allocate number of rep to each scope
    :param csv_path:
    :return:
    '''
    pass


def get_iteration_id(test_dir):
    out_file_l = pt.walk_rec(test_dir, [], 'bug_detection',lv=-2)
    ##print out_file_l
    if len(out_file_l) == 1:
        out_file = out_file_l[0]
    else:
        return None
    df_tmp = pd.read_csv(out_file)
    if len(df_tmp)>0:
        it = df_tmp.iloc[0]['test_id']
        if try_to_cast(it):
            return it
        else:
            return None
    else:
        return None
    return it

def try_to_cast(s):
    try:
        i = int(s)
    except ValueError as verr:
        print "err::",s
        return False
    except Exception as ex:
        print "err::",s
        return False
    return True

def get_Test_name_fail_Junit(path_dir_root,debug=False, retrun_df= False):
    '''
    this function list all class name package that triggerd the bug using the Test_P_ dir parsing the junit file,
    extract the class name
    :param path_dir_root: root dir
    :param debug:
    :return: CSV file in the root father dir, clean version filter only the bugs that detected
    '''
    out = '/'.join(str(path_dir_root).split('/')[:-1])
    bug_dirs_Test = pt.walk_rec(path_dir_root,[],'Test_P_',False,lv=-6)
    list_d=[]
    set_project = set()
    for dir_i in bug_dirs_Test:
        if debug:
            print "--- {}".format(dir_i)
        bug_root_dir = '/'.join(str(dir_i).split('/')[:-2])
        time_budget= str(dir_i).split('/')[-2].split('=')[1]
        bug_id = str(bug_root_dir).split('/')[-1].split('_')[3]
        project_id = str(bug_root_dir).split('/')[-1].split('_')[1]

        father_dir = get_father_dir_by_prefix(dir_i)

        it_id = get_iteration_id(dir_i)
        if it_id is None:
            continue
        set_project.add(project_id)
        d_diff_results = get_deff(dir_i)
        d = {'project': project_id, 'bug_ID': bug_id, 'time_budget': time_budget}
        if len(d_diff_results)>0:
            try:
                buggy_test_case = str(d_diff_results['bug']['class']).split(':')
                fixed_test_case = d_diff_results['fix']['class'].split(':')
            except Exception as e:
                print "Exception --> error :: {0}".format(e.message)
                print d_diff_results
                continue
            buggy_test_case = [x for x in buggy_test_case if x != '-']
            fixed_test_case = [x for x in fixed_test_case if x != '-']
            for klass in buggy_test_case:
                list_d.append({'project': project_id, 'father_dir':father_dir,'bug_ID': bug_id, 'time_budget': time_budget, 'iteration_id':it_id,'dir':'buggy', 'class':klass[:-7]})
            for klass in fixed_test_case :
                list_d.append({'project': project_id, 'father_dir':father_dir, 'bug_ID': bug_id, 'time_budget': time_budget, 'iteration_id':it_id,'dir':'fixed', 'class':klass[:-7]})
        else:
            list_d.append(d)
    df_faulty = get_all_faulty_comp_by_project(set_project)
    df_faulty['faulty_class'] = 1
    df = pd.DataFrame(list_d)
    #df.to_csv('{}/ALL_class_fail.csv'.format(out))
    print list(df)
    print list(df_faulty)
    df = pd.merge(df,df_faulty,on=['bug_ID','project','class'],how="left")
    df.to_csv('{}/ALL_class_fail.csv'.format(out))
    df = df.loc[df['class'].str.len() > 1]
    if retrun_df:
        return df
    df = df.loc[df['dir'] == 'buggy']
    df['faulty_class'].fillna(value=0, inplace=True)
    df.to_csv('{}/ALL_class_fail_CLEAN.csv'.format(out))
    return '{}/ALL_class_fail.csv'.format(out)

def get_father_dir_by_prefix(path,prefix='OUT_'):
    arr = str(path).split('/')
    for item in arr:
        if str(item).startswith(prefix):
            return item
    return None

def get_all_faulty_comp_by_project(list_porject_all):
    '''
    This function retrun csv file with the faulty component by defect4j dur
    :param list_porject_all: list/set of project name
    :return: DataFrame with the projects faulty component (classes)
    '''
    list_project = list(list_porject_all)
    print "list_porject_all: ",list_porject_all
    list_all=None
    for item_proj in list_project:
        if list_all is None:
            list_all = get_faulty_comp_defe4j_dir(item_proj)
        else:
            res_list_tmp = get_faulty_comp_defe4j_dir(item_proj)
            list_all.extend(res_list_tmp)
    df = pd.DataFrame(list_all)
    return df

def uniform_vs_prefect_oracle(csv_path, allocation_mode_name ='allocation_mode',name_modfiy='Math_faulty_comp.csv'):
    '''
    this function map between the uniform allocation to the prefect oracle
    '''
    out = '/'.join(str(csv_path).split('/')[:-1])
    if os.path.isfile(csv_path) is False:
        msg  = "[Error] invalid csv path -> {}".format(csv_path)
        raise Exception(msg)
    if csv_path.split('.')[-1] == 'tsv':
        df = pd.read_csv(csv_path, sep='\t')
    else:
        df = pd.read_csv(csv_path)
    #clean all the FP rows
    df = df[df[allocation_mode_name] != 'FP' ]

    #sum all u mode results
    df['sum_err'] = df.groupby(['bug_ID','time_budget'])['binary_bug_err'].transform('sum')
    df['sum_fail'] = df.groupby(['bug_ID', 'time_budget'])['binary_bug_fail'].transform('sum')
    ####
    arr_time_budget =  df['time_budget'].unique()
    print arr_time_budget
    arr_time_budget = sorted(arr_time_budget)
    print arr_time_budget
    df['rec_package_size'] = df.groupby(['bug_ID','time_budget'])['bug_ID'].transform('count')
    df.sort_values("bug_ID", inplace=True)
    df.to_csv("{}/df_uniform.csv".format(out),sep=';')
    print "df_uniform",len(df)
    #df['package'] = 'org.' + df['package'].astype(str)
    df['package'] = df['CUT'].map(lambda a: '.'.join(str(a).split('.')[:-1]))
    df_modify = pd.read_csv("{}/{}".format(out,name_modfiy), index_col=0)
    col_list = list(df_modify)
    col_list.remove('CUT')
    df_tmp = df_modify[col_list]
    df = pd.merge(df, df_tmp, on=['package', 'bug_ID'], how='left')
    df['rec_package_size'] = df.groupby(['bug_ID','time_budget'])['bug_ID'].transform('count')
    df.drop_duplicates(inplace=True)
    df = df.fillna({'faulty': 0})
    df.rename(columns={'faulty': 'faulty_package'}, inplace=True)
    df = df[df['faulty_package'] > 0 ]

    df['only_package_size'] = df.groupby(['bug_ID','time_budget'])['bug_ID'].transform('count')
    df['package_err'] = df.groupby(['bug_ID','time_budget'])['err'].transform('sum')
    df['package_fail'] = df.groupby(['bug_ID', 'time_budget'])['fail'].transform('sum')
    df.sort_values("bug_ID", inplace=True)
    df.to_csv("{}/df_middle.csv".format(out), sep=';')
    print "df_middle", len(df)
    del df_modify['package']
    df_merge = pd.merge(df, df_modify, on=['CUT', 'bug_ID'],how='left')
    df_merge.drop_duplicates(inplace=True,)
    df_merge = df_merge.fillna({'faulty': 0})

    df_merge['faulty_comp'] = df_merge.groupby(['bug_ID','time_budget'])['faulty'].transform('sum')

    df_merge.to_csv("{}/df_merge.csv".format(out),sep=';')
    print "df_merge", len(df_merge)
    #df_merge['only_package_size'] = df_merge.groupby(['bug_ID','time_budget'])['bug_ID'].transform('count')
    df_merge['prefect_eq_oracle']=df_merge['time_budget']*df_merge['only_package_size']/df_merge['faulty_comp']
    df_merge.sort_values("bug_ID", inplace=True)
    df_merge.to_csv("{}/df_merge_clean.csv".format(out),sep=';')
    df_merge =df_merge[df_merge['faulty']==1]
    df_merge.to_csv("{}/only_faulty.csv".format(out), sep=';')
    print "df_merge_clean", len(df_merge)
    df_q_deep  = df_merge.copy(deep=True)
    df_merge['nearest_value'] = df_merge.apply(my_test2,time_budget_arr=arr_time_budget,out=out, df=df_q_deep,axis=1)

    df_merge['orcale_acutalle_time_budget'] = df_merge.apply(my_test1, time_budget_arr=arr_time_budget, out=out, df=df_q_deep, axis=1)

    df_merge = df_merge[df_merge['nearest_value'] >=0 ]

    df_merge['uniform_budget']= df_merge['time_budget']

    df_merge['binary_nearest_value'] = df_merge['nearest_value'].apply(lambda x: 1 if x > 0 else 0)

    df_merge['sum_fail_binary'] = df_merge['sum_fail'].apply(lambda x: 1 if x > 0 else 0)

    df_merge['oracle_%_time_budget'] = df_merge['orcale_acutalle_time_budget']/df_merge['prefect_eq_oracle'] * 100

    df_merge.to_csv("{}/test.csv".format(out), sep=';')



def merge_oracle_out(p_name='Chart',Debug=True):
    dir_csvs = pt.mkdir_system('/home/ise/eran/D4j','csv_dir',False)
    csv_out = '/home/ise/eran/D4j/out/{}__out.csv'.format(p_name)
    csv_oracle= '/home/ise/eran/D4j/oracle/{}__oracle.csv'.format(p_name)
    csv_oracle_dir = '/'.join(str(csv_oracle).split('/')[:-1])
    # Read the DataFrame
    get_fualty_components('/home/ise/eran/D4j/out',out_dir_path=dir_csvs)
    oracle_dir = '/'.join(str(csv_oracle).split('/')[:-1])
    get_df_size_actual_out('{}/log_generated_tests'.format(oracle_dir),out_dir_path=dir_csvs)
    oracle_dir_log_csv = '{}/log.csv'.format(oracle_dir)
    df_oracle = pd.read_csv(csv_oracle,index_col=0)
    df_out = pd.read_csv(csv_out,index_col=0)
    log_oracle = pd.read_csv(oracle_dir_log_csv,index_col=0)
    df_acutal_size = pd.read_csv('{}/actual_size.csv'.format(dir_csvs),index_col=0)
    df_faulty_info = pd.read_csv('{}/faulty_info.csv'.format(dir_csvs),index_col=0)
    df_faulty_info.drop(['classes'], axis=1, inplace=True)



    # Filter the data frame by project id name
    df_acutal_size = df_acutal_size[df_acutal_size['project_id']==p_name]
    df_oracle = df_oracle[df_oracle['project_id'] == p_name]
    df_out = df_out[df_out['project_id'] == p_name]
    log_oracle = log_oracle[log_oracle['project'] == p_name]

    # i
    df_oracle_out = pd.concat([df_oracle,df_out])
    df_oracle_out = pd.merge(df_oracle_out ,df_acutal_size,on=['bug_id','project_id','test_id'],how='inner')
    df_oracle_out = pd.merge(df_faulty_info ,df_oracle_out,on=['bug_id','project_id','scope'],how='inner')
    if Debug:
        print "df_oracle_out Befor clean Nan in [kill_binary] size: {}".format(len(df_oracle_out ))
    df_oracle_out = df_oracle_out[np.isfinite(df_oracle_out['kill_binary'])]
    if Debug:
        print "df_oracle_out After clean Nan in [kill_binary] size: {}".format(len(df_oracle_out ))
    df_oracle_out.to_csv('{}/DF_{}.csv'.format(dir_csvs,p_name))
    #TODO: clean all the empty rows wihtout using inner in the merge process
    second_pahse_merge_oracle_out(df_oracle_out,p_name,dir_csvs)



def get_df_DF_by_project_name(p_path='/home/ise/eran/out_csvs_D4j',p_name='Time'):
    res_list_df = pt.walk_rec(p_path,[],'DF_{}'.format(p_name))
    out_dir = pt.mkdir_system('/home/ise/eran/out_csvs_D4j/project',p_name,True)
    list_df = []
    print res_list_df
    for csv_path in res_list_df:
        df = pd.read_csv(csv_path,index_col=0)
        list_df.append(df)
    df_oracle_out = pd.concat(list_df)
    df_oracle_out.to_csv('{}/concat_{}.csv'.format(out_dir, p_name))
    df_oracle_out = df_oracle_out.reset_index(drop=True)
    second_pahse_merge_oracle_out(df_oracle_out,p_name,out_dir)



def second_pahse_merge_oracle_out(df_oracle_out,p_name,dir_out):
    df_oracle_out = get_avg_csv_file(df_oracle_out)


    df_oracle_out.loc[df_oracle_out['scope'] == 'target', 'actual_size'] = df_oracle_out['size_scope']
    df_oracle_out['time_generating_tests'] = df_oracle_out['actual_size'] * df_oracle_out['time_budget']



    df_oracle_out.to_csv('{}/{}_GroupBy.csv'.format(dir_out,p_name))
    pivot_groupby('{}/{}_GroupBy.csv'.format(dir_out,p_name),scope='package_only')
    pivot_groupby('{}/{}_GroupBy.csv'.format(dir_out, p_name),scope='target')
    list_rep = list(df_oracle_out)
    list_rep = [x for x in list_rep if str(x).__contains__('rep_')]

    df_oracle_out_target = df_oracle_out[df_oracle_out['scope'] == 'target']
    df_oracle_out_not_target = df_oracle_out[df_oracle_out['scope'] != 'target']
    #df_oracle_out_target.to_csv('{}/target.csv'.format(dir_csvs))
    #df_oracle_out_not_target.to_csv('{}/not_target.csv'.format(dir_csvs))
    df_oracle_out_target['package_info'] = df_oracle_out_target.apply(lambda row: make_comparison(row,df_oracle_out_not_target),axis=1)
    df_oracle_out_target['package_total_time_gen'] = df_oracle_out_target['package_info'].apply(lambda x: str(x).split('|')[-1])
    df_oracle_out_target['package_time_budget'] = df_oracle_out_target['package_info'].apply(lambda x: str(x).split('|')[-2])
    df_oracle_out_target['package_kill'] = df_oracle_out_target['package_info'].apply(lambda x : '|'.join(str(x).split('|')[:-2]))
    for col in list_rep:
        df_oracle_out_target["package_{}".format(col)] = df_oracle_out_target['package_kill'].apply(lambda val: split_info(val=val,col_name=col))


    df_oracle_out_target.drop('package_info', axis=1, inplace=True)
    df_oracle_out_target.drop('package_kill', axis=1, inplace=True)

    df_oracle_out_target.to_csv('{}/{}_res.csv'.format(dir_out, p_name))
    #df_oracle_out_target['vaild_comparison'] = df_oracle_out_target.apply(lambda x : 0 if x['package_total_time_gen'] > x['time_generating_tests'] else 1)
    #df_oracle_out_target.to_csv('{}/{}_res.csv'.format(dir_out,p_name))
    print "\n\n\n----DONE----\n\n\n"

def split_info(val,col_name):
    arr = str(val).split('|')
    for x in arr:
        split_info_val = str(x).split('-')
        if col_name == split_info_val[0]:
            return split_info_val[1]
    return 'err'


def make_comparison(row_target,df_not_target):
    total_time = row_target['time_generating_tests']
    bug_id = row_target['bug_id']
    df_filter = df_not_target.loc[df_not_target['bug_id'] == bug_id]
    # df_filter = df_not_target[df_not_target['bug_id']==bug_id]
    df = df_filter[df_filter['time_generating_tests'] <= total_time ]
    if len(df) == 0 :
        df = df_filter[df_filter['time_generating_tests'] >= total_time]
        if len(df) == 0:
            return '{}|{}|{}'.format(None, None, None)
        val = df['time_generating_tests'].argmin()
    else:
        val = df['time_generating_tests'].argmax()
    list_rep = list(df)
    list_rep = [x for x in list_rep if str(x).__contains__('rep_')]
    res_kill = []
    for col in list_rep:
        res_kill.append("{}-{}".format(col,df.loc[val][col]) )
    kill = '|'.join(res_kill)
    time = df.loc[val]['time_budget']
    total = df.loc[val]['time_generating_tests']
    return "{}|{}|{}".format(kill,time,total)

def get_fualty_components(path_dir,out_dir_path):
    son_dir = '/'.join(str(path_dir).split('/')[:-1])
    dirs_list = pt.walk_rec(path_dir,[],'fault_components',False,lv=-3)
    d_list=[]
    for dir_i in dirs_list:
        father_dir = '/'.join(str(dir_i).split('/')[:-1])
        scope_i = read_scope_test_gen(father_dir)
        project_id = str(dir_i).split('/')[-2].split('_')[1]
        list_files = pt.walk_rec(dir_i,[],'.txt')
        for file_i in list_files:
            name = str(file_i).split('/')[-1][:-4]
            bug_id = str(name).split('_')[1]
            if True is False:
                continue
            else:
                classes_list = []
                with open(file_i,'r+') as f:
                    for line in f:
                        line = str(line).replace('\n','')
                        classes_list.append(line)
                if name.__contains__('bug'):
                    d_list.append({'bug_id':bug_id,'project_id':project_id,'size_scope':len(classes_list),'classes':'-'.join(classes_list),'scope':'target'})
                else:
                    d_list.append({'bug_id': bug_id, 'project_id': project_id,'size_scope':len(classes_list), 'classes': '-'.join(classes_list), 'scope': scope_i})
    df = pd.DataFrame(d_list)

    df.drop_duplicates(inplace=True)

    df.to_csv('{}/faulty_info.csv'.format(out_dir_path))


def get_df_size_actual_out(p_dir_path='/home/ise/D4j/oracle/log_generated_tests',out_dir_path='/home/ise/D4j'):
    '''
    this function crate a acutal size generated test
    :param p_dir_path:
    :return:
    '''
    list_dico=[]
    if os.path.isdir(p_dir_path):
        res_files = pt.walk_rec(p_dir_path,[],'.log')

        for file_i in res_files:
            name = str(file_i).split('/')[-1]
            project_id = str(name).split('_')[0]
            bug_id = str(name).split('_')[1]
            iter_id = str(name).split('_')[2][:-4]
            size_lines = -1
            with open(file_i,'r+') as f_file:
                lines = f_file.readlines()
                lines = list(set(lines))
                size_lines = len(lines)
            list_dico.append({'project_id':project_id, 'bug_id':bug_id, 'test_id':iter_id, 'actual_size':size_lines})
    if len(list_dico) > 0 :
        df = pd.DataFrame(list_dico)
        out_dir = '/'.join(str(p_dir_path).split('/')[:-1])
        df.to_csv('{}/actual_size.csv'.format(out_dir_path))
    else:
        print "[Error] no file to process found in the given path : {}".format(p_dir_path)


def get_avg_csv_file(df=None,path_csv_file='/home/ise/eran/out_csvs_D4j/smart/csv_dir/DF_Mockito.csv'):
    import random
    if df is None:
        df = pd.read_csv(path_csv_file, index_col=0)
    #path_csv_file = '/home/ise/eran/D4j/csv_dir/DF_Chart.csv'
    #namnew_col = "kill_rep_{}".format(rep)
    #if rep < 1 :
    #    print "rep must be grater then 1 : rep={}".format(rep)
    #    return None
    #df = pd.read_csv(path_csv_file,index_col=0)
    #df.to_csv('{}/orginal_df.csv'.format('/home/ise/eran'))
    #list_uniqe = df['test_id'].unique()
    #if rep > len(list_uniqe):
    #    print "[msg] rep was grater then the unique val rep equle now to max "
    #    rep = len(list_uniqe)
    #group_of_items = list_uniqe  # a sequence or set will work here.
    #num_to_select = rep  # set the number to select here.
    #list_of_random_items = random.sample(group_of_items, num_to_select)
    #print list_of_random_items
    ky_name_col = ['bug_id','project_id','scope','size_scope','gen_mode','time_budget','actual_size']
    df= df[['bug_id','project_id','scope','size_scope','gen_mode','kill_binary','time_budget','actual_size']]
    df_copy = df.copy(deep=True)
    df_copy.to_csv('{}/df_copy.csv'.format('/home/ise/eran'))
    df['sum'] = df_copy.groupby(ky_name_col).transform('sum')
    df['count'] = df_copy.groupby(ky_name_col).transform('count')
    df.drop_duplicates(inplace=True)
    list_occur = df['count'].unique()
    list_occur = [int(x) for x in list_occur ]
    max_occur = max(list_occur)+1
    print "MAX X =",max_occur-1
    for x in range(1,max_occur):
        print '-' * 100
        print "rep_{}".format(x)
        print '-'*100
        df["rep_{}".format(x)] = df.apply(lambda row_i : make_rep(row=row_i,val=x),axis=1)
    df["rep_avg".format(x)] = df.apply(lambda row_i: make_rep(row=row_i, val='avg'), axis=1)
    return df




def apply_avg_func(row,list_df,list_col):
    for col in list_col:
        for df_i in list_df:
            df_i.loc[df_i[col] == row[col]]
    list_kill=[]
    for df_i in list_df:
        if len(df_i)==0:
            continue
        print "df_i: ",len(df_i)
        list_kill.append(df_i['kill_binary'])
    res_kill=0
    for kill in list_kill:
        res_kill+=kill
    if res_kill>0:
        return 1
    return 0

def binary_kill(row,fix_col='fixed_test_case_fail (diff)',buggy_col='buggy_test_case_fail (diff)'):
    if row[fix_col] == '':
        fix=0
    else:
        fix=1
    if row[buggy_col]=='':
        buggy=0
    else:
        buggy=1
    if buggy==1 and fix==0:
        return 1
    else:
        return 0


def my_test1(row,time_budget_arr,df,out):
    id = row['bug_ID']
    oracle_budet = row['prefect_eq_oracle']
    time_uni = row['time_budget']
    tar=-1
    for time in time_budget_arr:

        if time - oracle_budet == 0:
            tar=time
            break
        elif time - oracle_budet < 0 :
            tar = time
        elif time-oracle_budet > 0:
            break
    return tar


def my_test2(row,time_budget_arr,df,out):
    id = row['bug_ID']
    oracle_budet = row['prefect_eq_oracle']
    time_uni = row['time_budget']
    tar=-1
    for time in time_budget_arr:
        if time - oracle_budet == 0:
            tar=time
            break
        elif time - oracle_budet < 0 :
            tar = time
        elif time-oracle_budet > 0:
            break
    df_cut = df[df['bug_ID'] == id]
    df_cut = df_cut[df_cut['time_budget'] == tar]
    if len(df_cut)>0:
        arr_time_budget = df_cut['sum_fail'].unique()
        arr_time_budget = list(set(arr_time_budget))
        if len(arr_time_budget)!=1:
            raise Exception('error in my test_2')
        arr_time_budget = arr_time_budget[0]
    else:
        if tar > 0:
            print "time={} id={}".format(tar,id)
        arr_time_budget=-1
    return arr_time_budget

def get_package_csv(root_dir):
    '''
    this function take a dir and count the evosuite class generate and the faulty class put put this info to csv
    :param root_dir:
    :return:
    '''
    list_of_d=[]
    dirs_bug_id = pt.walk_rec(root_dir,[],'P_',lv=-1,file_t=False)
    for dir in dirs_bug_id:
        name = str(dir).split('/')[-1]
        bug_id = name.split('_')[3]
        proj_name = name.split('_')[1]
        size_of_package = 0
        size_of_faulty = 0
        if os.path.isdir("{}/Evo_Test".format(dir)):
            num_log_test = pt.walk_rec("{}/Evo_Test".format(dir),[],'.txt')
            size_of_package=len(num_log_test)-1
        else:
            size_of_package=-1
        if os.path.isfile("{}/log/bug_classes.txt".format(dir)):
            with open("{}/log/bug_classes.txt".format(dir),'r') as f:
                lines = f.readlines()
                ctr=0
                for line in lines:
                    if str(line).__contains__('org'):
                        ctr=ctr+1
            size_of_faulty=ctr
        else:
            size_of_faulty=-1
        list_of_d.append({'bug_id':bug_id,'project':proj_name,'size_package':size_of_package,'size_faulty':size_of_faulty})
    out = '/'.join(str(root_dir).split('/')[:-1])
    df=pd.DataFrame(list_of_d)
    df.to_csv("{}/info_pakage.csv".format(out))


def pivot_groupby(csv_path='/home/ise/eran/out_csvs_D4j/project/Math/Math_GroupBy.csv',avg=True,scope='package_only'):
    out_dir = '/'.join(str(csv_path).split('/')[:-1])
    df = pd.read_csv(csv_path,index_col=0)
    all_rep_col = list(df)
    all_rep_col = [x for x in all_rep_col if str(x).__contains__('rep_')]
    table = None
    df_rep=[]
    df = df[df['scope']==scope]
    for col in all_rep_col:
        if avg:
            table_i = pd.pivot_table(df, values=col, index=['bug_id'],columns = ['time_budget'], aggfunc = np.average)
        else:
            table_i = pd.pivot_table(df, values=col, index=['bug_id'], columns=['time_budget'], aggfunc=np.sum)
        #table_i["{}_Total".format(col)] = table_i.sum(axis=1)
        #table_i.to_csv('{}/table_{}.csv'.format(out_dir,col))
        df_rep.append(table_i)
        if table is None:
            if avg:
                table_i["{}_Total".format(col)]=table_i.mean(axis=1)
            else:
                table_i["{}_Total".format(col)] = table_i.sum(axis=1)
            table=table_i[["{}_Total".format(col)]].copy()
        else:
            if avg:
                table["{}_Total".format(col)] = table_i.mean(axis=1)
            else:
                table["{}_Total".format(col)]=table_i.sum(axis=1)
    if avg:
        table.to_csv('{}/table_pivot_{}_AVG.csv'.format(out_dir,scope))
    else:
        table.to_csv('{}/table_pivot_{}_SUM.csv'.format(out_dir,scope))

'''
need to go over all the bug ID and extract the fault class and all its package class
'''
import sys

def wrapper():
    get_df_DF_by_project_name(p_name='Time')
    get_df_DF_by_project_name(p_name='Chart')
    get_df_DF_by_project_name(p_name='Closure')
    get_df_DF_by_project_name(p_name='Lang')
    get_df_DF_by_project_name(p_name='Math')
    get_df_DF_by_project_name(p_name='Mockito')

def unkillable():
    group_by_unkillabe('Time')
    group_by_unkillabe('Chart')
    group_by_unkillabe('Closure')
    group_by_unkillabe('Lang')
    group_by_unkillabe('Math')
    group_by_unkillabe('Mockito')

def parser():
    args = sys.argv
    if len(args) == 1:
        print "---- no args -----"
        exit()
    if args[1]=='fail_test':
        get_Test_name_fail_Junit(args[2])
    exit()


def mvn_get_test_fail(csv_p):
    out = '/'.join(str(csv_p).split('/')[:-1])
    dico=[]
    df=pd.read_csv(csv_p,index_col=0)
    print list(df)
    df = df.loc[df['fix_fail']==0]
    df.apply(itrate_rows,dico_l=dico,axis=1)
    df_res = pd.DataFrame(dico)
    list_project = list(df_res['project'].unique())
    df_fault = get_all_faulty_comp_by_project(list_project)
    df_fault['is_faulty']=1
    df_fault.to_csv('{}/tmper.csv'.format(out))
    print list(df_fault)
    print list(df_res)
    df_res.to_csv("{}/fail_class.csv".format(out))
    df_fault['bug_ID'] = df_fault['bug_ID'].astype(int)
    df_res = pd.merge(df_res, df_fault, on=['bug_ID', 'project', 'class'], how="left")
    df_res['is_faulty']=df_res['is_faulty'].fillna(0)
    #df_res['is_faulty'] = df_res.apply(merge_by_row,df=df_fault,axis=1)
    df_res = df_res.loc[df_res['dir'] == 'buggy']
    df_res = df_res.loc[df_res['class'].str.len() > 2]
    df_res.drop_duplicates(inplace=True)
    df_res.to_csv("{}/fail_class_CLEAN.csv".format(out))

def merge_by_row(row,df):
    bug_id = row['bug_ID']
    test_class = row['class']
    project_id = row['project']
    df_filter = df.loc[df['project'] == project_id]
    df_filter = df_filter.loc[df_filter['bug_ID'] == bug_id]
    list_klass = df_filter['class'].tolist()
    if test_class in list_klass:
        return 1
    return 0

def itrate_rows(row,dico_l):
    bug_id = row['bug_ID']
    test_class = row['name']
    project_id = row['project']
    time_b = row['time_budget']
    list_fail_buggy = row['buggy_class_fail']
    list_fail_fix = row['fix_class_fail']
    for item in str(list_fail_buggy)[1:-1].split(','):
        item  = str(item).replace("'",'').split('_')[0].replace(' ','')
        dico_l.append({'bug_ID':bug_id, 'dir':'buggy','project':project_id, 'time_budget':time_b, 'TEST_NAME':test_class, 'class':item})
    for item in str(list_fail_fix)[1:-1].split(','):
        dico_l.append(
            {'bug_ID': bug_id, 'dir': 'fixed', 'project': project_id, 'time_budget': time_b, 'TEST_NAME': test_class,
             'class': item})



def util(p_name='Closure',time_b=60):
    '''

    :param p_name:
    :param time_b:
    :return:
    '''
    print "-"*30,p_name,"-"*30
    out = '/home/ise/eran/out_csvs_D4j/rep_exp'
    df = pd.read_csv('/home/ise/eran/out_csvs_D4j/rep_exp/all.csv',index_col=0)
    print "df_size = {}".format(len(df))
    print "cols: {}".format(list(df))
    df = df.loc[df['project']==p_name]
    print df['time_budget'].value_counts()
    #df['time_budget'] = df['time_budget'].apply(lambda val : time_b if val > time_b-11 and val < time_b + 11 else val)
    #df['time_budget'] = df['time_budget'].apply(lambda val: time_b if val == 120 else val)
    print df['time_budget'].value_counts()
    df['sum_detected']= df.groupby(['bug_ID', 'time_budget','project','TEST'])['detected_bug'].transform('sum')
    df['count_detected'] = df.groupby(['bug_ID', 'time_budget', 'project', 'TEST'])['detected_bug'].transform('count')
    df.drop('father_dir', axis=1, inplace=True)
    df.drop('iteration_id', axis=1, inplace=True)
    df.drop('detected_bug', axis=1, inplace=True)
    df = df.loc[df['time_budget']==time_b]
    df = df.sort_values(by=['TEST'])
    df.drop_duplicates(inplace=True)
    df.to_csv("{}/df_grouped_{}.csv".format(out,p_name))

    print len(df)
    exit()



def get_size_classes_csv(id, p_name,out_csv_path,tmp_dir='/tmp',root_d4j ='/home/ise/programs/defects4j/framework/bin/defects4j'):
    '''
    get the LOC size of each class (src file) in the current bug project (the commit)
    :param id: the bug id
    :param p_name: the project name
    :param out_csv_path: where to write the csv file (dir path)
    :param tmp_dir: for tmp files
    :param root_d4j: the root dir for the Defect4J framework
    :return: None
    '''
    out_fix = pt.mkdir_system(tmp_dir, 'Defects4j_{}_{}'.format(p_name,id))
    str_command = root_d4j + ' checkout -p {1} -v {0}"f" -w {2}/'.format(id, p_name, out_fix)
    print '[OS] {}'.format(str_command)
    os.system(str_command)
    java_class = pt.walk_rec(out_fix, [], '.java')
    inf_classes = []
    size_loc=-1
    start_package = 'org'
    if p_name == 'Closure':
        start_package = 'com'
    for item in java_class:
        if item[-5:] != '.java':
            continue
        try:
            pack = pt.path_to_package(start_package, item, -1 * len('.java'))
        except Exception as e:
            pack=None
        if pack is None:
            continue
        size_loc = get_LOC(item)
        inf_classes.append({'project':p_name,'bug_ID':id,'path':item, 'name':pack, 'LOC':size_loc})
    df = pd.DataFrame(inf_classes)
    df.to_csv("{}/LOC_{}_{}.csv".format(out_csv_path, p_name,id))




def get_LOC(class_path):
    '''
    given class path (src) retrun the size of the line of code
    :param class_path: path to class file
    :return: int, size LOC
    '''
    if os.path.isfile(class_path) is False:
        return None
    bash_command = 'loc {}'.format(class_path)
    print "[OS] {}".format(bash_command)
    process = Popen(shlex.split(bash_command), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print "[std_err] {}".format(stderr)
    last_line = str(stdout).split('\n')[-3]
    size_loc=''
    index=-1
    while(last_line[index] != ' '):
        size_loc=last_line[index] + size_loc
        index=index-1
    #print "size_loc: {}".format(size_loc)
    try:
        size = int(size_loc)
    except Exception as e:
        print '[Error] Exception as been ocuur while trying to conver {} to an int, in the function get_LOC'.format(size)
        size = None
    return size


def get_bug_ID_contains_FP(p_name='Lang'):
    '''
    get the bug_ID that has FP and FP_Gen values
    '''
    print "Project Name : {}".format(p_name)
    csv_path = '/home/ise/tmp_d4j/out/raw_data/{}.csv'.format(p_name)
    df = pd.read_csv(csv_path, index_col=0)
    if 'no_fp' in df['FP'].values:
        df.loc[df['FP'] == 'no_fp', 'FP'] = None
    print "Size_Before:\t",len(df)
    df_filter = df.dropna(subset=['FP'])                      # TODO: maybe add the Gen_FP
    print "Size_After:\t",len(df_filter )
    id_list_bug = df_filter['bug_ID'].unique()
    filter_coluoms_by_bug_ID(list(id_list_bug ),p_name)
    with open('/home/ise/tmp_d4j/out/id_has_FP/{}_BUG_FP.txt'.format(p_name),'w') as f:
        for item in id_list_bug:
            item = str(item).replace('\n','')
            f.write("{}\n".format(item))
    print id_list_bug



def filter_coluoms_by_bug_ID(bug_ids,p_name='Lang'):
    path_csv = '{}/{}_tmp.csv'.format('/home/ise/tmp_d4j/out/result', p_name)
    df = pd.read_csv(path_csv)
    print len(df)
    df = df.loc[df['bug_ID'].isin(bug_ids)]
    print len(df)
    df.to_csv('{}/{}_FP_tmp.csv'.format('/home/ise/tmp_d4j/out/result_only_fp/', p_name))



def frange(x, y, jump):
  while x < y:
    yield x
    x += jump

def rep_exp_new(p_name='Lang',rep=4,item=2,heuristic_method=True,pre_gen=True):
    gamma_arr=[]
    list_d_ranking = []
    intreval = 0.05
    for num_val in frange(0,1+intreval,intreval):
        gamma_arr.append(num_val)
    gamma_arr=[1,0]
    d_list_res = []
    if heuristic_method:
        import heuristic
        d_heuristic_res = heuristic.csv_to_dict(p_name,False)
    csv_path = '/home/ise/tmp_d4j/out/raw_data/{}.csv'.format(p_name)
    df = pd.read_csv(csv_path, index_col=0)
    max_all_rep = df['count_detected'].max()
    print 'max_rep', df['count_detected'].max()
    print 'min_rep', df['count_detected'].min()
    max_rep = df['count_detected'].max()
    x =  df['count_detected'].value_counts().reset_index().rename(columns={'index': 'Rep Index', 'count_detected': 'Value'})
    x.to_csv('{}/rep_frq_{}.csv'.format('/home/ise/tmp_d4j/out', p_name))
    for x in range(1, max_rep + 1):
        df['{}_rep'.format(x)] = df.apply(make_rep, val=x, count='count_detected', sum='sum_detected', axis=1)
    #df.to_csv('/home/ise/df.csv')
    print list(df)
    id_list_bug = df['bug_ID'].unique()
    for bug_i in id_list_bug[2+1:]:
        print "--- BUG {} ----".format(bug_i)
        df_filter = df.loc[df['bug_ID'] == bug_i]
        df_target = df_filter.loc[df_filter['faulty_class'] == 1]
        size_tset_suite = len(df_filter)
        size_faulty_suite = len(df_target)
        rep_target_max = df_target['count_detected'].sum()

        print "rep_target_max: {}".format(rep_target_max)
        if 'no_fp' in df_filter['FP'].values :
            df_filter.loc[df_filter['FP'] == 'no_fp', 'FP'] = None
        if 'no_fp' in df_filter['FP_genric'].values:
            df_filter.loc[df_filter['FP_genric'] == 'no_fp', 'FP_genric'] = None


        for col in ['FP','LOC_P','LOC']:
            df_filter[col] = df_filter[col].astype(float)

        # add to clean the missing value rows that have no FP value
        df_filter.dropna(subset=['FP'], how='any', inplace=True)

        # this section is mapping between the faulty component and the ranking from LOC and FP
        l_bug_i = get_ranking_bug(df_filter,bug_i)
        list_d_ranking.extend(l_bug_i)

        if pre_gen:
            for gamma in gamma_arr:
                df_filter['pre_gen_score_{}'.format(gamma)] = df_filter['FP'] * gamma + (1.0 - gamma) * df_filter['LOC_P']
                df_filter.to_csv("{}/{}.csv".format('/home/ise/tmp',bug_i))
        for item_number in range(1,item):
            for rep_i in range(1, max_all_rep + 1):
                d_pre_gen = {}
                val_random = pick_by_prop(df_filter, 'Random', rep=rep_i,item_num=item_number)
                val_fp = pick_by_prop(df_filter, 'FP', rep=rep_i, item_num=item_number)
                val_fp_gen = pick_by_prop(df_filter, 'FP_genric', rep=rep_i, item_num=item_number)
                val_loc = pick_by_prop(df_filter, 'LOC', rep=rep_i, item_num=item_number)
                val_target = pick_by_prop(df_target, 'faulty_class',rep=rep_i,item_num=item_number)
                if heuristic_method:
                    d_val_heuristic = heuristic_pick(d_heuristic_res,bug_i,df_filter,rep=rep_i,item_num=item_number)
                for gamma in gamma_arr:

                    val_post_gen = pick_by_prop(df_filter,'pre_gen_score_{}'.format(gamma),rep=rep_i,item_num=item_number)
                    d_pre_gen['pre_gen_score_{}'.format(gamma)] = val_post_gen

                d_list_res.append({'bug_ID': bug_i, 'kill_val': val_target, 'method': 'target', 'rep_sampled': rep_i,'item':item_number,
                                   'size_suite': size_tset_suite, 'size_faulty_classes': size_faulty_suite})


                d_list_res.append({'bug_ID': bug_i, 'kill_val': val_random, 'method': 'random', 'rep_sampled': rep_i,'item':item_number,
                                   'size_suite': size_tset_suite, 'size_faulty_classes': size_faulty_suite})


                d_list_res.append({'bug_ID': bug_i, 'kill_val': val_fp, 'method': 'FP', 'rep_sampled': rep_i,'item':item_number,
                                   'size_suite': size_tset_suite, 'size_faulty_classes': size_faulty_suite})

                d_list_res.append({'bug_ID': bug_i, 'kill_val': val_loc, 'method': 'LOC', 'rep_sampled': rep_i,'item':item_number,
                                   'size_suite': size_tset_suite, 'size_faulty_classes': size_faulty_suite})

                d_list_res.append({'bug_ID': bug_i, 'kill_val': val_fp_gen, 'method': 'FP_gen', 'rep_sampled': rep_i,'item':item_number,
                                   'size_suite': size_tset_suite, 'size_faulty_classes': size_faulty_suite})

                if pre_gen:
                    for ky in d_pre_gen:
                        d_list_res.append(
                            {'bug_ID': bug_i, 'kill_val': d_pre_gen[ky], 'method': ky, 'rep_sampled': rep_i,
                             'item': item_number,'size_suite': size_tset_suite, 'size_faulty_classes': size_faulty_suite})


                if heuristic_method:
                    for ky_h in d_val_heuristic:
                        d_list_res.append(
                            {'bug_ID': bug_i, 'kill_val': d_val_heuristic[ky_h], 'method': ky_h, 'rep_sampled': rep_i,
                             'item': item_number,'size_suite': size_tset_suite, 'size_faulty_classes': size_faulty_suite})

    df_res = pd.DataFrame(d_list_res)
    df_res.to_csv('{}/{}_tmp.csv'.format('/home/ise/tmp_d4j/out/result/', p_name))

    # flushing out the ranking csv
    df_rank = pd.DataFrame(list_d_ranking)
    df_rank.to_csv('{}/{}_RANK.csv'.format('/home/ise/tmp', p_name))


def clean_missing_value_row(df,col):
    df.dropna(axis=1, how='any', subset=[col], inplace=True)
    return df


def get_ranking_bug(df,bug_id,path_to_disk='/home/ise/tmp'):
    d_list=[]
    df['rank_fp'] = df['FP'].rank(ascending=False)
    df['rank_loc'] = df['LOC'].rank(ascending=False)
    size = len(df)
    fault_component_df = df.loc[df['faulty_class'] > 0 ]
    if len(fault_component_df)==0:
        d = {'bug_id':bug_id,'rank_fp':None,'rank_loc':None,'size':0}
        d_list.append(d)
        return d_list
    fp_list_rank = fault_component_df['rank_fp'].tolist()
    loc_list_rank = fault_component_df['rank_loc'].tolist()
    for i in range(len(fp_list_rank)):
        d={'bug_id':bug_id,'rank_fp':fp_list_rank[i],'rank_loc':loc_list_rank[i],'size':size}
        d_list.append(d)
    df.to_csv('{}/{}_rank.csv'.format(path_to_disk,bug_id))
    return d_list


def rep_exp(p_name='Math',rep=4):
    d_list_res=[]
    #csv_path = '/home/ise/eran/out_csvs_D4j/rep_exp/df_grouped_{}.csv'.format(p_name)
    csv_path = '/home/ise/tmp_d4j/out/{}.csv'.format(p_name)
    df = pd.read_csv(csv_path,index_col=0)
    max_all_rep = df['count_detected'].max()
    print 'max_rep',df['count_detected'].max()
    print 'min_rep',df['count_detected'].min()
    print list(df)
    for x in range(1,max_all_rep+1):
        df['{}_rep'.format(x)] = df.apply(make_rep, val=x, count='count_detected', sum='sum_detected',axis=1)
#    df.to_csv('/home/ise/eran/out_csvs_D4j/rep_exp/df.csv')
    print list(df)
    id_list_bug = df['bug_ID'].unique()
    for bug_i in id_list_bug:
        print "--- BUG {} ----".format(bug_i)
        df_filter = df.loc[df['bug_ID']==bug_i]
        df_target = df_filter.loc[df_filter['faulty_class'] == 1 ]
        size_tset_suite = len(df_filter)
        size_faulty_suite = len(df_target)
        rep_target_max = df_target['count_detected'].sum()
        print "rep_target_max: {}".format(rep_target_max )

        d_target_list = df_target[['TEST','count_detected']].to_dict('records')
        d_list_all = df_filter[['TEST','count_detected']].to_dict('records')
        dico_TEST={}
        dico_TEST_TARGET={}
        for d in d_list_all:
            dico_TEST[d['TEST']]=d['count_detected']
        for d in d_target_list:
            dico_TEST_TARGET[d['TEST']]=d['count_detected']

        for rep_i in range(1,max_all_rep+1):
            val_random = pick_choose_rep_exp(dico_TEST,df_filter,num_of_rep=rep_i)
            val_target = pick_choose_rep_exp(dico_TEST_TARGET,df_target,num_of_rep=rep_i)
            d_list_res.append({'bug_ID':bug_i, 'kill_val':val_random,'method':'random','rep_sampled':rep_i,'size_suite':size_tset_suite,'size_faulty_classes':size_faulty_suite})
            d_list_res.append({'bug_ID': bug_i, 'kill_val': val_target, 'method': 'target', 'rep_sampled': rep_i,'size_suite':size_tset_suite,'size_faulty_classes':size_faulty_suite})
    df_res = pd.DataFrame(d_list_res)
    df_res.to_csv('{}/{}.csv'.format('/home/ise/eran/out_csvs_D4j/rep_exp/out',p_name))



def heuristic_pick(d,bug_id,df_filter,rep=3,item_num=1,clean=True):
    picked=[]
    d_size={}
    suite_ctr=0
    if bug_id in d:
        for ky_a_b in d[bug_id].keys():
            for ky_date in d[bug_id][ky_a_b].keys():
                picked=[]
                for i in range(item_num):
                    if i in d[bug_id][ky_a_b][ky_date]:
                        if clean:
                            name_test = d[bug_id][ky_a_b][ky_date][i]
                            name_test = str(name_test).split('_EST')[0]
                            picked.append(name_test)
                        else:
                            picked.append(d[bug_id][ky_a_b][ky_date][i])
                print "picked:\t",picked
                df_cut = df_filter.loc[df_filter['TEST'].isin(picked)]
                size_len = len(picked)
                ky = "{}__{}".format(ky_a_b,ky_date)
                frist_ky = ky_a_b
                if frist_ky not in d_size:
                    d_size[frist_ky]={}
                if size_len not in d_size:
                    d_size[frist_ky][ky]={}
                if len(df_cut)==0:
                    d_size[frist_ky][ky] = {"val":None,'size':0}
                else:
                    val = df_cut['{}_rep'.format(rep)].sum()
                    d_size[frist_ky][ky] = {"val":val, 'size': 0}
    ans={}
    for f_key in d_size:
        dico_filter_by_max_size = filter_val_max_only(d_size[f_key])
        key_max_size = get_max_val(dico_filter_by_max_size)
        key_max_all = get_max_val(d_size[f_key])
        if d_size[f_key][key_max_all]['val'] != d_size[f_key][key_max_size]['val']:
            raise  Exception("hurstic !!!!")
        else:
            ans[str(key_max_size).split('__')[0]] = d_size[f_key][key_max_size]['val']
    return ans


def filter_max_item():
    pass

def filter_val_max_only(d):
    ky_max = get_max_val(d,'size')
    max_size = d[ky_max]['size']
    d_res = {}
    for key_i in d.keys():
        if d[key_i]['size'] == max_size:
            d_res[key_i]={"size":max_size,'val':d[key_i]['val']}
    return d_res

def get_max_val(d,key_traget='val'):
    '''
    helper for the hurstic dico
    '''
    val_max = -1
    key_val = None
    for ky_i in d.keys():
        if val_max<d[ky_i][key_traget]:
            val_max=d[ky_i][key_traget]
            key_val=ky_i
    return key_val





def pick_by_prop(df_filter,prop='FP',rep=3,item_num=1):
    df_filter = df_filter.dropna(subset=[prop])
    if len(df_filter) == 0 :
        return None
    if len(df_filter)<item_num:
        item_num=len(df_filter)
    df_filter[prop] = df_filter[prop].astype(float)
    df_cut = df_filter.nlargest(item_num, columns=[prop])
    print "{} : {}".format(prop,df_cut['TEST'])
    if len(df_cut) > item_num:
        print 'in'
        df_elements = df_cut.sample(n=item_num)
        val = df_elements['{}_rep'.format(rep)].sum()
    else:
        val = df_cut['{}_rep'.format(rep)].sum()
    return val


def pick_choose_rep_exp(d,df,num_of_rep=4):
    list_tests = []
    for ky in d:
        num = int(d[ky])
        tmp_list = [ky]*num
        list_tests.extend((tmp_list))
    if num_of_rep>len(list_tests):
        num_of_rep = len(list_tests)
    res = np.random.choice(list_tests,num_of_rep,replace=False)
    d_count = Counter(res)
    sum_kill=0.0
    for ky in d_count:
        time_rep = d_count[ky]
        filter_df = df.loc[df['TEST']==ky]
        val = filter_df['{}_rep'.format(time_rep)].sum()
        sum_kill+=val
    return sum_kill


def make_rep(row,val,count='count',sum='sum'):
    count_i = row[count]
    sum_i = row[sum]
    if val == 'avg':
        res =  float(sum_i)/float(count_i)
        return res
    if val > count_i: #################################TODO: look at this line hendel the missing value of the rep
        val=count_i
    if val <= count_i:
        Pr = float(sum_i)/float(count_i)
        res = pow((float(1)-Pr),float(val))
        res = 1 - res
        if res > 1:
            return 1
        else:
            return res
    return None


def merger(): # 1
    '''
    merge all the data from diff server into one big csv (all.csv)
    :return:
    '''
    res = pt.walk_rec('/home/ise/eran/out_csvs_D4j/rep_exp',[],'rep_raw_data.csv')
    l=[]
    for x in res:
        l.append(pd.read_csv(x,index_col=0))
    all = pd.concat(l)
    all.to_csv('/home/ise/eran/out_csvs_D4j/rep_exp/all.csv')


def add_random_probabilityes(path_dir='/home/ise/tmp_d4j/LOC/Chart',loc=False):
    if path_dir[-1]=='/':
        path_dir=path_dir[:-1]
    project=str(path_dir).split('/')[-1]
    path_out = pt.mkdir_system('/home/ise/tmp_d4j/Prob',project,False)
    csvFiles = pt.walk_rec(path_dir,[],'.csv')
    for file_csv_i in csvFiles:
        name_i = str(file_csv_i).split('/')[-1]
        df = pd.read_csv(file_csv_i,index_col=0)
        if loc:
            max_LOC = df['LOC'].max()
            min_LOC = df['LOC'].min()
            df['FP']=df['LOC'].apply(lambda x: float(x-min_LOC)/float(max_LOC-min_LOC))
        else:
            df['FP'] = np.random.random_sample(size=len(df))
        df.to_csv('{}/{}'.format(path_out,name_i))

def normalizer_col(df,target,suffix='normalize'):
    '''
    normalize colunm in dataframe
    :param df: Dataframe
    :param target: col_names (list) or name (str)
    :param suffix: suffix to add after the process to the new colunm
    :return: Dataframe
    '''
    if isinstance(target, basestring):
        target = [target]
    for col_name in target:
        max_value = df[col_name].max()
        min_value = df[col_name].min()
        df["{}_{}".format(col_name,suffix)] = (df[col_name] - min_value) / (max_value - min_value)
    return df

def get_bug_d4j_major(p_name='Mockito',fp_dir='/home/ise/tmp_d4j/out_pred/out',dir_rep_exp='/home/ise/eran/out_csvs_D4j/rep_exp',config_dir='/home/ise/tmp_d4j/config',out='/home/ise/tmp_d4j/out',major=False):
    '''
    Taking as an input the group csv and the fp cvs and df info on each bug making | FP colounm | LOC colounm | RANODM colounm |
    :param p_name: project name
    :param fp_dir: where all the FP csvs
    :param dir_rep_exp: where the group csv
    :param config_dir: where df csv
    :param out: where to write the output
    :return: None
    '''
    df = pd.read_csv('{}/{}/df.csv'.format(config_dir,p_name),index_col=0)
    df_group = pd.read_csv('{}/df_grouped_{}.csv'.format(dir_rep_exp,p_name))
    csv_files = pt.walk_rec('{}/{}'.format(fp_dir,p_name),[],'FP.csv')
    d_csv_fp={}
    for item in csv_files:
        name=str(item).split('/')[-1].split('.')[0].split('_')[1]
        df_i = pd.read_csv(item,index_col=0)
        d_csv_fp[name]=df_i
    print "done"
    if p_name =='Math':
        df.loc[df['TAG_NAME'] == 'trunk_tmp_2012-03-01', 'TAG_NAME'] = 'MATH_2_2_1'
    for i in range(4):
        df['MAJOR_{}'.format(i)] = df['TAG_NAME'].apply(lambda x : " " if len(str(x).split('_')) <= i else str(x).split('_')[i])
    print list(df)
    if major is False:
        ky = d_csv_fp.keys()[0]
        df['MAJOR_1']=ky
    df_group['FP']=df_group.apply(get_FP,dico_fp=d_csv_fp,df_info=df,axis=1)
    df_group['FP_genric']=df_group.apply(get_FP,dico_fp=d_csv_fp,df_info=df,mean=True,axis=1)
    df_group['LOC'] = df_group.apply(add_LOC,p_name=p_name,axis=1)
    max_LOC = df_group['LOC'].max()
    min_LOC = df_group['LOC'].min()
    df_group['LOC_P'] = df_group['LOC'].apply(lambda x: float(x - min_LOC) / float(max_LOC - min_LOC))
    df_group['Random'] = np.random.random_sample(size=len(df_group))
    df_group.to_csv('{}/{}.csv'.format(out,p_name))


def get_FP(row,dico_fp,df_info,mean=False,gen_name='name_genric'):
    '''
    add the FP probability to the group dataframe
    '''
    id_i = row['bug_ID']
    test_i = row['TEST']
    value = df_info.loc[df_info['bug_ID'] == id_i, 'MAJOR_1'].iloc[0]
    if value not in dico_fp:
        return "no_fp"
    df_fp = dico_fp[value]
    df_tmp = df_fp.loc[df_fp['name'] == test_i, 'FP']
    if len(df_tmp) > 0:
        value_fp = df_tmp.iloc[0]
    else:
        print test_i
        return "no_fp"
    if mean:
        value_fp = np.mean(df_tmp )
        #value_fp =df_fp.loc[df_fp[gen_name] == test_i, 'FP'].mean()
    return value_fp

def add_LOC(row,p_name,path='/home/ise/tmp_d4j/LOC'):
    '''
    adding the line of code for the class
    '''
    bug_id_i = row['bug_ID']
    test_i = row['TEST']
    file_csv = "{0}/{1}/LOC_{1}_{2}.csv".format(path,p_name,bug_id_i)
    if os.path.isfile(file_csv) is False:
        return None
    df_loc = pd.read_csv(file_csv)
    value_loc = df_loc.loc[df_loc['name'] == test_i, 'LOC'].iloc[0]
    return value_loc

def make_FP_pred(dir_target='/home/ise/tmp_d4j/out_pred/out/Lang/Lang_2'):
    '''
    concat the two csv files from the weka dir to one big Dateframe and make the probabily for bug,
    by 1-probablit for a vaild component
    '''
    print "dir_target=\t{}".format(dir_target)
    out = '/'.join(str(dir_target).split('/')[:-1])
    name = str(dir_target).split('/')[-1]
    p_name = str(name).split('_')[0]
    res_test_set = pt.walk_rec(dir_target,[],'testing')
    res_test_set = [x for x in res_test_set if str(x).endswith('csv')]
    most_csv = pt.walk_rec(dir_target,[],'Most_names_File')
    if len(most_csv)==1 and len(res_test_set)==1 is False:
        print "[Error] no csv in the dir-> {}".format(dir_target)
        return None
    df_most = pd.read_csv(most_csv[0],names=['class'])
    df_res =  pd.read_csv(res_test_set [0])
    print 'df_most: ',list(df_most),'\tsize: ',len(df_most)
    print 'df_res: ',list(df_res),'\tsize: ',len(df_res)
    df = pd.concat([df_res, df_most], axis=1)
    df['FP'] = float(1) - df['prediction']
    df['name'] = df['class'].apply(lambda x: path_to_package_name(p_name,x))
    if p_name == 'Math':
        df['name_genric'] = df['name'].apply(lambda x: str(x).replace('.math2.','.math.').replace('.math3.','.math.').replace('.math4.','.math.'))
    if p_name == 'Lang':
        df['name_genric'] = df['name'].apply(lambda x: str(x).replace('.lang2.','.lang.').replace('.lang3.','.lang.').replace('.lang4.','.lang.'))
    df.to_csv("{}/{}_FP.csv".format(dir_target,name))
    return "{}/{}_FP.csv".format(dir_target,name)


def path_to_package_name(p_name,path_input):
    item = str(path_input).replace('\\','/')
    start_package = 'org'
    if p_name == 'Closure':
        start_package = 'com'
    if item[-5:] != '.java':
        return None
    try:
        pack = pt.path_to_package(start_package, item, -1 * len('.java'))
    except Exception as e:
        pack=None
    return pack


def parser():
    flag = sys.argv[1]
    if flag == 'Make_FP':
        # make a FP file using the Weka outputs files from the Fault-Prediction model
        make_FP_pred(sys.argv[2])
    if flag == 'Only_FP':
        # this Function filter out only the bug IDs that has FP prediction
        get_bug_ID_contains_FP(sys.argv[2])
    if flag == 'exp_rep':
        # make the rep experiment
        rep_exp_new(sys.argv[2])
    if flag =='LOC':
        proj = sys.argv[2]
        #proj = 'Lang'
        for i in range(1, 200):
            get_size_classes_csv(i, proj, '/home/ise/tmp_d4j/LOC/{}'.format(proj))


def merger(dir_t = '/home/ise/eran/JARS'):
    res = pt.walk_rec(dir_t,[],'.csv',lv=-1)
    list_Df = []
    for item in res:
        list_Df.append(pd.read_csv(item))
    df_all = pd.concat(list_Df)
    df_all.to_csv("{}/all_H.csv".format(dir_t))
    exit()

def helper(df1 = '/home/ise/eran/out_csvs_D4j/rep_exp/df_grouped_Lang.csv',
           df2 = '/home/ise/tmp_d4j/out/raw_data/Lang.csv'):
    out='/home/ise'
    df1 = pd.read_csv(df1,index_col=0)
    df1 = df1[['TEST','bug_ID','project']]
    df2 = pd.read_csv(df2,index_col=0)
    print list(df1)
    print list(df2)
    print "df2 len: ",len(df2)
    print "df1 len: ",len(df1)
    res_df = pd.merge(df1,df2,how='left',on=['TEST','bug_ID','project'])
    print "res len: ",len(res_df)
    exit()

if __name__ == "__main__":
    #make_FP_pred('/home/ise/tmp_d4j/out_pred/out/Math/Math_3')
    #exit()
    #rep_exp_new('Mockito')
    #helper()
    ###merger()
   # get_bug_d4j_major(p_name='Math')
    #exit()
    project_arr=['Math']
    for x in project_arr:
        rep_exp_new(p_name=x,heuristic_method=False)
        get_bug_ID_contains_FP(p_name=x)
    exit()
    util(p_name="Lang")
    exit()
    get_bug_d4j_major('Lang',out='/home/ise/Desktop',major=False)
    rep_exp_new('Time')
    get_bug_ID_contains_FP('Time')
    get_bug_ID_contains_FP(p_name='Lang')

    #exit()
    #add_random_probabilityes(loc=True)


    exit()
    util(p_name='Time')
    rep_exp(p_name='Time')
    exit()
    parser()
    #get_avg_csv_file()
    p='/home/ise/MATH/Defect4J/D4J_MATH - Sheet2.csv'
    p = '/home/ise/MATH/Defect4J/D4J_MATH - Sheet2.tsv'
    p='/home/ise/eran/math/D4J_MATH - Sheet2.tsv'
    #get_package_csv('/home/ise/eran/eran_D4j/MATH_t=2')
    #exit()
    args = sys.argv
    args ='py Chart'.split()
    if len(args) == 2 :
        merge_oracle_out(args[1])
    #uniform_vs_prefect_oracle(p)