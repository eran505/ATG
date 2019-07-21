import pit_render_test as pt
import sys, os, xml
import re
from csv_D4J_headler import get_LOC
from csv_D4J_headler import make_FP_pred
import numpy as np
# sys.path.append("/home/ise/eran/git_repos/mvnpy")
from subprocess import Popen, PIPE
import shlex
import pandas as pd
import budget_generation as bg
import pandas as pd
import xml.etree.ElementTree as ET
import independent_builder as indep_bulilder
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
    print "tag"
    if len(std_out) < 1:
        command_git = 'git describe --contains {}'.format(commit_id)
        std_out, std_err = run_GIT_command_and_log(path_repo, command_git, None, None,False)
        print "contains"
        if len(std_out)<1:
            command_git = 'git describe --tag --contains --all {}'.format(commit_id)
            print "all"
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
    print "std_out={}".format(std_out)
    return current_tag


def checkout_repo(dir_dis, p_name):
    path_ATG = os.getcwd()
    df= pd.read_csv('{}/tmp_files/git_clone.csv'.format(path_ATG), index_col=0)
    res = df.loc[df['project']==p_name]
    if len(res)!=1:
        msg = "[Error] no Project name in the data_set git_clone --> {}".format(p_name)
        raise Exception(msg)
    url_i = res.iloc[0]['url']
    print "url_i -> {}".format(url_i)
    cwd = os.getcwd()
    os.chdir(dir_dis)
    os.system('git clone {}'.format(url_i))
    os.chdir(cwd)
    print "Done cloning {}".format(p_name)


def dependency_getter(repo, dir_jars, m2='/home/ise/.m2/repository'):
    '''
    get all dependency jars
    '''
    res_jar2 = pt.walk_rec('/home/ise/.m2/repository', [], '.jar')
    print len(res_jar2)
    res_jar2 = [x for x in res_jar2 if str(x).split('.')[-1] == 'jar']
    print len(res_jar2)
    res_jar1 = pt.walk_rec('{}/{}'.format(repo, dir_jars), [], '.jar')
    jarz = res_jar2 + res_jar1
    str_jarz = ':'.join(jarz)
    return str_jarz


def csv_bug_process(p_name, repo_path='/home/ise/eran/tika_exp/tika', out='/home/ise/eran/tika_exp/res',
                    oracle=False,remove_dup=False,jarz=True,killable=False,pref='org',self_complie=False):

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
    list_index = None
    if killable:
        p_csv = '{}/killable_{}.csv'.format('/home/ise/eran/repo/ATG/tmp_files',p_name)
        if os.path.isfile(p_csv):
            df_index = pd.read_csv(p_csv)
            list_index = df_index['bug_id'].tolist()
        else:
            print "No killable.csv file as been found !!!! --> path = {}".format(p_csv)
            return None
    df = df.reindex(index=df.index[::-1])
    df.apply(applyer_bug, repo=repo_path, out_dir=out,jarz=jarz,list_index=list_index,prefix_str=pref,self_complie=self_complie,axis=1)
    return
    #if self_complie:
    #    res = pt.walk_rec(out,[],'report.csv')
    #    l_df = []
    #    for item in res:
    #        l_df.append(pd.read_csv(item))
    #    all_df = pd.concat(l_df)
    #    all_df.to_csv("{}/all_report.csv".format(out))






def start_where_stop_res(res_dir):
    dirs_res = pt.walk_rec(res_dir,[],'',False,lv=-1,full=False)
    return dirs_res

