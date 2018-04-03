import os, copy, csv
import sys, time
import subprocess
import shutil
import pit_render_test as pt
from contextlib import contextmanager
import budget_generation as bg
import fail_cleaner as fc

project_dict = {}
root_dir = '~/'


class Bug_4j:
    # b_mod = 'class' / 'package' , to kill the bug
    def __init__(self, pro_name, bug_id, info_args, root_dir,
                 defect4j_root="/home/ise/programs/defects4j/framework/bin/defects4j"
                 , csv_path='/home/ise/eran/repo/ATG/csv/Most_out_files.csv', b_mod='class'):
        os.system('export PATH=$PATH:/home/ise/programs/defects4j/framework/bin')
        self.root = root_dir
        self.p_name = pro_name
        self.id = bug_id
        self.k_budget = None
        self.mod = b_mod
        self.fp_dico = None
        self.info = info_args
        self.defects4j = defect4j_root
        self.csvFP = csv_path
        self.modified_class = []
        self.infected_packages = []
        self.contractor()

    def isValid(self):
        total_bugs = project_dict[self.p_name]['num_bugs']
        if self.id > total_bugs or self.id < 1:
            m_error = 'Error in ID number bug {0} in project:{1} the range is 1 - {2}'.format(self.id, self.p_name,
                                                                                              total_bugs)
            raise Exception(m_error)
        return True

    def get_data(self):
        self.check_out_data('f')
        self.check_out_data('b')
        self.rm_all_test(self.root)
        sig = self.compile_data_maven()
        return sig

    def rm_all_test(self, path):
        dirs = ['buggy', 'fixed']
        for d in dirs:
            rel_p = 'src/test/org'
            rel_p_only_test = 'src/test'
            dir_org = '{}{}/{}'.format(path, d, rel_p)
            dir_test = '{}{}/{}'.format(path, d, rel_p_only_test)
            if os.path.isdir(dir_org):
                os.system('rm -r {}'.format(dir_org))
            elif os.path.isdir(dir_test):
                os.system('rm -r {}/* '.format(dir_test))
            else:
                print "[Error] no Test dir : {}".format(dir_test)

    def correspond_package(self):
        for klass in self.modified_class:
            arr_pac = str(klass).split(".")
            arr_pac = arr_pac[:-1]
            str1_pac = '.'.join(str(e) for e in arr_pac)
            self.infected_packages.append(str1_pac)

    def evo_testing(self):
        print "preparing test suite ..."
        bg.regression_testing(self)

    def init_shell_script(self, command):
        print "-----command=" + command + "--------------"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        process.wait()
        return process.returncode

    def compile_data_maven(self):
        self.modfiy_pom()
        print "compiling..."
        path_p = '{}fixed'.format(self.root)
        self.add_main_dir_src(path_p)
        os.chdir(path_p)
        os.system('mkdir log_dir')
        sig_f = self.init_shell_script('mvn install >> log_dir/mvn_install_command.txt 2>&1')
        path_p = '{}buggy'.format(self.root)
        self.add_main_dir_src(path_p)
        os.chdir(path_p)
        os.system('mkdir log_dir')
        sig_b = self.init_shell_script('mvn install >> log_dir/mvn_install_command.txt 2>&1')
        if sig_b == 1:
            return 1
        elif sig_f == 1:
            return -1
        return 0

    def compile_data(self):
        if self.p_name == 'Math':
            print "compile fixed version..."
            relative_path = "bash_scripts/ant_compile.sh"
            command_str = relative_path + " " + self.root + "fixed"
            sig_f = self.init_shell_script(command_str)
            command_str = relative_path + " " + self.root + "buggy"
            sig_b = self.init_shell_script(command_str)
            if sig_b == 1 or sig_f == 1:
                return 1
            return 0

    def check_out_data(self, var='f'):
        print "checking out version..."
        if var == 'f':
            str_command = self.defects4j + ' checkout -p {1} -v {0}"{3}" -w {2}fixed/'.format(self.id, self.p_name,
                                                                                              self.root, var)
        elif var == 'b':
            str_command = self.defects4j + ' checkout -p {1} -v {0}"{3}" -w {2}buggy/'.format(self.id, self.p_name,
                                                                                              self.root, var)
        else:
            raise Exception("input to the method can be either 'f' or 'b' ")
        x = os.system(str_command)
        if x == 0:
            return True
        print "[Error] in the check out:\n " + str_command + "\n -----------------------"
        return False

    def contractor(self):
        if self.root[-1] != '/':
            self.root = self.root + "/"
        if os.path.isdir(self.root) == False:
            raise Exception("cant find the path {0}".format(self.root))
        dir_d4j = ["fixed", "buggy"]
        # dir_d4j = [] #--------Remove---
        for item in dir_d4j:
            if os.path.isdir(self.root + item):
                shutil.rmtree(self.root + item)
            os.mkdir(self.root + item)
        self.extract_data()
        self.correspond_package()
        self.info[4] = self.root

    def add_main_dir_src(self,path_project):
        '''
        if in the src there is no main dir for the src java add one
        '''
        if path_project[-1]=='/':
            path_project=path_project[:-1]
        if os.path.isdir("{}/src/main".format(path_project)):
            return
        else:
            if os.path.isdir("{}/src/java".format(path_project)):
                os.system("mkdir {}/src/main".format(path_project))
                os.system("mv {}/src/java/ {}/src/main/".format(path_project,path_project))
        return

    def extract_data(self):
        if self.isValid():
            str_c = "/home/ise/programs/defects4j/framework/bin/defects4j info -p  {1} -b {0}".format(self.id,
                                                                                                      self.p_name)
            print str_c
            result = subprocess.check_output(str_c, shell=True)
            x = result.find("List of modified sources:")
            # print result
            # print "val = ", result[x+len("List of modified sources:"):-81]
            y = result[x + len("List of modified sources:"):].replace("-", "").replace(" ", "").split('\n')
            for y1 in y:
                if len(y1) > 1:
                    print y1
                    self.modified_class.append(y1)
            print "______modified_class_______"
            for item in self.modified_class:
                print item

    def modfiy_pom(self):
        bugg_path = "{}buggy".format(self.root)
        fixed_path = "{}fixed".format(self.root)
        if os.path.isfile("{}/pom.xml".format(bugg_path)):
            os.system('rm {}'.format("{}/pom.xml".format(bugg_path)))
            os.system('cp /home/ise/eran/repo/ATG/D4J/pom.xml {}'.format(bugg_path))
        if os.path.isfile("{}/pom.xml".format(fixed_path)):
            os.system('rm {}'.format("{}/pom.xml".format(fixed_path)))
            os.system('cp /home/ise/eran/repo/ATG/D4J/pom.xml {}'.format(fixed_path))

    def analysis_test(self, dir='buggy', dir_out='results'):  # TODO:hendel the folder with the different time budgets
        print ""
        res_path = pt.mkdir_system(self.root, dir_out, False)

        if os.path.isdir('{}/Evo_Test'.format(self.root)) is False:
            print "No dir Evo_Test {}".format(self.root)
            exit(-1)
        evo_test_dir = pt.walk('{}Evo_Test'.format(self.root), 'exp', False)
        path_dir = "{}{}/src/test/".format(self.root, dir)
        project_dir = "{}{}/".format(self.root, dir)
        command_rm = "rm -r {}src/test/*".format(project_dir)
        if len(os.listdir("{}src/test/".format(project_dir))):
            os.system(command_rm)
        pt.mkdir_system('{}src/test/'.format(project_dir), 'java')
        for test_dir in evo_test_dir:
            arr_path = str(test_dir).split('/')[-1]
            name_arr = str(arr_path).split('_')
            name = "Res_{}_{}_{}_".format(name_arr[0], name_arr[-2], name_arr[-1])
            command_cp = 'cp -r {}/org {}src/test/java/'.format(test_dir, project_dir)
            os.system(command_cp)
            os.chdir(project_dir)
            if dir == 'fixed':
                fc.cleaning(project_dir)
                command_rm = "rm -r {}/org/".format(test_dir)
                os.system(command_rm)
                command_mv = "mv {}src/test/java/org/ {}/".format(project_dir, test_dir)
                os.system(command_mv)
                continue
            os.system('mvn clean test')
            os.system('mv {}target/surefire-reports {}{}/{}'.format(project_dir, self.root, dir_out, name))
            command_rm = "rm -r {}src/test/java/*".format(project_dir)
            os.system(command_rm)

    def clean_flaky_test(self):
        self.analysis_test(dir='fixed', dir_out='flaky')

    def get_fp_budget(self, b_per_class):
        list_packages = self.infected_packages
        dico, project_allocation = cal_fp_allocation_budget(list_packages, self.csvFP,
                                                            "{}fixed/target/classes/org/".format(self.root),
                                                            b_per_class)
        root_cur = self.root
        if root_cur[-1] != '/':
            root_cur = root_cur + '/'
        with open('{}{}_b={}_.csv'.format(self.root, 'FP_Allocation', b_per_class), 'w') as f:
            f.write('{0},{1},{2}\n'.format('class', 'probability_fp', 'time_budget'))
            [f.write('{0},{1},{2}\n'.format(key, value[0], value[1])) for key, value in project_allocation.items()]
        self.fp_dico = dico


