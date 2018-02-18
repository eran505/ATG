import sys, os ,time,csv

from copy import deepcopy

import pit_render_test


def csv_to_dict(path,key_name,val_name ):
    dico = {}
    with open(path) as csvfile:
        reader1 = csv.DictReader(csvfile)
        for row in reader1:
            val_i = row[val_name]
            key_i = row[key_name]
            dico[key_i] = val_i
    return dico

def clean_dict(dic,prefix,start,end):
    dico_result={}
    for key in dic.keys():
        if str(key).__contains__(prefix) is False:
            del dic[key]
        else:
            org_key = key
            val = float(dic[org_key])
            key = key[start:-end]
            key = key.replace('\\','.')
            dico_result[key]=val
    return dico_result

def match_dic(class_list,dico):
    list_key = dico.keys()
    for k in list_key:
        if k in class_list:
            continue
        else:
            del dico[k]
    return dico

# TODO: old version delete it after checking the new version is working
'''''
def time_pred(time_per_class,dico,prefix):
    for k in dico.keys():
        if str(k).__contains__(prefix):
            del dico[k]
    total_sum_predection= sum(dico.values())
    for k in dico.keys() :
        dico[k]=dico[k]/total_sum_predection
    size = len(dico.keys())
    fac = size*time_per_class
    d= dico.copy()
    for k in dico.keys():
        dico[k]=dico[k]*fac
        d[k]=[d[k],d[k]*fac]
    return dico,d
'''''

def get_time_fault_prediction(path,key,value,root,upper_b,lower_b,per_class_b):
    dico= csv_to_dict(path,key,value)
    dico = clean_dict(dico,'src\main',14,5)
    class_list = get_all_class(root,6)
    dico = match_dic(class_list,dico)
    dico,d=allocate_time_FP(dico,per_class_b,upper_b,lower_b,'age-in')  #######
    return dico,d


def boundary_budget_allocation(dico,time_per_k,upper,lower,filtering):
    for k in dico.keys():
        if str(k).__contains__(filtering):
            del dico[k]
    total_sum_predection= sum(dico.values())
    for k in dico.keys() :
        dico[k]=dico[k]/total_sum_predection
    size_set_classes=len(dico.keys())
    Total = size_set_classes*time_per_k
    LB = size_set_classes*lower
    budget_time = Total - LB
    if budget_time < 0 :
        budget_time=0
    d = dico.copy()
    for entry in dico.keys() :
        time_b = ( dico[entry] * budget_time ) + lower
        if float(time_b) > float(upper):
            time_b = upper
            #print "in"
        d[entry] = [ d[entry] , time_b]
        dico[entry] = time_b
    return dico, d



def allocate_time_FP(dico,time_per_k,upper,lower,filtering):
    for k in dico.keys():
        if str(k).__contains__(filtering):
            del dico[k]
    total_sum_predection = sum(dico.values())
    for k in dico.keys():
        dico[k] = dico[k] / total_sum_predection
    size_set_classes = len(dico.keys())
    print "dico size=",size_set_classes
    Total = size_set_classes * time_per_k
    print "Total=",Total
    LB = size_set_classes * lower
    print "LB=",LB
    budget_time = Total - LB
    d_fin={}
    not_max = {}
    for k in dico.keys():
        d_fin[k]=[dico[k],lower]
        not_max[k] = dico[k]
    lower_b = lower
    while( budget_time>0 or len(not_max.keys())==0 ):
        left_over = budget_time
        for entry in not_max.keys():
            time_b = (not_max[entry] * budget_time)
            if float(time_b) + d_fin[entry][1]   >  float(upper) :
                time_b = upper - d_fin[entry][1]
                d_fin[entry][1]+=time_b
                del not_max[entry]
                #budget_time+=lower_b
            else:
                d_fin[entry][1] += time_b
            left_over = left_over - time_b
        budget_time=left_over
        #lower_b=0
        total_sum_predection = sum(not_max.values())
        if total_sum_predection == 0 :
            break
        for k in not_max.keys():
            not_max[k] = not_max[k] / total_sum_predection
    if len(dico) != len(d_fin):
        raise Exception("in function (allocate_time_FP) the dico and d_fin is not in the same size")
    for k in dico:
        dico[k]=d_fin[k][1]
    return dico,d_fin

