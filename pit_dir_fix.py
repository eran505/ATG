from pit_render_test import walker
import os,csv
import shutil
import pickle
import sys
from time import gmtime, strftime


def get_all_bugs_dir(pit_dir_path,arg):
    script_py = extract_script(pit_dir_path)
    print script_py
    obj_walk = walker(pit_dir_path)
    all_dir = obj_walk.walk('org',False)
    bugs_dir=[]
    empty_dir=[]
    empty_csv = []
    for dir in all_dir:
        name_class_dir = str(dir).split('/')[-1]
        if is_empty_dir(str(dir)) is False:
            path_to_csv =  dir+'/mutations.csv'
            print path_to_csv
            name_class = get_class_name_csv(path_to_csv)
            if name_class is None:
                empty_csv.append([dir,name_class_dir])
                continue
            if name_class != name_class_dir:
                bugs_dir.append([dir,name_class_dir])
        else:
            empty_dir.append([dir,name_class_dir])
    fix_error_list(bugs_dir,script_py,'bug_dir',arg)
    fix_error_list(empty_csv, script_py,'empty_csv',arg)
    fix_error_list(empty_dir, script_py,'empty_dir',arg)

def extract_script(p):
    arr = str(p).split('/')
    res=[]
    for string in arr:
        if string == 'commons-math3-3.5-src':
            res.append(string)
            #res.append('pti_init.py')
            break
        res.append(string)
    return '/'.join(res)

def fix_error_list(list_err_dir,root_dir,name_file,arg):
    log_to_dir(root_dir,list_err_dir,name_file)
    for item in list_err_dir: #pti_init.py
        del_dir(item[0],item[1],root_dir+"/target/log_pit/")
        print "class: ",item[1]
        os.chdir(root_dir)
        py_script =root_dir+'/pti_init.py'
        if arg is None:
            os.system("python {} {}".format(py_script,item[1]))
        else:
            os.system("python {} {} {}".format(py_script, item[1],arg))

def log_to_dir(root_path,li,name_file):
    if os.path.isdir(root_path+'/logs') is False:
        os.mkdir(root_path+'/logs')
    with open(root_path+"/logs/{}_{}.txt".format(name_file,get_date()), "w") as output:
        output.write(str(li))
    with open(root_path+"/logs/{}_object_{}.txt".format(name_file,get_date()), 'wb') as fp:
        pickle.dump(li, fp)


def get_date():
    d_date = strftime("%m_%d_%H_%M", gmtime())  ##"%Y-%m-%d %H:%M:%S"
    return str(d_date)

def del_dir(dir_path,class_name,log_dir):
    shutil.rmtree(dir_path)
    log_file = log_dir+class_name+".txt"
    bol = os.path.isfile(log_file)
    if bol:
        os.system("rm {}".format(log_file))
    return True



def get_class_name_csv(csv_p):
    with open(csv_p,'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            print(row)
            if row[0] in (None, ""):
                return None
            else :
                return row[1]


def is_empty_dir(path):
    dir_contents = os.listdir(path)
    print dir_contents
    if dir_contents:
        return False
    else:
        return True



def get_all_pit_dir_exp(root_exp,arg=None):
    obj = walker(root=root_exp)
    all_pp = obj.walk('pit-reports',False)
    if len(all_pp)==0:
        print "No dir pit-report dir in the following path : {}".format(root_exp)
    for p in all_pp:
        get_all_bugs_dir(p,arg)



import pandas as pd
def tmper():
    p = '/home/ise/eran/exp_little/fin_out/big.csv'
    df = pd.read_csv(p)
    x = list(df)
    x = x [1:-1]
    for col in x:
        size = float(len(df[col]))
        is_empty = float(df[col].isnull().sum())
        precentage = is_empty/size
        full = float(df[col].count())
        p_full = (full/size)*100
        precentage_empty= precentage*100
        print "name: {}".format(col)
        print "empty: ", precentage_empty
        print "full: ",p_full
        b = p_full+precentage_empty
        print "both",b
        print "-"*27
    exit()

if __name__ == "__main__":
    #tmper()
    #pp_path = '/home/ise/Desktop/test_50/pit_test/ALL_FP__t=50_it=1/commons-math3-3.5-src/target/pit-reports/'
    #get_all_bugs_dir(pp_path)
    args = sys.argv
    if len(args)==2:
        get_all_pit_dir_exp(args[1])
    elif len(args)==3:
        get_all_pit_dir_exp(args[1],args[2])
    else:
        print "exit ---> no args !!!"