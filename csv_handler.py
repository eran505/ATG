import matplotlib
import numpy as np
import sys,os
import  pit_render_test
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import xml_mutation as xm
from csv_PIT import arr_sign


def find_biggest_time_b(df,debug=False):
    '''
    finding the max key with zero nan values as the upper bound for kill-able mutation
    :param df:
    :param debug:
    :return:
    '''
    list_col = list(df)
    list_col = [x for x in list_col if str(x).startswith('t=')]
    list_col = [x for x in list_col if str(x).__contains__('Sum')]
    #list_col_fp = [x for x in list_col if str(x).__contains__('FP')]
    list_col_uni = [x for x in list_col if str(x).__contains__('_U')]
    all_size = len(df)
    if debug:
        print 'all_size :{}'.format(all_size)
    d={}
    for x in list_col_uni:
        time_b = str(x).split('_')[0]
        mode = str(x).split('_')[-1]
        count_row = df[x].count()
        count_nan = all_size - count_row
        d[x] = {'t':time_b,'mode':mode,'size':count_row,'nan':count_nan}
    list_candid = []
    max_key = None
    for k in d.keys():
        if float(d[k]['nan'] ) > 0 :
            del d[k]
            continue
        else:
            if debug:
                print '{}:{}'.format(k, d[k])
        if max_key is None:
            max_key=k
        else:
            if int(d[max_key]['t'][2:]) < int(d[k]['t'][2:]):
                max_key=k
    if debug:
        print '---max_key----'
        print '{}:{}'.format(max_key, d[max_key])
    return max_key


def remove_unkillable(df_old,debug=False,out='/home/ise/Desktop'):
    '''
    this function aggregate all uniform column (only the Sum) and all zero rows is been remove from the Data_frame
    :param df_old: the Data_frame
    :param debug:
    :param out: the dir output
    :return: None (write to the disk csv file )
    '''
    list_col = list(df_old)
    print list_col
    list_col = [x for x in list_col if str(x).__contains__('Sum')]
    list_col_uni = [x for x in list_col if str(x).__contains__('_U')]
    list_col_uni.append('ID')
    df = df_old[list_col_uni]
    print list(df)
    print df.dtypes
    df['sum_all']=0.0
    for x in list_col_uni:
        if x =='ID':
            continue
        df[x]=df[x].astype(np.float64)
    df['sum_all'] = df.sum(axis=1)
    if debug:
        print df['sum_all']
    #print pd.value_counts(df['sum_all'].values, sort=False)
    print '--'*88
    val_zero =  df['sum_all'][df['sum_all'] == 0.0].count()
    df_filter = df[df['sum_all'] > 0]
    print 100-float(len(df_filter))/float(len(df))*100
    df_filter_ID = df_filter['ID']
    print df_filter_ID
    df_cut = df_old[df_old['ID'].isin(df_filter_ID)]
    df_cut = df_cut.loc[:, ~df_cut.columns.str.contains('^Unnamed')]
    df_cut.to_csv('{}/df_cut.csv'.format(out))
    diff = len(df_old) - len(df_cut)
    precnet = float(len(df_cut))/float(len(df_old))*100
    with open('{}/diff.txt'.format(out),'w') as f:
        f.write('old:{}\ncut:{}\ndiff:{}\npercentage_change:{}'.format(len(df_old),len(df_cut),diff,precnet))
    return df_cut


def remvoe_unkillable_mutations(csv_big,debug=False,proj='proj'):
    print csv_big
    df = pd.read_csv(csv_big)
    out_dir = pit_render_test.mkdir_system('/'.join(str(csv_big).split('/')[:-1]),'killable_{}'.format(proj),True)

    #res = find_biggest_time_b(df,False)
    df_cut = remove_unkillable(df,debug,out_dir)

    xm.ana_big_df_all(df_cut,out_dir)


def init_script():
    #sys.argv = ["p","info","/home/eran/Desktop/testing/new_test/info.txt"]
    if len(sys.argv) == 3 :
        mode = sys.argv[1]
        if mode == 'info':
            pass
        elif mode == "csv":
            pass
        else :
            print('error no mode ')
    else:
        print 'Usage : -csv [path] '