def before_op():
    project_dict['Chart'] = {'project_name': "JFreechart", "num_bugs": 26}
    project_dict['Closure'] = {'project_name': "Closure compiler", "num_bugs": 133}
    project_dict['Lang'] = {'project_name': "Apache commons-lang", "num_bugs": 65}
    project_dict['Math'] = {'project_name': "Apache commons-math", "num_bugs": 106}
    project_dict['Mockito'] = {'project_name': "Mockito", "num_bugs": 38}
    project_dict['Time'] = {'project_name': "Joda-Time", "num_bugs": 27}


def main_bugger(info, proj, idBug,
                out_path):  # [ Evo_path , evo_version , mode , out_path , budget_time , upper , lowe ,
    print "starting.."
    time_budget = [2]  # 10 , 5, 1
    bug22 = Bug_4j(proj, idBug, info, out_path)
    val = bug22.get_data()
    if val == 0:
        for time in time_budget:
            bug22.k_budget = time
            bug22.get_fp_budget(time)
            bg.Defect4J_analysis(bug22)
        bug22.clean_flaky_test()
        bug22.analysis_test()
    else:
        print "Error val={0} in project {2} BUG {1}".format(val, idBug, proj)


def main_wrapper():
    args = pars_parms()
    args = ["", "Math", 'A', str(os.getcwd() + '/') + "csv/Most_out_files.csv"
        , '/home/ise/Desktop/defect4j_exmple/out/', "evosuite-1.0.5.jar", "/home/ise/eran/evosuite/jar", '10', '1',
            '100']
    proj_name = args[1]
    path_original = copy.deepcopy(args[4])
    num_of_bugs = project_dict[proj_name]["num_bugs"]
    project_counter = 0
    max = 400
    start_index = 1
    for i in range(start_index, num_of_bugs):
        if project_counter > max:
            break
        project_counter += 1
        print "*" * 50
        print "project:{} | i={} ".format(proj_name, i)
        print "*" * 50
        localtime = time.asctime(time.localtime(time.time()))
        localtime = str(localtime).replace(":", "_")
        dir_name = "P_{0}_B_{1}_{2}".format(proj_name, str(i), str(localtime))
        full_dis = bg.mkdir_Os(path_original, dir_name)
        if full_dis == 'null':
            print('cant make dir')
            exit(1)
        main_bugger(args, proj_name, i, full_dis)



