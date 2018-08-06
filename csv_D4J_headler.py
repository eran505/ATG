import pandas as pd
import numpy as np
import pit_render_test as pt
import os

'''
This script handel the csv operation on the D4J exp
'''

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


'''
need to go over all the bug ID and extract the fault class and all its package class
'''

if __name__ == "__main__":
    p='/home/ise/MATH/Defect4J/D4J_MATH - Sheet2.csv'
    p = '/home/ise/MATH/Defect4J/D4J_MATH - Sheet2.tsv'
    #get_package_csv('/home/ise/eran/eran_D4j/MATH_t=2')
    #exit()
    uniform_vs_prefect_oracle(p)