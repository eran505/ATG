import os, copy, csv, xml
import sys, time
import subprocess
import pandas as pd
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
                 , csv_path='/home/ise/eran/repo/ATG/csv/Most_out_files.csv', b_mod='package', it=1):
        self.root = root_dir
        self.p_name = pro_name
        self.id = bug_id
        self.bug_date = ''
        self.k_budget = None
        self.mod = info_args[-1]  # package // class
        self.fp_dico = None
        self.iteration = it
        self.info = info_args
        self.defects4j = defect4j_root
        self.csvFP = csv_path
        self.modified_class = []
        self.infected_packages = []
        self.clean_flaky = info_args[-2]
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
        self.infected_packages = list(set(self.infected_packages))

    def evo_testing(self):
        print "preparing test suite ..."
        bg.regression_testing(self)

    def init_shell_script(self, command):
        print "-----command=" + command + "--------------"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        process.wait()
        return process.returncode

    def compile_data_maven(self):
        # TODO : modfiy pom by project name
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
        self.info[2] = self.root

    def add_main_dir_src(self, path_project):
        '''
        if in the src there is no main dir for the src java add one
        '''
        if path_project[-1] == '/':
            path_project = path_project[:-1]
        if os.path.isdir("{}/src/main".format(path_project)):
            return
        else:
            if os.path.isdir("{}/src/java".format(path_project)):
                os.system("mkdir {}/src/main".format(path_project))
                os.system("mv {}/src/java/ {}/src/main/".format(path_project, path_project))
        return

    def extract_data(self):
        if self.isValid():
            str_c = "/home/ise/programs/defects4j/framework/bin/defects4j info -p  {1} -b {0}".format(self.id,
                                                                                                      self.p_name)
            print str_c
            result = subprocess.check_output(str_c, shell=True)
            x = result.find("List of modified sources:")
            date_index = result.find("Revision date (fixed version):")
            stoper = result.find("Root cause in triggering tests")

            data_time = result[date_index + len("Revision date (fixed version):"):stoper].replace('-', "")
            data_time = data_time.replace('\n', "").split()[0]
            year = data_time[:4]
            month = data_time[4:6]
            day = data_time[-2:]
            str_data_bug = "{}_{}_{}".format(year, month, day)
            # for Debug ----------------------------------------------------------------
            with open("/home/ise/Desktop/time_d4j.txt", "a") as myfile:
                myfile.write('\n')
                myfile.write(str_data_bug)
            print 'date : %s' % str_data_bug
            # for Debug -----------------------------------------------------------------
            y = result[x + len("List of modified sources:"):].replace("-", "").replace(" ", "").split('\n')
            for y1 in y:
                if len(y1) > 1:
                    print y1
                    self.modified_class.append(y1)
            print "______modified_class_______"
            for item in self.modified_class:
                print item
            self.bug_date = str_data_bug

    def modfiy_pom(self):
        if self.p_name == 'Lang':
            return
        bugg_path = "{}buggy".format(self.root)
        fixed_path = "{}fixed".format(self.root)
        if os.path.isfile("{}/pom.xml".format(bugg_path)):
            os.system('rm {}'.format("{}/pom.xml".format(bugg_path)))
            if self.p_name == 'Math':
                os.system('cp /home/ise/eran/repo/ATG/D4J/math/pom.xml {}'.format(bugg_path))
            elif self.p_name =='Lang':
                os.system('cp /home/ise/eran/repo/ATG/D4J/lang/pom.xml {}'.format(bugg_path))
        if os.path.isfile("{}/pom.xml".format(fixed_path)):
            os.system('rm {}'.format("{}/pom.xml".format(fixed_path)))
            if self.p_name == 'Math':
                os.system('cp /home/ise/eran/repo/ATG/D4J/math/pom.xml {}'.format(fixed_path))
            elif self.p_name == 'Lang':
                os.system('cp /home/ise/eran/repo/ATG/D4J/lang/pom.xml {}'.format(fixed_path))


    def analysis_test(self, dir='buggy', dir_out='results'):  # TODO:hendel the folder with the different time budgets
        print ""
        res_path = pt.mkdir_system(self.root, dir_out, False)

        if os.path.isdir('{}/Evo_Test'.format(self.root)) is False:
            err_str = "[Error] No dir Evo_Test {}".format(self.root)
            raise Exception(err_str)
        evo_test_dir = pt.walk('{}Evo_Test'.format(self.root), 'exp', False)
        path_dir = "{}{}/src/test/".format(self.root, dir)
        project_dir = "{}{}/".format(self.root, dir)
        command_rm = "rm -r {}src/test/*".format(project_dir)
        if len(os.listdir("{}src/test/".format(project_dir))):
            os.system(command_rm)
        pt.mkdir_system('{}src/test/'.format(project_dir), 'java')
        for test_dir in evo_test_dir:
            arr_path = str(test_dir).split('/')[-1]
            java_name = str(test_dir).split('/')[-2]
            name_arr = str(arr_path).split('_')
            dir_name_test = "{}_{}_{}".format(name_arr[0], name_arr[-2], name_arr[-1])

            name = "{}_{}".format(java_name ,dir_name_test)
            command_cp = 'cp -r {}/org {}src/test/java/'.format(test_dir, project_dir)
            os.system(command_cp)
            os.chdir(project_dir)
            if dir == 'fixed':
                fc.cleaning(project_dir, dir_name_test)
                command_rm = "rm -r {}/org/".format(test_dir)
                os.system(command_rm)
                command_mv = "mv {}src/test/java/org/ {}/".format(project_dir, test_dir)
                os.system(command_mv)
                continue
            os.system('mvn clean test')
            if os.path.isdir('{}{}/{}'.format(self.root, dir_out, name)) is False:
                os.system('mkdir {}{}/{}'.format(self.root, dir_out, name))
            os.system('mv {}target/surefire-reports/* {}{}/{}'.format(project_dir, self.root, dir_out, name))
            command_rm = "rm -r {}src/test/java/*".format(project_dir)
            os.system(command_rm)

    def clean_flaky_test(self):
        self.analysis_test(dir='fixed', dir_out='flaky')

    def get_the_prediction_csv(self):
        """
        This function look for the most proper csv file for the prediction task in the FP
        :return: The right csv for the project, path to csv
        """
        print "in get the csv !!!"
        d = {}
        lower_case_project_name = str(self.p_name).lower()
        csv_paths = "/home/ise/eran/repo/ATG/D4J/csvs/{}".format(lower_case_project_name)
        list_csv = pt.walk_rec(csv_paths, [], '.csv')
        for csv_item in list_csv:
            if len(str(csv_item)) > 10:
                name = csv_item[-9:]
                name = str(name[:-4]).split('_')
                date_i = name[1] + name[0]
                num_date, bol = _intTryParse(date_i)
                if bol:
                    d[num_date] = csv_item
                else:
                    raise Exception('[Error] cant pars the date in the csv files in ATG')
            else:
                print "[Error] in parsing the csv date {}".format(csv_item)

        arr_date = self.bug_date.split('_')
        num_date = arr_date[0][-2:] + arr_date[1]
        num_date, bol = _intTryParse(num_date)
        if bol is False:
            raise Exception('[Error] cant parse the date bug !!! {}'.format(self.bug_date))
        csv_path_name = self.get_min_csv(d, num_date)
        print "{} : {}".format(self.p_name, self.bug_date)
        self.csvFP = csv_path_name
        return csv_path_name

    def get_min_csv(self, d, num):
        min_val = None
        min_number = float('-inf')
        for x in d.keys():
            if x - num <= 0 and x - num > min_number:
                min_number = x - num
                min_val = d[x]
        return min_val

    def get_fp_budget(self, b_per_class):
        list_packages = self.infected_packages
        dico, project_allocation = self.cal_fp_allocation_budget(list_packages, self.csvFP,
                                                                 "{}fixed/target/classes/org/".format(self.root),
                                                                 b_per_class)
        if dico is None:
            return None
        root_cur = self.root
        if root_cur[-1] != '/':
            root_cur = root_cur + '/'
        with open('{}{}_budget={}_.csv'.format(self.root, 'FP_Allocation', b_per_class), 'w') as f:
            f.write('{0},{1},{2}\n'.format('class', 'probability_fp', 'time_budget'))
            [f.write('{0},{1},{2}\n'.format(key, value[0], value[1])) for key, value in project_allocation.items()]
        with open('{}{}_package_b={}.csv'.format(self.root, 'FP_Allocation', b_per_class), 'w') as f:
            f.write('{0},{1}\n'.format('class', 'time_budget'))
            [f.write('{0},{1}\n'.format(key, value)) for key, value in dico.items()]
        self.fp_dico = dico
        return 'good'

    def remove_unknown_classes(self, dico):
        print ""
        unknow_klasses_path = "{}log/missing_pred_class.txt".format(self.root)
        target = []
        print unknow_klasses_path
        with open(unknow_klasses_path, 'r') as file_unknown:
            target = file_unknown.readlines()
        if len(target) == 0:
            return None
        for klass in target:
            if len(str(klass)) < 4:
                continue
            class_ky = str(klass).split(' ')[0]
            pack = '.'.join(str(klass).split(' ')[0].split('.')[:-1])
            if pack in self.infected_packages:
                return 'package'
            if klass in self.modified_class:
                return 'class'
            if class_ky in dico:
                try:
                    del dico[class_ky]
                except KeyError:
                    with open("{}log/err_del.txt".format(self.root), 'w+') as f:
                        f.write('{} -- in the fp dico but error while del in proj: {} '.format(class_ky, self.p_name))
        return None

    def gen_test_copy(self, param):
        os.system('cp -r {} {} '.format(param, self.root))

    def cal_fp_allocation_budget(self, package_name_list, FP_csv_path, root_classes, t_budget):
        all_classes = pt.walk(root_classes, '.class')
        if os.path.isdir("{}apache/commons/math3".format(root_classes)):
            bol_math3 = True
        else:
            bol_math3 = False
        dict_fp = csv_to_dict(FP_csv_path, math3=bol_math3)
        self.mereg_dicos(dict_fp, all_classes, FP_csv_path)
        res = self.remove_unknown_classes(dict_fp)
        if res != None:
            with open("{}log/err_del.txt".format(self.root), 'a') as f:
                f.write('{} - problem with missing pred class'.format(res))
                return None,None
        dico, d_project_fp = allocate_time_FP(dict_fp, time_per_k=t_budget)
        res_dico = {}
        for key_i in dico.keys():
            for package_name in package_name_list:
                if str(key_i).lower().startswith(str(package_name).lower()):
                    res_dico[key_i] = dico[key_i]
        return res_dico, d_project_fp

    def mereg_dicos(self, dico, list_klass, csv_path, delimiter='org'):
        """
        Make sure that the FP dict is contains only class with in the project.
        the unknown var is the prediction of unknown class we give it a small prediction for being fault
        """
        proj_name = str(csv_path).split('/')[-2]
        ctr_in = 0
        memort_csvs = None
        ctr_unknow = 0
        unknown = 0.00001
        new_d = {}
        before_size = len(list_klass)

        list_klass = [x for x in list_klass if str(x).__contains__('$') is False]
        print "class with $ : {}".format(before_size - len(list_klass))
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
                if memort_csvs is None:
                    ans, memort_csvs = look_for_old_pred(klass_i, csv_path, proj_name)
                else:
                    ans, memort_csvs = look_for_old_pred(klass_i, csv_path, proj_name, memort_csvs)
                print ans
                if ans is None:
                    self.write_log("{} / {}".format(klass_i, len(list_klass)))
                    continue
                new_d[klass_i] = ans
                ctr_unknow += 1
        print "merg {} classes out of {}".format(ctr_in, len(list_klass))
        print "unknown class = {} / {}".format(ctr_unknow, len(list_klass))
        self.write_log('EOF')
        return new_d

    def write_log(self, info,name='missing_pred_class'):
        '''
        write to log dir
        :param info:
        :return:
        '''
        dir_p = pt.mkdir_system(self.root, 'log', False)
        with open("{}/{}".format(dir_p, '{}.txt'.format(name)), 'a') as f:
            f.write(info)
            f.write('\n')


