

import glob, os ,sys ,re
import time

class Tree(object):
    def __init__(self):
        self.descendants=None
        self.data=None
        self.str =''
        self.prefix=''


def get_son(node):
    acc=[]
    acc.append([node.prefix,node.data])
    for pac in node.descendants:
        acc+=get_son(node.descendants[pac])
    return acc


def get_class_tree(root,package_class):
    arr_package_class = str(package_class).split('.')
    cur =root
    package = arr_package_class[:-1]
    class_name = arr_package_class[-1]
    for item in package:
        cur = cur.descendants[item]
    all_son_class = get_son(cur)
    return all_son_class

def walking(root, rec="", file_t=True, lv=-1, full=True):
    size = 0
    ctr = 0
    class_list = []
    if lv == -1:
        lv = float('inf')
    for path, subdirs, files in os.walk(root):
        if lv < ctr:
            break
        ctr += 1
        if file_t:
            for name in files:
                tmp = re.compile(rec).search(name)
                if tmp == None:
                    continue
                size += 1
                if full:
                    class_list.append(os.path.join(path, name))
                else:
                    class_list.append(str(name))
        else:
            for name in subdirs:
                tmp = re.compile(rec).search(name)
                if tmp == None:
                    continue
                size += 1
                if full:
                    class_list.append(os.path.join(path, name))
                else:
                    class_list.append(str(name))
    return class_list

def path_to_package(path,begin):
    path1 = path[:-5]
    res =''
    split_me = path1.split('/')
    gen = [i for i, x in enumerate(split_me) if x == begin]
    if len(gen) > 0 :
        strat = gen[0]
        for i in range(strat,len(split_me)):
            res=res + '.'+split_me[i]
    return  res[1:]

def path_to_package_v2(first,path,cut):
    arr=[]
    dim=0
    while(path.find(first,dim) != -1):
        arr.append(path.find(first,dim))
        dim = path.find(first,dim) + len(first)
    if len(arr) != 1 :
        raise Exception('confilcet in path to package :' ,path, "with the key:",first  )
    packa = path[arr[0]:]
    packa =str(packa).replace("/",'.')
    return  packa[:cut]

def walk(root) :
    size=0
    class_list = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            #print os.path.join(path, name)
            if ( name.__contains__("scaffolding") or name.__contains__("$") ) is False:
                    size+=1
                    class_list.append([str(path),str(name)])
    #print "size=",size
    return class_list

def equal_strings(s1,s2):
    acc_s1 =''
    acc_s2 = ''
    for w in s1 :
        if w == '.' :
            break
        else:
            acc_s1=acc_s1+w
    for w in s2 :
        if w == '.' :
            break
        else:
            acc_s2=acc_s2+w
    if(acc_s1>acc_s2) :
        if(acc_s1.__contains__(acc_s2+'_')):
            return True
    else :
        if(acc_s2.__contains__(acc_s1+'_')):
            return True

    return False
#Fraction_ESTest_scaffolding

def mod_test(root):
    size=0
    class_list = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            if name.__contains__("ES") is True:
                if name.__contains__("scaffolding") is False :
                    size+=1
                    class_list.append(os.path.join(path, name))
    for path_i in class_list:
        with open(path_i, 'r') as myfile:
            data = myfile.read().replace('separateClassLoader = true', 'separateClassLoader = false')
        text_file = open(path_i, "w")
        text_file.write(data)
        text_file.close()

def make_package(list_item):
    dict={}
    for item_i in list_item:
        item = path_to_package(item_i[0]+'/'+item_i[1],'org')
        item_arr = str(item).split('.')
        package_it = ""
        for str_i in item_arr[:-1]:
            package_it=package_it+"."+str_i
        package_it=package_it[1:]
        if package_it in dict:
            val_tmp = dict[package_it]
            #val_tmp.append(item)
            val_tmp[item[:-7]] = item
            dict[package_it] = val_tmp
        else :
            d ={}
            d[item[:-7]]=item
            dict[package_it] = d
    return dict