def first_kill(p_path='/home/ise/eran/lang/U_lang_15/big_all_df.csv'):
    rel_path = '/'.join(str(p_path).split('/')[:-1])
    out_dir = pit_render_test.mkdir_system(rel_path,'first_kill',False)
    df = pd.read_csv(p_path,index_col=0)
    get_col_time_budget = list(df)
    get_col_time_budget = [x for x in get_col_time_budget if str(x).__contains__('t=')]
    get_col_time_budget_U = [x for x in get_col_time_budget if str(x).__contains__('_U')]
    for x in get_col_time_budget_U:
        print x
    df['First'] = df.apply(my_test2,cols=get_col_time_budget_U, axis=1)
    df['freq'] = df.apply(my_test1, cols=get_col_time_budget_U, axis=1)
    df[['ID','First','freq']].to_csv('{}/first_kill.csv'.format(out_dir))
    exit()



def k_replication(k=2,csv_path = '/home/ise/eran/lang/U_lang_15/18_00_00_00_00_t=15/replication_kill/all_rep.csv'):
    '''
    given the all_rep CSV this function take k replication and output the kill rate data frame
    :param k: num_of_rep
    :param csv_path: path to all_rep.csv
    :return: dico (look down) with time_budget,k,AVG arr_sing
    '''
    arr_sign = ['NO_COVERAGE', 'SURVIVED', 'TIMED_OUT', 'RUN_ERROR']
    arr_sign =['KILLED','NO_COVERAGE']
    time_b = str(csv_path).split('_t=')[1].split('/')[0]
    out = '/'.join(str(csv_path).split('/')[:-1])
    df = pd.read_csv(csv_path, index_col=0)
    col_rep = list(df)
    col_rep = [x for x in col_rep if str(x).__contains__('ALL_')]
    size_rep = int(len(col_rep))
    if k > size_rep:
        k=size_rep
    arr_index = range(size_rep)
    arr_index = np.array(arr_index)
    choise = np.random.choice(arr_index,k,replace=False)
    candidat_col = ['ID']
    for i in range(k):
        candidat_col.append(col_rep[choise[i]])
    df = df[candidat_col]
    candidat_col.remove('ID')
    for sign in arr_sign:
        df['{}_SUM'.format(sign)]=0
        df['{}_binary'.format(sign)] = 0
    for col in candidat_col:
        for sign in arr_sign:
            df['{}_SUM'.format(sign)]+=df[col].apply(lambda x: 1 if x == str(sign) else 0)
    if 'NO_COVERAGE' in arr_sign:
        df['NO_COVERAGE_binary'] = df['NO_COVERAGE_SUM'].apply(lambda x: 1 if x == int(k) else 0)
    if 'KILLED' in arr_sign:
        df['KILLED_binary'] = df['KILLED_SUM'].apply(lambda x: 1 if x > 0 else 0)
    d={'time_budget':time_b, 'k_replication':k}
    for sign in arr_sign:
        df["{}_AVG".format(sign)] = df["{}_SUM".format(sign)]
        d['AVG_{}'.format(sign)]=df["{}_AVG".format(sign)].mean()
        d['Binary_{}'.format(sign)] = float(df["{}_binary".format(sign)].sum())/float(df['ID'].count())
    flush_csv(out,df,'rep_raw_k={}'.format(k))
    return d


def replication(dir_out_xml='/home/ise/eran/lang/U_lang_15/18_00_00_00_00_t=15/out_xml_all',killable=True):
    '''
    make CSV conatins repleication and the results
    :param dir_out_xml:
    :return:  making a dir
    '''
    rel_path = '/'.join(str(dir_out_xml).split('/')[:-1])
    out_dir = pit_render_test.mkdir_system(rel_path, 'replication_kill', False)
    csv_lists = pit_render_test.walk_rec(dir_out_xml,[],'.csv')
    acc = 0
    big_df = None
    for csv_item in csv_lists:
        print "csv_item =", csv_item
        df = pd.read_csv(csv_item, index_col=0)
        list_col = list(df)
        list_col = [x for x in list_col if str(x).__contains__('_it=')]
        list_col.append('ID')
        df = df[list_col]
        acc += int(len(df))
        if big_df is None:
            big_df = df
        else:
            big_df = pd.concat([big_df, df])
        if acc != int(len(big_df)):
            print "acc: {} big: {}".format(acc, int(len(big_df)))
    if killable:
        df_first_kill = pd.read_csv('/home/ise/eran/lang/first_kill.csv') #TODO: read the CSV frist kill and merge the ID and remove all ids that cant be kill
        df_all = df_first_kill.merge(big_df, on=['ID'], how='outer', indicator=True)
        print df_all['_merge'].value_counts()
        df_all = df_all[df_all['First'] > 0]
        col_ALL = list(df_all)
        col_ALL = [x for x in col_ALL if str(x).__contains__('ALL_')]
        col_ALL.append('ID')
        flush_csv(out_dir, df_all, 'merge')
        flush_csv(out_dir,df_all[col_ALL],'all_rep_killable')
    else:
        flush_csv(out_dir, big_df, 'all_rep')

