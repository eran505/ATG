import pandas as pd
import numpy as np
import os

import subprocess

import pit_render_test as pt


def get_class_size(root_path):
    walker_obj = pt.walk(root_path,"")


def missing_class_gen(root_class,root_test,java_src,log,name='tmp'):
    # full path for the test and the .class files

    scanner_class = pt.walk(root_class,".class")
    scanner_java = pt.walk(java_src,".java")
    scanner_tests = pt.walk(root_test, "ESTest.java")
    print "classes size ={}".format(len(scanner_class))
    print "tests size ={}".format(len(scanner_tests))
    # convert the full path to package format
    scanner_class_pak = [pt.path_to_package('org',x,-6) for x in scanner_class ]
    scanner_tests_pak = [pt.path_to_package('org',y,-12) for y in scanner_tests ]
    d = dict_diff(list_one=scanner_class_pak,list_two=scanner_tests_pak,path_root_test=root_test)
    look_at_test(scanner_java,scanner_tests,d)
    dff =  make_df(d,log,name)
    return d

def dict_diff(list_one,list_two,path_root_test):
    '''see the different between two list with class as package'''

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
    return d



def make_df(d,log,name):
    data_df = []
    for vali in d.values():
        data_df.append(vali)
    df = pd.DataFrame(data_df)
    df.to_csv("{}{}.csv".format(log,name))
    print "Done !"
    return  df

def system_call(command):
    p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    return p.stdout.read()

def get_LOC(p):
    c_command = "/home/ise/.cargo/bin/loc {}".format(str(p))
    string_out = system_call(c_command)
    res = str(string_out).split()
    return res[13],res[10]



def look_at_test(classes,tests,d):
    '''some info'''
    for entry in d.keys():
        d[entry]['loc_TEST']=0
        d[entry]['loc_class'] = 0
    for item in classes:
        ky = pt.path_to_package('org',item,-5)
        if str(ky).__contains__('package-info'):
            continue
        loc_class= get_LOC(p=item)
        if ky in d:
            d[ky]['loc_class'] = int(loc_class[0])
        else :
            print ("the .java in not in the dict .class --> {}".format(ky))
            continue
    for cut in tests:
        ky = pt.path_to_package('org',cut,-12)

        loc_class= get_LOC(p=cut)
        if ky in d:
            d[ky]['loc_TEST'] = int(loc_class[0])


        else :
            print ("the .java in not in the dict .class --> {}".format(ky))
            continue


def func_start(main_root):
    scan_obj = pt.walk(main_root,"t=",False,0)
    for x in scan_obj:
        print x
        time_budget_analysis(x)

def time_budget_analysis(path_root):
    list_d = []
    res_scanner = pt.walk(path_root, "commons-math3-3.5-src", False)
    p_path = path_root
    if p_path[-1] != '/':
        p_path= p_path+'/'
    if os.path.isdir("{}stat/".format(p_path)) is False :
        os.system("mkdir {}".format(p_path+"stat/"))
    log_path = "{}stat/".format(p_path)
    for i_path in res_scanner:
        name_i = get_name_path(i_path,-2)
        javas_path="{}/src/main/java/org/".format(i_path)
        classes_path = "{}/target/classes/org/".format(i_path)
        tests_path = "{}/src/test/java/org/".format(i_path)
        df_i = missing_class_gen(root_class=classes_path, root_test=tests_path, java_src=javas_path,log=log_path,name=name_i)
        list_d.append(df_i)
    merge_df(list_d,log_path)




def merge_df(list_d,log_path_dir):
    size = len(list_d)
    d_big ={}
    for dico in list_d:
        for ky in dico.keys():
            if ky in d_big:
                #print "d_big[ky]:: ",d_big[ky]
                #print "dico[ky]:: ",dico[ky]
                d_big[ky]['arr'] = str(d_big[ky]['arr']) + "," + str(dico[ky]['loc_TEST'])
                if dico[ky]['loc_TEST'] == 12:
                    d_big[ky]['empty_test'] += 1
                if dico[ky]['loc_TEST'] == 0:
                    d_big[ky]['no_test'] += 1
                for filed_i in dico[ky]:
                    if filed_i == 'class':
                        continue
                    d_big[ky][filed_i]+=dico[ky][filed_i]
            else:
                d_big[ky] = {'empty_test':0,'no_test':0,'arr':""}
                d_big[ky]['arr'] =  str(dico[ky]['loc_TEST'])
                if dico[ky]['loc_TEST'] == 12:
                    d_big[ky]['empty_test'] += 1
                if dico[ky]['loc_TEST'] == 0:
                    d_big[ky]['no_test'] += 1
                for filed_i in dico[ky]:
                    d_big[ky][filed_i]=dico[ky][filed_i]

    for entry in d_big.keys():
        arr_str = d_big[entry]['arr']
        arr_str = str(arr_str).split(',')
        arr=[]
        for x in arr_str:
            arr.append(int(x))
        d_big[entry]['var'] = np.var(arr)
        d_big[entry]['mean'] = np.mean(arr)
    df = pd.DataFrame(d_big.values())
    df.to_csv("{}FinStat_Size_{}_.csv".format(log_path_dir,size))
    return d_big





def get_name_path(v_path,index):
    arr = str(v_path).split('/')
    return arr[index]


if __name__ == "__main__":
    func_start('/home/ise/eran/exp_little/')


