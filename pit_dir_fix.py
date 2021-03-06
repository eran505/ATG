from pit_render_test import walker
import pit_render_test
import os,csv
import shutil,pickle
import sys
from time import gmtime, strftime
import pandas as pd
import xml.etree.ElementTree

def is_empty_file(path_f):
    '''
    Check whether a file is empty or not
    :param path_f: path to file
    :return: T / F
    '''
    if os.stat(path_f).st_size == 0:
        return True
    return False

def get_all_bugs_dir(pit_dir_path,arg):
    d={}
    script_py = extract_script(pit_dir_path)
    print script_py
    obj_walk = walker(pit_dir_path)
    all_dir = obj_walk.walk('org',False)
    empty_dir=[]
    diff_names_dir = []
    empty_xml = []
    for dir in all_dir:
        name_class_dir = str(dir).split('/')[-1]
        if is_empty_dir(str(dir)) is False:
            xml_file_path =  dir+'/mutations.xml'
            if is_empty_file(xml_file_path):
                d[name_class_dir]={'class':name_class_dir,'path':xml_file_path,'empty_file':1}
                empty_xml.append(xml_file_path)
                continue
            test_name = pars_xml_name(xml_file_path,arg)
            if test_name is not None:
                if test_name != name_class_dir:
                    d[name_class_dir] = {'class': name_class_dir, 'path': xml_file_path, 'diff': 1}
                    diff_names_dir.append([dir,name_class_dir])

        else:
            d[name_class_dir] = {'class': name_class_dir, 'path': dir, 'empty_dir': 1}
            empty_dir.append([dir,name_class_dir])
    print ""
    p_log = '{}/logS'.format(script_py)
    log_to_dir_pit(d,p_log)
    #fix_error_list(bugs_dir,script_py,'bug_dir',arg)
    #fix_error_list(empty_csv, script_py,'empty_csv',arg)
    fix_error_list(empty_dir, script_py,'empty_dir',arg)
    #fix_error_list(test_dir, script_py, 'test_csv', 'rev')


def log_to_dir_pit(d,p_log):
    list_log=[]
    for ky_class in d.keys():
        list_log.append(d[ky_class])
    df = pd.DataFrame(list_log)
    flush_csv(p_log,df,'log_pit_dir')

def flush_csv(out_path_dir, xml_df, name_file):
    if xml_df is None:
        return
    if out_path_dir[-1]=='/':
        xml_df.to_csv("{}{}.csv".format(out_path_dir, name_file))
    else:
        xml_df.to_csv("{}/{}.csv".format(out_path_dir,name_file))

def extract_script(p):
    arr = str(p).split('/')
    res=[]
    for string in arr:
        if string.startswith('commons-'):
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
    else:
        raise Exception("[Error] cant find the PIT log of class {} ".format(class_name))
    return True

def fix_by_stat(root_dir,arg=None): ##item ['dir_path','name_class']
    if os.path.isdir(root_dir) is False:
        print "the root dir is invalid :{}".format(root_dir)
        return


def get_class_name_csv(csv_p):
    with open(csv_p,'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if row[0] in (None, ""):
                return None
            else :
                return row[1]

def get_test_name_csv(csv_p):
    res = None
    with open(csv_p,'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if row[-1] in (None, "",'none'):
                continue
            else :
                tmp = row[-1]
                tmp= str(tmp).split('_ESTest')
                res = tmp[0]
                break
    return res


def pars_xml_name(path_xml,mod):
    test_name =None
    list_xml=[] #the dict that will become to DataFrame
    if os.path.isfile(path_xml) is False:
        raise "[Error] no file in the path --> {}".format(path_xml)
    try:
        root_node = xml.etree.ElementTree.parse(path_xml).getroot()
    except (Exception, ArithmeticError) as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print (message)
        os.system('rm {}'.format(path_xml))
        return None,None
    for item in root_node._children:
        for  x in item._children:
            if x.tag == 'mutatedClass':
                mutated_class_name =  x.text
                return mutated_class_name
    return None


def is_empty_dir(path):
    dir_contents = os.listdir(path)
    print dir_contents
    if len(dir_contents)>0:
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


def xml_replace(project_path='/home/ise/eran/xml/02_26_13_27_45_t=30_/pit_test/ALL_U_t=30_it=0_/commons-math3-3.5-src'):
    '''
    if PIT output is xml, working on the csvs dir
    '''
    class_csv = '{}/csvs/class'.format(project_path)
    list_csvs = pit_render_test.walk(class_csv,'.csv')
    err={}
    for item in list_csvs:
        name = str(item).split('/')[-1][:-4]
        df = pd.read_csv(item)
        print list(df)
        exit()

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
    args = ['','/home/ise/eran/test_replic']
    if len(args)==2:
        get_all_pit_dir_exp(args[1])
    elif len(args)==3:
        get_all_pit_dir_exp(args[1],args[2])
    else:
        print "exit ---> no args !!!"