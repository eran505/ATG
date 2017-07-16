
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

    criterion = " -criterion EXCEPTION "
    parms1="-Dsearch_budget="+time
    parms2=" -Dglobal_timeout="+time
    parms3=" -Dreport_dir="+dis_path
    parms4=" -Dtest_dir="+dis_path

    all_p = parms1+parms2+parms2+parms3+parms4
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

def exp_test(evo_name,evo_path,classes_list,time,dis_path,names) :
    cuts = []
    for cut in classes_list:
        for name in names:
            if cut[1] == name:
                cuts.append(cut)

    exp_test_evo(evo_name,evo_path,cuts,time,dis_path)

def exp_test_evo(evo_name,evo_path,classes_list,time,dis_path):
    evo_string = "java -jar " + evo_path +evo_name
    criterions = ['none','LINE', 'BRANCH', 'EXCEPTION' ]
    parms1="-Dsearch_budget="+time
    parms2=" -Dglobal_timeout="+time
    parms3=" -Dreport_dir="+dis_path
    parms4=" -Dtest_dir="+dis_path
    parms5=" -Doutput_variables=TARGET_CLASS,criterion,Size,Length,MutationScore,Total_Time,Covered_Goals,Total_Goals,Coverage"

    all_p = parms1+parms3+parms4+parms5+parms2
    all_command=''
    for cut in classes_list :
        for c in criterions:
            criterion = " -criterion "+c+" "
            cut_names = str(cut[1]).split('.')
            pre,suf = assemble_path_string2(cut[0])
            test = suf  + cut_names[0]
            if c == 'none':
                command = evo_string + " -class " +test+" -projectCP "+pre+" "+all_p
            else:
                command = evo_string + " -class " + test + " -projectCP " + pre + criterion + all_p
            all_command=all_command+'\n'+command
            print command
            os.system(command)
    text_file = open(dis_path+"command.txt", "w")
    text_file.write("commands: \n %s" % all_command)
    text_file.close()
    remove_dot_csv(dis_path+'statistics.csv')


str_commands = "evo_call.py /home/eran/thesis/projects-ex/commons-math3-3.6.1-src/target/classes/org/ evosuite-master-1.0.6-SNAPSHOT.jar /home/eran/programs/EVOSUITE/jar/ /home/eran/Desktop/evo_result/ 60"
str_arry = str_commands.split(" ")
sys.argv = str_arry

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
    #exp_test(v_evo_name,v_evo_path,target_list,v_time,full_dis,['AdamsFieldStepInterpolator.class'])
    single_call_EvoSuite(v_evo_name,v_evo_path,target_list,v_time,full_dis)
    print ("done !")
else:
    print "miss argv (-Path -EvoName -EvoPath -DistPath -Time)"




path_1 = "/home/eran/thesis/Tutorial/Tutorial_Experiments/target/classes/tutorial/"

path_2 = "/home/eran/thesis/projects-ex/commons-math3-3.6.1-src/target/classes/org/"

evo_path="/home/eran/programs/EVOSUITE/jar/"

evo_name = "evosuite-1.0.4.jar"

evo_name_sanpshot = "evosuite-master-1.0.6-SNAPSHOT.jar"

evo_st_name ="evosuite-standalone-runtime-1.0.4.jar"

dis_path = "/home/eran/Desktop/evo_result/"

#target_list = get_all_class(path_2)

#single_call_EvoSuite(evo_name_sanpshot,evo_path,target_list,'5',dis_path)
