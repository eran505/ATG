from subprocess import Popen, PIPE, check_call, check_output
import subprocess
import pit_render_test as pt
import shlex
import sys
import os.path
import git,re
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

import pit_render_test as pt
import pandas as pd

path_defect4j = '/home/ise/programs/defects4j/framework/bin/defects4j'
project_dict = {}


def befor_op():
    project_dict['Chart'] = {'project_name': "JFreechart", "num_bugs": 26, 'repo_path': '/home/ise/tmp_d4j/jfreechart'
                             }

    project_dict['Closure'] = {'project_name': "Closure compiler", "num_bugs": 133, 'repo_path': '/home/ise/tmp_d4j/closure-compiler'}

    project_dict['Lang'] = {'project_name': "Apache commons-lang", "num_bugs": 65,
                            'repo_path': '/home/ise/tmp_d4j/commons-lang'
        , 'issue_tracker': 'jira', 'issue_tracker_url': 'https://issues.apache.org/jira',
                            'issue_tracker_product_name': 'LANG',
                            'git': r'C:\Users\eranhe\Fault_Predicition_Defect4J\repo\commons-lang', 'workingDir': ''}

    project_dict['Math'] = {'project_name': "Apache commons-math", "num_bugs": 106,
                            'repo_path': '/home/ise/tmp_d4j/commons-math'
        , 'issue_tracker': 'jira', 'issue_tracker_url': 'https://issues.apache.org/jira',
                            'issue_tracker_product_name': 'MATH',
                            'git': r'C:\Users\eranhe\Fault_Predicition_Defect4J\repo\commons-math', 'workingDir': ''}

    project_dict['Mockito'] = {'project_name': "Mockito", "num_bugs": 38, 'repo_path': '/home/ise/tmp_d4j/mockito',
                               'issue_tracker_product_name': 'mockito', 'issue_tracker_url': 'mockito',
                               'issue_tracker': 'github','git': r'C:\Users\eranhe\Fault_Predicition_Defect4J\repo\mockito'}

    project_dict['Time'] = {'project_name': "Joda-Time", 'repo_path': '/home/ise/tmp_d4j/joda-time', "num_bugs": 27}

    project_dict['tika'] = {'project_name': "tika", 'repo_path': '/home/ise/eran/git_repos/tika', "num_bugs": 1000}

    project_dict['commons-math'] = {'project_name': "commons-math", 'repo_path': '/home/ise/bug_miner/math/commons-math', "num_bugs": 1000}

    project_dict['commons-lang'] = {'project_name': "commons-lang",'repo_path': '/home/ise/bug_miner/lang/commons-lang', "num_bugs": 1000}


def new_data_set():
    project_dict['accumulo']={'repo_path':'/home/ise/programs/bugs-dot-jar/accumulo'}
    project_dict['camel'] = {'repo_path': '/home/ise/programs/bugs-dot-jar/camel'}
    project_dict['commons-math'] = {'repo_path': '/home/ise/programs/bugs-dot-jar/commons-math'}
    project_dict['flink'] = {'repo_path': '/home/ise/programs/bugs-dot-jar/flink'}
    project_dict['jackrabbit-oak'] = {'repo_path': '/home/ise/programs/bugs-dot-jar/jackrabbit-oak'}
    project_dict['maven'] = {'repo_path': '/home/ise/programs/bugs-dot-jar/maven'}
    project_dict['wicket'] = {'repo_path': '/home/ise/programs/bugs-dot-jar/wicket'}
    project_dict['logging-log4j2'] = {'repo_path': '/home/ise/programs/bugs-dot-jar/logging-log4j2'}

