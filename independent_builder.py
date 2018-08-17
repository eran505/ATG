from os import path, system
from subprocess import Popen, PIPE, check_call, check_output
import pit_render_test as pt
import subprocess
import shlex
import os.path

def compile_java_class(dir_to_compile, output_dir, dependent_dir):
    """
    this function compile the .java tests to .class
    :param dir_to_compile: path where .java files
    :param output_dir: output dir where .class will be found
    :param dependent_dir: .jar for the compilation process
    :return: output dir path
    """
    if path.isdir(dir_to_compile) is False:
        msg = "no dir : {}".format(dir_to_compile)
        raise Exception(msg)
    out_dir = pt.mkdir_system(output_dir, 'test_classes')
    files = pt.walk_rec(dependent_dir, [], '.jar', lv=-2)
    files.append('/home/ise/eran/evosuite/jar/evosuite-standalone-runtime-1.0.5.jar')
    jars_string = ':'.join(files)
    dir_to_compile = '{}*'.format(dir_to_compile)
    string_command = "javac {0} -verbose -Xlint -cp {1} -d {2} -s {2} -h {2}".format(dir_to_compile, jars_string,
                                                                                out_dir)
    print string_command
    x = system(string_command)
    return x
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
        index = split_arr.index(prefix_package)
        if index >= 0:
            package_string = '.'.join(split_arr[index:])
            d[package_string] = item
        else:
            msg = 'no prefix package {} in the path: {}'.format(prefix_package, item)
            raise Exception(msg)
    command_Junit = "java -cp {} org.junit.runner.JUnitCore".format(jars_string)
    d_res={}
    for ky in d:
        print ky
        final_command = "{} {}".format(command_Junit, ky)
        print final_command
        process = Popen(shlex.split(final_command), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print "----stdout----"
        print stdout
        print "----stderr----"
        print stderr
        d_res[ky]={'out':stdout,'err':stderr,'status':parser_std_out_junit(stdout)}
        with open('{}/{}_out_test.txt'.format(out,ky),'w') as f:
            f.write("stdout:\n{}stderr:\n{}".format(stdout,stderr))
    for k in d_res.keys():
        print "{} : {}".format(k,d_res[k])
    return d_res


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
    mvn_builder = False
    ant_builder = False
    if os.path.isfile('{}/pom.xml'.format(project_dir_path)):
        mvn_builder=True
    if os.path.isfile('{}/build.xml'.format(project_dir_path)):
        ant_builder=True

    os.chdir(project_dir_path)
    if mvn_builder:
        command = 'mvn package -Dmaven.test.skip=true'
        os.system(command)
        ans = pt.walk_rec("{}/target".format(project_dir_path),[],'.jar')
        if len(ans) == 1:
            return ans[0]
    if ant_builder:
        command = 'ant jar'
        os.system(command)
        ans = pt.walk_rec("{}/target".format(project_dir_path),[],'.jar')
        if len(ans) == 1:
            return ans[0]

    return None

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





if __name__ == "__main__":
    fix_p='/home/ise/eran/eran_D4j/Lang_t=5/P_Lang_B_36_Mon_Aug_13_22_00_06_2018/fix_jar'
    dir_compile='{}/org/apache/'.format(fix_p)
    out_dir = '{}/out_test'.format(fix_p)
    jar_dir='{}/jars/'.format(fix_p)
    class_dir = '{}/test_classes'.format(fix_p)


    #dir_compile = '/home/ise/Desktop/mock_ex/U_exp_mock/org/mockito/'
    #out_dir = '/home/ise/Desktop/mock_ex'
    #jar_dir = '/home/ise/Desktop/mock_ex/jars/'
    #class_dir = '/home/ise/Desktop/mock_ex/test_classes'
    #compile_java_class(dir_compile, out_dir, jar_dir)
    test_junit_commandLine(class_dir, jar_dir,out_dir)
