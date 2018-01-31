from pit_render_test import walker
import os,csv
import shutil
import pickle
import sys


def get_all_bugs_dir(pit_dir_path):
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
    fix_error_list(bugs_dir,script_py,'bug_dir')
    fix_error_list(empty_csv, script_py,'empty_csv')
    fix_error_list(empty_dir, script_py,'empty_dir')

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

def fix_error_list(list_err_dir,root_dir,name_file):
    log_to_dir(root_dir,list_err_dir,name_file)
    for item in list_err_dir: #pti_init.py
        del_dir(item[0])
        print "class: ",item[1]
        os.chdir(root_dir)
        py_script =root_dir+'/pti_init.py'
        os.system("python {} {}".format(py_script,item[1]))


def log_to_dir(root_path,li,name_file):
    if os.path.isdir(root_path+'/logs') is False:
        os.mkdir(root_path+'/logs')
    with open(root_path+"/logs/{}.txt".format(name_file), "w") as output:
        output.write(str(li))
    with open(root_path+"/logs/{}_object.txt".format(name_file), 'wb') as fp:
        pickle.dump(li, fp)



def del_dir(path):
    shutil.rmtree(path)
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



def get_all_pit_dir_exp(root_exp):
    obj = walker(root=root_exp)
    all_pp = obj.walk('pit-reports',False)
    for p in all_pp:
        get_all_bugs_dir(p)


if __name__ == "__main__":
    #pp_path = '/home/ise/Desktop/test_50/pit_test/ALL_FP__t=50_it=1/commons-math3-3.5-src/target/pit-reports/'
    #get_all_bugs_dir(pp_path)
    args = sys.argv
  #  args = ["","/home/ise/Desktop/new_exp"]
    get_all_pit_dir_exp(args[1])