def path_to_package_v11(first,path):
    arr=[]
    dim=0
    while(path.find(first,dim) != -1):
        arr.append(path.find(first,dim))
        dim = path.find(first,dim) + len(first)
    if len(arr) != 1 :
        raise Exception('confilcet in path to package :' ,path, "with the key:",first  )
    packa = path[arr[0]:]
    packa =str(packa).replace("/",'.')
    return  packa[:-5]

def pair_test_class11(list_tests,list_class):
    dict = {}
    for node_test in list_tests :
        for node_class in list_class:
            str_class = str(node_class[0]+'/'+node_class[1])
            str_class = str_class.split('/org/')[1][:-5]
            str_test = str(node_test[0]+'/'+node_test[1])
            str_test = str_test.split('/org/')[1][:-12]
            if str_class == str_test :
                dict[path_to_package(str(node_class[0])+'/'+str(node_class[1]),'org')] = [str(node_class[0])+'/'+str(node_class[1]),str(node_test[0])+'/'+str(node_test[1]) ]
                break

    return dict

def pair_test_class_v1(list_tests,list_classes):
    dict_res={}
    for node_class in list_classes:
        if str(node_class[1]).__contains__('.class') is False:
           # print node_class[1]
            continue
        str_class = str(node_class[0] + '/' + node_class[1])
        str_class = str_class.split('/org/')[1][:-6]
        prefix_package = path_to_package_v2('org',str(node_class[0])+'/'+str(node_class[1]),-6)
        if prefix_package in dict_res :
            raise Exception("[Error] there is two classes with the same name (prefix package) --> {}".format(prefix_package))
        else:
            dict_res[prefix_package]=[str(node_class[0])+'/'+str(node_class[1]),"None"]
    for node_test in list_tests:
        if str(node_test[1]).__contains__('.class') is False:
            #print node_test[1]
            continue
        str_test = str(node_test[0] + '/' + node_test[1])
        str_test = str_test.split('/org/')[1][:-12]
        prefix_package = path_to_package_v2('org',str(node_test[0])+'/'+str(node_test[1]),-13)
        if prefix_package in dict_res :
            dict_res[prefix_package][1] = str(node_test[0])+'/'+str(node_test[1])
        else:
            raise Exception("[Error] there is no matching .class for the test --> {}".format(prefix_package))
    return dict_res


def tree_build(dico):
    root = Tree()
    root.descendants={}
    root.str='root'
    recursive_package_mode(dico,root)
    return root

def recursive_package_mode(dico,root_node):
    d= make_package_dict(dico)
    #root = root_node
    size = len(d.keys())
    ctr=0

    for key in d:
        package_prefix = ''
        cur_node = root_node
        splited_key = str(key).split('.')
        for pac in splited_key:
            package_prefix = package_prefix+str(pac)+'.'
            if pac in cur_node.descendants:
                cur_node=cur_node.descendants[pac]
                continue
            else:
                tree_obj = Tree()
                tree_obj.descendants = {}
                tree_obj.str=str(pac)
                tree_obj.prefix=package_prefix[:-1]
                cur_node.descendants[pac] = tree_obj
                cur_node=cur_node.descendants[pac]
        cur_node.data=d[key]

def make_package_dict(dico):
    package_dict=dict()
    for key,vale in dico.iteritems():
        str_key_arr = str(key).split('.')
        class_name = str(str_key_arr[-1])
        if len(str_key_arr[:-1])>1:
            package_name = '.'.join(str_key_arr[:-1])
        else :
            package_name = str((str_key_arr[:-1]))
        if package_name  in package_dict:
            package_dict[package_name][class_name]=dico[key]
        else:
            package_dict[package_name] = {class_name:dico[key]}
    return package_dict






def make_pom_package(dico):
    target_str_data = "<targetClasses>"+'\n'
    test_str_data = "<targetTests>"+'\n'
    p_s = "<param>"
    p_e = "</param>"
    for key, value in dico.iteritems():
        pac_class = key
        pac_test =  value
        target_str_data = target_str_data + p_s + pac_class + p_e + '\n'
        test_str_data = test_str_data + p_s + pac_test + p_e + '\n'
    target_str_data+='</targetClasses> '
    test_str_data+='</targetTests> '
    return target_str_data,test_str_data


