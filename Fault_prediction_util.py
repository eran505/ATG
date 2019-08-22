import os
import pandas as pd
import numpy as np
import pit_render_test as pt
import git_util
import git_evosuite as ge
from csv_D4J_headler import path_to_package_name

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

    repo_name = str(repo).split('/')[-1]

    # Split to train and test
    cut_df(df,out_dir_path)
    # write the whole df to disk
    df.to_csv('{}/{}_bug.csv'.format(out_dir_path,repo_name))

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



def add_FP_val(project,xgb=True):
    father_dir ='/home/ise/bug_miner/{}'.format(project)
    df_exp = pd.read_csv('{}/exp.csv'.format(father_dir),index_col=0)
    res_fp_dfs = pt.walk_rec('{}/FP'.format(father_dir),[],'FP.csv')
    if xgb:
        res_fp_dfs = pt.walk_rec('{}/FP/best_FP/best'.format(father_dir), [], '.csv')
    all_df_fps=[]
    for item in res_fp_dfs:
        df_i = pd.read_csv(item,index_col=0)
        if xgb is False:
            tag_name = '_'.join(str(item).split('/')[-1].split('_')[:-1])
        else:
            if project=='commons-math':
                tag_name ='_'.join(str(item).split('/')[-1].split('_CONF_')[0].split('_')[1:])
            elif project == 'commons-lang':
                tag_name = '_'.join(str(item).split('/')[-1].split('_CONF_')[0].split('_')[2:])
            elif project == 'commons-net':
                tag_name = '_'.join(str(item).split('/')[-1].split('_CONF_')[0].split('_')[2:])
            else:
                tag_name = '_'.join(str(item).split('/')[-1].split('_CONF_')[0].split('_')[2:])
        df_i['tag'] = tag_name
        print tag_name
        all_df_fps.append(df_i)
    df_all_fp = pd.concat(all_df_fps)
    df_info=pd.read_csv('/home/ise/eran/repo/ATG/tmp_files/{}_bug.csv'.format(project),index_col=0)
    print list(df_info)
    print list(df_exp)
    print list(df_all_fp)
    # add tag to exp DF
    df_info= df_info[['issue','tag_parent']]
    print len(df_exp)
    res_exp = pd.merge(df_exp,df_info,'left',right_on=['issue'],left_on=['bug_name'])
    print len(res_exp)
    res_exp.to_csv('{}/exp_new.csv'.format(father_dir))

    # get sorted version repo
    git_command = r"git for-each-ref --sort=taggerdate --format '%(tag)' "
    #git_command = r"git tag"

    std_out,std_err = ge.run_GIT_command_and_log('{}/{}'.format(father_dir,project),git_command,None,None,False)
    arry_tag_sorted = str(std_out).split()
    arry_tag_sorted = [ str(x).replace('-','_').replace('.','_').replace('/','_') for x in arry_tag_sorted]
    arry_tag_sorted.append('master')

    # make a Genric class path
    print list(res_exp)
    print list(df_all_fp)
    res_exp['G_package']=res_exp['name'].apply(lambda x: '.'.join(str(x).split('.')[4:]))
    df_all_fp['G_package']=df_all_fp['name'].apply(lambda x: '.'.join(str(x).split('.')[4:]))
    df_all_fp.to_csv('{}/df_all_fp.csv'.format(father_dir))
   ### exit()


    # Fill the FP
    res_exp['fault_pred_raw'] = res_exp.apply(add_FP_val_helper,sorted_tag=arry_tag_sorted,fp_df_all=df_all_fp,axis=1)
    res_exp['FP'] = res_exp['fault_pred_raw'].apply(lambda x: str(x).split('_')[0] if x is not None else None)
    res_exp['tag_FP_val'] = res_exp['fault_pred_raw'].apply(lambda x: '_'.join(str(x).split('_')[1:]) if x is not None else None)
    res_exp.drop('fault_pred_raw', axis=1, inplace=True)

    res_exp = prep_df_for_exp(res_exp)

    if 'test_case_fail_num' in res_exp:
        to_del = ['test_case_fail_num']
        print len(res_exp)
        res_exp.drop(to_del, axis=1, inplace=True)
        res_exp.drop_duplicates(subset=['LOC', 'bug_ID', 'TEST', 'bug_id', 'mode', 'time', 'faulty_class', 'sum_detected', 'count_detected', 'issue', 'tag_parent', 'G_package', 'FP', 'tag_FP_val', 'LOC_P'],inplace=True)
        print len(res_exp)

    res_exp.to_csv('{}/exp_new_new.csv'.format(father_dir))


