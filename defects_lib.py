
import  os,copy
import sys,time
import subprocess
project_dict = {}
root_dir = '~/'
import shutil
from contextlib import contextmanager
import budget_generation as bg

class Bug_4j:

    def __init__(self, pro_name,bug_id,info_args,root_dir,defect4j_root="/home/eran/programs/Defects4j/defects4j/framework/bin/defects4j"):
        self.root = root_dir
        self.p_name = pro_name
        self.id = bug_id
        self.info=info_args
        self.defects4j = defect4j_root
        self.modified_class=[]
        self.infected_packages = []
        self.contractor()

    def isValid(self):
        total_bugs = project_dict[self.p_name]['num_bugs']
        if self.id  > total_bugs or self.id  < 1:
            m_error = 'Error in ID number bug {0} in project:{1} the range is 1 - {2}'.format(self.id, self.p_name, total_bugs)
            raise Exception(m_error)
        return True

    def get_data(self):
        self.check_out_data('f')
        self.check_out_data('b')
        sig = self.compile_data()
        return sig

    def correspond_package(self):
        for klass in self.modified_class :
            arr_pac = str(klass).split(".")
            arr_pac = arr_pac[:-1]
            str1_pac= '.'.join(str(e) for e in arr_pac)
            self.infected_packages.append(str1_pac)

    def evo_testing(self):
        print "preparing test suite ..."
        bg.regression_testing(self)

    def init_shell_script(self,command):
        print "-----command=\n"+command+"\n --------------"
        process = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE)
        process.wait()
        return process.returncode


    def compile_data(self):
        if self.p_name == 'Math':
            print "compile fixed version..."
            relative_path = "bash_scripts/ant_compile.sh"
            command_str = relative_path+" "+self.root+"fixed"
            sig_f = self.init_shell_script(command_str)
            command_str = relative_path+" "+self.root+"buggy"
            sig_b = self.init_shell_script(command_str)
            if sig_b == 1 or sig_f==1 :
                return 1
            return 0


    def check_out_data(self,var='f'):
        print "checking out version..."
        if var =='f':
            str_command = self.defects4j+' checkout -p {1} -v {0}"{3}" -w {2}fixed/'.format(self.id, self.p_name, self.root,var)
        elif var =='b':
            str_command = self.defects4j+' checkout -p {1} -v {0}"{3}" -w {2}buggy/'.format(self.id, self.p_name, self.root,var)
        else :
            raise Exception("input to the method can be either 'f' or 'b' ")
        x = os.system(str_command)
        if x == 0 :
            return True
        print "[Error] in the check out:\n "+str_command+"\n -----------------------"
        return False


    def contractor(self):
        if self.root[-1] != '/':
            self.root = self.root + "/"
        if os.path.isdir(self.root) == False :
            raise Exception("cant find the path {0}".format(self.root))
        dir_d4j = ["fixed","buggy"]
        #dir_d4j = [] #-----------------------------------Remove------------------------------------------------------
        for item in dir_d4j :
            if os.path.isdir(self.root+item):
                shutil.rmtree(self.root+item)
            os.mkdir(self.root+item)
        self.extract_data()
        self.correspond_package()
        self.info[4] = self.root

    def extract_data(self):
        if self.isValid():
            str_c = "/home/eran/programs/Defects4j/defects4j/framework/bin/defects4j info -p  {1} -b {0}".format(self.id, self.p_name)
            #print str_c
            result = subprocess.check_output(str_c, shell=True)
            x=result.find("List of modified sources:")
            #print result
            #print "val = ", result[x+len("List of modified sources:"):-81]
            y=result[x+len("List of modified sources:"):].replace("-","").replace(" ","").split('\n')
            for y1 in y:
                if len(y1)>1:
                    self.modified_class.append(y1)
            for item in self.modified_class :
                print item




def before_op():
    project_dict['Chart'] = {'project_name':"JFreechart", "num_bugs":26}
    project_dict['Closure'] = {'project_name':"Closure compiler", "num_bugs":133}
    project_dict['Lang'] = {'project_name':"Apache commons-lang", "num_bugs":65}
    project_dict['Math'] = {'project_name':"Apache commons-math", "num_bugs":106}
    project_dict['Mockito'] = {'project_name':"Mockito", "num_bugs":38}
    project_dict['Time'] = {'project_name':"Joda-Time", "num_bugs":27}



def main_bugger(info,proj,idBug,out_path): #[ Evo_path , evo_version , mode , out_path , budget_time , upper , lowe ,
    print "starting.."
    bug22 = Bug_4j(proj,idBug,info,out_path)
    val = bug22.get_data()
    if val == 0:
        bg.regression_testing_handler(bug22)
    else:
        print "Error val={0} in project {2} BUG {1}".format(val,idBug,proj)
def main_wrapper():
    args = pars_parms()
    args = ["","Math", 'A', str(os.getcwd() + '/') + "csv/Most_out_files.csv"
        ,'/home/eran/Desktop/defect4j_exmple/out/', "evosuite-1.0.5.jar", "/home/eran/programs/EVOSUITE/jar/", '100','30', '180']
    proj_name = args[1]
    path_original = copy.deepcopy(args[4])
    num_of_bugs = project_dict[proj_name]["num_bugs"]
    for i in range(92,num_of_bugs):
        localtime = time.asctime(time.localtime(time.time()))
        localtime = str(localtime).replace(":","_")
        dir_name = "P_{0}_B_{1}_{2}".format(proj_name,str(i) ,str(localtime) )
        full_dis = bg.mkdir_Os( path_original , dir_name)
        if full_dis == 'null':
            print('cant make dir')
            exit(1)
        main_bugger(args,proj_name,i,full_dis)


def pars_parms():
    if len(sys.argv) != 10 :
        print "[ project_name ,mode, csv_path, out_path, Evo_Version, Evo_path, upper, lower ,budget_time]"
        return []
    args = sys.argv
    return args


if __name__ == "__main__":
    before_op()
    main_wrapper()