def make_pom_data(dico):
    target_str_data = "<targetClasses>"+'\n'
    test_str_data = "<targetTests>"+'\n'
    p_s = "<param>"
    p_e = "</param>"
    for key, value in dico.iteritems():
        pac_class = path_to_package(value[0],'org')
        pac_test =  path_to_package(value[1],'org')
        target_str_data = target_str_data + p_s + pac_class + p_e + '\n'
        test_str_data = test_str_data + p_s + pac_test + p_e + '\n'
    target_str_data+='</targetClasses> '
    test_str_data+='</targetTests> '
    return target_str_data,test_str_data

def modf_pom(path,tag_c,tag_t):
    with open(path, 'r') as myfile:
        data = myfile.read()
        data = re.sub('\n','<nlt>',data)
        data = re.sub('<targetClasses>(.*?)</targetClasses>',tag_c,data)  #TODO:in  "all-mode"  this line in comment
        data = re.sub('<targetTests>(.*?)</targetTests>',tag_t,data)
        data = re.sub('<nlt>', '\n', data)
    text_file = open(path, "w")
    text_file.write(data)
    text_file.close()

def modf_only_one(dico):
    target_str_data = "<targetClasses>"+'\n'
    test_str_data = "<targetTests>"+'\n'
    for key, value in dico.iteritems():
        pac_test =  path_to_package(value[1],'org')
        test_str_data = test_str_data  + pac_test  + '\n'
    target_str_data+='</targetClasses> '
    test_str_data+='</targetTests> '
    return target_str_data,test_str_data


def get_java_and_test(dico):
    javas=[]
    tests=[]
    package = []
    for key in dico:
        package.append(key)
        javas.append(dico[key][0])
        tests.append(dico[key][1])
    return javas,tests,package

def transform_data(list_son):
    d={}
    print 'size=',len(list_son)
    for item in list_son:
        #print item
        #print '-'*30
        prefix = item[0]
        dic = item[1]
        if dic is None:
            continue
        for key  in dic :
            d[prefix+'.'+key]=prefix+'.'+key+'_ESTest'
    return d

def fixer_class(pom_path,class_path,test_path):
    print "fix..."


def isPrefix(prefix,str_package):
    bol = str(str_package).startswith(prefix)
    return bol

def log_dir(path):
    bol = os.path.isdir(path)
    if bol is False:
        os.system("mkdir {}".format(path))


def fix_class_not_generate(path_dir,dico):
    print "len before:{}".format(len(dico))
    list_log = walk(path_dir)
    d={}
    for log in list_log:
        ky = log[1][:-4]
        if ky in dico:
            del dico[ky]
    print "len after:{}".format(len(dico))
    return dico


def rec_package_test(pom_path,class_path,test_path,arg=None,arg_2=None):
    proj_path = pom_path[:-8]
    proj_path_log = proj_path+"/target/log_pit"
    log_dir(proj_path_log)
    list_calss=walk(class_path)
    list_test = walk(test_path)
    if len(list_test) == 0:
        print "no tests founds"
        exit(0)
    print 'class=',len(list_calss)
    print 'test=',len(list_test)
    #dico = pair_test_class11(list_test,list_calss)
    dico = pair_test_class_v1(list_test, list_calss)
    r = tree_build(dico)
    ########################################################## fix_class_not_generate(proj_path_log,dico)
    rev = False #reverse var that indict that the each test is analysis on a package of classes
    if arg is not None:
        str_arg = str(arg).replace(' ','')
        if str_arg=='rev':
            rev=True
    if arg_2 is not None:
        str_arg = str(arg_2).replace(' ','')
        if str_arg=='rev':
            rev=True
    ctr = len(dico)
    for key,value in dico.iteritems():
        print "class left: ",ctr
        ctr-=1
        if arg_2 is None:
            if arg is not None and rev is False:
                if isPrefix(arg,key) is False:
                    continue
        else:
            if arg is not None:
                if isPrefix(arg, key) is False:
                    continue
        dico_son_val= get_class_tree(r, key)
        value_target = transform_data(dico_son_val)
        tag_key, tag_val = make_pom_package({key:str(key)+'_ESTest'})
        tag_c, tag_t = make_pom_package(value_target)

        if rev:
            print "--rev--"
            modf_pom(pom_path, tag_c, tag_val)
        else:
            modf_pom(pom_path, tag_key, tag_t)

        command_v1 = " mvn org.pitest:pitest-maven:mutationCoverage >> target/log_pit/{0}.txt 2>&1 ".format(key)
        #command =" mvn org.pitest:pitest-maven:mutationCoverage "
        os.system(command_v1)
        proj_path1 = os.getcwd()
        arr= walking(proj_path1+'/target/pit-reports/','2',False,0)
        d_dis=''
        if len(arr) > 0:
            if len(arr) > 1:
                d_dis =get_min_dir(arr)
            else:
                d_dis=arr[0]
            str2 = 'mv '+d_dis+" "+proj_path1+"/target/pit-reports/"+key
            os.system(str2)