def prep_df_for_exp(df):
    max_LOC = df['LOC'].max()
    min_LOC = df['LOC'].min()
    df['LOC_P'] = df['LOC'].apply(lambda x: float(x - min_LOC) / float(max_LOC - min_LOC))
    df['Random'] = np.random.random_sample(size=len(df))
    df.rename(columns={'name': 'TEST', 'count_rep': 'count_detected','bug_name':'bug_ID',
                       'sum_rep':'sum_detected','is_faulty':'faulty_class'}, inplace=True)

    return df

def add_FP_val_helper(row,sorted_tag,fp_df_all,col_name_class='name'):
    tag_cur = row['tag_parent']
    tag_cur = str(tag_cur).replace('-','_').replace('.','_').replace('/','_')
    klass = row[col_name_class]
    print "tag_cur={}".format(tag_cur)
    try:
        index_start = list(sorted_tag).index(tag_cur)
    except Exception as e:
        print '[Error] in the add_FP_val_helper function e={}'.format(e.message)
        return None
    cut_list = sorted_tag[:index_start+1]
    cut_list.reverse()
    for tag in cut_list:
        print tag
        filter_tag_df = fp_df_all[fp_df_all['tag']==tag]
        if len(filter_tag_df)>0:
            filter_klass = filter_tag_df[filter_tag_df[col_name_class]==klass]
            if len(filter_klass)>0:
                if row['is_faulty']>0:
                    print "max"
                    fp_val = filter_klass['FP'].max()
                else:
                    #fp_val = filter_klass['FP'].min()
                    fp_val = filter_klass['FP'].iloc[0]
                    fp_val = filter_klass['FP'].mean()
                    #fp_val = filter_klass['FP'].median()
                return '{}_{}'.format(fp_val,tag)


    ########
    cut_list = sorted_tag
    for tag in cut_list:
        print tag
        filter_tag_df = fp_df_all[fp_df_all['tag'] == tag]
        if len(filter_tag_df) > 0:
            filter_klass = filter_tag_df[filter_tag_df[col_name_class] == klass]
            if len(filter_klass) > 0:
                if row['is_faulty'] > 0:
                    print "max"
                    fp_val = filter_klass['FP'].max()
                else:
                    # fp_val = filter_klass['FP'].min()
                    fp_val = filter_klass['FP'].iloc[0]
                return '{}_{}'.format(fp_val, tag)
    return None

def path_to_package_name(p_name,path_input):
    item = str(path_input).replace('\\','/')
    start_package = 'org'
    if p_name == 'opennlp':
        start_package = 'opennlp'
    if item[-5:] != '.java':
        return None
    try:
        pack = pt.path_to_package(start_package, item, -1 * len('.java'))
    except Exception as e:
        pack=None
    return pack



def get_miss_classes(project_path_repo,fp_name_dir,out_info):
    '''
    the main func that count the missing class inrespect to the bug commit and FP results tags
    '''
    project = str(project_path_repo).split('/')[-1]
    atg_path=os.getcwd()
    df_bug = pd.read_csv('{}/tmp_files/{}_bug.csv'.format(atg_path,project))
    print list(df_bug)
    res_file = pt.walk_rec(fp_name_dir,[],'Most_names')
    d_name_tag={}
    tag_l=[]
    for item in res_file:
        tag_name = '_'.join(str(item).split('/')[-2].split('_')[1:])
        tag_index = str(item).split('/')[-2].split('_')[0]
        tag_l.append([tag_name,int(tag_index)])
        d_name_tag[tag_name]={'csv':item,'index':tag_index}

    # get sorted list tags
    sorted_tags = sorted(tag_l, key=lambda tup: tup[-1])
    tags_sort = []
    for item_t in sorted_tags:
        tags_sort.append(item_t[0])

    # Go over each bug commit and get the list of classes
  #  df_bug.apply(get_miss_classes_applyer,out_dir=out_info,repo_path=project_path_repo,axis=1)

    # make a comparison
    res_csv = pt.walk_rec(out_info,[],'.csv')

    for item in res_csv:
        df_commit = pd.read_csv(item,index_col=0)
        if len(df_commit)==0:
            continue
        tag_bug = df_commit['tag_bug'].iloc[0]
        tag_bug = str(tag_bug).replace('-','_')
        df_fp_res_tag_cur = pd.read_csv(d_name_tag[tag_bug]['csv'],names=['path'])
        index = tags_sort.index(tag_name)
        if index>0:
            old_tag = tags_sort[index-1]
            df_fp_res_tag_old = pd.read_csv(d_name_tag[old_tag]['csv'], names=['path'])
            df_fp_res_tag_old['name'] = df_fp_res_tag_old['path'].apply(lambda x: path_to_package_name(None,x))
        else:
            df_fp_res_tag_old=None
        df_fp_res_tag_cur['name'] = df_fp_res_tag_cur['path'].apply(lambda x: path_to_package_name(None, x))
        df_commit['is_exists'] = df_commit.apply(is_exists_helper,df_cur=df_fp_res_tag_cur,df_old=df_fp_res_tag_old,axis=1)
        df_commit.to_csv('{}_mod.csv'.format(str(item)[:-4]))

        # get all mod file
        res_mod(out_info)

