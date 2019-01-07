import pit_render_test as pt
import sys, os, xml
import re
import numpy as np
# sys.path.append("/home/ise/eran/git_repos/mvnpy")
from subprocess import Popen, PIPE
import shlex
import budget_generation as bg
import pandas as pd
import xml.etree.ElementTree as ET

'''
-pl, --projects
        Build specified reactor projects instead of all projects
-am, --also-make
        If project list is specified, also build projects required by the list
        
E.G -> mvn install -pl B -am
'''



def get_Tag_name_by_commit(commit_id, path_repo):
    '''
    getting the tag that the commit with in.
    '''
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


def checkout_repo(dir_dis, p_name):
    path_ATG = os.getcwd()
    df= pd.read_csv('{}/tmp_files/git_clone.csv'.format(path_ATG), index_col=0)
    res = df.loc[df['project']==p_name]
    if len(res)!=1:
        print "[Error] no Project name in the data_set git_clone --> {}".format(p_name)
    url_i = df.iloc[0]['url']
    print "url_i -> {}".format(url_i)
    cwd = os.getcwd()
    os.chdir(dir_dis)
    os.system('git clone {}'.format(url_i))
    os.chdir(cwd)
    print "Done cloning {}".format(p_name)


def csv_bug_process(p_name, repo_path='/home/ise/eran/tika_exp/tika', out='/home/ise/eran/tika_exp/res',oracle=True,remove_dup=False):
    csv_bug = '/home/ise/eran/repo/ATG/tmp_files/{}_bug.csv'.format(p_name)
    if os.path.isdir(repo_path) is False:
        repo_path_father = '/'.join(str(repo_path).split('/')[:-1])
        checkout_repo(repo_path_father, p_name)
    if os.path.isdir(out) is False:
        os.system('mkdir {}'.format(out))
    print "{}".format(csv_bug)
    df = pd.read_csv(csv_bug)
    print list(df)

    if 'testcase' in df:
        df['package'] = df['testcase'].apply(lambda x: '/'.join(str(x).split('.')[:-1]))
        df['fail_component'] = df['testcase'].apply(lambda x: str(x).split('#')[0])
        df.drop('testcase', axis=1, inplace=True)

    if oracle:
        df['target'] = df['fail_component'].apply(lambda x: '/'.join(str(x).split('.')) )
        #df.rename(columns={'fail_component': 'target'}, inplace=True)
    else:
        df['target'] = df['package'].apply(lambda x: '/'.join(str(x).split('.')))
        #df.rename(columns={'package': 'target'}, inplace=True)
    if remove_dup:
        print len(df)
        df.drop_duplicates(subset=['commit','parent','package'],inplace=False)
        print len(df)

    df.apply(applyer_bug, repo=repo_path, out_dir=out, axis=1)


def start_where_stop_res(res_dir):
    dirs_res = pt.walk_rec(res_dir,[],'',False,lv=-1,full=False)
    return dirs_res

def applyer_bug(row, out_dir, repo):
    p_name = str(repo).split('/')[-1]
    tag_parent = row['tag_parent']
    module = row['module']
    commit_buggy = row['parent']  # old
    commit_fix = row['commit']  # new
    bug_name = row['issue']
    index_bug = row['index_bug']
    ######
    list_done = start_where_stop_res(out_dir)
    look_for = "{}_{}".format(bug_name,index_bug)
    if look_for in list_done:
        return
    ######
    target = row['target']
    out_dir_new = pt.mkdir_system(out_dir, "{}_{}".format(bug_name, index_bug))
    out_evo = pt.mkdir_system(out_dir_new, 'EVOSUITE')
    path_to_pom = "{}/pom.xml".format(repo)

    print "module={} \t tag_p = {} \t commit_p ={}".format(module, tag_parent, commit_fix)
    checkout_version(commit_fix, repo, out_dir_new)
    proj_dir = '/'.join(str(path_to_pom).split('/')[:-1])

    rm_exsiting_test(proj_dir, p_name)

    out_log = pt.mkdir_system(out_dir_new, 'LOG', False)
    mvn_command(repo, module, 'clean', out_log)
    mvn_command(repo, module, 'compile', out_log)
    discover_dir_repo('{}/target'.format(repo), p_name, is_test=False)

    if str(module).__contains__('-'):
        path_to_pom = '{}/{}/pom.xml'.format(repo, module)
        dir_to_gen = '{}/{}/target/classes/{}'.format(repo, module, target)
        dir_to_gen = discover_dir_repo('{}/{}'.format(repo, module), p_name, is_test=False)
    else:
        dir_to_gen = discover_dir_repo('{}'.format(repo), p_name, is_test=False)
    dir_to_gen = '{}/{}'.format(dir_to_gen, target)
    # Run Evosuite generation mode
    add_evosuite_text(path_to_pom, None)
    sys.argv = ['.py', dir_to_gen, 'evosuite-1.0.5.jar',
                '/home/ise/eran/evosuite/jar/', out_evo + '/', 'exp', '100', '1', '2', '2', 'U']
    bg.init_main()
    evo_test_run(out_evo, repo, module, proj_dir, mode='fixed')
    checkout_version(commit_fix, repo, out_dir_new, clean=True)

    # Run test-suite on the buugy version
    checkout_version(commit_buggy, repo, out_dir_new)
    rm_exsiting_test(proj_dir, p_name)
    mvn_command(repo, module, 'clean', out_log)
    mvn_command(repo, module, 'compile', out_log)
    add_evosuite_text(path_to_pom, None)
    evo_test_run(out_evo, repo, module, proj_dir, mode='buggy')
    checkout_version(commit_buggy, repo, out_dir_new, clean=True)

    # rm pom.xml for the next checkout
    mvn_command(repo, module, 'clean', out_log)