def mkdir_Os(path,name):
    name_r = str(name).replace(' ','_')
    full_path=str(path)+str(name_r)+'/'
    try:
        os.makedirs(full_path)
        return full_path
    except OSError:
        if not os.path.isdir(full_path):
            raise
    return 'null'

def assemble_path_string2(str) :

    cutoff = 0
    suffix=""
    prefix=""
    len_str = len(str)
    word =''
    for i in range(len_str-1, 0, -1) :
        cutoff += 1
        if str[i]=='/' :
           # word_r = reversed(word)
           # word = ''.join(word_r)
            if word == 'classes':
                prefix = str[0:len_str - cutoff + len(word)+1]
                break
            if len(word)>1:
                 suffix=word+"."+suffix
            word = ""
        else :
            word=str[i]+word

    return prefix,suffix

def mereg_dic(list_new,list_org):
    if len(list_new) > len(list_org):
        size=len(list_org)
    else:
        size= len(list_new)
    dic_new={}
    dic_org={}
    for item_new in list_new :
        cut_names = str(item_new[1]).split('.')
        new_path,suf = assemble_path_string2(item_new[0])
        cut = suf  + cut_names[0]
        dic_new[cut]=str(new_path)
    for item_org in list_org:
        cut_names = str(item_org[1]).split('.')
        new_org,suf = assemble_path_string2(item_org[0])
        cut = suf  + cut_names[0]
        dic_org[cut]=str(new_org)
    return dic_new,dic_org

def remove_dot_csv(path):
    with open(path, 'r') as myfile:
        data = myfile.read().replace(';','_')
        text_file = open(path, "w")
        text_file.write(" %s" % data)
        text_file.close()
    return "done"


def clean_path_MATH(p):
    p_str = str(p)
    if len(p)<1:
        return 'null-str'
    val = p_str.find('/org/')
    val_end = p_str.find('.class')
    if val == -1 :
        return 'null-org'
    ans = p_str[val+1:val_end]
    return  ans

def get_all_class(root,end) :
    size=0
    root =root
    class_list = []
    walker=pit_render_test.walker(root)
    classes_list = walker.walk(".class")
    for item in classes_list:
        if str(item).__contains__("$"):
            continue
        val = clean_path_MATH(item)
        val = val.replace('/', '.')
        class_list.append(val)
    print (len(class_list))
    return class_list

def get_all_command(budget_time,seed,mem=1000):
    commands=[]
    search = int(budget_time)
    const_factor = 5
    half_budget =  int(budget_time)/2
    x_budget = half_budget/const_factor
    initialization = x_budget
    minimization = x_budget
    assertions= x_budget
    extra = int(budget_time) - ( (x_budget)*5 + half_budget )
    junit = x_budget
    write_t = x_budget

    commands.append("-seed %s"%seed)
    commands.append("-Dsearch_budget=%s" % search)
    commands.append("-Dshow_progress=false")
    commands.append("-Dtest_comments=false")
    commands.append("-Dconfiguration_id=%s" %seed)
    #commands.append("-Dsandbox=false") #TODO:???? (Execute tests in a sandbox environment)

    return " ".join(str(i) for i in commands)


    commands.append("-Dreuse_leftover_time=true")
    #commands.append("-Dglobal_timeout=%s" % search)
    commands.append("-Dinitialization_timeout=%s" %  initialization)
    commands.append("-Dminimization_timeout=%s" %  minimization)
    commands.append("-Dassertion_timeout=%s" % assertions)
    commands.append("-Dextra_timeout=%s" %  extra)
    commands.append("-Djunit_check_timeout=%s" % junit)
    commands.append("-Dwrite_junit_timeout=%s" % write_t)


    #commands.append("-Xmx%sm" %mem)
    #commands.append(("-mem %s" %mem))

    return " ".join(str(i) for i in commands )