def res_mod(out_info):
    res_mod = pt.walk_rec(out_info, [], 'mod.csv')
    l_df = []
    for item in res_mod:
        l_df.append(pd.read_csv(item, index_col=0))
    df_all = pd.concat(l_df)
    x = df_all['is_exists'].value_counts()
    print "missing class % \n {}".format(x)

def is_exists_helper(row,df_cur,df_old):
    class_name = row['name']

    # try find the name in the cur df
    res_cur = df_cur.loc[df_cur['name'] == class_name, 'path']
    print len(res_cur)
    if len(res_cur) == 0 :
        res_old = df_old.loc[df_old['name'] == class_name, 'path']
        if len(res_old)==0:
            return 0

    return 1


def get_miss_classes_applyer(row,out_dir,repo_path):
    '''
    Go over each bug commit and get the list of classes
    '''
    commit_bug=row['parent']
    commit_fix = row['commit']
    bug_tag = row['tag_parent']
    issue_id = row['issue']
    index_bug = row['index_bug']

    #checkout the buugy version
    git_cmd = 'git checkout {}'.format(commit_bug)
    print ge.run_GIT_command_and_log(repo_path,git_cmd,None,None,False)

    # get classes from src
    d_l=[]
    res = pt.walk_rec('{}/src'.format(repo_path),[],'.java')
    for item_java in res:
        class_name = pt.path_to_package('org',item_java,-5)
        d_l.append({'class_path':item_java,'name':class_name,'tag_bug':bug_tag,'commit_bug':commit_bug})
    df = pd.DataFrame(d_l)
    df.to_csv('{}/{}_{}.csv'.format(out_dir,issue_id,index_bug))




def xgb_FP_wrapper(info_weka_dir,results_csv,mode='most',out_dir=None):
    '''
    this function is mereging the name file with the pred file on the XGBoost model
    '''
    # get the info from the Weka dir
    dico_info = get_weka_info(info_weka_dir,mode)

    # get the results from the FP-Model
    d_results={}
    csvz_res = pt.walk_rec(results_csv,[],'.csv')
    for item in csvz_res :
        file_name = str(item).split('/')[-1][:-4]
        proj_minor_name = str(file_name).split('_CONF_')[0][2:]
        conf_ID = str(file_name).split('_CONF_')[1].split('_')[0]
        d_results[file_name]={'conf':conf_ID,'file_pred':item,'minor':proj_minor_name}
        if proj_minor_name in dico_info:
            name_path = dico_info[proj_minor_name]['name']
            d_results[file_name]['name']=name_path
        else:
            print '[Error] MISSING --> {}'.format(proj_minor_name)
    name_d = None
    # tmp section
    name_d = {}
    for k_i in dico_info.keys():
        csv_path_name_file_i = dico_info[k_i]['name']
        df_tmp = pd.read_csv(csv_path_name_file_i)
        size_len = len(df_tmp)
        if size_len not in name_d:
            name_d[size_len]=[]
        name_d[size_len].append(csv_path_name_file_i)

    # the merge process
    for ky in d_results.keys():
        merge_xgboost_name_pred(d_results[ky]['name'],d_results[ky]['file_pred'],out_dir,d_name=name_d)