def evo_test_run(out_evo, mvn_repo, moudle, project_dir, mode='fix'):
    p_name = str(mvn_repo).split('/')[-1]
    out_evo = '/'.join(str(out_evo).split('/')[:-1])
    res = pt.walk_rec(out_evo, [], 'org', False)
    if len(res) == 0:
        return
    test_dir = get_test_dir(project_dir)
    rm_exsiting_test(project_dir, p_name)
    for path_res in res:
        command_cp_test = "cp -r {} {}".format(path_res, test_dir)
        dir_name_evo = str(path_res).split('/')[-2]
        print "[OS] {}".format(command_cp_test)
        out_log = pt.mkdir_system(out_evo, 'LOG', False)
        os.system(command_cp_test)
        mvn_command(mvn_repo, moudle, 'install', out_log)
        # mvn_command(mvn_repo,moudle,'test-compile',out_log)
        # mvn_command(mvn_repo, moudle, 'test', out_log)

        # moving the results to the evo_out dir
        test_dir = "{}/target/surefire-reports".format(project_dir)
        res_test_file = pt.walk_rec(test_dir, [], '.xml')
        # filter only the evo_suite test
        res_test_file = [x for x in res_test_file if str(x).split('/')[-1].__contains__('_ESTest')]
        out_results = pt.mkdir_system(out_evo, 'Result', False)
        out_results_evo = pt.mkdir_system(out_results, "{}_{}".format(dir_name_evo, mode), False)
        for test_item in res_test_file:
            command_mv = "mv {} {}".format(test_item, out_results_evo)
            print "[OS] {}".format(command_mv)
            os.system(command_mv)
        rm_exsiting_test(project_dir, p_name)


def rm_exsiting_test(path_p, p_name):
    dir_to_del = '{}/src/test/java/org'.format(path_p)
    dir_to_del = discover_dir_repo(path_p, p_name)
    if dir_to_del is None:
        print('[Warning] cant find the test dir of the project -> {}'.format(path_p))
        return
    if os.path.isdir(dir_to_del):
        command_ram = 'rm -r {}'.format(dir_to_del)
        print "[OS] {}".format(command_ram)
        os.system(command_ram)
    else:
        print '[Warning] cant find the test dir of the project -> {}'.format(path_p)


def log_to_file(dir_log, name_file, txt_to_log):
    '''
    log the info into a log file
    '''
    with open('{}/{}.log'.format(dir_log, name_file), 'w+') as file_log:
        file_log.write(txt_to_log)


def discover_dir_repo(path, p_name, target='org', is_test=True):
    if p_name == 'tika':
        if is_test is False:
            return "{}/target/classes".format(path)
        else:
            return "{}/src/test/java/org".format(path)
    res = pt.walk_rec(path, [], target, False, lv=-4)
    for item in res:
        if is_test:
            if str(item).__contains__('/src/test') or str(item).__contains__('src/test/java'):
                return item
        else:
            item = '/'.join(str(item).split('/')[:-1])
            if str(item).__contains__('/target/classes'):
                return item


