import os
import pandas as pd
import numpy as np
import pit_render_test as pt
import git_util
import git_evosuite as ge

def csv_commit_db(csv_db,repo,out_dir_path,is_max=True,is_test=True,only_java=True):

    df = pd.read_csv(csv_db, names=['component_path', 'commit', 'issue', 'LOC_change'])

    df['is_java_file'] = df['component_path'].apply(lambda x: str(x).split('.')[-1])
    df['is_java'] = np.where(df['is_java_file'] == 'java', 1, 0)
    df['src/tset'] =  df['component_path'].apply(lambda x: 1 if str(x).__contains__(r'src\test') else 0)
    df['first_name'] = df['component_path'].apply(lambda x: str(x).split('\\')[1])
    df['comp_name'] = df['component_path'].apply(lambda x: str(x).split('\\')[-1].split('.')[0])
    df['suffix_test'] = df['comp_name'].apply(lambda x: 1 if str(x).endswith('Test') else 0)
    df['is_test'] = np.where(df['first_name'] == 'test', 1, 0)
    df.to_csv('{}/tmp_1.csv'.format(out_dir_path))
    print "df_size = {}".format(len(df))

    if only_java:
        df = df.loc[df['is_java'] > 0 ]
        print "After cleaning the non java component df_size = {}".format(len(df))

    if is_test:
        df = df[df['is_test'] == 0 ]
        df = df[df['src/tset'] == 0 ]
        print "After cleaning the test component df_size = {}".format(len(df))

    if is_max:
        df = df.groupby('issue').apply(
            lambda x: x.loc[x['LOC_change'].idxmax(), ['component_path', 'commit', 'LOC_change','is_test']]).reset_index()


    df.to_csv('{}/tmp.csv'.format(out_dir_path))
    df['parent'] = df['commit'].apply(lambda x: get_the_previous_commit(x,repo))
    df['tag_commit'] =  df['commit'].apply(lambda x: ge.get_Tag_name_by_commit(x,repo))
    df['date_commit'] =  df['commit'].apply(lambda x: get_the_Date_commit(x,repo))
    df['tag_parent'] =  df['parent'].apply(lambda x: ge.get_Tag_name_by_commit(x,repo))
    df['date_commit'] = pd.to_datetime(df['date_commit'])
    df["module"] = np.nan
    # make path to package name
    df['fail_component'] = df['component_path'].apply(lambda x: '.'.join(str(pt.path_to_package('org', x, -5)).split('\\')))
    df['package'] = df['fail_component'].apply(lambda x: '.'.join(str(x).split('.')[:-1]))

    # sorted DF
    df.sort_values("date_commit", inplace=True)
    df = df.reset_index(drop=True)
    df['index_bug'] = df.index

    # Split to train and test
    cut_df(df,out_dir_path)
    # write the whole df to disk
    df.to_csv('{}/commit_file_modify.csv'.format(out_dir_path))

def cut_df(df,out_dir_path,split=0.2):
    from sklearn.model_selection import train_test_split
    size = len(df)
    split_row = int(float(size)*split)
    bin = size-split_row
    print "bin:\t",bin
    print "size:\t",size
    print "split_row:\t",split_row

    train_df = df.loc[df.index <= bin]
    test_df = df.loc[df.index > bin]

    #train_df, test_df = train_test_split(df, test_size=0.2)
    train_df.to_csv('{}/train.csv'.format(out_dir_path))
    test_df.to_csv('{}/test.csv'.format(out_dir_path))

def get_the_previous_commit(commit_id,repo,n=1):
    print "commit_id:\t",commit_id
    print 'repo:\t',repo
    print 'p1'
    command= 'git log {}~{} -n 1'.format(commit_id,n)
    print 'p2'
    stdout, stderr = ge.run_GIT_command_and_log(repo,command,None,None,log=False)
    print 'p3'
    ans = git_util.pars_commit_block(stdout,None)
    print 'p4'
    return ans['id_commit']


def get_the_Date_commit(commit_id,repo):
    command= 'git log {} -n 1'.format(commit_id)
    stdout, stderr = ge.run_GIT_command_and_log(repo,command,None,None,log=False)
    ans = git_util.pars_commit_block(stdout,None)
    return ans['Date']

def make_FP_pred(dir_target='/home/ise/tmp_d4j/out_pred/out/Lang/Lang_2'):
    '''
    concat the two csv files from the weka dir to one big Dateframe and make the probabily for bug,
    by 1-probablit for a vaild component
    '''
    out = '/'.join(str(dir_target).split('/')[:-1])
    name = str(dir_target).split('/')[-1]
    p_name = str(name).split('_')[0]
    res_test_set = pt.walk_rec(dir_target,[],'testing__results_pred.csv')
    most_csv = pt.walk_rec(dir_target,[],'Most_names_File.csv')
    if len(most_csv)==1 and len(res_test_set)==1 is False:
        print "[Error] no csv in the dir-> {}".format(dir_target)
        return None

    connect_name_pred_FP( most_csv, name, p_name, res_test_set,dir_target)


def connect_name_pred_FP( most_csv_name, p_name, csv_pred,dir_target=None):
    if dir_target is None:
        dir_target = '/'.join(str(csv_pred).split('/')[:-1])
    df_most = pd.read_csv(most_csv_name, names=['class'])
    df_res = pd.read_csv(csv_pred)
    print 'df_most: ', list(df_most), '\tsize: ', len(df_most)
    print 'df_res: ', list(df_res), '\tsize: ', len(df_res)
    df = pd.concat([df_res, df_most], axis=1)
    df['FP'] = float(1) - df['prediction']
    df['name'] = df['class'].apply(lambda x: path_to_package_name(p_name, x))
    if p_name == 'Math':
        df['name_genric'] = df['name'].apply(
            lambda x: str(x).replace('.math2.', '.math.').replace('.math3.', '.math.').replace('.math4.', '.math.'))
    if p_name == 'Lang':
        df['name_genric'] = df['name'].apply(
            lambda x: str(x).replace('.lang2.', '.lang.').replace('.lang3.', '.lang.').replace('.lang4.', '.lang.'))
    df.to_csv("{}/{}_FP.csv".format(dir_target, p_name))
    return df




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


if __name__ == "__main__":
    pig_name = '/home/ise/bug_miner/PIG/Most_names_File.csv'
    pig_pred = '/home/ise/bug_miner/PIG/testing__results_pred_I_3K.csv.csv'
    dv_commit = '/home/ise/bug_miner/PIG/db_commit.csv'
    dir_db = '/home/ise/bug_miner/db_bugs'


    repo='/home/ise/bug_miner/commons-math/commons-math'
    db_Csv = '/home/ise/bug_miner/db_bugs/commons-math_db.csv'
    out = '/home/ise/bug_miner/commons-math/out'

    repo = '/home/ise/bug_miner/accumulo/accumulo'
    db_Csv = '/home/ise/bug_miner/db_bugs/accumulo_db.csv'
    out = '/home/ise/bug_miner/accumulo/out'

    csv_commit_db(repo=repo,out_dir_path=out,csv_db=db_Csv)


    print("done--"*8)