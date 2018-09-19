import pandas as pd
import numpy as np
import pit_render_test as pt
import os
from math import pow
from defects_lib import get_deff,get_faulty_comp_defe4j_dir
'''
This script handel the csv operation on the D4J exp
'''



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
    out_file_l = pt.walk_rec(test_dir, [], 'bug_detection', lv=-2)
    if len(out_file_l) == 1:
        out_file = out_file_l[0]
    else:
        return None
    df_tmp = pd.read_csv(out_file)
    it = df_tmp.iloc[0]['test_id']
    return it

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


def make_rep(row,val):
    count_i = row['count']
    sum_i = row['sum']
    if val == 'avg':
        res =  float(sum_i)/float(count_i)
        return res
    if val <= count_i:
        Pr = float(sum_i)/float(count_i)
        res = pow((float(1)-Pr),float(val))
        res = 1 - res
        if res > 1:
            return 1
        else:
            return res
    return None

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


if __name__ == "__main__":
    parser()
    exit()
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