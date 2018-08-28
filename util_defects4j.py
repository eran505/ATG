
import os
import pit_render_test as pt

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

if __name__ == "__main__":
    print '--- util file py -----'