def applyer_bug(row, out_dir, repo,list_index,jarz=True,prefix_str='org',self_complie=True):
    fix=False
    git_repo = repo
    p_name = str(repo).split('/')[-1]
    tag_parent = row['tag_parent']
    module = row['module']
    commit_buggy = row['parent']  # old
    commit_fix = row['commit']  # new
    bug_name = row['issue']
    index_bug = row['index_bug']
    component_path = row['component_path']
    print 'index_bug = {}'.format(index_bug)

    # if index_bug > 150:
    #     return
    print "{}".format(component_path)

    ######
    #list_done = start_where_stop_res(out_dir)
    if list_index is not None :
        if index_bug not in list_index:
            return
    ##########


    target = row['target']
    # if os.path.isdir("{}/{}_{}".format(out_dir,bug_name,index_bug)):
    #     fix=True
    # else:
    #     if self_complie:
    #         return
    out_dir_new = pt.mkdir_system(out_dir, "{}_{}".format(bug_name, index_bug),False)
    out_evo = pt.mkdir_system(out_dir_new, 'EVOSUITE',False)
    path_to_pom = "{}/pom.xml".format(repo)

    print "module={} \t tag_p = {} \t commit_p ={}".format(module, tag_parent, commit_fix)
    checkout_version(commit_fix, git_repo, out_dir_new)


    # open-nlp
    name = str(repo).split('/')[-1]
    if os.path.isfile('{}/pom.xml'.format(repo)) is False:
        if os.path.isdir('{}/{}'.format(repo,name)):
            repo = '{}/{}'.format(repo,name)
        else:
             if os.path.isdir('{}/{}'.format(repo,'build.xml')):
                 ant_command(repo,'ant compile')
                 jarz=False
             else:
                 return


    if self_complie:
        if is_evo_dir_full(out_evo) is False:
            # no tests were generated bt Evosuite
            return
        self_complie_bulider_func(repo,"{}/{}_{}".format(out_dir,bug_name,index_bug),prefix_str,suffix='fixed')
        checkout_version(commit_fix, git_repo, out_dir_new, clean=True)
        mvn_command(repo, module, 'clean', None)
        checkout_version(commit_buggy, git_repo, out_dir_new)
        self_complie_bulider_func(repo, "{}/{}_{}".format(out_dir, bug_name, index_bug), prefix_str,suffix='buggy')
        checkout_version(commit_buggy, git_repo, out_dir_new, clean=True)
        mvn_command(repo, module, 'clean', None)

        return



    proj_dir = '/'.join(str(path_to_pom).split('/')[:-1])



    prefix = src_to_target(component_path,end=prefix_str)
    if prefix is None:
        return
    repo_look = "{}{}".format(git_repo,prefix)

    rm_exsiting_test(repo_look , p_name,prefix_str=prefix_str)

    out_log = pt.mkdir_system(out_dir_new, 'LOG', False)
    # reset the commit

    mvn_command(repo, module, 'clean', None)
    mvn_command(repo, module, 'install -DskipTests=true', out_log, '')

    # Get all jars dependency
    str_dependency=''
    if jarz:
        res,path_dep = package_mvn_cycle(repo)
        if path_dep is None:
            print "[Error] cant make jarzz"
            return
        res = clean_jar_path(res)
        str_dependency=':'.join(res)

    discover_dir_repo('{}/target'.format(repo_look), p_name, is_test=False)

    if str(module).__contains__('-'):
        path_to_pom = '{}/{}/pom.xml'.format(repo, module)
        dir_to_gen = '{}/{}/target/classes/{}'.format(repo, module, target)
        dir_to_gen = discover_dir_repo('{}/{}'.format(repo, module), p_name, is_test=False,prefix_str=prefix_str)
    else:
        dir_to_gen = discover_dir_repo('{}'.format(repo_look), p_name, is_test=False,prefix_str=prefix_str)
    dir_to_gen = '{}/{}'.format(dir_to_gen, target)
    # Run Evosuite generation mode

    # add Evosuite to pom xml
    get_all_poms_and_add_evo(repo)

    sys.argv = ['.py', dir_to_gen, 'evosuite-1.0.6.jar',
                '/home/ise/eran/evosuite/jar/', out_evo + '/', 'exp', '200', '1', '180', '5', 'U',str_dependency]

    if fix is False:
        bg.init_main()
    evo_test_run(out_evo, repo, module, proj_dir, mode='fixed',prefix_str=prefix_str)
    checkout_version(commit_fix, git_repo, out_dir_new, clean=True)

    # Run test-suite on the buugy version
    checkout_version(commit_buggy, git_repo, out_dir_new)
    rm_exsiting_test(repo_look, p_name,prefix_str=prefix_str)
    mvn_command(repo, module, 'clean', out_log)
    mvn_command(repo, module, 'compile', out_log)

    # add Evosuite to pom xml
    #add_evosuite_text(path_to_pom, None)
    get_all_poms_and_add_evo(repo)

    evo_test_run(out_evo, repo, module, proj_dir, mode='buggy',prefix_str=prefix_str)
    checkout_version(commit_buggy, git_repo, out_dir_new, clean=True)

    # rm pom.xml for the next checkout
    mvn_command(repo, module, 'clean', out_log)


