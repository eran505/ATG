import pit_render_test as pt
import sys,os
import re
#sys.path.append("/home/ise/eran/git_repos/mvnpy")
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


def checkout_tika(dir_dis):
    url='https://github.com/apache/tika.git'
    cwd = os.getcwd()
    os.chdir(dir_dis)
    os.system('git clone {}'.format(url))
    os.chdir(cwd)
    print "Done cloning TIKA"

def csv_bug_process(csv_bug='/home/ise/eran/repo/ATG/tmp_files/tika_bug.csv',repo_path='/home/ise/eran/tika_exp/tika',out='/home/ise/eran/tika_exp/res'):

    if os.path.isdir(repo_path) is False:
        repo_path_father = '/'.join(str(repo_path).split('/')[:-1])
        checkout_tika(repo_path_father)
    print "{}".format(csv_bug)
    df = pd.read_csv(csv_bug,index_col=0)
    print list(df)
    df['package'] = df['testcase'].apply(lambda x : '/'.join(str(x).split('.')[:-1]))
    df['fail_test'] = df['testcase'].apply(lambda x : str(x).split('#')[0])
    df['fail_test_METHOD'] = df['testcase'].apply(lambda x: str(x).split('#')[1])
    df.drop('testcase', axis=1, inplace=True)
    print len(df)
    df.drop_duplicates(inplace=False)
    print len(df)
    df.apply(applyer_bug,repo=repo_path,out_dir=out,axis=1)
    exit()

def applyer_bug(row,out_dir,repo):
    tag_parent = row['tag_parent']
    module = row['module']
    commit_p = row['parent']
    commit_bug = row['commit']
    bug_name = row['issue']
    index_bug = row['index_bug']
    ######
    #look_for = "{}_{}".format(bug_name,index_bug)
    #ans  = to_del()
    #ans = ['TIKA-781_47']
    #if look_for not in ans:
    #   return
    ######
    package = row['package']
    out_dir_new = pt.mkdir_system(out_dir,"{}_{}".format(bug_name,index_bug))
    out_evo = pt.mkdir_system(out_dir_new,'EVOSUITE')
    path_to_pom = "{}/pom.xml".format(repo)
    dir_to_gen = '{}/target/classes/{}'.format(repo, package)
    if str(module).__contains__('-'):
        path_to_pom = '{}/{}/pom.xml'.format(repo,module)
        dir_to_gen = '{}/{}/target/classes/{}'.format(repo, module, package)
    print "module={} \t tag_p = {} \t commit_p ={}".format(module,tag_parent,commit_p)
    checkout_version(commit_p,repo,out_dir_new)
    proj_dir = '/'.join(str(path_to_pom).split('/')[:-1])
    rm_exsiting_test(proj_dir)
    out_log = pt.mkdir_system(out_dir_new, 'LOG', False)
    mvn_command(repo, module, 'clean', out_log)
    mvn_command(repo, module, 'compile', out_log)


    # Run Evosuite generation mode
    add_evosuite_text(path_to_pom,None)
    sys.argv = ['.py', dir_to_gen , 'evosuite-1.0.5.jar',
                '/home/ise/eran/evosuite/jar/', out_evo+'/', 'exp', '100', '1', '75', '2', 'U']
    bg.init_main()
    evo_test_run(out_evo,repo,module,proj_dir,mode='fixed')
    checkout_version(commit_p,repo,out_dir_new,clean=True)

    # Run test-suite on the buugy version
    checkout_version(commit_bug,repo,out_dir_new)
    rm_exsiting_test(proj_dir)
    mvn_command(repo, module, 'clean', out_log)
    mvn_command(repo, module, 'compile', out_log)
    add_evosuite_text(path_to_pom,None)
    evo_test_run(out_evo, repo, module, proj_dir,mode='buggy')
    checkout_version(commit_bug,repo,out_dir_new,clean=True)

    # rm pom.xml for the next checkout
    mvn_command(repo, module,'clean',out_log)

def evo_test_run(out_evo,mvn_repo,moudle,project_dir,mode='fix'):
    out_evo = '/'.join(str(out_evo).split('/')[:-1])
    res = pt.walk_rec(out_evo,[],'org',False)
    if len(res) == 0:
        return
    test_dir = "{}/src/test/java/".format(project_dir)
    rm_exsiting_test(project_dir)
    for path_res in res:
        command_cp_test = "cp -r {} {}".format(path_res,test_dir)
        dir_name_evo = str(path_res).split('/')[-2]
        print "[OS] {}".format(command_cp_test)
        out_log = pt.mkdir_system(out_evo,'LOG',False)
        os.system(command_cp_test)
        mvn_command(mvn_repo,moudle,'test-compile',out_log)
        mvn_command(mvn_repo, moudle, 'test', out_log)


        # moving the results to the evo_out dir
        test_dir = "{}/target/surefire-reports".format(project_dir)
        res_test_file = pt.walk_rec(test_dir,[],'.xml')
        # filter only the evo_suite test
        res_test_file = [x for x in res_test_file if str(x).split('/')[-1].__contains__('_ESTest')]
        out_results = pt.mkdir_system(out_evo, 'Result', False)
        out_results_evo = pt.mkdir_system(out_results, "{}_{}".format(dir_name_evo,mode) , False)
        for test_item in res_test_file:
            command_mv = "mv {} {}".format(test_item,out_results_evo)
            print "[OS] {}".format(command_mv)
            os.system(command_mv)
        rm_exsiting_test(project_dir)


