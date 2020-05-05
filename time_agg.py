
import os
import pandas as pd
import numpy as np
import pit_render_test as pt



def get_all_data_time_project(p_path):
    father_path = "/".join(str(p_path).split('/')[:-1])
    res = pt.walk_rec(p_path,[],"junit_out_buggy",lv=-3,file_t=False)
    list_report=[]
    for item in res:
        path_reports = pt.walk_rec(item,[],"report.csv")
        list_report.extend(path_reports)

    print (len(list_report))
    df_big=None
    my_list = filter(lambda x: os.stat(x).st_size > 4, list_report)
    print(len(my_list))
    for file_time in list_report:
        df_timee = extract_time_df(file_time)
        if df_timee is None:
            continue
        if df_big is None:
            df_big=df_timee
        else:
            df_new = pd.concat([df_big, df_timee])
            df_big=df_new
    df_big.to_csv("{}/time.csv".format(father_path))
    print list(df_big)
    return df_big

def extract_time_df(path_to_df):
    df = pd.read_csv(path_to_df,index_col=0)
    if len(df)==0:
        return None

    df["running_time"]=df.apply(get_time_record,axis=1)

    df.drop(['err', 'out'], axis=1,inplace=True)
    return df
def get_time_record(row):
    out_rec = row["out"]
    time_item = filter(lambda x: str(x).__contains__("Time:"), str(out_rec).split('\n'))
    if len(time_item)!=1:
        print "err"
        return None
    return time_item[0].split(':')[-1]

def group_by_time_class(path,df=None):
    if str(path).endswith(".csv"):
        df = pd.read_csv(path,index_col=0)
        father_p = "/".join(str(path).split('/')[:-1])
    else:
        father_p = path
    print list(df)
    df.drop(['mode', 'status'],axis=1,inplace=True)
    df["running_time"]=df["running_time"].astype('float')
#    df['running_time_num'] = df['running_time'].apply(lambda x: x.encode("ascii"))

    #print df.dtypes

    #df['time_mean'] = df.groupby('running_time')['bug_id', 'class'].transform('mean')
    df['time_mean'] = df.groupby(['bug_id', 'class'])['running_time'].transform('mean')
    df['time_std'] = df.groupby(['bug_id', 'class'])['running_time'].transform('std')
    df['time_count'] = df.groupby(['bug_id', 'class'])['running_time'].transform('count')
    df['time_sum'] = df.groupby(['bug_id', 'class'])['running_time'].transform('sum')
    df.drop(['running_time'], axis=1, inplace=True)
    #print "Before drop_duplicates = ",len(df)
    df.drop_duplicates(inplace=True)
    df['bug_ID']=df["bug_id"].apply(lambda x: str(x).split('_')[0])
    df['bug_id'] = df["bug_id"].apply(lambda x: str(x).split('_')[-1])
    df['TEST'] = df["class"].apply(lambda x: str(x).split('_')[0])
    df.drop(['class'], axis=1, inplace=True)
    #print "After drop_duplicates = ",len(df)
    df.to_csv("{}/out/time_grouped.csv".format(father_p))
    #df['time_std'] = df.groupby(['bug_id', 'class']).transform('std')

   # df['time_mean'] = df.groupby(ky_name_col).transform('count')


def merge_time_exp(exp_path,time_path):
    father_dir= "/".join(str(exp_path).split('/')[:-1])
    df_time = pd.read_csv(time_path,index_col=0)
    df_exp = pd.read_csv(exp_path, index_col=0)
    print ("df_time: ",list(df_time))
    print ("df_time(SIZE): ", len(df_time))
    print ("df_exp: ", list(df_exp))
    print ("df_exp(SIZE): ", len(df_exp))

    df_new = pd.merge(df_exp,df_time, how="left",on=['bug_id', 'bug_ID', 'TEST'])
    print ('df_new:',len(df_new))
    df_new.to_csv("{}/exp5.csv".format(father_dir))
    print "-"*100
    print df_new["time_mean"].isnull().values.any()

if __name__ == "__main__":
    items = ['opennlp', 'commons-imaging','commons-compress','commons-lang', 'commons-math']
    for item in items:
        p = "/home/eranhe/eran/bug_miner/{}".format(item)
        print (item)
        project_path = "{}/res".format(p)
        df = get_all_data_time_project(project_path)
        project_path = "{}/time.csv".format(p)
        group_by_time_class(project_path,df)
        merge_time_exp("{}/out/exp2.csv".format(p),"{}/out/time_grouped.csv".format(p))