def is_evo_dir_full(path_evo):
    res = pt.walk_rec(path_evo,[],'.java')
    if res is None or len(res)==0:
        return False
    return True

def get_all_poms_and_add_evo(repo):
    res = pt.walk_rec(repo,[],'pom.xml')
    for item in res:
        add_evosuite_text(item,None)

def self_complie_bulider_func(repo,dir_cur,prefix,suffix='fix',bug_id=''):
    if os.path.isdir("{}/EVOSUITE".format(dir_cur)):
        d={}
        java_dirz = pt.walk_rec("{}/EVOSUITE".format(dir_cur),[],'',False,lv=-1)
        for item in java_dirz:
            if os.path.isdir("{}/{}".format(item,prefix)):
                name_folder = str(item).split('/')[-1]
                tmp = pt.walk_rec("{}/{}".format(item,prefix),[],'.java')
                path2= '/'.join(str(tmp[0]).split('/')[:-1])
                tmp= str(name_folder).split('_')
                name_folder = 'test_suite_t_{}_it_{}'.format(tmp[-2].split('=')[1],tmp[-1].split('=')[1])
                d[name_folder]={'name':name_folder,'path':"{}/{}/*".format(item,prefix),'path2':'{}/*'.format(path2)}
    else:
        print "[error] no dir {}/EVOSUITE".format(dir_cur)
        return None
    d_adder = {'bug_id':str(dir_cur).split('/')[-1],'mode':suffix}
    res,path_jarz=package_mvn_cycle(repo)
    if path_jarz is None:
        return
    remove_junit(path_jarz)
    out_path_complie = pt.mkdir_system(dir_cur,'complie_out_{}'.format(suffix))
    out_path_junit = pt.mkdir_system(dir_cur, 'junit_out_{}'.format(suffix))
    for ky_i in d.keys():
        out_i_complie = pt.mkdir_system(out_path_complie, d[ky_i]['name'])
        out_i_junit = pt.mkdir_system(out_path_junit, d[ky_i]['name'])
        indep_bulilder.compile_java_class(d[ky_i]['path2'], out_i_complie, path_jarz)
        report_d = indep_bulilder.test_junit_commandLine("{}/{}".format(out_i_complie,'test_classes'), path_jarz, out_i_junit, prefix_package=prefix,d_add=d_adder)
    print "end"


def remove_junit(path,path_to_junit='/home/ise/eran/evosuite/junit-4.12.jar'):
    res = pt.walk_rec(path,[],'junit')
    res = [x for x in res if str(x).endswith('.jar')]
    for item in res:
        os.system('rm {}'.format(item))
    os.system('cp {} {}'.format(path_to_junit,path))
    # add hamcrest
    add_hamcrest(path)


def add_hamcrest(path,jar_path='/home/ise/eran/evosuite/dep/hamcrest-all-1.3.jar'):
    res = pt.walk_rec(path,[],'hamcrest')
    res = [x for x in res if str(x).endswith('.jar')]
    for item in res:
        os.system('rm {}'.format(item))
    os.system('cp {} {}'.format(jar_path,path))