def get_min_dir(list_dirs):
    min='9'*15
    min_path=None
    for x in list_dirs:
        arr_i = str(x).split('/')
        num_str = arr_i[-1]
        if min > num_str:
            min=num_str
            min_path=x
    if min_path is None:
        raise Exception("[Error] more than one dir but the path is None --> {}".format(list_dirs))
    return min_path

def package_test(pom_path,class_path,test_path):
    list_calss=walk(class_path)
    list_test = walk(test_path)
    if len(list_test) == 0:
        print "no tests founds"
        exit(0)
    print 'class=',len(list_calss)
    print 'test=',len(list_test)
    dico = pair_test_class11(list_test,list_calss)
    print 'dico=',len(dico)
    package_d = make_package(list_test)
    print 'package: ',len(package_d)
    for key,value in package_d.iteritems():
        tag_c,tag_t = make_pom_package(value)
        modf_pom(pom_path,tag_c,tag_t)
        command =" mvn org.pitest:pitest-maven:mutationCoverage"
        os.system(command)
        proj_path1 = os.getcwd()
        arr= walking(proj_path1+'/target/pit-reports/','2',False,0)
        if len(arr) >0:
            str2 = 'mv '+arr[0]+" "+proj_path1+"/target/pit-reports/"+key
            os.system(str2)


def pit_test(pom_path,class_path,test_path):
    list_calss=walk(class_path)
    list_test = walk(test_path)
    print 'class=',len(list_calss)
    print 'test=',len(list_test)
    dico = pair_test_class11(list_test,list_calss)
    print 'dico=',len(dico)
    tag_c,tag_t = make_pom_data(dico)
    modf_pom(pom_path,tag_c,tag_t)
    command =" mvn org.pitest:pitest-maven:mutationCoverage"
    os.system(command)

def main_one_by_one(pom_path,class_path,test_path):
    list_calss=walk(class_path)
    list_test = walk(test_path)
    dico = pair_test_class11(list_test,list_calss)
    for key,val in dico.iteritems():
        tag_c, tag_t=make_pom_data({key:val})
        modf_pom(pom_path, tag_c, tag_t)
        c_command = "mvn org.pitest:pitest-maven:mutationCoverage"
        os.system(c_command)
        proj_path1 = os.getcwd()
        arr= walking(proj_path1+'/target/pit-reports/','2',False,0)
        if len(arr) >0:
            str2 = 'mv '+arr[0]+" "+proj_path1+"/target/pit-reports/"+key
            os.system(str2)
    print('done !')


def main_one_vs_all(pom_path,class_path,test_path):
    list_calss=walk(class_path)
    list_test = walk(test_path)
    dico_done = get_class_done(pom_path[:-7]+'target/pit-reports/')
    dico = pair_test_class11(list_test,list_calss)
    print 'size=', len(dico.keys()) - len(dico_done.keys())
    for key,val in dico.iteritems():
        if key in dico_done:
            continue
        tag_c, tag_t=modf_only_one({key:val})
        modf_pom(pom_path, tag_c, tag_t)
        c_command = "mvn org.pitest:pitest-maven:mutationCoverage"
        os.system(c_command)
        proj_path1 = os.getcwd()
        arr= walking(proj_path1+'/target/pit-reports/','2',False,0)
        if len(arr) >0:
            str2 = 'mv '+arr[0]+" "+proj_path1+"/target/pit-reports/"+key
            os.system(str2)
    print('done !')