def get_instance_bug_and_fix(bug_lis, fix_lis , delimiter):
    result_dict={}
    if len(fix_lis) != len(bug_lis):
        print ("-----Errorbox: fix list and bug list not in the same size fix_size={0} bug_size={1}-----".format(len(fix_lis),len(bug_lis)))
    for item in bug_lis:
        for it in item:
            name_dot = it[0]+'/'+it[1]
            val= name_dot.find(delimiter)
            res = name_dot[val:-6]
            bug_path = name_dot[:val]
            res =res.replace("/",".")
            result_dict[res] = 1
    for tmp_pac in fix_lis:
        for tmp_k in tmp_pac:
            name_dot = tmp_k[0] + '/' +tmp_k[1]
            val = name_dot.find(delimiter)
            res = name_dot[val:-6]
            fix_path = name_dot[:val]
            res = res.replace("/", ".")
            if res in result_dict:
                result_dict[res] = 2
            else :
                print "---[Error] in get_instance_bug_and_fix function ---- "

    return result_dict,fix_path[:-1],bug_path[:-1]




def get_all_class_v3(root_p):
    arr_root = str(root_p).split('/')
    name_klass = arr_root[-1]
    path_klass = arr_root[:-1]
    str1_path_root = '/'.join(path_klass)
    walker = pit_render_test.walker(str1_path_root)
    list_java = walker.walk(name_klass+".class",True,0)
    if len(list_java)>0:
        return [str(str1_path_root),str(name_klass+".class")]
    else:
        return []

def spliter(str_path):
    arr_p = str(str_path).split("/")
    name_p = arr_p[-1]
    str1_path_root = '/'.join(arr_p[:-1])
    return [str1_path_root,name_p]
#'/home/eran/Desktop/defect4j_exmple/fixed/target/classes/org/apache/commons/math3/optim/nonlinear/scalar/gradient/.class'
def get_all_class_v2(root):
    walker = pit_render_test.walker(root)
    list_java = walker.walk(".class",True,0)
    new_list = [i for i in list_java if str(i).__contains__("$") == False and str(i).__contains__("package-info") == False]
    new_list_sp =[]
    for p in new_list :
        new_list_sp.append(spliter(p))
    return new_list_sp

def get_all_class_v1(root) :
    size=0
    class_list = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            #print os.path.join(path, name)
            if name.__contains__("$") is False:
                size+=1
                class_list.append([str(path),str(name)])
    return class_list

'''
"The term original in our context refers to the version which EvoSuiteR considers as correct,
and the term regression refers to the version which EvoSuiteR considers to have potential regressions.
Thus, the generated tests are intended to pass on the original version, and fail on the regression version".
[Link] : https://github.com/EvoSuite/evosuite/wiki/Regression-Testing
'''
def regression_test(evo_name, evo_path, list_fixed, list_buggy,budget_dic, dis_path, lower_b , upper_b, seed , total_b,m_class) :  # fixed = original |||| bug =  regression
    evo_string = "java -jar " + evo_path + evo_name +" -regressionSuite"
    parms0 = " -Dregression_skip_similar=true"
    parms2 = " -Dregression_statistics=true"
    parms3 = " -Dreport_dir=" + dis_path
    parms4 = " -Dtest_dir=" + dis_path
    parms5 = " -Doutput_variables=TARGET_CLASS,criterion,configuration_id,Total_Methods,Covered_Methods,Total_Branches,Covered_Branches,Size,Length,Total_Time,Covered_Goals,Total_Goals,Coverage,search_budget"
    criterion = "-criterion BRANCH:EXCEPTION:METHOD"
    all_p = parms2+parms3+parms4+parms5+parms0
    all_command=""
    result_dict, fix_path, bug_path=get_instance_bug_and_fix(list_buggy,list_fixed,'org')

    if 'mode' in budget_dic:
        mode =  budget_dic['mode']
        list_class = []
    else :
        list_class = budget_dic.keys()
    size_list_class = len(list_class)

    for test_case in result_dict.keys():
        if test_case not in m_class:
            continue
        if size_list_class == 0:
            time_budget = total_b
        else:
            if test_case  in list_class:
                value_time = budget_dic[test_case]
                value_time = float(value_time)
                time_budget = int(round(value_time))
            else:
                time_budget = lower_b
        all_time = get_all_command(time_budget, seed)
        #all_time = ""
        all_p=all_time +" "+ all_p
        command = "{0} -projectCP {1} -Dregressioncp={2} -class {5} {3} {4}".format(evo_string,fix_path,bug_path,criterion,all_p,test_case)
        #command = evo_string + "-class " +test_case+" -projectCP "+fix_path+" -Dregressioncp="+bug_path+" "+criterion+" "+all_p
        print (command)
        all_command = all_command +'\n'*2 + command
        os.system(command)
    if os.path.exists(dis_path + 'statistics.csv'):
        remove_dot_csv(dis_path + 'statistics.csv')
    text_file = open(dis_path + "command.txt", "w")
    text_file.write("command: \n  %s" % all_command)
    text_file.close()