def extract_data(p_name, id):
    str_c = "/home/ise/programs/defects4j/framework/bin/defects4j info -p  {1} -b {0}".format(id, p_name)
    print str_c
    result = subprocess.check_output(str_c, shell=True)
    x = result.find("List of modified sources:")
    date_index = result.find("Revision date (fixed version):")
    stoper = result.find("Root cause in triggering tests")

    data_time = result[date_index + len("Revision date (fixed version):"):stoper].replace('-', "")
    try:
        data_time = data_time.replace('\n', "").split()[0]
    except Exception:  # TODO: fix it by looking at the comiit id and the date !!!! <------ this fix is very importenet (id 25 mockito [bug])
        print "[EError] in Date"
        data_time = '20120101'
    year = data_time[:4]
    month = data_time[4:6]
    day = data_time[-2:]
    str_data_bug = "{}_{}_{}".format(year, month, day)
    print str_data_bug
    # for Debug ----------------------------------------------------------------
    #with open(out_file_name, "a") as myfile:
    #    myfile.write('\n')
    #    myfile.write("{},{},{}".format(p_name, id, str_data_bug))
    #print 'date : %s' % str_data_bug
    return str_data_bug
    # for Debug -----------------------------------------------------------------


def get_commit_id(csv_path, tmp_dir='/home/ise/', p_name='Math'):
    df = pd.read_csv(csv_path, index_col=0)
    df.reset_index(drop=True, inplace=True)
    out = pt.mkdir_system(tmp_dir, 'tmp_d4j', False)
    out_csv = pt.mkdir_system(out, 'projects', False)
    out_git = pt.mkdir_system(out, 'gits', True)
    df['date_commit_buggy'] = df.apply(get_date_revsion,out=out_git,p_name=p_name,axis=1)
    df.to_csv('{}/{}_commit.csv'.format(out_csv,p_name))
    get_date_commit_repoGIT(project_dict[p_name]['repo_path'], '{}/{}_commit.csv'.format(out_csv, p_name))


