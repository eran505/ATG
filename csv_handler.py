

import numpy as np
import sys,os
import  pit_render_test
import pandas as pd

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


if __name__ == "__main__":
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