def merge_xgboost_name_pred(name_file,pred_csv,out=None,debug=False,d_name=None):
    name_file_i=str(pred_csv).split('/')[-1][:-4]
    df_name = pd.read_csv(name_file,names=['path'])
    df_pred = pd.read_csv(pred_csv,index_col=0)
    if len(df_name) != len(df_pred):

        print 'df_name={} \n df_pred={}'.format(len(df_name),len(df_pred))
        print "ERRRORRRR"
        return
    df = pd.concat([df_name, df_pred], axis=1)
    df.drop(['name'], inplace=True, axis=1, errors='ignore')
    df['FP'] = df['test_predictions'].apply(lambda x: x if x < 0 else x)
    df['name'] = df['path'].apply(lambda x: path_to_package_name('', x))
    size_s = len(df)
    df = df.dropna()
    if debug:
        if size_s-len(df) > 0:
            print "[Debug] from {} del num rows:\t{}".format(name_file_i,size_s-len(df))
    if out is None:
        df.to_csv(pred_csv)
    else:
        df.to_csv('{}/FP_{}.csv'.format(out,name_file_i))


def get_weka_info(p_path,mode):
    d_tags = {}
    res = pt.walk_rec(p_path, [], '_{}'.format(mode), False)
    arff_path, pred_1_path = None, None
    for item in res:
        if str(item).endswith('arff_{}'.format(mode)):
            arff_path = item
        elif str(item).endswith('pred_1_{}'.format(mode)):
            pred_1_path = item
    res_minor = pt.walk_rec(pred_1_path, [], '', False, lv=-1)
    res_models = pt.walk_rec(arff_path, [], '.arff')
    for item in res_minor:
        name = '_'.join(str(item).split('/')[-1].split('_')[1:])
        index_sort = str(item).split('/')[-1].split('_')[0]
        files_res = pt.walk_rec(item, [], '')
        d_tags[name] = {'sort_index': index_sort}
        d_tags[name]['model'] = None
        for file_i in files_res:
            if str(file_i).endswith('.csv'):
                d_tags[name]['name'] = file_i
            elif str(file_i).endswith(".arff"):
                d_tags[name]['test'] = file_i
    for item_arff in res_models:
        name = str(item_arff).split('/')[-1].split('.')[0]
        if name in d_tags:
            d_tags[name]['model'] = item_arff
        else:
            d_tags[name] = {'model': item_arff, 'test': None, 'name': None, 'sort_index': None}
    return d_tags

def rearrange_folder_conf_xgb(p_path_dir='/home/ise/bug_miner/XGB/Lang_DATA/csv_res/TEST'):
    res_csv_all = pt.walk_rec(p_path_dir,[],'.csv')
    for i in res_csv_all:
        tmp=str(i).split('/')[-1].split('_')
        num_conf= tmp[-2]
        path_conf_dir = pt.mkdir_system(p_path_dir,'conf_{}'.format(num_conf),False)
        os.system('mv {} {}'.format(i,path_conf_dir))
    exit()
if __name__ == "__main__":


    results_csvz = '/home/ise/bug_miner/XGB/csv_res/TEST'
    weka_info = '/home/ise/bug_miner/commons-compress/FP/all_compress'
    out_dir = '/home/ise/bug_miner/commons-compress/FP/xgb'
    #rearrange_folder_conf_xgb(out_dir )

    #xgb_FP_wrapper(weka_info,results_csvz,out_dir=out_dir)
    add_FP_val('commons-compress')
    #add_FP_val('commons-lang')
    ##add_FP_val('commons-math')
    #add_FP_val('opennlp')
    exit()



    repo='/home/ise/bug_miner/commons-math/commons-math'
    db_Csv = '/home/ise/bug_miner/db_bugs/commons-math_db.csv'
    out = '/home/ise/bug_miner/commons-math/out'

    repo = '/home/ise/bug_miner/commons-validator/commons-validator'
    db_Csv = '/home/ise/bug_miner/db_bugs/commons_validator_db.csv'
    out = '/home/ise/bug_miner/commons-validator'

    repo='/home/ise/bug_miner/commons-compress/commons-compress'
    db_Csv='/home/ise/bug_miner/db_bugs/commons-compress_db.csv'
    out='/home/ise/bug_miner/commons-compress'



    csv_commit_db(repo=repo,out_dir_path=out,csv_db=db_Csv)


    print("done--"*8)