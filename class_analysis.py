import pandas as pd
import numpy as np
import os
import pit_render_test as pt


def get_class_size(root_path):
    walker_obj = pt.walk(root_path,"")


def missing_class_gen(root_class,root_test):
    # full path for the test and the .class files
    scanner_class = pt.walk(root_class,".class")
    scanner_tests = pt.walk(root_test, "ESTest.java")
    print "classes size ={}".format(len(scanner_class))
    print "tests size ={}".format(len(scanner_tests))
    # convert the full path to package format
    scanner_class_pak = [pt.path_to_package('org',x,-6) for x in scanner_class ]
    scanner_tests_pak = [pt.path_to_package('org',y,-12) for y in scanner_tests ]
    look_at_test(classes=scanner_class,tests=scanner_tests)
    exit()
    dict_diff(list_one=scanner_class_pak,list_two=scanner_tests_pak,path_root_test=root_test)



def dict_diff(list_one,list_two,path_root_test):
    '''see the different between two list with class as package'''
    d_test_no_class=list()
    data_df = []
    d={}
    for item in list_one:
        if item in d:
            raise Exception("cant be two class with the same prefix package")
        else:
            if str(item).__contains__('$'):
                continue
            d[item]={'class':item, 'java(.class)':1, 'test':0 }
    for item_2 in list_two:
        if item_2 in d:
            d[item_2]['test']+=1
            if d[item_2]['test'] > 1 :
                raise Exception("cant be two class with the same prefix package")
        else:
            print "[Error] test has no matching java class "
            d[item_2] = {'class':item, 'java(.class)':0, 'test':1}
    data_df_miss = []



    for vali in d.values():
        if vali['test'] != 1 or vali['java(.class)'] != 1:
            data_df_miss.append(vali)
        data_df.append(vali)

    df = pd.DataFrame(data_df)
    df.to_csv('/home/ise/tmp/diff.csv')

    df = pd.DataFrame(data_df_miss)
    df.to_csv('/home/ise/tmp/miss.csv')
    print "Done !"
    return  df


def look_at_test(classes,tests):
    '''some info'''
    d={}
    for klass in classes:
        ky = pt.path_to_package('org',x,-6)
    file_n = 'jars/loc.txt'
    string_command = 'loc {}'.format(root_test_path,file_n )
    os.system(string_command)
    lines = [line.rstrip('\n') for line in open(file_n )]
    os.system('rm {}'.format(file_n ))
    d={}
    for line in lines:
        arr=line.split()
        if len(arr) != 2 :
            continue
        if str(arr[1]).__contains__('ESTest_scaffolding'):
            continue
        d[pt.path_to_package('org',arr[1],-12) ] = int(arr[0])
    return d


def func_start():
    print "...."


if __name__ == "__main__":
    path_class= '/home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/'
    path_test = '/home/ise/eran/exp_little/02_12_18_22_51_t=1_/U_exp_tMon_Feb_12_18:22:52_2018_t=1_it=0/org/'
    missing_class_gen(root_class=path_class,root_test=path_test)

