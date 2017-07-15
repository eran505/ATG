
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

    for cut in classes_list :
        cut_names = str(cut[1]).split('.')
        pre,suf = assemble_path_string2(cut[0])
        test = suf  + cut_names[0]
        command = evo_string + " -class " +test+" -projectCP "+pre+criterion+all_p
        print command
        os.system(command)
        text_file = open(dis_path+"command.txt", "w")
        text_file.write("command: %s" % command)
        text_file.close()



#str_commands = "evo_call.py /home/eran/thesis/projects-ex/commons-math3-3.6.1-src/target/classes/org/ evosuite-master-1.0.6-SNAPSHOT.jar /home/eran/programs/EVOSUITE/jar/ /home/eran/Desktop/evo_result/ 10"
#str_arry = str_commands.split(" ")
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
