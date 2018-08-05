import pandas as pd
import numpy as np
import pit_render_test as pt
import os

'''
This script handel the csv operation on the D4J exp
'''

def uniform_vs_prefect_oracle(csv_path, allocation_mode_name ='allocation_mode'):
    '''
    this function map between the uniform allocation to the prefect oracle
    '''
    out = '/'.join(str(csv_path).split('/')[:-1])
    if os.path.isfile(csv_path) is False:
        msg  = "[Error] invalid csv path -> {}".format(csv_path)
        raise Exception(msg)
    df = pd.read_csv(csv_path, index_col=0)
    #clean all the FP rows
    df_uniform = df[df[allocation_mode_name] != 'FP' ]
    df_uniform.to_csv("{}/df_uniform.csv".format(out),sep=';')
    df_uniform = df_uniform.groupby(['bug_ID']).size().reset_index(name='package_size')
    df_uniform.to_csv("{}/group_package.csv".format(out),sep=';')
    print len(df)
    print len(df_uniform)

def get_package_csv(root_dir):
    '''
    this function take a dir and count the evosuite class generate and the faulty class put put this info to csv
    :param root_dir:
    :return:
    '''
    list_of_d=[]
    dirs_bug_id = pt.walk_rec(root_dir,[],'P_',lv=-1,file_t=False)
    for dir in dirs_bug_id:
        name = str(dir).split('/')[-1]
        bug_id = name.split('_')[3]
        proj_name = name.split('_')[1]
        size_of_package = 0
        size_of_faulty = 0
        if os.path.isdir("{}/Evo_Test".format(dir)):
            num_log_test = pt.walk_rec("{}/Evo_Test".format(dir),[],'.txt')
            size_of_package=len(num_log_test)-1
        else:
            size_of_package=-1
        if os.path.isfile("{}/log/bug_classes.txt".format(dir)):
            with open("{}/log/bug_classes.txt".format(dir),'r') as f:
                lines = f.readlines()
                ctr=0
                for line in lines:
                    if str(line).__contains__('org'):
                        ctr=ctr+1
            size_of_faulty=ctr
        else:
            size_of_faulty=-1
        list_of_d.append({'bug_id':bug_id,'project':proj_name,'size_package':size_of_package,'size_faulty':size_of_faulty})
    out = '/'.join(str(root_dir).split('/')[:-1])
    df=pd.DataFrame(list_of_d)
    df.to_csv("{}/info_pakage.csv".format(out))


'''
need to go over all the bug ID and extract the fault class and all its package class
'''

if __name__ == "__main__":
    p='/home/ise/MATH/Defect4J/D4J_MATH - Sheet2.csv'
    #get_package_csv('/home/ise/eran/eran_D4j/MATH_t=2')
    #exit()
    uniform_vs_prefect_oracle(p)