
import glob, os ,sys
import time

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
    print str
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
    print prefix
    print suffix
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

def get_all_class(root) :
    size=0
    class_list = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            #print os.path.join(path, name)
            if name.__contains__("$") is False:
                size+=1
                class_list.append([str(path),str(name)])
    print "size=",size
    return class_list


def single_call_EvoSuite(evo_name,evo_path,classes_list,time,dis_path):

    evo_string = "java -jar " + evo_path +evo_name

    criterion = " "


    parms1="-Dsearch_budget="+time
   # parms2=" -Dglobal_timeout="+time
    parms3=" -Dreport_dir="+dis_path
    parms4=" -Dtest_dir="+dis_path
    parms5=" -Doutput_variables=TARGET_CLASS,criterion,Lines,Covered_Lines,Total_Methods,Covered_Methods,\
Total_Branches,Covered_Branches,ExceptionCoverage,Size,Length,MutationScore,Total_Time,Covered_Goals,Total_Goals,Coverage"

    all_p = parms1+parms3+parms4+parms5
    all_command=''
    for cut in classes_list :
        cut_names = str(cut[1]).split('.')
        pre,suf = assemble_path_string2(cut[0])
        test = suf  + cut_names[0]
        command = evo_string + " -class " +test+" -projectCP "+pre+criterion+all_p
        print command
        all_command = all_command +'\n'*2 + command
        os.system(command)
    text_file = open(dis_path + "command.txt", "w")
    text_file.write("command: \n  %s" % all_command)
    text_file.close()
    remove_dot_csv(dis_path+'statistics.csv')


def regression_test(evo_name, evo_path, classes_list_new,classes_list_original,time, dis_path) :
    evo_string = "java -jar " + evo_path + evo_name +" -regressionSuite "

    #parms0 = " -Dregression_skip_similar=true"
    parms1 = " -Dsearch_budget=" + time
    parms2=" -Dregression_statistics=true"
    parms3 = " -Dreport_dir=" + dis_path
    parms4 = " -Dtest_dir=" + dis_path
    all_p = parms1+parms2+parms3+parms4

    dic_new,dic_org = mereg_dic(classes_list_new,classes_list_original)
    all_command = ''
    for key, value in dic_new.iteritems():
        if key in dic_org :
            org_p=str(dic_org[key])
        else:
            continue
        new_p = str(value)
        if len(org_p)<1 :
            continue
        command = evo_string + " -class " +key+" -projectCP "+org_p+" -Dregressioncp="+new_p+all_p
        print command
        all_command = all_command +'\n'*2 + command
        os.system(command)
    text_file = open(dis_path + "command.txt", "w")
    text_file.write("command: \n  %s" % all_command)
    text_file.close()
    #remove_dot_csv(dis_path+'statistics.csv')




#str_regg = "evo_call.py /home/eran/thesis/common_math/commons-math3-3.5-src/target/classes/org/ /home/eran/thesis/common_math/commons-math3-3.6.1-src/target/classes/org/ evosuite-1.0.5.jar /home/eran/programs/EVOSUITE/jar/ /home/eran/Desktop/evo_result/ 30"

#str_commands_common_math = "evo_call.py /home/eran/thesis/common_math/commons-math3-3.6.1-src/target/classes/org/ evosuite-1.0.5.jar /home/eran/programs/EVOSUITE/jar/ /home/eran/Desktop/evo_result/ 60"

#str_command_tut = "evo_call.py /home/eran/thesis/Tutorial_Experiments/target/classes/tutorial/ evosuite-1.0.5.jar /home/eran/programs/EVOSUITE/jar/ /home/eran/Desktop/out_exp/ 10"

#str_arry = str_commands_common_math.split(" ")
#sys.argv = str_arry

if len(sys.argv) == 6 :
    v_path = sys.argv[1]
    v_evo_name = sys.argv[2]
    v_evo_path = sys.argv[3]
    v_dis_path = sys.argv[4]
    v_time = sys.argv[5]
    localtime = time.asctime(time.localtime(time.time()))
    localtime_str = str(localtime)+'_t='+str(v_time)
    full_dis = mkdir_Os(v_dis_path, localtime_str)
    if full_dis=='null':
        print 'cant make dir '
        exit(1)
    target_list = get_all_class(v_path)
    single_call_EvoSuite(v_evo_name,v_evo_path,target_list,v_time,full_dis)
    print "done !"
else:
    if len(sys.argv) == 7 :
        v_path_org = sys.argv[1]
        v_path_new = sys.argv[2]
        v_evo_name = sys.argv[3]
        v_evo_path = sys.argv[4]
        v_dis_path = sys.argv[5]
        v_time =     sys.argv[6]
        localtime = time.asctime(time.localtime(time.time()))
        localtime_str = str(localtime) + '_t=' + str(v_time)
        full_dis = mkdir_Os(v_dis_path, localtime_str)
        if full_dis == 'null':
            print 'cant make dir '
            exit(1)
        list_org = get_all_class(v_path_org)
        list_new = get_all_class(v_path_new)
        regression_test(v_evo_name, v_evo_path, list_new, list_org, v_time, full_dis)
        print 'Done !'



print "miss argv (-Path -EvoName -EvoPath -DistPath -Time)"