def before_op():
    project_dict['Chart'] = {'project_name': "JFreechart", "num_bugs": 26}
    project_dict['Closure'] = {'project_name': "Closure compiler", "num_bugs": 133}
    project_dict['Lang'] = {'project_name': "Apache commons-lang", "num_bugs": 65}
    project_dict['Math'] = {'project_name': "Apache commons-math", "num_bugs": 106}
    project_dict['Mockito'] = {'project_name': "Mockito", "num_bugs": 38}
    project_dict['Time'] = {'project_name': "Joda-Time", "num_bugs": 27}


def get_time_budget(arr_string):
    """
    :param arr_string: string that representing the diff time budget e.g. 10;44;100
    :return: list of int
    """
    arr = str(arr_string).split(';')
    time_budget_arr = []
    for x in arr:
        val, bol = _intTryParse(x)
        if bol:
            time_budget_arr.append(val)
    return time_budget_arr




def main_bugger(info, proj, idBug, out_path):
    print "starting.."
    time_budget = get_time_budget(info[5])
    bug22 = Bug_4j(proj, idBug, info, out_path)
    return
    val = bug22.get_data()
    if val == 0:
        for time in time_budget:
            bug22.k_budget = time
            out = bug22.get_the_prediction_csv()
            if out is None:
                bug22.write_log('DATE: {} , cant find a predction csv : ID:{} P:{} '.format(bug22.bug_date, idBug, proj),'error')
                return
            out = bug22.get_fp_budget(time)
            # out indicate that all process pass with a good results and we can move for Gen Test with Evosuite
            if out is None:
                with open(bug22.root+'log/error.txt0','a') as f:
                    f.write("[Error] val={0} in project {2} BUG {1}".format(val, idBug, proj))
                print "[Error]  in project {2} BUG {1}".format(val, idBug, proj)
                return
            # bug22.gen_test_copy(path_evo_dir_test) # for debugging
            bg.Defect4J_analysis(bug22)
        if bug22.clean_flaky:
            bug22.clean_flaky_test()
        bug22.analysis_test()
    else:
        print "Error val={0} in project {2} BUG {1}".format(val, idBug, proj)