def k_range_rep(arr_rang,csv_p,time_of_mean=3):
    '''
    this function take an arr of K range and make a CSV result
    :param arr_rang: the given range K wanted
    :param csv_p:  the path to all_rep.csv
    :return: None
    '''
    print arr_rang
    size =len(arr_rang)
    d_mean={}
    l_mean=[]
    for i in arr_rang:
        d_mean[i] = {'KILLED':0,'NO_COVERAGE':0}
    for j in range(time_of_mean):
        d_l = []
        for k in arr_rang:
            d_res = k_replication(k, csv_p)
            d_l.append(d_res)
            d_mean[k]['NO_COVERAGE'] += d_res['Binary_NO_COVERAGE']
            d_mean[k]['KILLED'] += d_res['Binary_KILLED']
    for ky in d_mean.keys():
        d_mean[ky]['NO_COVERAGE'] = d_mean[ky]['NO_COVERAGE'] / float(time_of_mean)
        d_mean[ky]['KILLED'] = d_mean[ky]['KILLED']/float(time_of_mean)
        l_mean.append({'K':ky, 'kill_rate':d_mean[ky]['KILLED'] , 'NO_coverage_rate':d_mean[ky]['NO_COVERAGE']})
    df = pd.DataFrame(d_l)
    df_mean = pd.DataFrame(l_mean)
    out = '/'.join(str(csv_p).split('/')[:-1])
    df_mean.to_csv("{}/k_rep_MEAN.csv".format(out))
    df.to_csv("{}/k_rep_out.csv".format(out))


def flush_csv(out_path_dir, xml_df, name_file):
    if xml_df is None:
        return
    ##print "{}/{}.csv".format(out_path_dir, name_file)
    xml_df.to_csv("{}/{}.csv".format(out_path_dir,name_file))

def my_test1(row,cols):
    l_int=[]
    for col in cols:
        if row[col] > 0:
            time_b = str(col).split('_')[0].split('=')[1]
            l_int.append(int(time_b))
    if len(l_int)==0:
        return 0
    l_int.sort()
    return float(len(l_int))/float(len(cols))*100

def my_test2(row,cols):
    l=[]
    l_int=[]
    for col in cols:
        if row[col] > 0:
            l.append(col)
            time_b = str(col).split('_')[0].split('=')[1]
            l_int.append(int(time_b))
    if len(l_int)==0:
        return 0
    l_int.sort()
    return l_int[0]