def single_call_EvoSuite(evo_name,evo_path,classes_list,time,dis_path,lower_b,seed,b_class):

    evo_string = "java -jar " + evo_path +evo_name

    criterion = " "

    parms3=" -Dreport_dir="+dis_path
    parms4=" -Dtest_dir="+dis_path
    parms5=" -Doutput_variables=TARGET_CLASS,criterion,configuration_id,\
Total_Branches,Covered_Branches,Size,Length,Total_Time,Covered_Goals,Total_Goals,Coverage,search_budget"

    all_p = parms3+parms4+parms5
    all_command=''
    if len(time) > 0:
        list_class = time.keys()
    else:
        list_class = []
    size_list_class = len(list_class)
    for cut in classes_list :
        all_p = parms3 + parms4 + parms5
        cut_names = str(cut[1]).split('.')
        pre,suf = assemble_path_string2(cut[0])
        test = suf  + cut_names[0]
        if size_list_class == 0 :
            time_budget = b_class
        else :
            if test in list_class:
                value_time =  time[test]
                value_time = float(value_time)
                time_budget = int(round(value_time))
            else:
                time_budget= lower_b
                print "[Warning] the {} did not get any budget time in the FP mode".format(test)
        all_time = get_all_command(time_budget,seed)
        all_p=all_time +" "+ all_p
        command = evo_string + " -class " +test+" -projectCP "+pre+criterion+all_p
        print (command)
        all_command = all_command +'\n'*2 + command
        file_name_class = str(test)
        str_log = "{} >> {}log_evo/{}.txt 2>&1".format(command,dis_path,file_name_class)
        os.system(str_log)
    if os.path.exists(dis_path + 'statistics.csv'):
        remove_dot_csv(dis_path + 'statistics.csv')
    text_file = open(dis_path + "command.txt", "w")
    text_file.write("command: \n  %s" % all_command)
    text_file.close()


def dict_to_csv(mydict,path):
    with open(path+'FP_budget_time.csv', 'wb') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in mydict.items():
            writer.writerow([key, value[0],value[1]])