def main_wrapper():
    '''
    1. project name
    2.
    :return:
    '''
    args = pars_parms()
    print args
    if len(args) == 0:
        args = ["", "Lang", '/home/ise/Desktop/defect4j_exmple/out/',
            "evosuite-1.0.5.jar", "/home/ise/eran/evosuite/jar/", '30', '1',
            '100', True, 'class']  # package / class
    proj_name = args[1]
    path_original = copy.deepcopy(args[2])
    num_of_bugs = project_dict[proj_name]["num_bugs"]
    project_counter = 0
    max = 400
    start_index = 30
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
    if len(sys.argv) < 3:
        print "printing usage:\n"
        print "[project_name, out_path, Evo_Version, Evo_path, budget_time_arr ,upper, lower, clean_flaky_test]"
        print "\n-----info-----\nbudget_time_arr: separation by ; e.g. 2;3;10"
        print "clean_flaky_test: clean the failing tests on the fix version (True/False)"
        return []
    args = sys.argv
    return args


def look_for_old_pred(class_name, cur_csv, proj_name, mem=None):
    ans = {}
    if mem is not None:
        d_csv = mem
    else:
        d_csv = {}
        list_csv = pt.walk_rec('/home/ise/eran/repo/ATG/D4J/csvs/{}/'.format(proj_name), [], '.csv')
        for csv_item in list_csv:
            d_dico = csv_to_dict(csv_item)
            d_csv[csv_item] = d_dico
    get_date = str(cur_csv[:-4]).split('_')[-2:]
    for ky in d_csv:
        if class_name in d_csv[ky]:
            get_date_cur = str(ky[:-4]).split('_')[-2:]
            print get_date_cur, get_date
            diff = abs(int(get_date_cur[1]) - int(get_date[1]))
            ans[diff] = d_csv[ky][class_name]
    if len(ans) > 0:
        lis = sorted(ans.keys())
        res = ans[lis[0]]
    else:
        res = None
    return res, d_csv


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
    prefix_str_old_v = 'src\\java\\'  # TODO: need to fix it for all prefix !!!!
    with open(path) as csvfile:
        reader1 = csv.DictReader(csvfile)
        for row in reader1:
            val_i = row[val_name]
            key_i = row[key_name]

            if str(key_i).startswith(prefix_str) is False:
                if str(key_i).startswith(prefix_str_old_v) is False:
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
            dico[key_i] = float(val_i)
    return dico