def make_data_again(path):
    csv_path = "{}all_self_junit.csv".format(path)
    df = pd.read_csv(csv_path ,index_col=0)
    print(len(df))
    print list(df)
    list_error = df['error'].unique()
    print "all error: ",df['trigger'].sum()
    map_d = {}
    for item in list_error:
        if item == 'AssertionError':
            map_d[item] = 1
        else:
            map_d[item] = 0
    df['trigger'] = df['error'].map(map_d)
    print 'only AssertionError error: ',df['trigger'].sum()
    df=df[df['mode']=='buggy']
    df.drop(['error','full_error','test_case','test_class','mode','time'],axis=1,inplace=True)

    df['count_test'] = df.groupby(['bug_id', 'jira_id', 'name'])[
        'iter'].transform('nunique')


    df['sum_test_case_fail'] = df.groupby(['bug_id', 'iter', 'jira_id', 'name'])[
        'trigger'].transform('sum')

    print(list(df))


    df['sum_test_case_fail_binary']=df['sum_test_case_fail'].apply(lambda x : 1 if x>0 else 0 )


    df['sum_kill'] = df.groupby(['bug_id', 'iter', 'jira_id', 'name','sum_test_case_fail_binary'])[
        'sum_test_case_fail_binary'].transform('sum')


    df['ALL_sum_test_case_fail'] = df.groupby(['bug_id', 'jira_id', 'name'])[
        'trigger'].transform('sum')


    #######
    # calc binary kill in each file test
    df_cut = df[['bug_id', 'iter', 'jira_id', 'name','sum_test_case_fail_binary']]

    df_cut.drop_duplicates(['bug_id', 'iter', 'jira_id', 'name','sum_test_case_fail_binary'],inplace=True)
    df_cut['kill_total_rep']=df_cut.groupby(['bug_id', 'jira_id', 'name'])[
        'sum_test_case_fail_binary'].transform('sum')
    df_cut.drop_duplicates(['bug_id', 'jira_id', 'name', 'kill_total_rep'], inplace=True)
    df_cut.drop(['sum_test_case_fail_binary','iter'],axis=1,inplace=True)

    df = pd.merge(df,df_cut,how='left',on=['bug_id', 'jira_id', 'name'])

    #######
    df.drop(['sum_test_case_fail_binary'],axis=1,inplace=True)
    df.drop_duplicates(inplace=True)

    df_test_cases = pd.read_csv('{}out/df_num_tset_cases.csv'.format(path),index_col=0)
    df_test_cases['AVG_test_case_number'] = df_test_cases.groupby(['name', 'bug_id','jira_id'])['num_of_test_cases'].transform('mean')
    df_test_cases['SUM_test_case_number'] = df_test_cases.groupby(['name', 'bug_id','jira_id'])['num_of_test_cases'].transform('sum')
    df_test_cases.drop(inplace=True,axis=1,labels=['num_of_test_cases'])
    df_test_cases.drop_duplicates(inplace=True)

    df_test_cases.rename(columns={'name': 'TEST'}, inplace=True)
    df_test_cases.rename(columns={'jira_id': 'bug_ID'}, inplace=True)

    print(list(df))
    print(list(df_test_cases))
    print ('df_test_cases : ',len(df_test_cases ))
    print('df : ',len(df))



    print('',len(df))


    df.to_csv('{}out/exp1.csv'.format(path))

    df_exp = pd.read_csv('{}exp_new_new.csv'.format(path),index_col=0)

    df.drop(['iter','sum_kill','sum_test_case_fail','trigger'],axis=1,inplace=True)

    df.rename(columns={'name': 'TEST'}, inplace=True)
    df.rename(columns={'jira_id': 'bug_ID'}, inplace=True)
    print(list(df_exp))
    print(list(df))
    print(len(df))
    print(len(df_exp))

    df = pd.merge(df_exp,df,how='left',on=['bug_id','bug_ID', 'TEST'])
    df.drop_duplicates(inplace=True)
    df = pd.merge(df, df_test_cases, on=['bug_id','bug_ID', 'TEST'], how='left')
    print(len(df))


    df.to_csv('{}out/exp2.csv'.format(path))

    exit()