def rm_exsiting_test(path_p):
    dir_to_del  = '{}/src/test/java/org'.format(path_p)
    if os.path.isdir(dir_to_del):
        command_ram='rm -r {}'.format(dir_to_del)
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

def checkout_version(commit,repo,log_dir,clean=False):
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


def mvn_command(repo,module,command_mvn='clean',log_dir=None):
    os.chdir(repo)
    if str(module).__contains__('-'):
        command_mvn = 'mvn {} -pl {} -am -fn'.format(command_mvn,module)
    else:
        command_mvn = 'mvn {} -fn'.format(command_mvn, module)
    process = Popen(shlex.split(command_mvn), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if log_dir is None:
        return
    log_to_file(log_dir, '{}_stdout'.format(command_mvn), stdout)
    log_to_file(log_dir, '{}_stderr'.format(command_mvn,), stderr)


def add_evosuite_pom(path_xml='/home/ise/eran/git_repos/tika/tika-core/pom.xml',out='/home/ise/test/pom'):
    if os.path.isfile(path_xml) is False:
        raise "[Error] no file in the path --> {}".format(path_xml)
    try:
        root_node = ET.parse(path_xml).getroot() #get the root xml
    except (Exception, ArithmeticError) as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print (message)
        return None
    for elem in root_node.iter():
        print elem.tag
    exit()


def add_evosuite_text(path_pom='/home/ise/eran/git_repos/tika/tika-core/pom.xml',out='/home/ise/test/pom'):
    dico_appends = dico_eco_pom_build()
    str_pom = None
    with open(path_pom,'r') as f_pom:
        str_pom=f_pom.read()
        #str_pom,bol = replacer(str_pom, '<plugins>', 'plugin',dico_appends )
        str_pom,bol = replacer(str_pom, '<artifactId>junit</artifactId>', 'junit_ar',dico_appends)
        if bol is False:
            str_pom,bol = replacer(str_pom,'<dependencies>','dep',dico_appends )
        else:
            str_pom,bol = replacer(str_pom, '<dependencies>', 'dependency', dico_appends)
    if bol is False:
        str_pom, bol = replacer(str_pom, '</project>', 'all_section', dico_appends)
    path_rel = '/'.join(str(path_pom).split('/')[:-1])
    ##os.system('rm {}'.format(path_pom))
    if out is None:
        out = path_rel
    with open('{}/pom.xml'.format(out),'w') as new_pom:
        new_pom.write(str_pom)
    return True



def replacer(str_input,str_look_for,str_append_after,d):
    '''
    this fuction adding the given seq to the pom by looking for a pattren
    '''
    ans = [m.start() for m in re.finditer(r'{}'.format(str_look_for), str_input)]
    print ans
    if len(ans) == 0 :
        print "[Error] the retrun is not one in the replacer function len(ans)={} look={}".format(len(ans),str_look_for)
        return str_input,False
    path = d[str_append_after]
    with open(path,'r') as f:
        str_ap = f.read()
    if str_look_for == '</project>':
        index = ans[0]-1
    else:
        index = ans[0] + len(str_look_for)
    if str_append_after == 'junit_ar':
        ver_index = clean_version_tag(str_input,index)
        ver_index+=1
        str_input = str_input[:index] + str_ap + str_input[index+ver_index:]
    else:
        str_input = str_input[:index] + str_ap + str_input[index:]
    return str_input,True

def clean_version_tag(str_input,start_index):
    '''
    if any version tag in the pom, clean in the junit scope
    '''
    acc=''
    ctr=0
    flag=2
    for letter in str_input[start_index:]:
        if letter!='\n':
            ctr+=1
            acc+=letter
        else:
            if acc.__contains__('version'):
                return ctr
            else:
                acc=''
            flag = flag - 1
            if flag == 0:
                return 0


def dico_eco_pom_build():
   d={}
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
    res_tiks = pt.walk_rec(p,[],'TIKA',False,lv=-1)
    res_org = pt.walk_rec(p,[],'org',False,lv=-6)
    print "res_tiks =",len(res_tiks )
    print "res_org  =", len(res_org )
    res_org = ['/'.join(str(x).split('/')[:-2] ) for x in res_org]
    dif  = []
    for y in res_tiks :
        if y not in res_org:
            dif.append(y)
    ans = []
    for item in dif:
        ans.append(str(item).split('/')[-1])
        #print str(item).split('/')[-1]
    exit()

if __name__ == "__main__":
    #to_del()
    #add_evosuite_text('/home/ise/test/pom.xml','/home/ise')
    csv_bug_process()
    print ""
