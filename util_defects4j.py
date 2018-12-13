
import os
import pandas as pd
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
        path_jar = '/'.join(str(item['path']).split('/')[:-1])
        command_test = '{0}/run_bug_detection.pl -d {1}/ -p {2} -v {3}f -o {4} {5} -D'.format(d4j_dir_bin,
                                                                                              path_jar,
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


def execute_command(command,name='log',log_dir=None):
    print "[OS] {}".format(command)
    process = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if log_dir is not None:
        write_log(log_dir, command, "{}_commnd".format(name))
        write_log(log_dir, stdout, "{}_stdout".format(name))
        write_log(log_dir, stderr, "{}_stderr".format(name))


def make_jar(path_target_dir, name, out, log=None):
    path_father_dir = '/'.join(str(path_target_dir).split('/')[:-1])
    os.chdir(path_father_dir)
    target = str(path_target_dir).split('/')[-1]
    command_jar = 'jar cvf {}.jar {}'.format(name, target)
    command_mv = 'mv {}/{}.jar {}/'.format(path_father_dir,name, out)
    execute_command(command_jar,log)
    execute_command(command_mv,log)

def rm_dir_by_name(root, name=None):
    if name is None:
        print '[Error] name is None'
        return
    all_res = pt.walk_rec(root, [], name, False)
    for x in all_res:
        final_command = 'rm -r -f {}'.format(x)
        process = Popen(shlex.split(final_command), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print "----stdout----"
        print stdout
        print "----stderr----"
        print stderr


def check_missing_fp_class(loc_dir='/home/ise/tmp_d4j/LOC',fp_dir='/home/ise/tmp_d4j/out_pred/out',p_name='Lang'):
    '''
    the loc dir has all the comppnents and the line of code, so by mergeing it with the fp file,
    we can see if ypu have mssing predection.
    '''
    LOC_target_dir_path = "{}/{}".format(loc_dir,p_name)
    fp_dir_project = "{}/{}".format(fp_dir,p_name)
    res_fp_files = pt.walk_rec(fp_dir_project ,[],'FP.csv')
    res_loc_files = pt.walk_rec(LOC_target_dir_path ,[],'csv')
    loc_df=[]
    fp_df=[]
    for item_loc in res_loc_files:
        loc_df.append(pd.read_csv(item_loc))
    for item_fp in res_fp_files:
        fp_df.append(pd.read_csv(item_fp,index_col=0))
    all_loc = pd.concat(loc_df)
    all_fp = pd.concat(fp_df)
    all_fp = all_fp[['name','FP','class']]
    all_loc = all_loc[['name','bug_ID','path']]
    loc_name = all_loc['name'].unique()
    fp_name = all_fp['name'].unique()
    ctr_miss =0
    miss=[]
    for x in loc_name:
        if x not in fp_name:
            print x
            miss.append(x)
            ctr_miss+=1
    filter_df = all_loc.loc[all_loc['name'].isin(miss)]
   ## print filter_df[['path','bug_ID']]
    #print 'loc_name\t',len(loc_name)
    #print 'fp_name\t',len(fp_name)
    print "ctr_miss:\t",ctr_miss



def make_repo_of_test(root_dir='/home/ise/eran/JARS/JARS_D4J'):
    res = pt.walk_rec(root_dir,[],'P_',False,lv=-1)
    out= '/'.join(str(root_dir).split('/')[:-1])
    DATA_folder = '/home/ise/eran/JARS/DATA_2'
    d_l=[]
    dico={}
    for dir_i in res:
        dir_name_i = str(dir_i).split('/')[-1]
        p_name_i = dir_name_i.split('_')[1]
        b_time = dir_name_i.split('_')[5]
        bug_id = dir_name_i.split('_')[3]
        index_test = dir_name_i.split('_')[7]
        date_time = '_'.join(dir_name_i.split('_')[9:])
        try:
            df = pd.read_csv("{}/tree_df.csv".format(dir_i), index_col=0)
        except IOError as e:
            continue
        list_test_df = df['test_component'].unique()
        size_test_suite = len(list_test_df)

        if bug_id not in dico:
            dico[bug_id]={}
        if size_test_suite not in dico[bug_id]:
            dico[bug_id][size_test_suite] = []
        dico[bug_id][size_test_suite].append(dir_i)

        d={'project':p_name_i,'time_budget':b_time,'bug_ID':bug_id,
           'dir_path':dir_i,'test_suite_size':size_test_suite}
        d_l.append(d)

    for ky_bug in dico:
        ky_size_list = dico[ky_bug].keys()
        ky_size_list = sorted(ky_size_list)
        #print 'bugID:',ky_bug,'\t',ky_size_list[-1],'\tsize=',len(dico[ky_bug][ky_size_list[-1]])
        for item in ky_size_list[:-1]:
            for x in dico[ky_bug][item]:
                command_mv = "mv {} {}".format(x, DATA_folder)
                print "[OS] {}".format(command_mv)
                os.system(command_mv)
    df_ans = pd.DataFrame(d_l)
    df_ans.to_csv('{}/dir_info.csv'.format(out))

    exit()



if __name__ == "__main__":
    make_repo_of_test()
    check_missing_fp_class()
    print '--- util file py -----'