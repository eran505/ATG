
import os
import pit_render_test as pt
from subprocess import Popen, PIPE, check_call, check_output
import sys, time,shlex


def change_runtime_and_gen_jars(version='0'):
    if version == '0':
        evo='evo_d4j'
        evo_rt = 'evo_d4j_rt'
    elif version == '5':
        evo='evosuite-1.0.5'
        evo_rt='evosuite-standalone-runtime-1.0.5'
    else:
        evo='evo_d4j'
        evo_rt = 'evo_d4j_rt'
    #generation
    change_evo_suite_version_D4j(new_ver=evo,path_d4j='/home/ise/programs/defects4j/framework/lib/test_generation/generation',default_name='evo_d4j',d4j_name_used='evosuite-current')
    #runtime
    change_evo_suite_version_D4j(new_ver=evo_rt,path_d4j='/home/ise/programs/defects4j/framework/lib/test_generation/runtime',default_name='evo_d4j_rt',d4j_name_used='evosuite-rt')

def change_evo_suite_version_D4j(new_ver='evosuite-1.0.5',path_d4j='/home/ise/programs/defects4j/framework/lib/test_generation/generation',path_jar_evo='/home/ise/eran/evosuite/jar',default_name='evo_d4j',d4j_name_used='evosuite-current'):
    # check if the default evo_suite version is in the OS jar dir
    #name_evo='evosuite-current'
    #name_evo_runtime='evosuite-rt'
    if os.path.isfile('{}/{}.jar'.format(path_jar_evo,default_name)):
        print '[py] The default exist in the JAR dir'
    else:
        # copy the default from the D4j path to JAR
        res = pt.walk_rec(path_d4j,[],'.jar')
        if len(res) == 0:
            msg = '[Error] cant find the evosuite jar in the defect4j dir --> {}'.format(path_d4j)
            raise Exception(msg)
        find=False
        for file in res:
            name = str(file).split('/')[-1]
            if name == '{}.jar'.format(d4j_name_used):
                comaand_cp = 'cp {} {}/{}.jar'.format(file,path_jar_evo,default_name)
                print '[OS] {}'.format(comaand_cp)
                os.system(comaand_cp)
                find=True
                break
        if find is False:
            print '[Warning] cant find the default d4j Evosuite version'
    if os.path.isfile('{}/{}.jar'.format(path_d4j,d4j_name_used)):
        command_rm = 'rm {}/{}.jar'.format(path_d4j,d4j_name_used)
        print '[OS] {}'.format(command_rm)
        os.system(command_rm)

    # Move the target version to d4j form jar dir
    if new_ver == 'def':
        new_ver=default_name
    res_file = pt.walk_rec(path_jar_evo,[],'{}.jar'.format(new_ver))
    if len(res_file) == 1:
        command_cp_mv = 'cp {} {}/{}.jar'.format(res_file[0],path_d4j,d4j_name_used)
        print '[OS] {}'.format(command_cp_mv)
        os.system(command_cp_mv)



def run_tests(list_test_tar,d4j_path='/home/ise/programs/defects4j/framework/bin/defects4j'):
    '''
    /home/ise/programs/defects4j/framework/bin/run_bug_detection.pl
    -d ~/Desktop/d4j_framework/test s/Math/evosuite-branch/0/ -p Math -v 3f -o ~/Desktop/d4j_framework/out/ -D

    sudo cpan -i DBD::CSV
    '''
    print "---test phase----"
    tmp_command=''
    d4j_dir_bin = '/'.join(str(d4j_path).split('/')[:-1])
    for item in list_test_tar:
        print item
        if 'tmp_dir' in item:
            tmp_command = '-t {}'.format(item['tmp_dir'])
        p_name = item['p_name']
        if 'output' not in item:

            dir_out_bug_i = '/'.join(str(item['path']).split('/')[:-3])
            out_test_dir = pt.mkdir_system(dir_out_bug_i, 'Test_P_{}_ID_{}'.format(p_name,
                                                                                       str(time.time() % 1000).split(
                                                                                           '.')[0]))
        else:
            dir_out_bug_i = item['log']
            out_test_dir = item['output']
        command_test = '{0}/run_bug_detection.pl -d {1}/ -p {2} -v {3}f -o {4} {5} -D'.format(d4j_dir_bin,
                                                                                              item['path'],
                                                                                              item['p_name'],
                                                                                              item['version'],
                                                                                              out_test_dir,
                                                                                            tmp_command)
        print "[OS] {}".format(command_test)
        process = Popen(shlex.split(command_test), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        write_log(dir_out_bug_i, command_test, 'testing_commands.log')
        write_log(dir_out_bug_i, stdout, 'testing_stdout.log')
        write_log(dir_out_bug_i, stderr, 'testing_stderr.log')

def write_log(father_dir, info, name='missing_pred_class'):
    """
    write to log dir
    """
    dir_p = pt.mkdir_system(father_dir, 'loging', False)
    with open("{}/{}".format(dir_p, '{}.txt'.format(name)), 'a') as f:
        f.write(info)
        f.write('\n')




if __name__ == "__main__":
    print '--- util file py -----'