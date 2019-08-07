from os import path, system
from subprocess import Popen, PIPE, check_call, check_output
import pit_render_test as pt
from csv_D4J_headler import diff_function,get_regex_res,get_regex_all
import subprocess
import shlex
import sys
import os.path
import pandas as pd

def compile_java_class(dir_to_compile, output_dir, dependent_dir):
    """
    this function compile the .java tests to .class
    :param dir_to_compile: path where .java files
    :param output_dir: output dir where .class will be found
    :param dependent_dir: .jar for the compilation process
    :return: output dir path
    """
    #if path.isdir(dir_to_compile) is False:
    #    msg = "no dir : {}".format(dir_to_compile)
    #    raise Exception(msg)
    out_dir = pt.mkdir_system(output_dir, 'test_classes')
    files = pt.walk_rec(dependent_dir, [], '.jar', lv=-2)
    files.append('/home/ise/eran/evosuite/jar/evosuite-standalone-runtime-1.0.6.jar')
    jars_string = ':'.join(files)
    dir_to_compile = '{}*'.format(dir_to_compile)
    string_command = "javac {0} -verbose -Xlint -cp {1} -d {2} -s {2} -h {2}".format(dir_to_compile, jars_string,
                                                                                out_dir)
    print "[OS] {}".format(string_command)
    os.system(string_command)
    return
    process = Popen(shlex.split(string_command), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print "----stdout----"
    print stdout
    print "----stderr----"
    print stderr
    return out_dir


def test_junit_commandLine(dir_class, dir_jars, out_dir,prefix_package='org',d_add=None):
    '''
    this function go over all the test clases and run the Junit test
    :param dir_class: 
    :param dir_jars: 
    :return: None
    '''
    out = pt.mkdir_system(out_dir,'junit_output')
    running_dir=None
    files_jars = pt.walk_rec(dir_jars, [], '.jar')
    files_jars.append('/home/ise/eran/evosuite/jar/evosuite-standalone-runtime-1.0.6.jar')
    files_jars.append(dir_class)
    jars_string = ':'.join(files_jars)
    tests_files = pt.walk_rec(dir_class, [], '.class')
    tests_files = [x for x in tests_files if str(x).__contains__('_scaffolding') is False]
    d = {}
    for item in tests_files:
        split_arr = str(item).split('/')
        name = split_arr[-1].split('.')[0]
        split_arr[-1] = name
        index = split_arr.index('test_classes')+1
        if index >= 0:
            package_string = '.'.join(split_arr[index:])
            running_dir='/'.join(split_arr[:index])
            d[package_string] = {'item':item,'chdir':running_dir}

        else:
            msg = 'no prefix package {} in the path: {}'.format(prefix_package, item)
            raise Exception(msg)
    command_Junit = "java -cp {} org.junit.runner.JUnitCore".format(jars_string)
    d_res=[]
    for ky in d:
        os.chdir(d[ky]['chdir'])
        print ky
        final_command = "{} {}".format(command_Junit, ky)
        print final_command
        process = Popen(shlex.split(final_command), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print "----stdout----"
        print stdout
        print "----stderr----"
        print stderr
        d_tmp = {'out':stdout,'err':stderr,'status':parser_std_out_junit(stdout),'class':ky}
        if d_add is not None:
            for key_d in d_add.keys():
                d_tmp[key_d]=d_add[key_d]
        d_res.append(d_tmp)
        with open('{}/{}_out_test.txt'.format(out,ky),'w') as f:
            f.write("stdout:\n{}stderr:\n{}".format(stdout,stderr))
    for k in d_res:
        print "{}".format(k)
    reporting_csv(out_dir,d_res)
    return d_res




def reporting_csv(path_p,d_res,name_file='report'):
    df=pd.DataFrame(d_res)
    if os.path.isfile('{}/{}.csv'.format(path_p,name_file)) is False:
        df.to_csv('{}/{}.csv'.format(path_p,name_file))
    else:
        df_all = pd.read_csv('{}/{}.csv'.format(path_p,name_file))
        df_merg = pd.concat(df_all,df)
        df_merg.to_csv('{}/{}.csv'.format(path_p, name_file))

def parser_std_out_junit(string_sdout):
    ok_index = str(string_sdout).find('OK')
    fail_index= str(string_sdout).find('FAILURES')
    if ok_index > 0:
        return 'OK'
    elif fail_index>0:
        return 'fail'
    return None

def make_jar_file(project_dir_path):
    '''
    make a jar file with the builder mvn or ant
    '''
    fix_dir = '{}/fixed'.format(project_dir_path)
    log_dir = '{}/log'.format(project_dir_path)
    mvn_builder = False
    ant_builder = False
    if os.path.isfile('{}/pom.xml'.format(fix_dir)):
        mvn_builder=True
    if os.path.isfile('{}/build.xml'.format(fix_dir)):
        ant_builder=True

    os.chdir(fix_dir)
    out_jar = pt.mkdir_system(project_dir_path,'jar_dir',False)
    if mvn_builder:
        command = 'mvn package -Dmaven.test.skip=true'
        process = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        loging_os_command(log_dir, 'jar_command', stdout, "stdout")
        loging_os_command(log_dir, 'jar_command', stderr, "stderr")
        # os.system(command)
        ans = pt.walk_rec("{}/target".format(fix_dir),[],'.jar')
        command='mvn dependency:copy-dependencies -DoutputDirectory={}'.format(out_jar)
        process = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        loging_os_command(log_dir, 'copy_dependencies', stdout, "stdout")
        loging_os_command(log_dir, 'copy_dependencies', stderr, "stderr")
        #os.system(command)
        if len(ans) == 1:
            cp_command ='mv {} {}'.format(ans[0], out_jar)
            print '[OS] {}'.format(cp_command)
            os.system(cp_command)
            return ans[0]
    if ant_builder:
        command = 'ant jar'
        process = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        loging_os_command(log_dir,'jar_command',stdout,"stdout")
        loging_os_command(log_dir,'jar_command',stderr,"stderr")
        # os.system(command)
        ans = pt.walk_rec("{}/target".format(fix_dir),[],'.jar')
        if len(ans) == 1:
            cp_command ='mv {} {}'.format(ans[0], out_jar)
            print '[OS] {}'.format(cp_command)
            os.system(cp_command)
            return ans[0]
    return None

def loging_os_command(path_target,dir_name,msg,file_name):
    if path_target[-1]=='/':
        path_target=path_target[:-1]
    if os.path.isdir("{}/{}".format(path_target,dir_name)) is False:
        out_d = pt.mkdir_system(path_target,dir_name,False)
    else:
        out_d = "{}/{}".format(path_target,dir_name)
    with open("{}/{}.log".format(out_d,file_name),'w') as f_log:
        f_log.write("[log] {}\n".format(msg))


def wrapper_har_all(p_dir):
    success_list=[]
    fail_list=[]
    all_dirs=pt.walk_rec(p_dir,[],'P_',False)
    for dir in all_dirs:
        path_jar = make_jar_file(dir)
        if path_jar  is None:
            print "[fail] {} cant make jar".format(dir)
            fail_list.append(dir)
        else:
            success_list.append([dir,path_jar])
            print "[success] {} the jar path:{}".format(dir,path_jar)
    print success_list

def copy_and_test(test_dir,project_dir,test_ptefix='src/test/'):
    '''
    :param test_dir:
    :param project_dir:
    :return:
    '''
    if os.path.isdir('{}/{}'.format(project_dir,test_ptefix)):
        command_mv = 'cp -r {} {}/{}'.format(test_dir,project_dir,test_ptefix)
        os.system(command_mv)
        os.chdir(project_dir)
        os.system('mvn test')
    else:
        print "[Error] fail to copy"

def make_test_with_builders(root, dir_test='org'):
    all_dirs=pt.walk_rec(root,[],'P_',False)
    for dir_bug in all_dirs:
        print dir_bug
        if os.path.isdir("{}/Evo_Test"):
            org_dir = pt.walk_rec(dir_bug,[],dir_test,False)



def get_static_dir(root):
    bug_dir = pt.walk_rec(root,[],'P_',False)
    list_d=[]
    for dir_i in bug_dir:
        time_budget = str(dir_i).split('/')[-2].split('=')[1]
        proj_name = str(dir_i).split('/')[-2].split('_')[0]
        bug_id = str(dir_i).split('/')[-1].split('_')[3]
        evo_dir = os.path.isdir('{}/Evo_Test'.format(dir_i))
        if evo_dir:
            evo_dir_num = 1
            num_test_generated = len(pt.walk_rec('{}/Evo_Test'.format(dir_i),[],'.java'))
            num_test_generated = num_test_generated/float(2)
        else:
            num_test_generated=-1
            evo_dir_num=0
        d_i={"time_budget":time_budget ,'proj_name':proj_name, 'bug_id':bug_id,'evo_dir':evo_dir, 'num_test_generated':num_test_generated }
        list_d.append(d_i)
    df = pd.DataFrame(list_d)
    df.to_csv('{}/static.csv'.format(root))



def scan_results_project(folder_res):
    res = pt.walk_rec(folder_res,[],'',False,lv=-1)
    list_df_path=[]
    for item in res:
        print "bug_ID = {}".format(str(item).split('/')[-1].split('_')[-1])
        df_path = get_pair_fix_bug_folder(item)
        if df_path  is None:
            continue
        list_df_path.append(df_path)
    df_l=[]
    for csv_i in list_df_path:
        df_l.append(pd.read_csv(csv_i,index_col=0))
    if len(df_l)==0:
        print('cant find any results ')
        return
    df_all= pd.concat(df_l)
    father = '/'.join(str(folder_res).split('/')[:-1])
    get_killable_bug_id(df=df_all,dist_path=father)
    df_all.to_csv("{}/all_self_junit.csv".format(father))


def rearrange_reults(df):
    pass



def get_killable_bug_id(df_path=None,df=None,dist_path=None,update_repo=False):
    if df_path is not None:
        df_info = pd.read_csv(df_path,index_col=0)
    elif df is not None:
        df_info = df
    else:
        print ("no Args given -- [get_killable_bug_id]")

    df_info_filter = df_info[df_info['trigger'] > 0 ]
    if len(df_info_filter )==0:
        print 'cant find bugs that have been killed'
    df_info_filter = df_info_filter[['bug_id','jira_id']]

    df_info_filter.drop_duplicates(subset=None, keep='first', inplace=True)
    print "number of killed: {}".format(len(df_info_filter))
    if dist_path is not None:
        df_info_filter.to_csv('{}/killalbe_{}.csv'.format(dist_path,find_project_name(dist_path)))
        if update_repo is True:
            os_command = 'cp {1} {0}'.format('{}/tmp_files/killable/'.format(os.getcwd()),'{}/kill_{}.csv'.format(df_info_filter,find_project_name(df_info_filter)))
            os.system(os_command)
    if df_path is not None:
        father = '/'.join(str(df_path).split('/')[:-1])
        df_info_filter.to_csv('{}/kill_{}.csv'.format(father,find_project_name(father)))
        if update_repo is True:
            os_command = 'cp {1} {0}'.format('{}/tmp_files/killable/'.format(os.getcwd()),'{}/kill_{}.csv'.format(father,find_project_name(father)))
            os.system(os_command)

    return df_info_filter

def find_project_name(path):
    path_name = str(path).split('/')
    try:
        index = path_name.index('bug_miner')
    except:
        return 'unknown'
    if len(path_name) <= index+1:
        return 'unknown'
    else:
        return path_name[index+1]

def get_pair_fix_bug_folder(folder_path):
    folder_bug = pt.walk_rec(folder_path,[],'test_suite_t',lv=-2,file_t=False)
    d_pair={}
    for item in folder_bug:
        folder_mode = str(item).split('/')[-2].split('_')[0]
        if folder_mode == 'complie':
            continue
        mode =  str(item).split('/')[-2].split('_')[-1]
        iter = str(item).split('/')[-1].split('_it_')[-1]
        if iter not in d_pair:
            d_pair[iter]={}
        if mode == 'fixed':
            d_pair[iter]['fixed']=item
        elif mode =='buggy':
            d_pair[iter]['buggy']=item
    d_l = []
    for key_i in d_pair.keys():
        if 'buggy' in  d_pair[key_i] and 'fixed' in d_pair[key_i] :
            info=get_diff_fix_buggy(d_pair[key_i]['buggy'],d_pair[key_i]['fixed'])
            d_l.extend(info)
    if len(d_l) == 0:
        return None
    df = pd.DataFrame(d_l)
    df.to_csv("{}/indep_report.csv".format(folder_path))
    return "{}/indep_report.csv".format(folder_path)

def get_diff_fix_buggy(root_dir_bug,root_dir_fix):
    d_start={}
    d={'bug':{},'fix':{}}
    res_fix = pt.walk_rec(root_dir_fix,[],'.txt')
    res_bug = pt.walk_rec(root_dir_bug, [], '.txt')
    for item_fix in res_fix:
        name=str(item_fix).split('/')[-1][:-4]
        d_start[name]={'fix':item_fix}
    for item_bug in res_bug:
        name_bug = str(item_bug).split('/')[-1][:-4]
        if name_bug in d_start:
            d_start[name_bug]['bug']=item_bug
        else:
            d_start[name_bug]={'bug':item_bug}
    d_both = {}
    for ky in d_start:
        if 'bug' in d_start[ky]  and 'fix' in d_start[ky]:
            d_both[ky]={'bug':d_start[ky]['bug'],'fix':d_start[ky]['fix']}
   # print "missing --> {}".format(len(d_start)-len(d_both))
    d_l = []
    for key_i in d_both.keys():
        diff_bug, diff_fix = diff_function(d_both[key_i]['bug'],d_both[key_i]['fix'])
        #if len('Time: 0.226x')<len(diff_bug):
        #    print 'yy'
            #print diff_bug
        #if len('Time: 0.226x') <len( diff_fix):
        #    print 'xx'
            #print diff_fix



        # pars the bug_id and itr number from the path dir

        d_buggy = pars_bug_id_iter_id(d_both[key_i]['bug'])
        d_buggy['mode']='buggy'
        d_fixed = pars_bug_id_iter_id(d_both[key_i]['fix'])
        d_fixed['mode'] = 'fixed'

        # Test add name
        d_buggy['name']=str(key_i).split('_')[0]
        d_fixed['name'] = str(key_i).split('_')[0]

        # pars the itration number and time budget

        list_junit_res = get_regex_all(diff_bug,r'(test\d+.+\n\njava.lang.+)',0,False)
        info_list = pars_junit_regex(list_junit_res,d_extand=d_buggy)
        if info_list is not None:
            d_l.extend(info_list)


        list_junit_res = get_regex_all(diff_fix,r'(test\d+.+\n\njava.lang.+)',0,False)
        info_list = pars_junit_regex(list_junit_res,d_extand=d_fixed)
        if info_list is not None:
            d_l.extend(info_list)


    return d_l

def filter_error(df):
    list_error =  df['error'].unique()
    print "all error: ",df['trigger'].sum()
    map_d = {}
    for item in list_error:
        if item == 'AssertionError':
            map_d[item] = 1
        else:
            map_d[item] = 0
    df['trigger'] = df['error'].map(map_d)
    print 'only AssertionError error: ',df['trigger'].sum()
    return df

def group_test_by_test_name(path_df,all_error=False):
    df_bugs = pd.read_csv(path_df,index_col=0)
    p_name = str(path_df).split('/')[-2]
    print list(df_bugs)
    if all_error is False:
        df_bugs = filter_error(df_bugs)
    # remove error info
    df_bugs.drop(['full_error','error'], axis=1, inplace=True)

    csv_p_info = "{}/tmp_files/{}_bug.csv".format(os.getcwd(),p_name)
    df_info = pd.read_csv(csv_p_info, index_col=0)
    df_info['is_faulty'] = 1
    df_faulty = df_info[['index_bug','issue','fail_component','is_faulty']]
    df_faulty.rename(columns={'index_bug': 'bug_id',
                       'issue': 'jira_id',
                       'fail_component': 'name'}, inplace=True)
    print list(df_faulty )
    print 'df_faulty: ',len(df_faulty)
    print 'df_bugs: ',len(df_bugs)
    print "df_bugs:\t",list(df_bugs)
    print "df_faulty:\t",list(df_faulty)
    df_merge = pd.merge(df_bugs,df_faulty, how='left', on=['bug_id','jira_id','name'] )
    df_merge['is_faulty'].fillna(0, inplace=True)

    # group by all test cases and del
    df_merge['test_case_fail_num'] = df_merge.groupby(['bug_id', 'jira_id', 'name', 'mode', 'time','iter','is_faulty'])['trigger'].transform('sum')

    to_del = ['test_case', 'test_class']
    df_merge.drop(to_del, axis=1, inplace=True)
    print len(df_merge)
    df_merge.drop_duplicates(inplace=True)
    print len(df_merge)

    df_merge['kill'] = df_merge.groupby(['bug_id', 'jira_id', 'name', 'mode', 'time','iter','is_faulty'])['trigger'].transform('max')
    df_merge.drop_duplicates(subset=['bug_id', 'jira_id', 'name', 'mode', 'time','iter','is_faulty','kill'],inplace=True)

    # sum up results
    df_merge['sum_rep'] = df_merge.groupby(['bug_id', 'jira_id', 'name', 'mode', 'time'])['trigger'].transform('sum')
    df_merge['count_rep'] = df_merge.groupby(['bug_id', 'jira_id', 'name', 'mode', 'time'])['name'].transform('count')

    df_merge.drop(['iter'], axis=1, inplace=True)
    print list(df_merge)



    # remove duplication
    print len(df_merge)
    df_merge.drop_duplicates(subset=['bug_id', 'jira_id', 'mode', 'name', 'time', 'trigger', 'is_faulty', 'test_case_fail_num', 'sum_rep', 'count_rep'],inplace=True)
    print len(df_merge)
    print list(df_merge)
    #split
    df_merge_buggy = df_merge[df_merge['mode'] == 'buggy']
    df_merge_fix = df_merge[df_merge['mode'] == 'fixed']

    df_merge_buggy.rename(columns={'jira_id': 'bug_name'}, inplace=True)
    #df_merge.to_csv('/home/ise/bug_miner/{}/tmp.csv'.format(p_name))
    df_merge_buggy.to_csv('/home/ise/bug_miner/{}/fin_df_buggy.csv'.format(p_name))
    #df_merge_fix.to_csv('/home/ise/bug_miner/{}/tmp_fixed.csv'.format(p_name))





def pars_bug_id_iter_id(path_file):
    arr = str(path_file).split('/')
    iter_id = arr[-3].split('_it_')[-1]
    time_budget = arr[-3].split('_t_')[-1].split('_')[0]
    jira_id = arr[-5].split('_')[0]
    bug_id = arr[-5].split('_')[1]
    return {'bug_id':bug_id,'jira_id':jira_id,'time':time_budget,'iter':iter_id}

def pars_junit_regex(list_junit_results,d_extand):
    d_l=[]
    if list_junit_results is None or len(list_junit_results)==0:
        d_extand['trigger']=0
        return [d_extand]
    for item in list_junit_results:
        test_case_number = ''
        for i in str(item):
            if i == '(':
                break
            test_case_number+=i
        removed_test_number_string = item[len(test_case_number):]
        class_name = str(removed_test_number_string ).split('\n\n')[0][1:-1]
        error_name = str(removed_test_number_string).split('\n\n')[1].split()[0].split('.')[-1]
        if error_name[-1]==':':
            error_name=error_name[:-1]
        error_full = str(removed_test_number_string).split('\n\n')[1]
        d = {'test_case':test_case_number,'test_class':class_name,'trigger':1,'error':error_name,'full_error':error_full}
        d.update(d_extand)
        d_l.append(d)
    return d_l



def parser():
    args=sys.argv
    print args
    if len(args ) <= 1:
        print "miss args"
        exit()
    comnd = args[1]
    if comnd  == 'stat':
        get_static_dir(args[2])
    exit()



def map_dir_after_run(path_res_folder):
    '''
    # this function map all the bug dir whether the process went well or not
    '''
    res = pt.walk_rec(path_res_folder,[],'_',False,lv=-1)
    d_l=[]
    for item in res:
        print item
        d={}
        d["jira_bug"]= str(item).split('/')[-1].split('_')[0]
        d["bug_id"]= str(item).split('/')[-1].split('_')[1]
        d["EVOSUITE_dir"] = 0
        d['rep'] = 0
        if os.path.isdir('{}/EVOSUITE'.format(item)):
            res_test_java = pt.walk_rec('{}/EVOSUITE'.format(item),[],'_ESTest.java')
            d["EVOSUITE_dir"] = len(res_test_java)
            d['rep']=len(pt.walk_rec('{}/EVOSUITE'.format(item),[],'',False,lv=-1))
        d["complie_dir_buggy"] = 0
        d["complie_dir_fixed"] = 0
        d["junit_dir_buggy"] = 0
        d["junit_dir_fixed"] = 0
        dir_class_dico={}
        junit_dico = {}
        for mode in ['buggy','fixed']:
            if os.path.isdir('{}/complie_out_{}'.format(item,mode)):
                res_test_class = pt.walk_rec('{}/complie_out_{}'.format(item,mode),[],'_ESTest.class')
                d["complie_dir_{}".format(mode)] = len(res_test_class )
                dir_class_dico[mode]=res_test_class
            if os.path.isdir('{}/junit_out_{}'.format(item,mode)):
                res_junit_file = pt.walk_rec('{}/junit_out_{}'.format(item,mode),[],'.txt')
                junit_dico[mode]=res_junit_file
                d["junit_dir_{}".format(mode)] = len(res_junit_file)
        d_l.append(d)
    df = pd.DataFrame(d_l)
    father_dir = '/'.join(str(path_res_folder).split('/')[:-1])
    df.to_csv('{}/info_indp.csv'.format(father_dir))


def get_all_self_report(res_folder):
    csv_files = pt.walk_rec(res_folder,[],'report.csv')
    df_list = []
    for item_csv in csv_files:
        df_list.append(pd.read_csv(item_csv))
    df_all = pd.concat(df_list)
    father_dir = '/'.join(str(res_folder).split('/')[:-1])
    print list(df_all)
    #df_list = df_all[['bug_id','status']].to_csv('{}/all_report.csv'.format(father_dir))

if __name__ == "__main__":

    #get_killable_bug_id('/home/ise/bug_miner/commons-imaging/all_self_junit.csv')
    #exit()
    proj_name = 'commons-compress'
    proj_folder = '/home/ise/bug_miner/{}/res'.format(proj_name)
    scan_results_project(proj_folder)
    map_dir_after_run(proj_folder)
    group_test_by_test_name('/home/ise/bug_miner/{}/all_self_junit.csv'.format(proj_name))
#   map_dir_after_run('/home/ise/bug_miner/commons-validator/res')

    exit()
    get_all_self_report('/home/ise/bug_miner/commons-scxml/res')

    res = pt.walk_rec('/home/ise/bug_miner/opennlp/res',[],'',False,lv=-1)
    for item in res:
        p_bug='{}/junit_out_buggy/test_suite_t_70_it_0/junit_output'.format(item)
        p_fix='{}/junit_out_fixed/test_suite_t_70_it_0/junit_output'.format(item)
        if os.path.isdir(p_bug) and os.path.isdir(p_fix):
            get_diff_fix_buggy(p_bug,p_fix)
    exit()
    #parser()
    class_dir='/home/ise/bug_miner/opennlp/res/1212_170/EVOSUITE/U_exp_tTue_Feb_12_20:10:16_2019_t=3_it=0/opennlp/tools/util/featuregen/DictionaryFeatureGenerator_ESTest.java'
    class_dir='/home/ise/bug_miner/opennlp/res/1212_170/EVOSUITE/U_exp_tTue_Feb_12_20:10:16_2019_t=3_it=0/opennlp/tools/util/featuregen/'
    jar_dir='/home/ise/bug_miner/opennlp/res/1212_170/dep'
    jar_dir='/home/ise/bug_miner/opennlp/opennlp/libb'
    out_dir='/home/ise/bug_miner/opennlp/res/1212_170/out'
    #compile_java_class(class_dir,out_dir,jar_dir)
    test_class='/home/ise/bug_miner/opennlp/res/1212_170/out/test_classes'
    test_junit_commandLine(test_class,jar_dir,out_dir,'opennlp')