def pars_parms():
    if len(sys.argv) != 10:
        print "[ project_name ,mode, csv_path, out_path, Evo_Version, Evo_path, upper, lower ,budget_time]"
        return []
    args = sys.argv
    return args


def mereg_dicos(dico, list_klass, delimiter='org'):
    '''
    Make sure that the FP dict is contains only class with in the project.
    '''
    ctr_in = 0
    new_d = {}
    for klass in list_klass:
        xs = str(klass).split('/')
        indexes = [i for i, x in enumerate(xs) if x == delimiter]
        if len(indexes) == 0:
            raise Exception('cant find the delimiter in the path: \n {} \n deli={}'.format(klass, delimiter))
        xs = xs[indexes[-1]:]
        klass_i = '.'.join(xs)
        klass_i = klass_i[:-6]  # to remove the .class from the prefix packages
        if klass_i in dico:
            new_d[klass_i] = dico[klass_i]
            ctr_in += 1
        else:
            print klass_i
    print "merg {} classes out of {}".format(ctr_in, len(list_klass))
    return new_d


def cal_fp_allocation_budget(package_name_list, FP_csv_path, root_classes, t_budget):
    all_classes = pt.walk(root_classes, '.class')
    if os.path.isdir("{}apache/commons/math3".format(root_classes)):
        bol_math3 = True
    else:
        bol_math3 = False
    dict_fp = csv_to_dict(FP_csv_path, math3=bol_math3)
    mereg_dicos(dict_fp, all_classes)
    dico, d_project_fp = allocate_time_FP(dict_fp, time_per_k=t_budget)
    res_dico = {}
    for key_i in dico.keys():
        for package_name in package_name_list:
            if str(key_i).lower().startswith(str(package_name).lower()):
                res_dico[key_i] = dico[key_i]
    return res_dico, d_project_fp