def merge_testcases_df(path_testcases, path_exp,proj_name):
    path_exp_raw_1 = "{}/exp_new.csv".format(path_exp)
    path_exp_mege_raw = "{}/exp_new_new.csv".format(path_exp)

    # Extract the number of fail testcase on ecah test_name
    df_exp_raw = pd.read_csv(path_exp_raw_1, index_col=0)

    df_exp_raw.rename(columns={'bug_name': 'bug_ID'}, inplace=True)
    df_exp_raw.rename(columns={'name': 'TEST'}, inplace=True)

    df_exp_raw['dup'] = df_exp_raw.duplicated(subset=['bug_ID', 'TEST', 'bug_id', 'mode'],keep=False)
    df_exp_raw.to_csv('/home/ise/bug_miner/{}/out/exp1.csv'.format(proj_name))
    print(len(df_exp_raw))
    exit()
    df_exp_raw['sum_test_cases_fails'] = df_exp_raw.groupby(['bug_name', 'name', 'bug_id', 'mode', 'time'])[
        'test_case_fail_num'].transform('sum')
    cols = ['bug_name', 'name', 'bug_id', 'test_case_fail_num', 'mode']
    df_exp_raw = df_exp_raw[cols]


    df_testcases = pd.read_csv(path_testcases, index_col=0)
    df_exp = pd.read_csv(path_exp_mege_raw, index_col=0)
    df_testcases = df_testcases[df_testcases['mode'] == 'buggy']
    df_testcases['count_test_file'] = df_testcases.groupby(['bug_id', 'jira_id', 'mode', 'name', 'time'])[
        'num_of_test_cases'].transform('count')
    df_testcases['avg_test_cases'] = df_testcases.groupby(['bug_id', 'jira_id', 'mode', 'name', 'time'])[
        'num_of_test_cases'].transform('mean')
    df_testcases['sum_test_cases'] = df_testcases.groupby(['bug_id', 'jira_id', 'mode', 'name', 'time'])[
        'num_of_test_cases'].transform('sum')

    df_testcases.rename(columns={'jira_id': 'bug_ID'}, inplace=True)
    # df_testcases.rename(columns={'jira_id': 'bug_ID'}, inplace=True)
    df_testcases.rename(columns={'name': 'TEST'}, inplace=True)
    df_testcases.drop(['iter', 'time'], axis=1, inplace=True)
    df_testcases.drop_duplicates(
        subset=['sum_test_cases', 'avg_test_cases', 'sum_test_cases', 'TEST', 'mode', 'bug_ID', 'bug_id'], inplace=True)



    result = pd.merge(df_exp, df_testcases, how='right', on=['bug_id', 'bug_ID', 'TEST', 'mode'])

    result.to_csv('/home/ise/bug_miner/{}/out/exp1.csv'.format(proj_name))

    print("result: ",len(result))
    print(list(result))
    print('df_exp_raw: ',len(df_exp_raw))
    print('\n\n')
    print(list(df_exp_raw))

    df_exp_raw['dup']=df_exp_raw.duplicated(subset=['bug_ID', 'TEST', 'bug_id', 'mode'])
    print('(drop_duplicates) df_exp_raw: ', len(df_exp_raw))
    df_exp_raw.to_csv('/home/ise/bug_miner/{}/out/exp2.csv'.format(proj_name))
    result = pd.merge(result, df_exp_raw, how='right', on=['bug_id', 'bug_ID', 'TEST', 'mode'])

    df_case = pd.read_csv("{}/out/case.csv".format(path_exp), index_col=0)
    df_case.rename(columns={'jira_id': 'bug_ID'}, inplace=True)
    df_case.rename(columns={'name': 'TEST'}, inplace=True)
    df_case.drop(['time'],axis=1,inplace=True)
    result = pd.merge(result, df_case, how='right', on=['bug_id', 'bug_ID', 'TEST', 'mode'])
    print('-'*200)
    print(list(df_case))
    print(list(result))
    print('-' * 200)
    result.to_csv('/home/ise/bug_miner/{}/out/exp.csv'.format(proj_name))
    print list(df_exp)
    print list(df_testcases)


def test_case_counter(file_tset_case,fix=False):
    father = '/'.join(str(file_tset_case).split('/')[:-1])
    data=None
    if fix is False:
        with open(file_tset_case,'r') as myfile:
            data = myfile.readlines()
            data = ''.join(data)
            data = str(data).replace('.java\n','.java,')
            print(data)
        with open("{}/new_test_case_count.csv".format(father),'w') as f:
            f.write(data)
    test_case_counter_helper("{}/new_test_case_count.csv".format(father))

def test_case_counter_helper(csv_path):
    father_dir= '/'.join(str(csv_path).split('/')[:-1])
    df=pd.read_csv(csv_path,names=['TEST','num_of_test_cases'])
    df['name']=df['TEST'].apply(lambda x: ".".join(x.split('/')[4:])[:-12])
    df['bug_id']=df['TEST'].apply(lambda x: str(x.split('/')[1]).split('_')[-1] )
    df['jira_id']=df['TEST'].apply(lambda x: str(x.split('/')[1]).split('_')[0] )
    df.drop(['TEST'],axis=1,inplace=True)
    df.to_csv('{}/df_num_tset_cases.csv'.format(father_dir))


from sklearn import metrics