def get_date_revsion(row, out, p_name):
    bug_id = row['bug_ID']
    buggy_commit_id = row['buggy_commit_id']
    out_dir_path_git = "{0}/P_{1}_B_{2}_buggy/".format(out, p_name, bug_id)
    cmd_in = '{0} checkout -p {1} -v {2}"{3}" -w {4}/P_{5}_B_{6}_buggy/'.format(path_defect4j, p_name, bug_id, 'b', out,
                                                                                p_name, bug_id)
    print cmd_in
    process = Popen(shlex.split(cmd_in), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print stdout
    print "err:\n"
    print stderr
    date_time = get_date_git(out_dir_path_git, buggy_commit_id)
    return date_time


def get_killable_bugs(p_name='Math', out='/home/ise/eran/out_csvs_D4j'):
    out_p = pt.mkdir_system(out, 'killable', False)
    csv_path = '/home/ise/eran/out_csvs_D4j/rep_exp/out_{}.csv'.format(p_name)
    df = pd.read_csv(csv_path)
    csv_commit_db_path = '/home/ise/programs/defects4j/framework/projects/{}/commit-db'.format(p_name)
    commit_db = pd.read_csv(csv_commit_db_path, names=['bug_ID', 'buggy_commit_id', 'fixed_commit_id'])
    df = df.loc[df['kill_val'] > 0]
    print list(df)
    print list(commit_db)
    df_mereg = pd.merge(df, commit_db, on=['bug_ID'], how='right')
    out_df = df_mereg[['bug_ID', 'buggy_commit_id', 'fixed_commit_id']]
    out_df.drop_duplicates(inplace=True)
    out_df.to_csv('{}/{}_killable_commit_ID.csv'.format(out_p, p_name))


def get_date_commit_repoGIT(path_dir='/home/ise/tmp_d4j/commons-math',
                            csv_path='/home/ise/tmp_d4j/projects/Math_commit.csv'):
    df = pd.read_csv(csv_path, index_col=0)
    print list(df)
    df['buggy_Git_ID_commit'] = df.apply(get_correspond_commit_id, repo_path=path_dir, axis=1)
    csv_out = '/'.join(str(csv_path).split('/')[:-1])
    name = str(csv_path).split('/')[-1][:-4]
    df.to_csv('{}/{}_Git.csv'.format(csv_out, name))


def get_correspond_commit_id(row, repo_path):
    date = row['date_commit_buggy']
    dt = parse(date)
    stdout, stderr = commit_log_by_day(dt, dt, repo_path)
    if len(stdout) < 2:
        new_dt = dt + relativedelta(year=dt.year - 1)
        stdout, stderr = commit_log_by_day(new_dt, dt, repo_path)
    print "err:\n"
    print stderr
    acc = ''
    for index in range(len(stdout)):
        if stdout[index] == '\n':
            break
        acc += stdout[index]
    res_index = acc.find('commit')
    res = acc[res_index + len('commit') + 1:]
    return res


def commit_log_by_day(after, untill, repo_path):
    print "after == {}    untill == {}".format(after, untill)
    os.chdir(repo_path)
    cmd_in = 'git log --pretty --after="{}" --until="{}"'.format(after, untill)
    process = Popen(shlex.split(cmd_in), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr

def run_GIT_command_and_log(repo_path, cmd, log_dir, name, log=True):
    '''
    run git command
    '''
    os.chdir(repo_path)
    process = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if log:
        log_to_file(log_dir, '{}_stderr'.format(name), stderr)
        log_to_file(log_dir, '{}_stdout'.format(name), stdout)
    return stdout, stderr


def log_to_file(dir_log, name_file, txt_to_log):
    '''
    log the info into a log file
    '''
    with open('{}/{}.log'.format(dir_log, name_file), 'w+') as file_log:
        file_log.write(txt_to_log)


def get_date_git(dir_p, commit_id):
    repo = git.Repo(dir_p)
    g = git.Git(dir_p)
    loginfo = g.log()
    res = get_date_log_info(loginfo.encode('utf8'), commit_id)
    return res


def get_date_log_info(info_txt, commit_id='f5bcba812fb8bc59ff5e4bc055811039b610aa2b'):
    print "commit_id:== {}".format(commit_id)
    res = str(info_txt).find(commit_id)
    print res
    acc = ''
    for index in range(res, len(info_txt)):
        if info_txt[index] == '\n':
            if acc.__contains__('Date:'):
                acc = acc[5:].replace('   ', '')
                print acc
                return acc
            else:
                acc = ''
                continue
        acc += info_txt[index]
    return None


def main():
    res = pt.walk_rec('/home/ise/eran/out_csvs_D4j/killable', [], '.csv')
    for csv_p in res:
        project_name = str(csv_p).split('/')[-1].split('_')[0]
        if project_name == 'Chart':
            get_commit_id(csv_p, p_name=project_name)


def get_Version_name_via_commit(commit_id,p_name):
    '''
    get the version that the commit id contains in.
    '''
    if p_name is None:
        return None
    path_repo = project_dict[p_name]['repo_path']
    command_git = 'git describe --tag {}'.format(commit_id)
    std_out, std_err = run_GIT_command_and_log(path_repo, command_git, None, None, False)
    if len(std_out) < 1:
        command_git = 'git describe --contains {}'.format(commit_id)
        std_out, std_err = run_GIT_command_and_log(path_repo, command_git, None, None,False)
        if len(std_out)<1:
            command_git = 'git describe --tag --contains --all {}'.format(commit_id)
            std_out, std_err = run_GIT_command_and_log(path_repo, command_git, None, None, False)
            if len(std_out) < 1:
                print "[Error] the stdout return empty --> {} ".format(commit_id)
                return None
    if str(std_out).__contains__('~'):
        delim='~'
    elif str(std_out).__contains__('-'):
        delim = '-'
    elif str(std_out).__contains__('^'):
        delim = '^'
    else:
        return std_out
    current_tag = str(std_out).split(delim)[0]
    if current_tag.__contains__('^'):
        current_tag = current_tag.split('^')[0]
    current_tag = current_tag.replace('\n', '')
    return current_tag

def make_auto_config_TAG(out_dir, log_dir, project_name='Math', commit_id='8c2199df0f613c63bd362303c953cee66712d56c',
                         time_bol=False,single=True):
    path_repo = project_dict[project_name]['repo_path']
    if os.path.isdir(path_repo) is False:
        print "the path is not valid ==> {}".format(path_repo)
        return None
    os.chdir(path_repo)
    command_git = 'git describe --contains {}'.format(commit_id)
    std_out, std_err = run_GIT_command_and_log(path_repo, command_git, log_dir, '{}_TagLookup'.format(commit_id))
    if len(std_out) < 1:
        print "[Error] the stdout return empty "
        return None
    current_tag = str(std_out).split('~')[0]
    if current_tag.__contains__('^'):
        current_tag = current_tag.split('^')[0]
    current_tag = current_tag.replace('\n', '')
    if single:
        return current_tag
    # the section below is to get older TAG name for the config file
    list_tag,std_out=get_sorted_git_tag(p_name=project_name)
    res = get_previous_TAG(current_tag, std_out, time=time_bol)
    if res is None:
        return None
    return ','.join(res)


def get_previous_TAG(cur, list_all_tags, num_prev=4, time_back_in_month=6, time=False):
    arr_tags = str(list_all_tags).split('\n')
    arr_tag_date = []
    arr_tags_name = []
    for item in arr_tags:
        if item.__contains__('\t'):
            arr_tag_date.append(item.split('\t')[1])
            arr_tags_name.append(item.split('\t')[0])
    size = len(arr_tags)
    print "-"*199
    for i in range(len(arr_tags_name)):
        print "{}\t\t{}".format(arr_tags_name[i],arr_tag_date[i])
    print "cur= {}".format(cur)
    index_cur = arr_tags_name.index(cur)
    if index_cur < 0:
        print "[Error] cant find the Tag in the list of all TAGS"
        return None
    if index_cur - num_prev < 0:
        num_prev = index_cur
        if time:
            return arr_tag_date[:num_prev+1]
        return arr_tags_name[:num_prev+1]
    if index_cur == size:
        print "[Error] the cur TAG is the newest version"
        return None
    res_date_index = subtract_time_date(arr_tag_date, index_cur)
    res_2 = arr_tags_name[res_date_index:index_cur + 2]
    if index_cur - num_prev < res_date_index:
        ans = arr_tags_name[index_cur - num_prev:index_cur + 2]
    else:
        result_arr = get_mid_point_list(res_2, num_point=num_prev)
        ans = result_arr
    date_res = []
    for tag in ans:
        date_res.append(arr_tag_date[arr_tags_name.index(tag)])
    if time:
        return date_res
    return ans


def get_mid_point_list(list_arr, num_point):
    size = len(list_arr)
    if size - num_point - 2 < 0:
        print "[Error] not enough points in the arr function rsie from get_mid_point_list"
        return None
    res = rec_mid(list_arr[1:-2], num_point - 2)
    res = [list_arr[0]] + res
    res.extend(list_arr[-2:])
    return res


def subtract_time_date(dates, cur_index):
    '''
    finding the nearset date to the cur date
    '''
    import datetime
    import dateutil.relativedelta
    cur_date = dates[cur_index]
    print cur_date[:-6]
    cur_date = datetime.datetime.strptime(cur_date[:-6], "%Y-%m-%d %H:%M:%S")
    dates = [datetime.datetime.strptime(x[:-6], "%Y-%m-%d %H:%M:%S") for x in dates]
    d = cur_date - dateutil.relativedelta.relativedelta(months=8)
    res_min = min(dates, key=lambda item_date: abs(item_date - d))
    return dates.index(res_min)


def rec_mid(list, num_item):
    '''
    give the mid points in the list (rec function)
    '''
    res = []
    num_item = num_item - 1
    if num_item == 0:
        return [list[len(list) / 2]]
    if len(list) == 1:
        return [list[0]]
    mid = len(list) / 2
    res.extend(rec_mid(list[mid:], num_item))
    res.extend(rec_mid(list[:mid], num_item))
    return res


def make_file_config(row, out_path, p_name):
    tags = row['TAG_NAME']
    commit_id = row['buggy_Git_ID_commit']
    git_path = project_dict[p_name]['git']
    workingDir = project_dict[p_name]['workingDir']
    issue_tracker_product_name = project_dict[p_name]['issue_tracker_product_name']
    issue_tracker_url = project_dict[p_name]['issue_tracker_url']
    issue_tracker = project_dict[p_name]['issue_tracker']
    str_info = 'workingDir={0}\r\ngit={1}\r\nissue_tracker_product_name={2}\r\nissue_tracker_url={3}\r\nissue_tracker={4}\r\nvers=({5})'.format(
        workingDir, git_path, issue_tracker_product_name, issue_tracker_url, issue_tracker, tags
    )
    with open('{}/{}.txt'.format(out_path, commit_id), 'w') as f_conf:
        f_conf.write(str_info)


def get_tag_commit(csv_file='/home/ise/tmp_d4j/projects/csvs/Closure_commit_Git.csv', out='/home/ise/tmp_d4j/config'):
    df = pd.read_csv(csv_file, index_col=0)
    project_name = str(csv_file).split('/')[-1].split('_')[0]
    out_proj_curr = pt.mkdir_system(out, '{}'.format(project_name),False)
    log_out_files = pt.mkdir_system(out_proj_curr, 'LOG',False)
    config_out_files = pt.mkdir_system(out_proj_curr, 'File_conf',False)
    df['TAG_NAME'] = df['buggy_Git_ID_commit'].apply(
        lambda commit_i: make_auto_config_TAG(config_out_files, log_out_files, project_name, commit_i))
    #df['TAG_DATE'] = df['buggy_Git_ID_commit'].apply(
    #    lambda commit_i: make_auto_config_TAG(config_out_files, log_out_files, project_name, commit_i, time_bol=True))
    df.to_csv('{}/df.csv'.format(out_proj_curr))
    #df.apply(make_file_config, out_path=config_out_files, p_name=project_name, axis=1)


def get_all_version_sorted(p_name):
    '''
    making file with all the version sorted by commit date
    '''
    repo_path = project_dict[p_name]['repo_path']
    df_path = "/home/ise/tmp_d4j/config/{}/df.csv".format(p_name)
    out = '/'.join(df_path.split('/')[:-1])
    df = pd.read_csv(df_path)
    list_tag = []
    for index, row in df.iterrows():
        val = row['TAG_NAME']
        arr = str(val).split(',')
        list_tag.extend(arr)
    list_tag = set(list_tag)
    list_tag = list(list_tag)
   # command_git = "git tag --sort=taggerdate"
   # std_out, std_err = run_GIT_command_and_log(repo_path, command_git, None, "", False)
   # list_sorted_tags = str(std_out).split('\n')
    var1,va2 = get_sorted_git_tag(p_name)
    list_sorted_tags = var1
    print list_sorted_tags
    res_tag = []
    for tag_i in list_sorted_tags:
        if tag_i in list_tag:
            res_tag.append(tag_i)
    with open('{}/tag.txt'.format(out), 'w') as f:
        f.write(','.join(res_tag))


def make_bug_date_D4j(out='/home/ise/tmp_d4j'):
    '''
    making a CSV file with date of all the projects bugs
    '''
    projects = ['Chart','Math','Lang','Time','Mockito','Closure']
    out_dir = pt.mkdir_system(out,'D4j_bugs_info',False)
    for name in projects:
        list_data=[]
        total_of_bugs = project_dict[name]['num_bugs']
        for bug_i in range(1,total_of_bugs+1):
            date_i = extract_data(name,bug_i)
            list_data.append({'project':name,'bug_ID':bug_i,'Date':date_i})
        df = pd.DataFrame(list_data)
        df.to_csv('{}/{}_Date.csv'.format(out_dir,name))


def get_date_tag_csv(p_name='Time'):
    p_path_repo = project_dict[p_name]['repo_path']
    command_git = "git tag --format='%(creatordate:short)%09%(refname:strip=2)' --sort=taggerdate"
    p_out='/home/ise/tmp_d4j/config/{}'.format(p_name)
    std_out, std_err = run_GIT_command_and_log(p_path_repo, command_git, None, "", False)
    arr_info = str(std_out).split('\n')
    d_l=[]
    for item in arr_info:
        if len(item)<1:
            continue
        tag_name = str(item).split('\t')[0]
        tag_date = str(item).split('\t')[1]
        if len(tag_name)>1:
            d_l.append({'project':p_name,'TAG_NAME':tag_name,'TAG_DATE':tag_date})
    df = pd.DataFrame(d_l)
    df.to_csv('{}/date_tag.csv'.format(p_out))

def pars_commit_msg(p_name='Time',out='/home/ise/tmp_d4j/config'):
    '''
    main function for parsing the commits on the repo project
    :param p_name:
    :param out:
    :return:
    '''
    print "pars_commit_msg({})".format(p_name)
    p_path_repo = project_dict[p_name]['repo_path']
    command_git = "git log --all "
    std_out, std_err = run_GIT_command_and_log(p_path_repo, command_git, None, "", False)
    look_for_commit(std_out,'{}/{}'.format(out,p_name),p_name)


def jira_is_bug(msg_str,p_name):
    uper_p_name = str(p_name).upper()
    rec = '{}-[0-9]+'.format(uper_p_name.lower())
    df = pd.read_csv('/home/ise/eran/git_repos/JIRA/{}/all.csv'.format(p_name.lower()))
    tmp = re.compile(rec).search(msg_str)
    list_cand=[]
    for item in tmp.regs:
        list_cand.append(msg_str[item[0]:item[1]])
    list_cand = [str(x).upper() for x in list_cand]
#    if msg_str.__contains__('tika-2599'):
#        print ""
    for x in list_cand:
        x= x.replace(' ','')
        if x in df['Issue key'].values:
            return 1, 'JIRA'

    return 0, 'not bug JIRA'

    #set_list = list(df['Issue key'].unique())
    #for cand in list_cand:
    #    if cand in set_list:
    #        return 1,'JIRA'
    #    else:
    #        return 0,'not bug JIRA'

def classifier_is_fixed(msg,p_name):
    if p_name is None:
        return None,None
    msg_str = str(msg).lower()
    if msg_str.__contains__('typo'):
        return 0,'typo'
    if msg_str.__contains__('javadoc'):
        return 0, 'javadoc'
    if p_name == 'tika':
        if regx_look_up(msg, r'TIKA-[0-9]+'):
            return jira_is_bug(msg_str,p_name)
    if  p_name == 'Math':
        if regx_look_up(msg, r'MATH-[0-9]+'):
            return jira_is_bug(msg_str,p_name)
    if p_name =='Lang':
        if regx_look_up(msg, r'LANG-[0-9]+'):
            return jira_is_bug(msg_str,p_name)
    if msg_str.__contains__('fixes #'):
        return 1,'Fixes #'
    if msg_str.__contains__('bug'):
        return 1,'bug'
    if regx_look_up(msg,r'#[0-9]+'):
        if msg_str.__contains__('patch'):
            return 1,'# & patch'
        if msg_str.__contains__('fix'):
            return 1, '# & fix'
        if msg_str.__contains__('pr'):
            return 1, '# & pr'
        if msg_str.__contains__('pull request'):
            return 1, '# & pull request'
        if msg_str.__contains__('issues'):
            return 1, '# & issues'
        if msg_str.__contains__('issue'):
            return 1, '# & issue'
        if msg_str.__contains__('close'):
            return 1, '# & close'
    if msg_str.__contains__('patch'):
        return 1,'patch'
    if msg_str.__contains__('fix'):
        if msg_str.__contains__('error'):
            return 1,'fix & error'
        if msg_str.__contains__('failure'):
            return 1,'fix & failure'
    return 0,None

def look_for_commit(string_info,out,p_name):
    flag=True
    size = len(string_info)
    get_index_first = acc_commit_lookup(0,size,string_info)
    if get_index_first == -1:
        return None
    d_l=[]
    while(flag):
        get_index_sec = acc_commit_lookup(get_index_first+1,size,string_info)
        if get_index_sec == -1:
            get_index_sec = size
            flag=False
        res = pars_commit_block(string_info[get_index_first:get_index_sec-1],p_name)
        get_index_first = get_index_sec
        d_l.append(res)
    df = pd.DataFrame(d_l)
    df.to_csv('{}/log_commits.csv'.format(out))

def pars_commit_block(txt_block,p_name):
    #print txt_block
    d={}
    size_max = len(txt_block)
    id_commit = ''
    val,end = str_acc_helper(txt_block ,len('commit '),size_max)
    print "id_commit:",val
    d['id_commit']=val
    index_find = str(txt_block).find('Author:',end )
    val, end = str_acc_helper(txt_block, len('Author:')+index_find+1, size_max)
    print "Author:",val
    d['Author'] = val
    index_find = str(txt_block).find('Date:', end)
    val, end = str_acc_helper(txt_block, len('Date:') + index_find+1, size_max)
    print "Date:", val
    d['Date'] = val
    d['msg'] =  str(txt_block)[end:].replace('\n','').replace('\t',' ')
    class_i,by_str = classifier_is_fixed(d['msg'],p_name)
    d['is_fix']=class_i
    d['by']=by_str
    d['version_TAG'] = get_Version_name_via_commit(d['id_commit'],p_name)
    return d

def get_sorted_git_tag(p_name='Time'):
    '''
    get a list of sorted tags with dico of date
    :param p_name:
    :return:
    '''
    path_rep = project_dict[p_name]['repo_path']
    repo = git.Repo(path_rep)
    tags_sort = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
    #tags_sort = map(lambda t: t.name, sorted(git.Repo('/home/ise/tmp_d4j/joda-time').tags, key=lambda x: x.commit.committed_date))
    str_results=''
    vaildtion_arr=[]
    for x in repo.tags:
        vaildtion_arr.append([x.name,x.commit.committed_datetime])
    z = sorted(vaildtion_arr, key=lambda x: x[1])
    tags_sort=[]
    for item in z:
        tags_sort.append(item[0])
        str_results += '{}\t{}\n'.format(item[0], item[1])
        print "{}\t\t{}".format(item[0], item[1])
    return tags_sort

def str_acc_helper(txt,strat,end):
    acc=''
    end_indx = -1
    for i in range(strat,end):
        if txt[i]!='\n':
            acc+=txt[i]
        else:
            end_indx=i
            break
    return acc,end_indx

def acc_commit_lookup(indx,max_size,string_info):
    starting_commit_index =-1
    acc=''
    for i in range(indx, max_size):
        if string_info[i] != ' ' and string_info[i] != '\n':
            acc+=string_info[i]
        else:
            if acc == 'commit':
                starting_commit_index = i - len('commit')
                if starting_commit_index == 0 or string_info[starting_commit_index-1]=='\n':
                    break
                else:
                    acc=''
            else:
                acc=''
    return starting_commit_index

def regx_look_up(txt,rec=r'#[0-9]+'):
    tmp = re.compile(rec).search(txt)
    if tmp is None:
        return False
    return True

import numpy as np

def bug_distribution(name_proj,dir='/home/ise/tmp_d4j/config'):
    csv_commit_log_path = '{}/{}/log_commits.csv'.format(dir,name_proj)
    out='/'.join(str(csv_commit_log_path).split('/')[:-1])
    df = pd.read_csv(csv_commit_log_path, index_col=0)
    print list(df)
    na_ctr =  df['version_TAG'].isnull().sum()
    indices = np.where(df['version_TAG'].isnull())
    df_null = df.ix[indices]
    df_null.to_csv('{}/index_null.csv'.format(out))
    print 'df_null size = ',float(na_ctr)/len(df)*100
    #df['version_TAG'].fillna(method='ffill', inplace=True)
    df_small = df[['is_fix', 'version_TAG']]
    res= df_small.groupby(['version_TAG'])['is_fix'].sum().reset_index()
    res['version_TAG'] = res['version_TAG'].apply(lambda x: str(x).replace('\n',''))
    res.to_csv('{}/bug_distribution.csv'.format(out))
    #print list(res)
    for i in range(0,5):
        res['major_{}'.format(i)]=res['version_TAG'].apply(lambda x: str(x).split('_')[i] if len(str(x).split('_')) > i else None)
    res.to_csv('{}/bug_distribution.csv'.format(out))

def foo():
    path_rep = project_dict['Lang']['repo_path']
    repo = git.Repo(path_rep)
    repo.commit()
    for x in repo.iter_commits():
        print x
    exit()



def add_tika_tags_csv(csv_p = '/home/ise/Downloads/tika/data/valid_bugs.csv',p_name='tika'):
    df= pd.read_csv(csv_p)
    father_dir = '/'.join(str(csv_p).split('/')[:-1])
    print list(df)
    df['tag_parent'] = df['parent'].apply(lambda x: get_Version_name_via_commit(x,p_name))
    df['tag_commit'] = df['commit'].apply(lambda x: get_Version_name_via_commit(x,p_name))
    df.to_csv('{}/{}_vail_bug.csv'.format(father_dir,p_name))
    exit()


def map_res_directory_generation_status(res_path='/home/ise/bug_miner/commons-scxml/res'):
    dirz_name = ['Result','EVOSUITE','LOG']
    d_l=[]
    res_folders = pt.walk_rec(res_path,[],'_',False,lv=-1)
    print res_folders
    for folder_bug in res_folders:
        d_sub_dir={}
        bug_jira_id = str(folder_bug).split('/')[-1].split('_')[0]
        bug_index_id = str(folder_bug).split('/')[-1].split('_')[1]
        d_sub_dir['bug_jira_id ']=bug_jira_id
        d_sub_dir['bug_index_id']=bug_index_id
        sub_folder = pt.walk_rec(folder_bug,[],'',False,lv=-1,full=False)
        for name in dirz_name:
            if name  in sub_folder:
                d_sub_dir[name]=1
            else:
                d_sub_dir[name]=0
        size_org=0
        if os.path.isdir('{}/EVOSUITE'.format(folder_bug)):
            count_org_dir = pt.walk_rec('{}/EVOSUITE'.format(folder_bug),[],'org',False,lv=-3)
            size_org = len(count_org_dir)
        d_sub_dir['org']=size_org
        d_sub_dir['xml_buggy']=0
        d_sub_dir['xml_fixed']=0
        if os.path.isdir('{}/Result'.format(folder_bug)):
            xml_filres= pt.walk_rec('{}/Result'.format(folder_bug),[],'xml')
            for item in xml_filres:
                f_folder_name = str(item).split('/')[-2].split('_')[-1]
                if f_folder_name == 'buggy':
                    d_sub_dir['xml_buggy'] +=1
                if f_folder_name == 'fixed':
                    d_sub_dir['xml_fixed'] += 1
        d_l.append(d_sub_dir)
    df = pd.DataFrame(d_l)
    res_path_father_dir = '/'.join(str(res_path).split('/')[:-1])
    df.to_csv('{}/map_res.csv'.format(res_path_father_dir))


if __name__ == "__main__":
    befor_op()
    map_res_directory_generation_status()
    exit()



    #add_tika_tags_csv()
    #add_tika_tags_csv(csv_p='/home/ise/bug_miner/math/valid_bugs.csv',p_name='commons-math')
    add_tika_tags_csv(csv_p='/home/ise/bug_miner/lang/commons-lang.csv', p_name='commons-lang')

    #projects = ['Math','Lang','Mockito','Time','Chart','Closure']
    #new_data_set()
    #pars_commit_msg('tika',out='/home/ise/eran/git_repos/out')
    bug_distribution(dir='/home/ise/tmp_jira/config',name_proj='camel')
    exit()
    #bug_distribution('Math')
    #    fixed compilation errors (oups
    #    fix to bypass ant failures
    projects = ['accumulo','camel','commons-math','flink',
                'jackrabbit-oak','logging-log4j2','maven','wicket']
    project = ['jackrabbit-oak','logging-log4j2','maven','wicket']
    #projects = ['Math','Lang']
    for x in projects:
        if x=='jackrabbit-oak':
            continue
        pars_commit_msg(x,out='/home/ise/tmp_jira/config')

    print "----git util----"
    exit()
