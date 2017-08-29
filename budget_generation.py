import sys, os ,time,csv

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
        if k in class_list is False:
            del dico[k]
    return dico

def time_pred(time_per_class,dico,prefix):
    for k in dico.keys():
        if str(k).__contains__(prefix):
            del dico[k]
    size = len(dico.keys())
    fac = size*time_per_class
    for k in dico.keys():
        dico[k]=dico[k]*fac
    return dico

def get_time_fault_prediction(path,key,value,root):
    dico= csv_to_dict(path,key,value)
    dico = clean_dict(dico,'src\main',14,5)
    total_sum_predection = float(0)
    class_list = get_all_class(root,66,5)
    dico = match_dic(class_list,dico)
    total_sum_predection= sum(dico.values())
    for k in dico.keys() :
        dico[k]=dico[k]/total_sum_predection
    time_pred(120,dico,'age-in')
    return dico




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

def get_all_class(root,start,end) :
    size=0
    class_list = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            #print os.path.join(path, name)
            if name.__contains__("$") is False:
                size+=1
                val = str(path)+'/'+str(name)
                val = val[start:-end]
                val = val.replace('/','.')
                class_list.append([str(path)+'/'+str(name)])
    print (len(class_list))
    return class_list



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

def single_call_EvoSuite(evo_name,evo_path,classes_list,time,dis_path):

    evo_string = "java -jar " + evo_path +evo_name

    criterion = " "


    #parms1="-Dsearch_budget="+time
    parms3=" -Dreport_dir="+dis_path
    parms4=" -Dtest_dir="+dis_path
    parms5=" -Doutput_variables=TARGET_CLASS,criterion,Lines,Covered_Lines,Total_Methods,Covered_Methods,\
Total_Branches,Covered_Branches,ExceptionCoverage,Size,Length,MutationScore,Mutants,Total_Time,Covered_Goals,Total_Goals,Coverage"

    all_p = parms3+parms4+parms5
    all_command=''
    for cut in classes_list :
        all_p = parms3 + parms4 + parms5
        cut_names = str(cut[1]).split('.')
        pre,suf = assemble_path_string2(cut[0])
        test = suf  + cut_names[0]
        list_class = time.keys()
        if test in list_class:
            value_time =  time[test]
            value_time = float(value_time)
            if value_time > 10 :
                value_time = int(10)
            elif value_time < 1 :
                continue
            else :
                value_time = int(round(value_time))
            time_budget = str(value_time)
        else:
            print('----o0ops-------')
            time_budget='120'
        time_command = "-Dsearch_budget=" + time_budget
        all_p=time_command + all_p
        command = evo_string + " -class " +test+" -projectCP "+pre+criterion+all_p
        print (command)
        all_command = all_command +'\n'*2 + command
        os.system(command)
    text_file = open(dis_path + "command.txt", "w")
    text_file.write("command: \n  %s" % all_command)
    text_file.close()
    remove_dot_csv(dis_path+'statistics.csv')







def init_main():

#    sys.argv=['py',"/home/eran/thesis/test_gen/poc/commons-math3-3.5-src/target/classes/org","evosuite-1.0.5.jar",
#             "/home/eran/programs/EVOSUITE/jar/","/home/eran/Desktop/",'FP']
    if len(sys.argv) < 3 :
        print("miss value ( -target_math -evo_version -vo_path -out_path -csv_file   )")
        exit(1)
    v_path = sys.argv[1]  # target = /home/eran/thesis/test_gen/poc/commons-math3-3.5-src/target/classes/org
    v_evo_name = sys.argv[2]  #evo_version = evosuite-1.0.5.jar
    v_evo_path = sys.argv[3] #evo_path  = /home/eran/programs/EVOSUITE/jar
    v_dis_path = sys.argv[4] #out_path = /home/eran/Desktop/
    mode = sys.argv[5]  #csv file = /home/eran/Desktop/budget.csv
    if mode == 'FP':
        budget_dico = get_time_fault_prediction('csv/Most_out_files.csv', 'FileName', 'prediction', v_path)
    else:
        budget_dico = csv_to_dict('csv/budget.csv','class','mean time- totalEffortInSeconds')

    for i in range(5):
        localtime = time.asctime(time.localtime(time.time()))
        localtime_str = str(localtime)+'it='+str(i)
        full_dis = mkdir_Os(v_dis_path, localtime_str)
        if full_dis=='null':
            print('cant make dir')
            exit(1)
        target_list = get_all_class_v1(v_path)
        single_call_EvoSuite(v_evo_name,v_evo_path,target_list,budget_dico,full_dis)

init_main()





#get_time_dico1("budget.csv")