def init_main():

   # sys.argv=['py',"/home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/apache/commons/math3/fraction/"  #fraction #distribution
   #       ,"evosuite-1.0.5.jar","/home/ise/eran/evosuite/jar","/home/ise/Desktop/out/",'exp','10','180','180']
    #str_val = "py /home/eranhe/eran/math/commons-math3-3.5-src/src/main/java/org/apache/commons/math3/ml/distance evosuite-1.0.5.jar /home/eranhe/eran/evosuite/jar/ /home/eran/Desktop/ exp 30 180 50"
    #arr_str = str_val.split(" ")
    #sys.argv = arr_str
   # string_command = '/home/ise/eran/repo/ATG/budget_generation.py /home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/apache/commons/math3/fraction/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ /home/ise/eran/exp_little/02_12_15_52_36_t=2_/ exp 1 300 1'
    #string_command = 'py /home/ise/eran/repo/common_math/commons-math3-3.5-src/target/classes/org/apache/commons/math3/fraction/ evosuite-1.0.5.jar /home/ise/eran/evosuite/jar/ /home/ise/eran/exp_little/02_12_13_07_52_t=10_/ U 1 300 10'
    #string_command_arr = string_command.split(' ')
    #sys.argv = string_command_arr   #TODO: remove it !!!!!!
    if len(sys.argv) < 3 :
        print("miss value ( -target_math -evo_version -vo_path -out_path -csv_file   )")
        exit(1)
    mode = sys.argv[5]
    if mode == 'exp':
        int_exp(sys.argv)
        return
    if mode == 'reg':
        #regression_testing(sys.argv)
        return
    v_path = sys.argv[1]  # target = /home/eran/thesis/test_gen/poc/commons-math3-3.5-src/target/classes/org
    v_evo_name = sys.argv[2]  #evo_version = evosuite-1.0.5.jar
    v_evo_path = sys.argv[3] #evo_path  = /home/eran/programs/EVOSUITE/jar
    v_dis_path = sys.argv[4] #out_path = /home/eran/Desktop/
    lower_b = int(sys.argv[6])
    upper_b = int(sys.argv[7])
    b_klass = int(sys.argv[8])
    rel_path = os.getcwd()+'/'
    if mode == 'FP':
        budget_dico,d = get_time_fault_prediction(str(rel_path)+'csv/Most_out_files.csv', 'FileName', 'prediction', v_path,upper_b,lower_b,b_klass)
    else:
        budget_dico = {}
    const = "345"
    print "all=",len(budget_dico.keys())
    print"time=",b_klass
    for i in range(3):
        seed = time.strftime('%s')[-5:]
        seed = str(i)+str(const)+str(i)  #<--------remove---remove---remove-----------
        localtime = time.asctime(time.localtime(time.time()))
        if mode == 'FP':
            localtime_str ='FP_'+ str(localtime)+'_t='+str(b_klass)+'_it='+str(i)
        else:
            localtime_str ='U_'+ str(localtime)+'_t='+str(b_klass)+'_it='+str(i)
        full_dis = mkdir_Os(v_dis_path, localtime_str)
        if full_dis=='null':
            print('cant make dir')
            exit(1)
        target_list = get_all_class_v1(v_path)
        if str(v_path).__contains__("frac"):
            target_list1 = get_all_class_v3(v_path+'Fraction')
            target_list2 = get_all_class_v3(v_path+'BigFraction')
            target_list = [target_list1 , target_list2]
        if mode == 'FP':
            dict_to_csv(d,v_dis_path)
        single_call_EvoSuite(v_evo_name,v_evo_path,target_list,budget_dico,full_dis,lower_b,seed,b_klass)



def int_exp(args):
    print 'exp...'
    v_path = sys.argv[1]  # target = /home/eran/thesis/test_gen/poc/commons-math3-3.5-src/target/classes/org
    v_evo_name = sys.argv[2]  #evo_version = evosuite-1.0.5.jar
    v_evo_path = sys.argv[3] #evo_path  = /home/eran/programs/EVOSUITE/jar
    v_dis_path = sys.argv[4] #out_path = /home/eran/Desktop/
    upper_b = int(sys.argv[7])
    lower_b = int(sys.argv[6])
    b_klass = int(sys.argv[8])
    rel_path = os.getcwd() + '/'
    fp_budget, d = get_time_fault_prediction(str(rel_path)+'csv/Most_out_files.csv', 'FileName', 'prediction', v_path,upper_b,lower_b,b_klass)
    uni_budget = {}
    comp = ["FP","U"]
    #comp = ["U"]
    target_list = get_all_class_v1(v_path)
    dict_to_csv(d, v_dis_path)
    for i in range(3): #TODO : change it back to two (2)
        seed = time.strftime('%s')[-5:]
        for parm in comp:
            localtime = time.asctime(time.localtime(time.time()))
            dir_name = str(parm)+'_exp_t'+ str(localtime) + '_t=' + str(b_klass) + '_it=' + str(i)
            full_dis = mkdir_Os(v_dis_path, dir_name )
            if full_dis == 'null':
                print('cant make dir')
                exit(1)
            #make a log dir
            is_log = mkdir_Os(full_dis, 'log_evo' )
            if is_log == 'null':
                print('cant make dir log')
                exit(1)
            if str(parm)== 'FP':
                single_call_EvoSuite(v_evo_name, v_evo_path, target_list, fp_budget, full_dis,lower_b,seed,b_klass)
            else :
                single_call_EvoSuite(v_evo_name, v_evo_path, target_list, uni_budget, full_dis,lower_b,seed,b_klass)