def clac_AUC(path_csv_df):
    father_dir='/'.join(str(path_csv_df).split('/')[:-1])
    d=[]
    df = pd.read_csv(path_csv_df,index_col=0)
    df = df[np.isfinite(df['LOC'])]
    print list(df)
    df['F1']=df['ALL_sum_test_case_fail']/df['SUM_test_case_number']
    df['F1'].fillna(0,inplace=True)
    df['F3'] = df['ALL_sum_test_case_fail']
    df['F5'] = df['sum_detected']/df['count_detected']
    df['F4'] = df['F5'].apply(lambda x: 1 if x>0 else 0 )
    df.to_csv("{}/tmp.csv".format(father_dir))
    value_id_list = df['bug_ID'].unique()
    print(len(value_id_list ))
    #exit()
    for value_id in value_id_list:
        print "process -> bug_ID =", value_id
        for score_metric in ['F1','F2','F3','F4','F5','F6']:
            df_min = df.loc[df['bug_ID']==value_id]
            size_df = len(df_min)
            #size_df = 33
            for i in range(1,size_df+1,1):
                loc_total_nmber = df_min['LOC'].sum()
                loc_size,score_sum,auc=min_func_per_method_auc('FP',df_min,score=score_metric,size=i)
                d.append(
                    {'mode_score': score_metric, 'score_sum': score_sum,'method':'FP','loc_size':loc_size, 'total_line_code': loc_total_nmber, 'bug_ID': value_id,'item':i,"AUC":auc})
                loc_size, score_sum,auc= min_func_per_method_auc('LOC_P', df_min,score=score_metric,size=i)
                d.append(
                    {'mode_score': score_metric,'method':'LOC','loc_size':loc_size, 'score_sum': score_sum, 'total_line_code': loc_total_nmber, 'bug_ID': value_id,'item':i,"AUC":auc})
                loc_size, score_sum,auc = min_func_per_method_auc('Random', df_min,score=score_metric,size=i)
                d.append({'method':'Random','mode_score':score_metric,'loc_size':loc_size,'score_sum':score_sum,'total_line_code':loc_total_nmber,'bug_ID':value_id,'item':i,"AUC":auc})
    df_res = pd.DataFrame(d)
    df_res.to_csv('{}/EACH_auc_bug_clean.csv'.format(father_dir))



def csv_graph_scatter(path_to_csv='/home/ise/bug_miner/commons-lang/out/EACH_auc_bug.csv'):
    df = pd.read_csv(path_to_csv,index_col=0)
    df=df[df['mode_score']=='F2']
    df = df[df['item'] < 5 ]

    scatter_x = df['loc_size']
    scatter_y =  df['score_sum']

    dow = {
        'FP': 1,
        'LOC': 5,
        'Random': 10
    }
    df["method_int"] = df['method'].map(dow)
    df["item_int"] = df['item'].map({1:1,2:20,3:40,4:60})

    plt.scatter(scatter_x, scatter_y, c=df['method_int'],s=df['item_int'])
    cb = plt.colorbar()
    plt.show()

def csv_graph_line(path_to_csv='/home/ise/bug_miner/commons-lang/out/EACH_auc_bug.csv'):
    df = pd.read_csv(path_to_csv,index_col=0)
    print(df['bug_ID'].unique())
    df=df[df['mode_score']=='F2']
    df=df[df['bug_ID']==1370]
    #df = df[df['item'] == 2 ]
    df_dp = df[df['method'] == 'FP']
    df_rand = df[df['method'] == 'Random']
    df_loc = df[df['method'] == 'LOC']

    plt.plot(df_loc['loc_size'],df_loc['score_sum'], '--c')
    plt.plot(df_dp['loc_size'], df_dp['score_sum'], '-.k')
    plt.plot(df_rand['loc_size'], df_rand['score_sum'], ':r')

    plt.show()