def evo_test_run(out_evo, mvn_repo, moudle, project_dir, mode='fix',prefix_str='org'):
    p_name = str(mvn_repo).split('/')[-1]
    out_evo = '/'.join(str(out_evo).split('/')[:-1])
    res = pt.walk_rec(out_evo, [], 'org', False)
    if len(res) == 0:
        return
    test_dir = get_test_dir(project_dir)
    rm_exsiting_test(project_dir, p_name,prefix_str=prefix_str)
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
        test_dir_suff = "{}/target/surefire-reports".format(project_dir)
        res_test_file = pt.walk_rec(test_dir_suff, [], '.xml')
        # filter only the evo_suite test
        res_test_file = [x for x in res_test_file if str(x).split('/')[-1].__contains__('_ESTest')]
        out_results = pt.mkdir_system(out_evo, 'Result', False)
        out_results_evo = pt.mkdir_system(out_results, "{}_{}".format(dir_name_evo, mode), False)
        for test_item in res_test_file:
            command_mv = "mv {} {}".format(test_item, out_results_evo)
            print "[OS] {}".format(command_mv)
            os.system(command_mv)
        rm_exsiting_test(project_dir, p_name,prefix_str=prefix_str)


def rm_exsiting_test(path_p, p_name,prefix_str):
    #dir_to_del = '{}/src/test/java/org'.format(path_p)
    dir_to_del = discover_dir_repo(path_p, p_name,prefix_str)
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


def src_to_target(comp_path,s='src',end='org',prefix=True):
    comp_path = str(comp_path).split('\\')
    try:
        index_src = comp_path.index(s)
        index_org = comp_path.index(end)
    except Exception as e:
        print e.message
        return None
    arr=['target','classes']
    prefix_path = comp_path[:index_src]
    if len(prefix_path) == 0 and prefix:
        prefix_path=''
        return prefix_path
    if prefix:
        prefix_path_str = '/'.join(prefix_path)
        prefix_path_str = '/'+prefix_path_str
        return prefix_path_str
    target_arr = comp_path[:index_src] + arr + comp_path[index_org:]
    test_arr = comp_path[:index_src+1]
    return '/'.join(target_arr )

def discover_dir_repo(path, p_name, prefix_str='org', is_test=True):
    if p_name == 'tika':
        if is_test is False:
            return "{}/target/classes".format(path)
        else:
            return "{}/src/test/java/org".format(path)
    res = pt.walk_rec(path, [], prefix_str, False, lv=-4)
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
    if log and log_dir is not None:
        log_to_file(log_dir, '{}_stderr'.format(name), stderr)
        log_to_file(log_dir, '{}_stdout'.format(name), stdout)
    return stdout, stderr


def ant_command(repo_path, cmd):
    run_GIT_command_and_log(repo_path, cmd)

def checkout_version(commit, repo, log_dir, clean=False):
    '''
    mange the checkout process
    '''
    if clean:
        command_git = 'git reset --hard'.format(commit)
        run_GIT_command_and_log(repo, command_git, log_dir, 'git_reset_hard')
        command_git = 'git clean -f'.format(commit)
        run_GIT_command_and_log(repo, command_git, log_dir, 'git_clean_f')
        del_dependency_dir(repo)

    else:
        command_git = 'git checkout {}'.format(commit)
        run_GIT_command_and_log(repo, command_git, log_dir, 'checkout')
    print "[OS] {}".format(command_git)


def del_dependency_dir(repo):
    '''
    del the libb dir
    '''
    if os.path.isdir("{}/libb".format(repo)):
        os.system('rm -r {}'.format("{}/libb".format(repo)))
    else:
        res = pt.walk_rec(repo, [], 'libb', False, lv=-3)
        if len(res) > 0:
            for x in res:
                os.system('rm -r {}'.format(x))


