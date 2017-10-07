

import glob, os ,sys ,re
import time


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


def walk(root) :
    size=0
    class_list = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            #print os.path.join(path, name)
            if name.__contains__("scaffolding") is False:
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
        #data = re.sub('<targetClasses>(.*?)</targetClasses>',tag_c,data)
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

def main_func():
    proj_path= os.getcwd()+'/'
    pom_path = proj_path+'pom.xml'
    classes_pth=proj_path+'src/main/java/org/'
    tests_path=proj_path+'src/test/java/org/'
    package_test(pom_path,classes_pth,tests_path)



def fixer(path_p):


#proj_path = '/home/eran/thesis/common_math/commons-math3-3.5-src'

main_func()
#main_all()