def get_test_dir(project_dir):
    if os.path.isdir("{}/src/test/java".format(project_dir)):
        test_dir = "{}/src/test/java".format(project_dir)
        return test_dir
    if os.path.isdir("{}/src/test".format(project_dir)):
        test_dir = "{}/src/test".format(project_dir)
        return test_dir
    raise Exception("cant find the test dir in the Project --> {}".format(project_dir))


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


def checkout_version(commit, repo, log_dir, clean=False):
    '''
    mange the checkout process
    '''
    if clean:
        command_git = 'git reset --hard {}'.format(commit)
        run_GIT_command_and_log(repo, command_git, log_dir, 'checkout_clean')
    else:
        command_git = 'git checkout {}'.format(commit)
        run_GIT_command_and_log(repo, command_git, log_dir, 'checkout')
    print "[OS] {}".format(command_git)


def mvn_command(repo, module, command_mvn='clean', log_dir=None):
    os.chdir(repo)
    if module is not None and str(module).__contains__('-'):
        command_mvn_str = 'mvn {} -pl {} -am -fn'.format(command_mvn, module)
    else:
        command_mvn_str = 'mvn {} -fn'.format(command_mvn)
    process = Popen(shlex.split(command_mvn_str), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if log_dir is None:
        return
    log_to_file(log_dir, '{}_stdout'.format(command_mvn_str), stdout)
    log_to_file(log_dir, '{}_stderr'.format(command_mvn_str), stderr)


def add_evosuite_pom(path_xml='/home/ise/eran/git_repos/tika/tika-core/pom.xml', out='/home/ise/test/pom'):
    if os.path.isfile(path_xml) is False:
        raise "[Error] no file in the path --> {}".format(path_xml)
    try:
        root_node = ET.parse(path_xml).getroot()  # get the root xml
    except (Exception, ArithmeticError) as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print (message)
        return None
    for elem in root_node.iter():
        print elem.tag
    exit()


def add_evosuite_text(path_pom='/home/ise/eran/git_repos/tika/tika-core/pom.xml', out='/home/ise/test/pom'):
    dico_appends = dico_eco_pom_build()
    str_pom = None
    with open(path_pom, 'r') as f_pom:
        str_pom = f_pom.read()
        # str_pom,bol = replacer(str_pom, '<plugins>', 'plugin',dico_appends )
        str_pom, bol = replacer(str_pom, '<artifactId>junit</artifactId>', 'junit_ar', dico_appends)
        if bol is False:
            str_pom, bol = replacer(str_pom, '<dependencies>', 'dep', dico_appends)
        else:
            str_pom, bol = replacer(str_pom, '<dependencies>', 'dependency', dico_appends)
    if bol is False:
        str_pom, bol = replacer(str_pom, '</project>', 'all_section', dico_appends)
    path_rel = '/'.join(str(path_pom).split('/')[:-1])
    ##os.system('rm {}'.format(path_pom))
    if out is None:
        out = path_rel
    with open('{}/pom.xml'.format(out), 'w') as new_pom:
        new_pom.write(str_pom)
    return True


def replacer(str_input, str_look_for, str_append_after, d):
    '''
    this fuction adding the given seq to the pom by looking for a pattren
    '''
    ans = [m.start() for m in re.finditer(r'{}'.format(str_look_for), str_input)]
    print ans
    if len(ans) == 0:
        print "[Error] the retrun is not one in the replacer function len(ans)={} look={}".format(len(ans),
                                                                                                  str_look_for)
        return str_input, False
    path = d[str_append_after]
    with open(path, 'r') as f:
        str_ap = f.read()
    if str_look_for == '</project>':
        index = ans[0] - 1
    else:
        index = ans[0] + len(str_look_for)
    if str_append_after == 'junit_ar':
        ver_index = clean_version_tag(str_input, index)
        ver_index += 1
        str_input = str_input[:index] + str_ap + str_input[index + ver_index:]
    else:
        str_input = str_input[:index] + str_ap + str_input[index:]
    return str_input, True


def clean_version_tag(str_input, start_index):
    '''
    if any version tag in the pom, clean in the junit scope
    '''
    acc = ''
    ctr = 0
    flag = 2
    for letter in str_input[start_index:]:
        if letter != '\n':
            ctr += 1
            acc += letter
        else:
            if acc.__contains__('version'):
                return ctr
            else:
                acc = ''
            flag = flag - 1
            if flag == 0:
                return 0


def dico_eco_pom_build():
    d = {}
    d['dependency'] = '/home/ise/eran/repo/ATG/pom/evo/dependency.txt'
    d['plugin'] = '/home/ise/eran/repo/ATG/pom/evo/plugin.txt'
    d['junit'] = '/home/ise/eran/repo/ATG/pom/evo/junit.txt'
    d['all_section'] = '/home/ise/eran/repo/ATG/pom/evo/all_section.txt'
    d['junit_ar'] = '/home/ise/eran/repo/ATG/pom/evo/junit_ar.txt'
    d['dep'] = '/home/ise/eran/repo/ATG/pom/evo/dep.txt'

    return d


def main_parser():
    args = sys.argv


def to_del(p='/home/ise/test/pom_3'):
    res_tiks = pt.walk_rec(p, [], 'TIKA', False, lv=-1)
    res_org = pt.walk_rec(p, [], 'org', False, lv=-6)
    print "res_tiks =", len(res_tiks)
    print "res_org  =", len(res_org)
    res_org = ['/'.join(str(x).split('/')[:-2]) for x in res_org]
    dif = []
    for y in res_tiks:
        if y not in res_org:
            dif.append(y)
    ans = []
    for item in dif:
        ans.append(str(item).split('/')[-1])
        # print str(item).split('/')[-1]
    exit()


def get_results(dir_res='/home/ise/test/pom_3'):
    res = pt.walk_rec(dir_res, [], 'TIKA', False, lv=-1)
    d_l = []
    d_l_empty = []
    for item in res:
        print "----{}----".format(str(item).split('/')[-1])
        name = str(item).split('/')[-1]
        d_test = {}
        id_bug = str(name).split('_')[1]
        bug_name = str(name).split('_')[0]
        folder_log_evo = pt.walk_rec(item, [], 'log_evo', False)
        folder_org = pt.walk_rec(item, [], 'org', False)
        res_log_test = pt.walk_rec(folder_log_evo[0], [], '.txt')
        for log_t in res_log_test:
            name = str(log_t).split('/')[-1][:-4]
            if name not in d_test:
                d_test[name] = {'id': id_bug, 'bug_name': bug_name, 'log': 1, 'name': name, 'test': 0}
            else:
                msg = '[Error] duplication in the test log dir := {}'.format(folder_log_evo)
                raise Exception(msg)
        if len(folder_org) > 0:
            res_test = pt.walk_rec(folder_org[0], [], 'ESTest.java')
            for test_i in res_test:
                test_name_package = pt.path_to_package('org', test_i, -5)
                test_name_package = test_name_package[:-7]
                if test_name_package not in d_test:
                    d_test[test_name_package] = {'id': id_bug, 'bug_name': bug_name, 'log': 0,
                                                 'name': test_name_package, 'test': 1}
                else:
                    d_test[test_name_package]['test'] = 1
        d_l_empty.extend(d_test.values())
    df = pd.DataFrame(d_l_empty)
    father = '/'.join(str(dir_res).split('/')[:-1])
    df.to_csv("{}/result_info_empty.csv".format(father))


def get_test_xml_csv(dir_res='/home/ise/test/res'):
    d_l = []
    res = pt.walk_rec(dir_res, [], 'Result', False)
    for item_dir in res:
        bug_id = str(item_dir).split('/')[-2].split('_')[1]
        if bug_id == '133':
            print ""
        bug_name = str(item_dir).split('/')[-2].split('_')[0]
        xml_files = pt.walk_rec(item_dir, [], '.xml')
        for xml_item in xml_files:
            d = None
            name_dir = str(xml_item).split('/')[-2]
            name_file_xml = str(xml_item).split('/')[-1]
            test_mode = str(name_dir).split('_')[-1]
            test_it = str(name_dir).split('_')[-2].split('=')[1]
            test_time_b = str(name_dir).split('_')[-3].split('=')[1]
            test_date = '_'.join(str(name_dir).split('_')[3:7])
            d = pars_xml_test_file(xml_item)
            d['test_mode'] = test_mode
            d['test_it'] = test_it
            d['test_time_b'] = test_time_b
            d['test_date'] = test_date
            d['bug_id'] = bug_id
            d['bug_name'] = bug_name
            d_l.append(d)
    df = pd.DataFrame(d_l)
    dir_father = '/'.join(str(dir_res).split('/')[:-1])
    df.to_csv("{}/res.csv".format(dir_father))
    return "{}/res.csv".format(dir_father)

def make_csv_diff(csv_raw_data_res='/home/ise/test/res.csv'):
    father_dir = '/'.join(str(csv_raw_data_res).split('/')[:-1])
    df = pd.read_csv(csv_raw_data_res, index_col=0)
    list_issue = df['bug_name'].unique()
    print "all the issue in the project:"
    print len(list_issue)
    print list(df)
    arr = set()
    df['diff_fail'] = df.apply(differ, df=df, set_l=arr, axis=1)
    df['diff_fail_count'] = df['diff_fail'].apply(lambda x: str(x).count('ESTest'))
    print "number of issue that Evosuit found:"
    print len(arr)
    df.to_csv('{}/tmp_df.csv'.format(father_dir))
    return '{}/tmp_df.csv'.format(father_dir)

def differ(row, df, set_l):
    '''
    '''
    bug_id = row['bug_id']
    bug_name = row['bug_name']
    name = row['name']
    test_it = row['test_it']
    test_time_b = row['test_time_b']
    test_mode = row['test_mode']
    filter_df = df.query(
        "test_mode != @test_mode & bug_id == @bug_id & bug_name == @bug_name & name == @name & test_it == @test_it & test_time_b==@test_time_b ")
    if len(filter_df) != 1:
        return "Err"
    if str(filter_df['class_fail'].iloc[0]).__contains__('--') is False:
        diff_other = []
    else:
        diff_other = str(filter_df['class_fail'].iloc[0]).split('--')
    if str(row['class_fail']).__contains__('--') is False:
        diff_cur = []
    else:
        diff_cur = str(row['class_fail']).split('--')
    if len(diff_cur) == 0:
        return None
    res_arry = []
    for item in diff_cur:
        if item not in diff_other:
            res_arry.append(item)
    if len(res_arry) == 0:
        return None
    print "{}_{} it={}".format(bug_name, bug_id, test_it)
    set_l.add(bug_name)
    return '\t'.join(res_arry)


def pars_xml_test_file(path_file, dico=None):
    """
    parsing the xml tree and return the results
    """

    name_test = str(path_file).split('/')[-1][:-11]  # remove xml + _ESTest
    d = {"err": float(0), "fail": float(0), "bug": 'no', 'class_err': [], 'class_fail': []}
    d['name'] = name_test
    if dico is not None:
        for ky in dico:
            d[ky] = dico[ky]
    if os.path.isfile(path_file) is False:
        raise Exception("'[Error] the path: {} is not valid ".format(path_file))
    root_node = xml.etree.ElementTree.parse(path_file).getroot()
    val, bol = _intTryParse(root_node.attrib['errors'])
    if bol is False:
        print "[Error] cant parse the xml file error val input : {}".format(path_file)
    errors_num = val
    val, bol = _intTryParse(root_node.attrib['failures'])
    if bol is False:
        print "[Error] cant parse the xml file failures val input : {}".format(path_file)
    failures_num = val
    if failures_num or errors_num > 0:
        d['bug'] = 'yes'
        for elt in root_node.iter():
            if elt.tag == 'testcase':
                if len(elt._children) > 0:
                    for msg in elt:
                        if msg.tag == 'error':
                            class_name = elt.attrib['classname']
                            test_case_number = elt.attrib['name']
                            d['class_err'].append("{}_{}".format(class_name, test_case_number))
                            d['err'] = d['err'] + 1
                        elif msg.tag == 'failure':
                            class_name = elt.attrib['classname']
                            test_case_number = elt.attrib['name']
                            d['class_fail'].append("{}_{}".format(class_name, test_case_number))
                            d['fail'] = d['fail'] + 1
    d['class_fail'] = '--'.join(d['class_fail'])
    d['class_err'] = '--'.join(d['class_err'])
    return d


def _intTryParse(value):
    try:
        return int(value), True
    except ValueError:
        return value, False


def parser():
    if sys.argv[1] == 'main':
        csv_bug_process()


def project_to_csv():
    d = {}
    path_p = '/home/ise/eran/repo/ATG/tmp_files'
    d['Lang'] = '{}/commons-lang_bug.csv'.format(path_p)
    d['Math'] = '{}/commons-math_bug.csv'.format(path_p)
    d['Tika'] = '{}/tika_bug.csv'.format(path_p)
    return d


def merge_csv_info_bug(csv_bug='/home/ise/bug_miner/math/tmp_df.csv', project_name='Math'):
    father_dir = '/'.join(csv_bug.split('/')[:-1])
    d_project = project_to_csv()
    df_bug = pd.read_csv(csv_bug, index_col=0)
    df_info = pd.read_csv(d_project[project_name], index_col=0)
    df_info.rename(columns={'index_bug': 'bug_id'}, inplace=True)
    df_bug.rename(columns={'bug_name': 'issue'}, inplace=True)

    df_merge = pd.merge(df_info, df_bug, how='right', on=['bug_id', 'issue'])
    df_merge.to_csv('{}/{}.csv'.format(father_dir, 'all'))

    exit()


def add_fulty_bug(path_df,p_name,path_csv_info=None):
    csv_p_info = "{}/tmp_files/{}_bug.csv".format(os.getcwd(),p_name)
    df_info = pd.read_csv(csv_p_info,index_col=0)
    df_info['fauly_component'] = df_info['testcase'].apply(lambda x: str(x).split('#')[0].split('Test')[0])
    df_bugs = pd.read_csv(path_df,index_col=0)
    df_info['is_faulty'] =1
    df_faulty = df_info[['index_bug','issue','fauly_component','is_faulty']]

    df_bugs['name'] = df_bugs['name'].apply(lambda x_i : str(x_i)[5:])
    #df_faulty['is_faulty'] = 1

    df_faulty.rename(columns={'index_bug': 'bug_id',
                       'issue': 'bug_name',
                       'fauly_component': 'name'}, inplace=True)



    print 'df_faulty: ',len(df_faulty)
    print 'df_bugs: ',len(df_bugs)
    df_merge = pd.merge(df_bugs,df_faulty, how='left', on=['bug_id','bug_name','name'] )
    df_merge['binary_kill'] = df_merge['diff_fail_count'].apply(lambda x: 1 if float(x)>0 else 0)

    print 'df_merge: ',len(df_merge)
    print list(df_merge)


    df_merge.to_csv('/home/ise/bug_miner/commons-math/merge.csv')
    to_del = ['bug', 'class_err','test_it', 'fail','class_fail', 'err', 'test_date', 'diff_fail', 'diff_fail_count' ]
    df_merge.drop(to_del, axis=1, inplace=True)
    df_merge['is_faulty'].fillna(0, inplace=True)
    df_merge.to_csv('/home/ise/bug_miner/commons-math/G.csv')
    print df_merge.dtypes
    df_merge['bb'] = df_merge.groupby(['bug_id', 'bug_name','name','test_mode','test_time_b','is_faulty'])['binary_kill'].transform('sum')
    df_merge.to_csv('/home/ise/bug_miner/commons-math/fin.csv')

def get_minmal_csv_bug_miner(p_name='Math'):
    '''
    remove duplicaion from the raw csv
    '''
    d_project = project_to_csv()
    df_info = pd.read_csv(d_project[p_name], index_col=0)
    father_dir = '/home/ise/bug_miner/math'
    print list(df_info)
    df_info['fault_class'] = df_info['testcase'].apply(lambda x: str(x).split('#')[0])
    df_info['fault_package'] = df_info['testcase'].apply(lambda x: '.'.join(str(x).split('#')[0].split('.')[:-1]))
    to_del = ['testcase', 'valid', 'type', 'has_test_annotation', 'description', 'index_bug']
    for item in to_del:
        df_info.drop(item, axis=1, inplace=True)
    print list(df_info)
    print len(df_info)
    df_info
    df_info = df_info.drop_duplicates()
    df_info.to_csv('{}/{}.csv'.format(father_dir, 'dup_off_info'))
    print len(df_info)


def parser():
    if len(sys.argv) > 1:
        dir_bug_miner = '/home/ise/bug_miner'
        project = sys.argv[1]
        if project == 'commons-math':
            repo_path = '{}/{}/commons-math'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_bug_process('commons-math', repo_path, out_p)
        elif project == 'commons-lang':
            repo_path = '{}/{}/commons-lang'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_bug_process('commons-lang', repo_path, out_p)
        elif project == 'tika':
            repo_path = '{}/{}/tika'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_bug_process('tika', repo_path, out_p)
        elif project == 'pig':
            repo_path = '{}/{}/pig'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_bug_process('pig', repo_path, out_p)
        elif sys.argv[1] == 'res':
            project = sys.argv[2]
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            #csv_path_res = get_test_xml_csv(out_p)
            #df_path = make_csv_diff(csv_path_res)
            add_fulty_bug('{}/{}/tmp_df.csv'.format(dir_bug_miner, project),project)


if __name__ == "__main__":
    sys.argv=['','commons-math']
    parser()
    print '\n\n'
    print "---Done"*10
