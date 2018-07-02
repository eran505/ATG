

import numpy as np
import sys,os
import  pit_render_test
import pandas as pd

import xml_mutation as xm

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
    df = pd.read_csv(csv_big)
    #res = find_biggest_time_b(df,False)
    df_cut = remove_unkillable(df,debug,'/home/ise/Desktop/dir_test/{}'.format(proj))
    xm.ana_big_df_all(df_cut,'/home/ise/Desktop/dir_test/{}'.format(proj))


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

if __name__ == "__main__":
    csv_p='/home/ise/eran/lang/big_all_df.csv'
    remvoe_unkillable_mutations(csv_p, True, 'LANG')
    csv_p='/home/ise/MATH/big_all_df.csv'
    remvoe_unkillable_mutations(csv_p,True,'MATH')
    exit()
    init_script()





'''''''''''
list = get_all_csv(str_path)
list.sort(key=lambda x: x.size, reverse=True)
res=join_data_frame(list)
res.to_csv("/home/eran/Desktop/evo_result/res.csv", sep='\t', encoding='utf-8')
'''''