####################################################
##################XML_parser_functions############
################################################

def wrapper_xml_test_file(list_dirz_path, name):
    """
    getting list dirs in results dir, and parsing them
    """
    name_dir_father = '_'.join(str(name).split('/')[-1].split('_')[:4])
    list_acc = []
    for dir_i in list_dirz_path:
        dir_name = str(dir_i).split('/')[-1][4:]
        files_arr = pt.walk_rec(dir_i, [], rec='.xml')
        if len(files_arr) == 0:
            print "in dir : {} no files ".format(dir_i)
        for file_i in files_arr:
            cut_name = str(file_i).split('/')[-1][5:-11]
            ans_income = pars_xml_test_file(file_i)
            ans_income['CUT'] = cut_name
            ans_income['project'] = str(name_dir_father).split('_')[1]
            ans_income['bug_ID'] = str(name_dir_father).split('_')[-1]
            ans_income['father_dir'] = name_dir_father
            time_b = str(dir_name).split('_')[1][2:]
            mode_allocation = str(dir_name).split('_')[0]
            iter_num = str(dir_name).split('_')[-1][3:]
            ans_income['time_budget'] = time_b
            ans_income['allocation_mode'] = mode_allocation
            ans_income['iteration_num'] = iter_num

            list_acc.append(ans_income)
    return list_acc


