from subprocess import Popen, PIPE, check_call, check_output

import shlex

import os.path
import git,re

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



def pars_commit_msg(p_name='Time',out='/home/ise/tmp_d4j/config'):
    '''
    main function for parsing the commits on the repo project
    :param p_name:
    :param out:
    :return:
    '''
    print "pars_commit_msg({})".format(p_name)
    p_path_repo = project_dict[p_name]['repo_path']
    command_git = "git log "
    std_out, std_err = run_GIT_command_and_log(p_path_repo, command_git, None, "", False)
    look_for_commit(std_out,'{}/{}'.format(out,p_name),p_name)




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

def jira_is_bug(msg_str,p_name):
    uper_p_name = str(p_name).upper()
    rec = '{}-[0-9]+'.format(uper_p_name.lower())
    df = pd.read_csv('/home/ise/tmp_d4j/JIRA/JIRA_{}.csv'.format(uper_p_name))
    tmp = re.compile(rec).search(msg_str)
    list_cand=[]
    for item in tmp.regs:
        list_cand.append(msg_str[item[0]:item[1]])
    list_cand = [str(x).upper() for x in list_cand]
    set_list = list(df['Issue key'].unique())
    for cand in list_cand:
        if cand in set_list:
            return 1,'JIRA'
    if msg_str.__contains__('correct'):
        return 1, 'correct'
    if msg_str.__contains__('patch'):
        return 1, 'patch'
    if msg_str.__contains__('improve'):
        return 1, 'improve'
    return 0,'Not Bug - JIRA'
def classifier_is_fixed(msg,p_name):
    msg_str = str(msg).lower()
    if msg_str.__contains__('typo'):
        return 0,'typo'
    if msg_str.__contains__('javadoc'):
        return 0, 'javadoc'
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
    if msg_str.__contains__('correct'):
        return 1,'correct'
    if msg_str.__contains__('patch'):
        return 1, 'patch'
    if msg_str.__contains__('improve'):
        return 1, 'improve'
    if msg_str.__contains__('fix'):
        if msg_str.__contains__('error'):
            return 1,'fix & error'
        if msg_str.__contains__('failure'):
            return 1,'fix & failure'
    return 0,None


def regx_look_up(txt,rec=r'#[0-9]+'):
    tmp = re.compile(rec).search(txt)
    if tmp is None:
        return False
    return True

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

def pars_commit_block(txt_block,p_name):
    print txt_block
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
    return d



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


if __name__ == "__main__":
    befor_op()
    projects = ['Lang','Math']
    projects = ['Time','Mockito','Chart','Lang','Math','Closure']
    for x in projects:
        #if x=='Closure':
        #    continue
        pars_commit_msg(x)
    exit()