def get_class_done(root_path):
    ctr = 0
    done_dict={}
    if os.path.isdir(root_path):
        results=walking(root_path,"org",False,0,False)
        for test in results:
            ctr+=1
            done_dict[test]=True
    print ctr
    return done_dict

def main_all():
    proj_path= os.getcwd()+'/'
    print 'path: ',proj_path
    pom_path = proj_path + 'pom.xml'
    classes_pth = proj_path + 'src/main/java/org/'
    tests_path = proj_path + 'src/test/java/org/'
    main_one_vs_all(pom_path,classes_pth,tests_path)

def main_in():
    proj_path= os.getcwd()+'/'
    print 'path: ',proj_path
    pom_path = proj_path + 'pom.xml'
    classes_pth = proj_path + 'src/main/java/org/'
    tests_path = proj_path + 'src/test/java/org/'
    main_one_by_one(pom_path,classes_pth,tests_path)

def main_func(arg=None,arg_2=None):
    #os.chdir('/home/ise/eran/exp_all/12_14_03_29_42_t=45_/pit_test/ALL_U__t=45_it=0/commons-math3-3.5-src')
    proj_path= os.getcwd()+'/'
   ### proj_path = '/home/ise/eran/flaky/commons-math3-3.5-src/'
    print proj_path
   # proj_path = '/home/eran/thesis/test_gen/experiment/commons-math3-3.5-src/'
    pom_path = proj_path+'pom.xml'
    classes_pth=proj_path+'src/main/java/org/'
    tests_path=proj_path+'src/test/java/org/'
    compile_path=proj_path+'target/classes/org'
    compile_test_path = proj_path+'target/test-classes/org'
    rec_package_test(pom_path,compile_path,compile_test_path,arg,arg_2)
    #package_test(pom_path,classes_pth,tests_path)

def fixer():
    proj_path= os.getcwd()+'/'
    path_result = walking(proj_path,"ALL",False,2)
    print "path_result=",path_result
    for p_r in path_result:
        relative_path = p_r+"/commons-math3-3.5-src/"
        pom_path = relative_path + 'pom.xml'
        classes_pth = relative_path + 'src/main/java/org/'
        tests_path = relative_path + 'src/test/java/org/'
        if os.path.isdir(p_r+"/commons-math3-3.5-src/"):
            empty, full=clean_empty_dir(p_r+"/commons-math3-3.5-src/")
            print "empty="
            print empty
            print "full:"
            print full
            #rec_package_test(pom_path, classes_pth, tests_path,full)
        else:
            print "no path:: ",p_r,"commons-math3-3.5-src/"


def clean_empty_dir(path):
    empty=[]
    full=[]
    path_p = path+"target/pit-reports/"
    res_walking = walking(path_p,"org",False,-1,False)
    if len(res_walking) == 0:
        print "Path = {0} has no mutation dir".format(path_p)
        return None,None
    for dir in res_walking:
        if not os.listdir(path_p+dir):
            empty.append(dir)
            print "XXX->>> ",path_p+dir
            os.system("rm -r "+path_p+dir)
        else:
            full.append(dir)
    return empty,full



    #proj_path = '/home/eran/thesis/common_math/commons-math3-3.5-src'
if __name__ == "__main__":
    os.chdir("/home/ise/eran/rev/02_26_13_27_45_t=30_/pit_test/ALL_U_t=30_it=0_/commons-math3-3.5-src")
    args = sys.argv
    args =['py','rev']
    print args
    if len(args)==1:
        main_func()
    elif len(args)==2:
        if len(args[1])>2:
            main_func(args[1])
        else:
            main_func()
    elif len(args)==3:
        main_func(args[1],args[2])
    else:
        print "fixer"
        fixer()