def regression_testing_handler(bug_obj): #params [ -buggy_path  -fixed_path -[U/F/O/A] -path_csv_FP -mode -output_path -evo_version -evo_path -time_budget -Lower_b -Up_b  ]
    print "[regression]"

    #args=["",'A',str(rel_path)+"csv/Most_out_files.csv"
    #    ,'/home/eran/Desktop/defect4j_exmple/out/',"evosuite-1.0.5.jar", "/home/eran/programs/EVOSUITE/jar/",'100' , '30', '180']
    #buggy_path = args[1]
    #fixed_path = args[2]
    args=bug_obj.info
    buggy_path = str(bug_obj.root)+"buggy/target/classes/"
    fixed_path = str(bug_obj.root)+"fixed/target/classes/"
    m_class = bug_obj.modified_class
    modified_class_paths = []
    modified_package_path=[]
    for p_path in bug_obj.modified_class:
        modified_class_paths.append(str(p_path).replace(".","/"))

    for pac_path in bug_obj.infected_packages:
        modified_package_path.append(str(pac_path).replace(".", "/"))

    run_var=args[2]
    csv_path_fp=args[3]
    out_path=args[4]
    evo_version=args[5]
    evo_path=args[6]
    total_budget_class=int(args[7])
    lower_b = int(args[8])
    upper_b = int(args[9])



    if run_var == 'A':
        comp = ["OR", "FP","U"]
    else :
        comp = [run_var]
    if "FP" in comp :
        fp_budget, d = get_time_fault_prediction(csv_path_fp, 'FileName', 'prediction', out_path,upper_b,lower_b,total_budget_class)
        dict_to_csv(d, out_path)

    target_list_fixed_list_package = []
    target_list_buggy_list_package= []
    for modified_item in set(modified_package_path):
        target_list_fixed_list_package.append(get_all_class_v2(fixed_path+modified_item))
        target_list_buggy_list_package.append(get_all_class_v2(buggy_path+modified_item))

    target_list_fixed_list_classes = []
    target_list_buggy_list_classes = []
    for modified_item in modified_class_paths:
        target_list_fixed_list_classes.append(get_all_class_v3(fixed_path+modified_item))
        target_list_buggy_list_classes.append(get_all_class_v3(buggy_path+modified_item))

    if len(target_list_buggy_list_classes) == 0 or len(target_list_fixed_list_classes) == 0  :
        print " [Error] no target class has been found "
        return

    for i in range(1):

        seed = time.strftime('%s')[-5:]
        for parm in comp:
            localtime = time.asctime(time.localtime(time.time()))
            dir_name = "{0}_D4j_{1}_t={2}_it={3}_b={4}_p={5}".format(str(parm),str(localtime),str(total_budget_class),str(i),str(bug_obj.id),str(bug_obj.p_name)[:2])
            full_dis = mkdir_Os(out_path, dir_name)
            if full_dis == 'null':
                print('cant make dir')
                exit(1)
            if str(parm) == 'FP' :
                regression_test(evo_version, evo_path, target_list_fixed_list_package, target_list_buggy_list_package, fp_budget, full_dis, lower_b, upper_b, seed, total_budget_class,m_class)
            elif str(parm )== 'U':
                mode_budget={'mode':'U'}
                regression_test(evo_version, evo_path, target_list_fixed_list_package, target_list_buggy_list_package, mode_budget, full_dis, lower_b, upper_b,seed, total_budget_class,m_class)
            elif str(parm) == 'OR':
                mode_budget = {'mode': 'OR'}
                regression_test(evo_version, evo_path, [target_list_fixed_list_classes], [target_list_buggy_list_classes], mode_budget, full_dis, lower_b, upper_b,seed,total_budget_class,m_class)


def get_bug_object(bug_obj):
    args_params=[]
    args_params.append("")
    args_params.append(bug_obj.root+"buggy/") #path to bug version
    args_params.append(bug_obj.root+"fixed/") #path to the fixed version
    args_params.append(bug_obj.info[2])  #runnig mode
    args_params.append(bug_obj.info[7])  #csv_path
    args_params.append("D4j") #mode
    args_params.append(bug_obj.info[3])  #out path
    args_params.append(bug_obj.info[1])  #evo_version
    args_params.append(bug_obj.info[0])  #evo_path
    args_params.append(bug_obj.info[4])  #total budget per class
    args_params.append(bug_obj.info[6])  #lower
    args_params.append(bug_obj.info[5])  #upper
    return args_params



if __name__ == "__main__":
    init_main()




#get_time_dico1("budget.csv")
