

import glob, os ,sys ,re
import time


def path_to_package(path,begin):
    path1 = path[:-6]
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


def pair_test_class(list_tests,list_class):
    dict = {}
    for node_class in list_class :
        for node_test in list_tests:
            if (equal_strings(node_class[1],node_test[1])) is True :
                dict[node_class[1][:-6]] = [str(node_class[0])+'/'+str(node_class[1]),str(node_test[0])+'/'+str(node_test[1]) ]
    return dict

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
        data = re.sub('<targetClasses>(.*?)</targetClasses>',tag_c,data)
        data = re.sub('<targetTests>(.*?)</targetTests>',tag_t,data)
        data = re.sub('<nlt>', '\n', data)
    text_file = open(path, "w")
    text_file.write(data)
    text_file.close()



def pit_test(pom_path,class_path,test_path):
    list_calss=walk(class_path)
    list_test = walk(test_path)
    dico = pair_test_class(list_test,list_calss)
    tag_c,tag_t = make_pom_data(dico)
    modf_pom(pom_path,tag_c,tag_t)
    os.chdir(pom_path[:-7])
    command =" mvn org.pitest:pitest-maven:mutationCoverage"
    #os.system(command)



def main_func(args):
    # ( path-pom  , path-class , path test )
    if len(args) == 5 :
        pom_path = args[1]
        classes_pth = args[2]
        tests_path = args[3]
        test_java = args[4]
        #mod_test(test_java)
        pit_test(pom_path,classes_pth,tests_path)
    else:
        print "miss argv (path-pom  , path-classes , path tests)"

relativ = sys.args[1]

class_p = '/target/classes/org/apache/commons/math3/fraction'
test_p = '/target/test-classes/org/apache/commons/math3/fraction'
pom_p = '/pom.xml'
test_java = '/src/test/java/org/apache/commons/math3'

ppp = '/home/eran/thesis/test_gen/poc/'

args = ["",relativ+pom_p,relativ+class_p,relativ+test_p,relativ+ppp]
main_func(args)