def pars_xml_test_file(path_file):
    """
    parsing the xml tree and return the results
    """
    err = {}
    failure = {}
    d = {"err": float(0), "fail": float(0), "bug": 'no', 'class_err': [], 'class_fail': []}
    if os.path.isfile(path_file) is False:
        raise Exception("'[Error] the path: {} is not valid ".format(path_file))
    root_node = xml.etree.ElementTree.parse(path_file).getroot()
    val, bol = _intTryParse(root_node.attrib['errors'])
    if bol is False:
        print "[Error] cant parse the xml file error val input : {}".format(path_file)
    errors_num = val
    val, bol = _intTryParse(root_node.attrib['failures'])
    if bol is False:
        print "[Error] cant parse the xml file failures val input : {}".format(path_file)
    failures_num = val
    if failures_num or errors_num > 0:
        d['bug'] = 'yes'
        for elt in root_node.iter():
            if elt.tag == 'testcase':
                if len(elt._children) > 0:
                    for msg in elt:
                        if msg.tag == 'error':
                            class_name = elt.attrib['classname']
                            test_case_number = elt.attrib['name']
                            d['class_err'].append("{}_{}".format(class_name, test_case_number))
                            d['err'] = d['err'] + 1
                        elif msg.tag == 'failure':
                            class_name = elt.attrib['classname']
                            test_case_number = elt.attrib['name']
                            d['class_fail'].append("{}_{}".format(class_name, test_case_number))
                            d['fail'] = d['fail'] + 1
    return d


def _intTryParse(value):
    try:
        return int(value), True
    except ValueError:
        return value, False


def analysis_dir(path_root_dir):
    """
    going over all the dirs and getting all the results form the bugs_dir
    """
    out_df_path = '/'.join(path_root_dir.split('/')[:-1])
    if os.path.isdir(path_root_dir) is False:
        str_err = "[Error ]{} is not a dir ".format(path_root_dir)
        raise Exception(str_err)
    all_dirz = pt.walk_rec(path_root_dir, [], rec='P_', file_t=False, lv=-2)
    if len(all_dirz) == 0:
        str_err = "no dirs to analysis found in path: {}".format(path_root_dir)
        print str_err
        exit(0)
    list_dir_empty = []
    list_no_dir = []
    dict_dir = {}
    for dir_item in all_dirz:
        if dir_item[-1] == '/':
            dir_item = dir_item[:-1]
        if os.path.isdir("{}/results".format(dir_item)):
            res_files = pt.walk_rec("{}/results".format(dir_item), [], rec='Res', file_t=False)
            if len(res_files) == 0:
                list_dir_empty.append(dir_item)
            else:
                dict_dir[dir_item] = res_files
        else:
            list_no_dir.append(dir_item)
    list_dico_data = []
    for ky_dir in dict_dir.keys():
        x = wrapper_xml_test_file(dict_dir[ky_dir], ky_dir)
        list_dico_data.extend(x)
    df = pd.DataFrame(list_dico_data)
    if path_root_dir[-1] != '/':
        df.to_csv('{}/out.csv'.format(out_df_path))
    else:
        df.to_csv('{}out.csv'.format(out_df_path))
    print "Done !"


if __name__ == "__main__":
    path_test = '/home/ise/Desktop/defect4j_exmple/out'
    ########################
    # analysis_dir(path_test)
    # exit()
    ##################
    before_op()
    main_wrapper()
