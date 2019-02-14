from os import path, system
from subprocess import Popen, PIPE, check_call, check_output
import pit_render_test as pt
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
    files.append('/home/ise/eran/evosuite/jar/evosuite-standalone-runtime-1.0.5.jar')
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


def test_junit_commandLine(dir_class, dir_jars, out_dir,prefix_package='org'):
    '''
    this function go over all the test clases and run the Junit test
    :param dir_class: 
    :param dir_jars: 
    :return: None
    '''
    out = pt.mkdir_system(out_dir,'junit_output')
    running_dir=None
    files_jars = pt.walk_rec(dir_jars, [], '.jar')
    files_jars.append('/home/ise/eran/evosuite/jar/evosuite-standalone-runtime-1.0.5.jar')
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
        d_res.append({'out':stdout,'err':stderr,'status':parser_std_out_junit(stdout),'class':ky})
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


if __name__ == "__main__":
    #parser()
    class_dir='/home/ise/bug_miner/opennlp/res/1212_170/EVOSUITE/U_exp_tTue_Feb_12_20:10:16_2019_t=3_it=0/opennlp/tools/util/featuregen/DictionaryFeatureGenerator_ESTest.java'
    class_dir='/home/ise/bug_miner/opennlp/res/1212_170/EVOSUITE/U_exp_tTue_Feb_12_20:10:16_2019_t=3_it=0/opennlp/tools/util/featuregen/'
    jar_dir='/home/ise/bug_miner/opennlp/res/1212_170/dep'
    jar_dir='/home/ise/bug_miner/opennlp/opennlp/libb'
    out_dir='/home/ise/bug_miner/opennlp/res/1212_170/out'
    #compile_java_class(class_dir,out_dir,jar_dir)
    test_class='/home/ise/bug_miner/opennlp/res/1212_170/out/test_classes'
    test_junit_commandLine(test_class,jar_dir,out_dir,'opennlp')