def package_mvn_cycle(repo,folder_name='libb'):
    # mvn dependency:copy-dependencies -DskipTests=true -DoutputDirectory=${project.build.directory}/lib
    # make a dir lib with all projects dep
    mvn_command_str='dependency:copy-dependencies -DskipTests=true -DoutputDirectory={0}/{1}'.format(repo,folder_name)
    print "[mvn] {}".format(mvn_command_str)
    mvn_command(repo,None,mvn_command_str,str_command='')

    # make snapshot jar
    mvn_command_str = '-Dmaven.test.skip=true package'
    print "[mvn] {}".format(mvn_command_str)
    mvn_command(repo, None, mvn_command_str, str_command='')
    get_snapshot_to_jar_dir(repo,"{}/{}/".format(repo,folder_name))

    if os.path.isdir("{}/{}".format(repo,folder_name)) is False:
        print '[Error] maven did not crate the dependencies folder'
        return None,None
    res = pt.walk_rec("{}/{}".format(repo,folder_name),[],'.jar')
    return res,"{}/{}".format(repo,folder_name)

def get_snapshot_to_jar_dir(repo,path_to_target_folder):
    res = pt.walk_rec("{}".format(repo),[],'SNAPSHOT.jar',lv=-6)
    res = [x for x in res if str(x).__contains__('/libb/') is False]
    for item in res:
        command_cp='cp {} {}'.format(item,path_to_target_folder)
        print "[OS] {}".format(command_cp)
        os.system(command_cp)



def mvn_command(repo, module, command_mvn='clean', log_dir=None,str_command=''):
    os.chdir(repo)
    if module is not None and str(module).__contains__('-'):
        command_mvn_str = 'mvn {} -pl {} -am -fn'.format(command_mvn, module)
    else:
        command_mvn_str = 'mvn {} {}'.format(command_mvn,str_command)
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


def clean_jar_path(res):
    fin_res = []
    add_to = True
    to_del_remove = ['evosuite-standalone-runtime', 'hamcrest-core', 'junit']
    for item in res:
        add_to=True
        jar_name = str(item).split('/')[-1]
        for x in to_del_remove:
            if str(jar_name).__contains__(x):
                add_to = False
                break
        if add_to:
            fin_res.append(item)
    return fin_res

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
            if str(xml_item).endswith('xml') is False:
                continue
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
    df_killable = df[df['diff_fail_count']>0]
    df_killable = df_killable[['bug_name','bug_id']]
    df_killable.drop_duplicates(inplace=True)
    df_killable.to_csv('{}/killable.csv'.format(father_dir))
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
    print "path_file:= {}".format(path_file)
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
                            if 'classname' not in elt.attrib:
                                name_tmp = elt.attrib['name']
                                d['class_fail'] = "{}_{}".format('.'.join(str(name_tmp).split('.')[:-1]),str(name_tmp).split('.')[-1])
                            else:
                                class_name = elt.attrib['classname']
                                test_case_number = elt.attrib['name']
                                d['class_err'].append("{}_{}".format(class_name, test_case_number))
                            d['err'] = d['err'] + 1
                        elif msg.tag == 'failure':
                            if 'classname' not in elt.attrib:
                                name_tmp = elt.attrib['name']
                                d['class_fail'] = "{}_{}".format('.'.join(str(name_tmp).split('.')[:-1]),str(name_tmp).split('.')[-1])
                            else:
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
    #df_info['fauly_component'] = df_info['testcase'].apply(lambda x: str(x).split('#')[0].split('Test')[0])
    df_info['fauly_component'] = df_info['fail_component']
    #fail_component
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


    to_del = ['bug', 'class_err','test_it', 'fail','class_fail', 'err', 'test_date', 'diff_fail', 'diff_fail_count' ]
    df_merge.drop(to_del, axis=1, inplace=True)
    df_merge['is_faulty'].fillna(0, inplace=True)

    df_merge = df_merge[df_merge['test_mode'] == 'buggy']


    df_merge['count_rep'] = df_merge.groupby(['bug_id', 'bug_name', 'name', 'test_mode', 'test_time_b', 'is_faulty'])['name'].transform('count')

    df_merge['sum_rep'] = df_merge.groupby(['bug_id', 'bug_name', 'name', 'test_mode', 'test_time_b'])['binary_kill'].transform('sum')

    print df_merge.dtypes

    df_merge.drop_duplicates(subset=['bug_id', 'bug_name', 'name', 'test_mode', 'test_time_b'],inplace=True)


    df_merge.to_csv('/home/ise/bug_miner/{}/fin_df_buggy.csv'.format(p_name))


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