def min_func_per_method_auc(method,df_min,score,size):

    df_min = df_min[np.isfinite(df_min[method])]

    df_min.sort_values(by=[method], inplace=True, ascending=False)
    df_min = df_min.nlargest(size,method)
    if score == 'F2':
        df_min['cumsum_SUM_test_case_number']=df_min['SUM_test_case_number'].cumsum()
        df_min['cumsum_ALL_sum_test_case_fail'] = df_min['ALL_sum_test_case_fail'].cumsum()
        df_min['F2']=df_min['cumsum_ALL_sum_test_case_fail'] / df_min['cumsum_SUM_test_case_number']
        df_min['F2'].fillna(0,inplace=True)
        score_sum = df_min['F2'].iloc[-1]
        df_min['acc_score'] = df_min[score].cumsum()
        df_min['acc_LOC'] = df_min['LOC'].cumsum()
        auc = np.trapz(df_min['acc_score'], df_min['acc_LOC'])
        df_min.drop(['cumsum_SUM_test_case_number','cumsum_ALL_sum_test_case_fail','F2'], axis=1, inplace=True)
    elif score == 'F6':
        df_min['cumsum_sum_detected']=df_min['sum_detected'].cumsum()
        df_min['cumsum_count_detected'] = df_min['count_detected'].cumsum()
        df_min['F6']=df_min['cumsum_sum_detected'] / df_min['cumsum_count_detected']
        df_min['F6'].fillna(0,inplace=True)
        score_sum = df_min['F6'].iloc[-1]
        df_min['acc_score'] = df_min[score].cumsum()
        df_min['acc_LOC'] = df_min['LOC'].cumsum()
        auc = np.trapz(df_min['acc_score'], df_min['acc_LOC'])
        df_min.drop(['cumsum_count_detected','cumsum_sum_detected','F6'], axis=1, inplace=True)
    else:
        score_sum = df_min[score].sum()
        df_min['acc_score'] = df_min[score].cumsum()
        df_min['acc_LOC'] = df_min['LOC'].cumsum()
        auc = np.trapz(df_min['acc_score'], df_min['acc_LOC'])

    x = df_min['LOC'].sum()


    df_min.drop(['acc_LOC','acc_score'],axis=1,inplace=True)

    return x,score_sum,auc

def clac_AUC_all_project(path_csv_df):
    father_dir='/'.join(str(path_csv_df).split('/')[:-1])
    d=[]
    df = pd.read_csv(path_csv_df,index_col=0)
    df = df[np.isfinite(df['LOC'])]
    print list(df)

    #df['cumsum_SUM_test_case_number']=df['SUM_test_case_number'].cumsum()
    #df['cumsum_ALL_sum_test_case_fail'] = df['ALL_sum_test_case_fail'].cumsum()
    #df['F2'] = df['cumsum_ALL_sum_test_case_fail'] / df['cumsum_SUM_test_case_number']

    df['F1']=df['ALL_sum_test_case_fail']/df['SUM_test_case_number']
    df['F1'].fillna(0,inplace=True)
    df['file_score'] = df['sum_detected']/df['count_detected']
    df['file_score_binary'] = df['file_score'].apply(lambda x: 1 if x>0 else 0 )
    df.to_csv("{}/tmp.csv".format(father_dir))
    score_metric='test_case_score'
    df_min = df
    df.to_csv('{}/tmp.csv'.format(father_dir))
    for score_metric in ['file_score','file_score_binary','F1','F2']:
        loc_total_nmber = df_min['LOC'].sum()
        fp_auc=min_func_per_method_auc('FP',df_min,score=score_metric)
        loc_auc = min_func_per_method_auc('LOC_P', df_min,score=score_metric)
        random_auc = min_func_per_method_auc('Random', df_min,score=score_metric)
        d.append({"score_metric":score_metric,'total_line_code':loc_total_nmber,'fp_auc':fp_auc,'loc_auc':loc_auc,'random_auc':random_auc})
        print d
    df_res = pd.DataFrame(d)
    df_res.to_csv('{}/AUC_all_project.csv'.format(father_dir))




if __name__ == "__main__":
    #csv_graph_scatter('/home/ise/bug_miner/commons-math/out/EACH_auc_bug_clean.csv')
    #exit()

    arr_p_project=['opennlp','commons-lang','commons-math','commons-imaging','commons-compress']
    for p_project in arr_p_project:
        if p_project != 'commons-math':
            continue
        path='/home/ise/bug_miner/{}/out/exp2.csv'.format(p_project)
        clac_AUC(path)
        # clac_AUC_all_project(path)
        #make_data_again(path)


    exit()
    csv_p = '/home/ise/eran/lang/U_lang_15/18_00_00_00_00_t=15/replication_kill/all_rep_killable.csv'
    #csv_p='/home/ise/eran/lang/U_lang_15/big_all_df.csv'
    #replication()
    k_range_rep(range(1,10,1),csv_p)
    exit()
    first_kill()
    #remvoe_unkillable_mutations(csv_p, True, 'LANG')
    #csv_p='/home/ise/MATH/big_all_df.csv'
    #remvoe_unkillable_mutations(csv_p,True,'MATH')
    exit()
    init_script()





'''''''''''
list = get_all_csv(str_path)
list.sort(key=lambda x: x.size, reverse=True)
res=join_data_frame(list)
res.to_csv("/home/eran/Desktop/evo_result/res.csv", sep='\t', encoding='utf-8')
'''''