def allocate_time_FP(dico, time_per_k, upper=120, lower=1):
    total_sum_predection = sum(dico.values())
    for k in dico.keys():
        dico[k] = dico[k] / total_sum_predection
    size_set_classes = len(dico.keys())
    print "dico size=", size_set_classes
    Total = size_set_classes * time_per_k
    print "Total=", Total
    LB = size_set_classes * lower
    print "LB=", LB
    budget_time = Total - LB
    d_fin = {}
    not_max = {}
    for k in dico.keys():
        d_fin[k] = [dico[k], lower]
        not_max[k] = dico[k]
    lower_b = lower
    while (budget_time > 0 or len(not_max.keys()) == 0):
        left_over = budget_time
        for entry in not_max.keys():
            time_b = (not_max[entry] * budget_time)
            if float(time_b) + d_fin[entry][1] > float(upper):
                time_b = upper - d_fin[entry][1]
                d_fin[entry][1] += time_b
                del not_max[entry]
            else:
                d_fin[entry][1] += time_b
            left_over = left_over - time_b
        budget_time = left_over
        total_sum_predection = sum(not_max.values())
        if total_sum_predection == 0:
            break
        for k in not_max.keys():
            not_max[k] = not_max[k] / total_sum_predection
    if len(dico) != len(d_fin):
        raise Exception("in function (allocate_time_FP) the dico and d_fin is not in the same size")
    for k in dico:
        dico[k] = d_fin[k][1]
    return dico, d_fin


def csv_to_dict(path, key_name='FileName', val_name='prediction', delimiter='org', prefix_str='src\\main\\java\\',
                filter_out='package-info', math3=True):
    dico = {}
    with open(path) as csvfile:
        reader1 = csv.DictReader(csvfile)
        for row in reader1:
            val_i = row[val_name]
            key_i = row[key_name]

            if str(key_i).startswith(prefix_str) is False:
                continue
            # key_i= key_i.replace('\\','.')
            xs = str(key_i).split('\\')
            indexes = [i for i, x in enumerate(xs) if x == delimiter]
            if len(indexes) == 0:
                raise Exception(
                    'cant find the delimiter in the path: \n {} \n deli={}'.format(row[key_name], delimiter))
            xs = xs[indexes[-1]:]
            key_i = '.'.join(xs)
            key_i = key_i[:-5]  # to remove the .java from the prefix packages
            if str(key_i).__contains__(filter_out):
                continue
            if math3 is False:
                key_i = str(key_i).replace('math3',
                                           'math')  # TODO: FIX IT # because the fp is on common math 3+ need to remove the math3. form the prefix paac
            dico[key_i] = float(val_i)
    return dico


if __name__ == "__main__":
    before_op()
    main_wrapper()