def dic_parser(arr_args):
    usage='no usage'
    dico_args = {}
    array = arr_args
    i = 1
    while i < len(array):
        if str(array[i]).startswith('-'):
            key = array[i][1:]
            i += 1
            val = array[i]
            dico_args[key] = val
            i += 1
        else:
            msg = "the symbol {} is not a valid flag".format(array[i])
            print(msg)
            print(usage)
            raise Exception('[Error] in parsing Args')
    return dico_args

def tmp_function(df_path='/home/ise/bug_miner/commons-math/fin_df_buggy.csv'):
    df = pd.read_csv(df_path,index_col=0)
    print list(df)
    print df['count_rep'].value_counts(sort=False)
    print ""
    exit()


def add_loc(project_name):
    csv_p = '/home/ise/bug_miner/{}/fin_df_buggy.csv'.format(project_name)
    df_fin = pd.read_csv(csv_p, index_col=0)
    p_name = str(csv_p).split('/')[-2]
    father_dir='/'.join(str(csv_p).split('/')[:-1])
    out_loc = pt.mkdir_system(father_dir,'LOC',False)
    repo_path = "{}/{}".format('/'.join(str(csv_p).split('/')[:-1]),p_name)
    print repo_path
    df_info = pd.read_csv("{}/tmp_files/{}_bug.csv".format(os.getcwd(),p_name),index_col=0)
    list_bug_generated = df_fin['bug_name'].unique()
    print list(df_info)
    print len(df_info)
    df_info = df_info[df_info['issue'].isin(list_bug_generated)]
    df_info.apply(add_loc_helper,repo=repo_path,out=out_loc,axis=1)
    # get all df loc from LOC folder
    res_df_loc_path = pt.walk_rec(out_loc,[],'.csv')
    all_loc_list = []
    for item_loc_path in res_df_loc_path:
        all_loc_list.append(pd.read_csv(item_loc_path,index_col=0))
    df_all_loc = pd.concat(all_loc_list)
    print list(df_all_loc)
    print list(df_fin)
    print len(df_fin)
    df_all_loc.to_csv('{}/{}.csv'.format(father_dir,'loc'))
    result_df = pd.merge(df_all_loc,df_fin,'right',on=['bug_name', 'name'])
    result_df.to_csv('{}/{}.csv'.format(father_dir,'exp'))
    print len(result_df)

def add_loc_helper(row,repo,out):
    '''
    getting the loc info to LOC dir
    :param repo: path to repo
    :param out: path where to write the csv
    '''
    commit_buggy = row['parent']
    bug_id = row['issue']
    path_to_faulty = row['component_path']
    package_name = row['package']
    print path_to_faulty
    checkout_version(commit_buggy,repo,None)
    pack = '/'.join(str(path_to_faulty).split('\\')[:-1])
    klasses = pt.walk_rec('{}/{}'.format(repo,pack),[],'.java')
    d_l=[]
    for class_i in klasses:
        name = pt.path_to_package('org',class_i,-5)
        size = get_LOC(class_i)
        d_l.append({'name':name,'LOC':size,'bug_name':bug_id})
    df=pd.DataFrame(d_l)
    df.to_csv('{}/{}_LOC.csv'.format(out,bug_id))


def FP_dir_clean(dir_p='/home/ise/bug_miner/commons-lang/FP/raw'):
    res = pt.walk_rec(dir_p,[],'testing')
    res = [x for x in res if str(x).endswith('csv')]
    for csv_p in res:
        continue
        father_path = '/'.join(str(csv_p).split('/')[:-1])
        new_name='testing__results_pred.csv'
        command = 'mv {} {}/{}'.format(csv_p , father_path,new_name)
        print '[OS] {}'.format(command)
        os.system('{}'.format(command))
    res_father_folder = ['/'.join(str(x).split('/')[:-1]) for x in res]
    for item in res_father_folder:
        name_tag = str(item).split('/')[-1]
        print name_tag
        df_path = make_FP_pred(item)

def get_all_commons_dir(p):
    res = pt.walk_rec(p,[],'commons-',False,-1)
    return res

def parser():
    if len(sys.argv) > 1:
        dir_bug_miner = '/home/ise/bug_miner'
        project = sys.argv[1]
        if sys.argv[1] == 'p':
            project = sys.argv[2]
            repo_path = '{0}/{1}/{1}'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_bug_process(project, repo_path, out_p,killable=False,jarz=True)
            csv_bug_process(project, repo_path, out_p, killable=False,self_complie=True)
        if sys.argv[1] == 'fix':
            project = sys.argv[2]
            repo_path = '{0}/{1}/{1}'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_bug_process(project, repo_path, out_p, killable=False, self_complie=True)
        elif project == 'tika':
            repo_path = '{0}/{1}/{1}'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_bug_process(project, repo_path, out_p,jarz=True)
        elif project == 'opennlp':
            repo_path = '{0}/{1}/{1}'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            #csv_bug_process(project, repo_path, out_p,killable=False,pref='opennlp',jarz=True)
            csv_bug_process(project, repo_path, out_p, killable=False,pref='opennlp', self_complie=True)
        elif project == 'commons-net':
            repo_path = '{0}/{1}/{1}'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_bug_process(project, repo_path, out_p,killable=False)
        elif project == 'commons-collections':
            repo_path = '{0}/{1}/{1}'.format(dir_bug_miner, project)
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_bug_process(project, repo_path, out_p,killable=False)
            csv_bug_process(project, repo_path, out_p, killable=False,self_complie=True)
        elif sys.argv[1] == 'fix_all':
            path_hard_bug_miner = dir_bug_miner
            res = get_all_commons_dir(path_hard_bug_miner)
            for item in res:
                project_name = str(item).split('/')[-1]
                repo_path = '{0}/{1}/{1}'.format(dir_bug_miner, project_name)
                out_p = '{}/{}/res'.format(dir_bug_miner, project_name)
                csv_bug_process(project_name, repo_path, out_p, killable=False,self_complie=True)
        elif sys.argv[1] == 'res':
            project = sys.argv[2]
            out_p = '{}/{}/res'.format(dir_bug_miner, project)
            csv_path_res = get_test_xml_csv(out_p)
            df_path = make_csv_diff(csv_path_res)
            add_fulty_bug('{}/{}/tmp_df.csv'.format(dir_bug_miner, project),project)
        elif sys.argv[1]=='add_loc':
            add_loc(sys.argv[2])
        elif sys.argv[1] == 'make_fp_raw':
            FP_dir_clean()
        elif sys.argv[1] == 'clean':
            res = pt.walk_rec('/home/ise/bug_miner/{}'.format(sys.argv[2]),[],'complie_out',False)
            for item in res:
                os.system('rm -r {}'.format(item))
            res = pt.walk_rec('/home/ise/bug_miner/{}'.format(sys.argv[2]), [], 'junit_out',False)
            for item in res:
                os.system('rm -r {}'.format(item))



if __name__ == "__main__":
    #TODO: Max 2 fault component the next one it the big test change

    #sys.argv=['','p','commons-math']
    #sys.argv = ['', 'opennlp']
    #sys.argv = ['','opennlp']
    parser()
    exit()
    #FP_dir_clean()
    #add_loc()
    get_all_poms_and_add_evo('/home/ise/bug_miner/commons-codec/commons-codec')
    #exit()
    print '\n\n'
    print "---Done"*10
    exit()


    # count dir
    p='/home/ise/bug_miner/commons-beanutils/res'
    res_xml = pt.walk_rec(p,[],'.xml')
    d={}

    for item in res_xml:
        bug_iss = str(item).split('/')[-4]
        if bug_iss not in d:
            d[bug_iss]=0
        d[bug_iss]+=1
    z =  d.values()
    from collections import Counter
    print Counter(z)