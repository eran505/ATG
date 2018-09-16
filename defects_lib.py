import os, copy, csv, xml
import sys, time
import subprocess
import pandas as pd
import shutil
import pit_render_test as pt
from contextlib import contextmanager
import budget_generation as bg
import fail_cleaner as fc
import shlex
import re
from subprocess import Popen, PIPE, check_call, check_output
import util_defects4j as util_d4j
import numpy as np
from tempfile import mkstemp
from shutil import move
from os import fdopen, remove

project_dict = {}
builder_dict = {}
root_dir = '~/'


######################TODO:FIXER

def fixer_maven(dir_root):
    all_dir_time = pt.walk_rec(dir_root, [], file_t=False, rec='P_', lv=-3)
    no_test_dir = []
    for dir_bug in all_dir_time:

        print "--{}--".format(dir_bug)
        project_name = str(dir_bug).split('/')[-1].split('_')[1]
        bug_id = str(dir_bug).split('/')[-1].split('_')[3]
        time_budget = str(dir_bug).split('/')[-2].split('=')[1]
        if dir_bug[-1] != '/':
            dir_bug = '{}/'.format(dir_bug)
        dico_info = {"project": project_name, 'bug_ID': bug_id, 'time_budget': time_budget}
        if os.path.isdir('{}Evo_Test'.format(dir_bug)) is False:
            no_test_dir.append(dico_info)
            continue
        pbject_Bug = Bug_4j(pro_name=project_name, bug_id=bug_id, root_dir=dir_bug, info_args=None)
        pbject_Bug.modfiy_pom()
        pbject_Bug.rm_all_test()
        name_dir_res = 'TEST_results'
        if os.path.isdir("{}{}".format(dir_bug, name_dir_res)):
            command_rm = 'rm -r {}{}'.format(dir_bug, name_dir_res)
            print "[OS] {}".format(command_rm)
            os.system(command_rm)
        out_dir_buggy = pbject_Bug.analysis_test('buggy', dir_out=name_dir_res)
        out_dir_fixed = pbject_Bug.analysis_test('fixed', dir_out=name_dir_res)

        files_fix = pt.walk_rec(out_dir_fixed, [], '.xml')
        files_buggy = pt.walk_rec(out_dir_buggy, [], '.xml')

        d_list_fix = []
        d_list_buggy = []

        for file_i in files_fix:
            d_list_fix.append(pars_xml_test_file(file_i, dico_info))

        for file_i in files_buggy:
            d_list_buggy.append(pars_xml_test_file(file_i, dico_info))

        csv_out_dir = pt.mkdir_system(dir_bug, 'csvs', False)

        df_bug = pd.DataFrame(d_list_fix)
        df_bug.to_csv('{}/fix_TEST.csv'.format(csv_out_dir))

        df_fix = pd.DataFrame(d_list_buggy)
        df_fix.to_csv('{}/buggy_TEST.csv'.format(csv_out_dir))
        print ""
    df_no_test = pd.DataFrame(no_test_dir)
    df_no_test.to_csv('{}/no_test_gen.csv'.format(dir_root))
    exit()  # TODO:REMOVE IT !!!


#######################

class Bug_4j:
    # b_mod = 'class' / 'package' , to kill the bug
    def __init__(self, pro_name, bug_id, info_args, root_dir,
                 defect4j_root="/home/ise/programs/defects4j/framework/bin/defects4j"
                 , csv_path='/home/ise/eran/repo/ATG/csv/Most_out_files.csv',
                 b_mod='package', it=1):
        self.root = root_dir
        self.id = bug_id
        self.bug_date = ''
        self.classes_dir = None
        self.k_budget = None
        self.src_dir_change = False
        self.fp_dico = None
        self.iteration = it
        self.info = info_args
        self.defects4j = defect4j_root
        self.csvFP = csv_path
        self.modified_class = []
        self.p_name = pro_name
        self.infected_packages = []
        if info_args is not None:
            self.mod = info_args['t']  # package // class
            self.p_name = info_args['p']
            self.contractor()

    def isValid(self):
        total_bugs = project_dict[self.p_name]['num_bugs']
        if self.id > total_bugs or self.id < 1:
            m_error = 'Error in ID number bug {0} in project:{1} the range is 1 - {2}'.format(self.id, self.p_name,
                                                                                              total_bugs)
            raise Exception(m_error)
        return True

    def ant_build_pre_process(self):
        sig = 1
        self.remove_main_dir_src('{}/fixed'.format(self.root))
        self.remove_main_dir_src('{}/buggy'.format(self.root))
        if os.path.isfile('{}fixed/build.xml'.format(self.root)):
            self.replace('{}fixed/build.xml'.format(self.root),
                         '<fail if="mockito.tests.failed" message="Tests failed."/>', '<!-- eran -->')
            self.replace('{}buggy/build.xml'.format(self.root),
                         '<fail if="mockito.tests.failed" message="Tests failed."/>', '<!-- eran -->')
            sig = self.compile_data_builder('ant', 'clean compile')
            if sig == 0:
                project_dict['Mockito']['src'] = 'ant'
        return sig

    def get_data(self, builder):
        self.check_out_data('f')
        self.check_out_data('b')
        self.rm_all_test(self.root)
        sig = self.compile_data_builder(builder)
        if sig == 1:
            sig = self.ant_build_pre_process()
        return sig

    def replace(self, file_path, pattern, subst):
        # Create temp file
        fh, abs_path = mkstemp()
        with fdopen(fh, 'w') as new_file:
            with open(file_path) as old_file:
                for line in old_file:
                    new_file.write(line.replace(pattern, subst))
        # Remove original file
        remove(file_path)
        # Move new file
        move(abs_path, file_path)

    def rm_all_test(self):
        path = self.root
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
            # elif os.path.isdir():
            #    res = pt.walk_rec(path, [], 'GitHubTicketFetcherTest')
            #    for x in res:
            #        os.system('rm  {}'.format(x))
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

    def compile_data_builder(self, builder='mvn', command='install', flag=True):
        # TODO : modfiy pom by project name
        if builder == 'mvn':
            self.modfiy_pom()
        print "compiling..."
        path_p = '{}fixed'.format(self.root)
        if builder == 'mvn' and flag:
            bol_dir_fix = self.add_main_dir_src(path_p)
        os.chdir(path_p)
        if os.path.isdir('{}/log_dir'.format(path_p)) is False:
            os.system('mkdir log_dir')
        sig_f = self.init_shell_script('{0} {1} >> log_dir/{0}_install_command.txt 2>&1'.format(builder, command))
        path_p = '{}buggy'.format(self.root)
        if builder == 'mvn' and flag:
            bol_dir_buggy = self.add_main_dir_src(path_p)
        os.chdir(path_p)
        if os.path.isdir('{}/log_dir'.format(path_p)) is False:
            os.system('mkdir log_dir')
        sig_b = self.init_shell_script('{0} {1} >> log_dir/{0}_install_command.txt 2>&1'.format(builder, command))
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
        print "[OS] {}".format(str_command)
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
            pt.mkdir_system(self.root, item)
        self.extract_data()
        self.correspond_package()

    def add_main_dir_src(self, path_project):
        '''
        if in the src there is no main dir for the src java add one
        '''
        if path_project[-1] == '/':
            path_project = path_project[:-1]
        if os.path.isdir("{}/src/main".format(path_project)):
            return False
        else:
            if os.path.isdir("{}/src/java".format(path_project)):
                os.system("mkdir {}/src/main".format(path_project))
                os.system("mv {}/src/java/ {}/src/main/".format(path_project, path_project))
                self.src_dir_change = True
                return True
        return False

    def remove_main_dir_src(self, path_project):
        if path_project[-1] == '/':
            path_project = path_project[:-1]
        if os.path.isdir("{}/src/main".format(path_project)):
            os.system('mv {0}/src/main/* {0}/src/'.format(path_project))
        return

    def make_uniform_package_dict(self, delim='org', rec=False):
        d_classes = {}
        fix_class = self.root + 'fixed'
        if self.info['t'] == 'package':
            modify = self.infected_packages
        elif self.info['t'] == 'class':
            modify = self.modified_class
        elif self.info['t'] == 'project':
            modify = [delim]
        time_b = self.k_budget
        walking_res = pt.walk_rec(fix_class, [], '.class')
        res_classes = []
        print len(walking_res)
        for item in walking_res:
            prefix = str(item).split(delim)[-1]
            prefix = prefix.split('.')[0]
            prefix = prefix.replace('/', '.')
            prefix = 'org' + prefix
            if prefix.__contains__('$') is False:
                for fault_comp in modify:
                    if self.info['t'] == 'project':
                        if prefix.startswith(fault_comp):
                            res_classes.append(prefix)
                    elif self.info['t'] == 'package':
                        if prefix.startswith(fault_comp):
                            if rec is False:
                                if len(fault_comp.split('.')) + 1 == len(prefix.split('.')):
                                    res_classes.append(prefix)
                            else:
                                res_classes.append(prefix)
                    elif self.info['t'] == 'class':
                        if fault_comp == prefix:
                            res_classes.append(prefix)
        print "--res--"
        for x in res_classes:
            d_classes[x] = time_b
        self.fp_dico = d_classes
        return d_classes

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
            try:
                data_time = data_time.replace('\n', "").split()[0]
            except Exception:  # TODO: fix it by looking at the comiit id and the date !!!! <------ this fix is very importenet (id 25 mockito [bug])
                print "[EError] in Date"
                data_time = '20120101'
            year = data_time[:4]
            month = data_time[4:6]
            day = data_time[-2:]
            str_data_bug = "{}_{}_{}".format(year, month, day)
            print str_data_bug
            # for Debug ----------------------------------------------------------------
            # with open("/home/ise/Desktop/time_d4j.txt", "a") as myfile:
            #    myfile.write('\n')
            #    myfile.write(str_data_bug)
            # print 'date : %s' % str_data_bug
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
        bugg_path = "{}buggy".format(self.root)
        fixed_path = "{}fixed".format(self.root)
        if os.path.isfile("{}/pom.xml".format(bugg_path)):
            os.system('rm {}'.format("{}/pom.xml".format(bugg_path)))
        if self.p_name == 'Math':
            os.system('cp /home/ise/eran/repo/ATG/D4J/csvs/math/pom.xml {}'.format(bugg_path))
        elif self.p_name == 'Lang':
            os.system('cp /home/ise/eran/repo/ATG/D4J/csvs/lang/pom.xml {}'.format(bugg_path))
        if os.path.isfile("{}/pom.xml".format(fixed_path)):
            os.system('rm {}'.format("{}/pom.xml".format(fixed_path)))
        if self.p_name == 'Math':
            os.system('cp /home/ise/eran/repo/ATG/D4J/csvs/math/pom.xml {}'.format(fixed_path))
        elif self.p_name == 'Lang':
            os.system('cp /home/ise/eran/repo/ATG/D4J/csvs/lang/pom.xml {}'.format(fixed_path))

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
        if len(os.listdir("{}src/test/".format(project_dir))) > 0:
            os.system(command_rm)
        pt.mkdir_system('{}src/test/'.format(project_dir), 'java')
        for test_dir in evo_test_dir:
            arr_path = str(test_dir).split('/')[-1]
            java_name = str(test_dir).split('/')[-2]
            name_arr = str(arr_path).split('_')
            dir_name_test = "{}_{}_{}_{}".format(dir, name_arr[0], name_arr[-2], name_arr[-1])

            name = "{}_{}".format(java_name, dir_name_test)
            command_cp = 'cp -r {}/org {}src/test/java/'.format(test_dir, project_dir)
            os.system(command_cp)
            os.chdir(project_dir)
            os.system('mvn clean test')
            if os.path.isdir('{}{}/{}'.format(self.root, dir_out, name)) is False:
                os.system('mkdir {}{}/{}'.format(self.root, dir_out, name))
            os.system('mv {}target/surefire-reports/* {}{}/{}'.format(project_dir, self.root, dir_out, name))
            command_rm = "rm -r {}src/test/java/*".format(project_dir)
            os.system(command_rm)
            return "{}{}/{}".format(self.root, dir_out, name)

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
                date_string = str(csv_item)[:-4].split('_')[3:]
                date_string.reverse()
                if len(date_string) == 2:
                    date_string.append('00')
                date_i = ''.join(date_string)
                num_date, bol = _intTryParse(date_i)
                if bol:
                    d[num_date] = csv_item
                else:
                    raise Exception('[Error] cant pars the date in the csv files in ATG')
            else:
                print "[Error] in parsing the csv date {}".format(csv_item)

        arr_date = self.bug_date.split('_')
        arr_date[0] = arr_date[0][-2:]  # make the yeat from XXXX to XX format
        num_date = ''.join(arr_date)
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
        path_to_class = builder_dict[project_dict[self.p_name]['src']]['class_p']
        dico, project_allocation = self.cal_fp_allocation_budget(list_packages, self.csvFP,
                                                                 "{}fixed{}".format(self.root, path_to_class),
                                                                 b_per_class)
        if dico is None:
            return None
        root_cur = self.root
        if root_cur[-1] != '/':
            root_cur = root_cur + '/'
        with open('{}All_{}_budget={}_.csv'.format(self.root, 'FP_Allocation', b_per_class), 'w') as f:
            f.write('{0},{1},{2}\n'.format('class', 'probability_fp', 'time_budget'))
            [f.write('{0},{1},{2}\n'.format(key, value[0], value[1])) for key, value in project_allocation.items()]
        with open('{}Pack_{}_b={}.csv'.format(self.root, 'FP_Allocation', b_per_class), 'w') as f:
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
            # if pack in self.infected_packages:
            #    return 'package'
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
        dict_fp = csv_to_dict(FP_csv_path, project_name=self.p_name, math3=bol_math3)

        self.mereg_dicos(dict_fp, all_classes, FP_csv_path)
        res = self.remove_unknown_classes(dict_fp)
        if res != None:
            with open("{}log/err_del.txt".format(self.root), 'a') as f:
                f.write('{} @#@ problem with missing pred class'.format(res))
                f.write("\nPACKAGE:{}\nCLASS:{}\n".format(self.infected_packages, self.modified_class))
                f.close()
                return None, None
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
                ctr_unknow += 1
                if ans is None:
                    self.write_log("{} / {}".format(klass_i, len(list_klass)))
                    continue
                new_d[klass_i] = ans
        print "merg {} classes out of {}".format(ctr_in, len(list_klass))
        print "unknown class = {} / {}".format(ctr_unknow, len(list_klass))
        self.write_log('EOF')
        return new_d

    def write_log(self, info, name='missing_pred_class'):
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
    project_dict['Chart'] = {'project_name': "JFreechart", "num_bugs": 26, 'prefix': 'org'}
    project_dict['Closure'] = {'project_name': "Closure compiler", "num_bugs": 133, 'prefix': 'com'}
    project_dict['Lang'] = {'project_name': "Apache commons-lang", "num_bugs": 65, 'prefix': 'org',
                            'src': 'mvn', 'csv_prefix': ['src\\org\\', 'src\\main\\java\\']}
    project_dict['Math'] = {'project_name': "Apache commons-math", "num_bugs": 106, 'src': 'mvn', 'prefix': 'org',
                            'csv_prefix': ['src\\org\\', 'src\\main\\java\\']}
    project_dict['Mockito'] = {'project_name': "Mockito", "num_bugs": 38, 'src': 'gradle', 'prefix': 'org',
                               'csv_prefix': ['src\\org\\']}
    project_dict['Time'] = {'project_name': "Joda-Time", 'prefix': 'org', "num_bugs": 27}
    # ############### builder dict ####################33
    builder_dict['mvn'] = {'class_p': '/target/classes/org/', 'evo_p': '/target/classes/'}
    builder_dict['ant'] = {'class_p': '/target/classes/org/', 'evo_p': '/target/classes/'}
    builder_dict['gradle'] = {'class_p': '/build/classes/java/main/org/', 'evo_p': '/build/classes/java/main/'}


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


def main_bugger(info, proj, idBug, out_path, builder='mvn'):
    print "starting.."
    time_budget = get_time_budget(info['b'])
    bug22 = Bug_4j(proj, idBug, info, out_path)
    val = bug22.get_data(builder)
    print "--" * 200
    print val
    print "--" * 200
    if val == 0:
        for time in time_budget:
            bug22.k_budget = time
            bug22.classes_dir = builder_dict[project_dict[bug22.p_name]['src']]['evo_p']
            for klass in bug22.modified_class:
                bug22.write_log(str(klass), 'bug_classes')
            if info['M'] == 'U':
                bug22.make_uniform_package_dict()
                bg.Defect4J_analysis(bug22)
            else:
                out = bug22.get_the_prediction_csv()

                if out is None and bug22.info['M'] != 'U':
                    bug22.write_log(
                        'DATE: {} , cant find a predction csv : ID:{} P:{} '.format(bug22.bug_date, idBug, proj),
                        'error')
                    return
                if bug22.mod == 'info':
                    if 'z' in bug22.info:
                        list_str = bug22.info['z']
                        budget_arr = str(list_str).split(';')
                        for time_bb in budget_arr:
                            out = bug22.get_fp_budget(int(time_bb))
                else:
                    out = bug22.get_fp_budget(time)
                # out indicate that all process pass with a good results and we can move for Gen Test with Evosuite
                if out is None and bug22.info['M'] != 'U':
                    with open(bug22.root + 'log/error.txt', 'a') as f:
                        f.write("[Error] val={0} in project {2} BUG {1}".format(val, idBug, proj))
                        f.write('\ncsv :{}\ndate_bug:{}\n'.format(out, bug22.bug_date))
                    print "[Error]  in project {2} BUG {1}".format(val, idBug, proj)
                    return
                if bug22.mod == 'info':
                    return

        # if bug22.p_name != 'Mockito':
        # if bug22.clean_flaky:
        # bug22.clean_flaky_test()
        # bug22.analysis_test()
    else:
        msg_err = "Error val={0} in project {2} BUG {1}".format(val, idBug, proj)
        bug22.write_log(msg_err, 'error_compile')
        print msg_err


def pars_ids(ids_str, num_of_bugs):
    if str(ids_str).__contains__('-'):
        lower_bug_id = int(str(ids_str).split('-')[0])
        upper_bug_id = int(str(ids_str).split('-')[1])
    else:
        lower_bug_id = int(str(ids_str))
        upper_bug_id = int(str(ids_str))
    if int(upper_bug_id) > int(num_of_bugs):
        upper_bug_id = int(num_of_bugs)
    if lower_bug_id > upper_bug_id:
        lower_bug_id = upper_bug_id
    return lower_bug_id, upper_bug_id


def main_wrapper(args=None):
    '''
    1. project name
    2.
    :return:
    '''
    if args is None:
        args = sys.argv
        dico_info = parser_args(args)
    else:
        dico_info = parser_args(args.split())
    if 'F' in dico_info:
        if args == sys.argv:
            fix_wrapper()
        else:
            fix_wrapper(args)
        return
    proj_name = dico_info['p']
    path_original = dico_info['o']
    if path_original[-1] != '/':
        path_original = "{}/".format(path_original)
    num_of_bugs = project_dict[proj_name]["num_bugs"]
    if 'r' in dico_info:
        low_id, up_id = pars_ids(dico_info['r'], num_of_bugs)
    if up_id > num_of_bugs:
        up_id = num_of_bugs
        if low_id > up_id:
            low_id = up_id
    for i in range(low_id, up_id + 1):
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
        if proj_name == 'Mockito':
            project_dict['Mockito']['src'] = 'gradle'
            main_bugger(dico_info, proj_name, i, full_dis, 'gradle')
        else:
            main_bugger(dico_info, proj_name, i, full_dis)
    if dico_info['t'] == 'info':
        rm_dir_by_name(dico_info['o'], 'fixed')
        rm_dir_by_name(dico_info['o'], 'buggy')


def remve_F_flag(arr):
    i = 0
    new_arg = []
    while i < len(arr):
        if arr[i] == '-F':
            i = i + 2
            continue
        new_arg.append(arr[i])
        i += 1
    return ' '.join(new_arg)


def fix_wrapper(args=None):
    print 'in args:'.format(args)
    if args is None:
        args = sys.argv
        args = remve_F_flag(args)
        dico_info = parser_args(args.split())
    else:
        args = remve_F_flag(args.split())
        dico_info = parser_args(args.split())
    dir_need_fix = get_problamtic_dirs(dico_info['o'])
    print dir_need_fix
    for dir_fixing in dir_need_fix:
        full_dis = dir_fixing
        bug_id = str(full_dis).split('/')[-1].split('_')[3]
        proj_name = str(full_dis).split('/')[-1].split('_')[1]
        command_rm = 'rm -r {}'.format(full_dis)
        print command_rm
        process = Popen(shlex.split(command_rm), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print "end"
        if os.path.isdir(full_dis):
            msg = 'the dir {} is not deleted'.format(full_dis)
            raise Exception("msg:{}\n err:{}".format(msg, stderr))
        args_new = '{0} -r {1}-{1} -p {2}'.format(args, bug_id, proj_name)
        print "args_new : {}".format(args_new)
        main_wrapper(args_new)
    exit()


def look_for_old_pred(class_name, cur_csv, proj_name, mem=None):
    ans = {}
    if mem is not None:
        d_csv = mem
    else:
        d_csv = {}
        list_csv = pt.walk_rec('/home/ise/eran/repo/ATG/D4J/csvs/{}/'.format(proj_name), [], '.csv')
        for csv_item in list_csv:
            d_dico = csv_to_dict(csv_item, proj_name)
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


def csv_to_dict(path, project_name, key_name='FileName', val_name='prediction', delimiter='org',
                filter_out='package-info', math3=True):
    dico = {}
    project_name = str(project_name).title()
    prefix_arr = project_dict[project_name]['csv_prefix']
    with open(path) as csvfile:
        reader1 = csv.DictReader(csvfile)
        for row in reader1:
            val_i = row[val_name]
            key_i = row[key_name]
            stop_bol = True
            for item in prefix_arr:
                if str(key_i).startswith(item):
                    stop_bol = False
                    break
            if stop_bol:
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


def get_statistic(path_root):
    '''
    get all the static on the bugs folder
    :param path_root: path
    :return: CSV
    '''
    d_list = []
    print ""
    if os.path.isdir(path_root) is False:
        mesg = 'problem with the path dir : {}'.format(path_root)
        print(mesg)
        return None
    all_sub_dirs = pt.walk_rec(path_root, [], 'P_', lv=-1, file_t=False)
    if len(all_sub_dirs) == 0:
        print "no folder to process the {} is empty".format(path_root)
        return None
    for sub_dir in all_sub_dirs:
        print sub_dir
        miss_classes, size = get_missing_class_pred(sub_dir)
        res = get_all_test(sub_dir)
        tset_res = get_test_res(sub_dir)
    # process the missing class without predication


####################################################
##################XML_parser_functions############
################################################


def get_test_res(path_dir):
    list_d = []
    if os.path.isdir('{}results'.format(path_dir)) is False:
        return None
    all_res = pt.walk_rec('{}results'.format(path_dir), [], '.xml')
    if len(all_res) == 0:
        return list_d
    for file_i in all_res:
        gen_config = '_'.join(str(file_i).split('/')[-2].split('_')[1:])
        allocation_mode = gen_config.split('_')[0]
        time_budget = gen_config.split('_')[1]
        iter_num = gen_config.split('_')[2]
        test_name = str(file_i).split('/')[-1]
        tmp_data = {'iter_num': iter_num, 'time_budget': time_budget, 'allocation_mode': allocation_mode,
                    'results_name_test': test_name}
        list_d.append(tmp_data)
    return list_d


def get_missing_class_pred(dir_path):
    '''
    handel the file miss_pred.txt in the log dir
    :param dir_path:
    :return:
    '''
    list_of_missing_pred = []
    m_dir = dir_path
    if m_dir[-1] != '/':
        m_dir = m_dir + '/'
    if os.path.isdir("{}log".format(m_dir)) is True:
        if os.path.isfile("{}log/missing_pred_class.txt".format(m_dir)) is True:
            with open("{}log/missing_pred_class.txt".format(m_dir), 'r+') as file_i:
                line_of_class = file_i.readlines()
                for line in line_of_class:
                    line = line[:-1]
                    if str(line) == 'EOF':
                        break
                    else:
                        class_name = str(line).split(' / ')[0]
                        size = str(line).split(' / ')[1]
                        list_of_missing_pred.append(class_name)
        else:
            return 'missing file'
    else:
        return 'no log dir'

    return list_of_missing_pred, size


def get_all_test(dir_path):
    '''
    counting the number of test that Evosuite Gen in the dir
    :param dir_path:
    :return:
    '''
    d_list = []
    if os.path.isdir('{}/Evo_Test'.format(dir_path)) is False:
        return None
    list_tests = pt.walk_rec('{}/Evo_Test'.format(dir_path), [], '_ESTest.java')
    for item in list_tests:
        arr_path = [x for x in str(item).split('/') if x.__contains__('_exp_')][0]
        mode = arr_path.split('_exp_')[0]
        arr_path = str(item).split('/')
        index_cut = arr_path.index('Evo_Test')
        test_name = '.'.join(arr_path[index_cut + 3:])
        test_name = test_name[:-5]  # remove the suffix .java at the end
        package = '.'.join(str(test_name).split('.')[:-1])
        print test_name, mode, package
        d_test = {'package': package, 'mode': mode, 'test': test_name}
        d_list.append(d_test)


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
            pack = str(dir_name).split('_')[0]
            time_b = str(dir_name).split('_')[2][2:]
            mode_allocation = str(dir_name).split('_')[1]
            iter_num = str(dir_name).split('_')[-1][3:]
            ans_income['package'] = pack
            ans_income['time_budget'] = time_b
            ans_income['allocation_mode'] = mode_allocation
            ans_income['iteration_num'] = iter_num

            list_acc.append(ans_income)
    return list_acc


def pars_xml_test_file(path_file, dico=None):
    """
    parsing the xml tree and return the results
    """

    name_test = str(path_file).split('/')[-1].split('_')[0]
    d = {"err": float(0), "fail": float(0), "bug": 'no', 'class_err': [], 'class_fail': []}
    d['name'] = name_test
    if dico is not None:
        for ky in dico:
            d[ky] = dico[ky]
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
            res_files = pt.walk_rec("{}/results".format(dir_item), [], rec='org', file_t=False)
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
        df.to_csv('{}/out.csv'.format(out_df_path), sep=';')
    else:
        df.to_csv('{}out.csv'.format(out_df_path), sep=';')
    print "Done !"


def memreg_all_df(dir_path):
    '''
    merge all df in dir and exiting the program
    :param dir_path:
    :return:
    '''
    df_list = {}
    list_csv = pt.walk_rec(dir_path, [], '.csv')
    for item in list_csv:
        if str(item).split('/')[-1] == 'all_dfs.csv':
            continue
        time_budget = str(item).split('/')[-1][:-4].split('_')[-1][1:]
        project_name = str(item).split('/')[-1][:-4].split('_')[-2]
        df = pd.read_csv(item, sep=';', index_col=0)
        df_list['{}_{}'.format(project_name, time_budget)] = df
    for ky in df_list.keys():
        print df_list[ky].shape
        df_list[ky]['binary_bug_err'] = np.where(df_list[ky]['err'] > 0, 1, 0)  # | df_list[ky]['fail'] > 0 )
        df_list[ky]['binary_bug_fail'] = np.where(df_list[ky]['fail'] > 0, 1, 0)
        col_name = list(df_list[ky])
    df_big = pd.concat(df_list.values())
    if dir_path[-1] == '/':
        df_big.to_csv('{}all_dfs.csv'.format(dir_path), sep=';')
    else:
        df_big.to_csv('{}/all_dfs.csv'.format(dir_path), sep=';')
    exit()


def check_FP_prediction_vs_reality(project_name):
    '''
    this function check if the real Bug probability is the same as the FP probability,
    by making CSV and computing the mean over all the package classes
    :return: CSV
    '''
    print ""
    num_of_bugs = project_dict[project_name]["num_bugs"]
    d_list = []
    for i in range(1, num_of_bugs):
        args = ["", project_name, '/home/ise/Desktop/defect4j_exmple/ex/',
                "evosuite-1.0.5.jar", "/home/ise/eran/evosuite/jar/", '7', '1',
                '100', True, 'info']  # package / class
        bug_object = Bug_4j(pro_name=project_name, bug_id=i, info_args=args, root_dir='')
        buggy_fixed_date = bug_object.bug_date
        buggy_class = bug_object.modified_class
        d = {'id': i, 'mod_class': buggy_class, 'data_fix': buggy_fixed_date}
        d_list.append(d)
    print '/' * 200
    for it in d_list:
        print it
    print "check_FP_prediction_vs_reality --> done"
    exit()


def get_FP_csv_by_ID(dir, flag='apache'):
    list_dir = pt.walk_rec(dir, [], 'P_', lv=-2, file_t=False)
    d_list = []
    for dir_i in list_dir:
        dir_name = str(dir_i).split('/')[-1]
        list_dir = pt.walk_rec(dir_i, [], 'FP_Allocation_budget', lv=-2, file_t=True)
        id = str(dir_name).split('_')[3]
        if len(list_dir) != 1:
            print "[Error] ID:{} = No FP_csv file in dir: {}".format(id, dir_i)
            continue
        list_dir_bugyy = pt.walk_rec(dir_i, [], 'bug_classes.txt', lv=-2, file_t=True)
        if len(list_dir_bugyy) != 1:
            print "[Error]  ID:{} = No bug_classes file in dir: {}".format(id, dir_i)
            continue
        project = str(dir_name).split('_')[1]
        d_list.append({'ID': id, 'proj': project, 'csv_FP': list_dir[0], 'buggy': list_dir_bugyy[0], 'dir_path': dir_i})
    for x in d_list:
        if x['ID'] == '26':
            print ""
        with open(x['buggy'], 'r+') as f:
            classes_bug = f.readlines()
            l = []
            l_package = set()
            for klass in classes_bug:
                klass = klass[:-1]
                pack = '.'.join(str(klass).split('.')[:-1])
                if flag == 'apache':
                    pack = '.'.join(str(pack).split('.')[4:])
                    klass = '.'.join(str(klass).split('.')[4:])
                l_package.add(pack)
                l.append(klass)
            # print l_package
            x['bugs'] = l
            x['package'] = list(l_package)
        df = pd.read_csv(x['csv_FP'])
        if flag == 'apache':
            df['packages'] = df['class'].apply(get_package_name_appche)
        else:
            df['packages'] = df['class'].apply(get_package_name)
        df.to_csv('{}/ex.csv'.format(x['dir_path']))
        values = x['package']
        # if x['ID'] ==str(26):
        #    print values[0]
        #    print (df.loc[df['packages'] == values[0]])
        df_filter = df.loc[df['packages'].isin(values)]
        df_filter.to_csv('{}/filter_df.csv'.format(x['dir_path']))
        print "ID:{} Filter:{}  old:{}".format(x['ID'], df_filter.shape, df.shape)
        x['df'] = df
    print 'done'

    exit()

def make_target_mvn_framework(p_path='/home/ise/eran/eran_D4j',p_name='Math'):
    if os.path.isdir(p_path) is False:
        print "[Error] the given path is not a valid dir -> {}".format(p_path)
        return
    list_info_bug = get_faulty_comp_defe4j_dir(p_name)
    if len(list_info_bug) == 0:
        print "[Error] cant make the info csv "
        return
    df = pd.DataFrame(list_info_bug)
    df.to_csv('{}/info_faulty_comp.csv'.format(p_path))
    #df = None # naive freeing the memory
    bug_dirs = pt.walk_rec(p_path,[],"P_",False,lv=-3)
    list_target=[]
    for bug_dir_i in bug_dirs:
        #print "---{}---".format(bug_dir_i)
        out = pt.mkdir_system(bug_dir_i,'TARGET',True)
        merge_csv_path = '{}/csvs/merge.csv'.format(bug_dir_i)
        if os.path.isfile(merge_csv_path) is False:
            continue
        df_merge = pd.read_csv(merge_csv_path)
        df_merge['class_name'] = df_merge['name'].apply(lambda x: str(x)[5:])
        cur_bug_id = str(bug_dir_i).split('/')[-1].split('_')[3]
        cur_project = str(bug_dir_i).split('/')[-1].split('_')[1]
        filter_info = df.loc[df['bug_ID'] == cur_bug_id ]
        if len(filter_info) != 1:
            print '[Error] the filter csv is differ from one --> len = {}'.format(len(filter_info))
            return
        filter_info.to_csv("{}/bla.csv".format(out))
        modified_comp_str = filter_info.iloc[0]['classes']
        modified_arry = str(modified_comp_str).split('\n')
        modified_arry = [x for x in modified_arry if len(str(x))>1]
        with open("{}/modified_comp.txt".format(out),'w+') as f:
            for item in modified_arry:
                f.write(item+'\n')
        filter_target = df_merge.loc[df_merge['class_name'].isin(modified_arry)]
        if len(filter_info)>0:
            filter_target.to_csv("{}/target.csv".format(out))
            list_target.append(filter_target)
    if len(list_target)>0:
        df_all_target = pd.concat(list_target)
        df_all_target.to_csv('{}/df_all_targets.csv'.format(p_path))


def get_faulty_comp_defe4j_dir(p_name='Math',dir_d4j='/home/ise/programs/defects4j/framework/projects'):
    faluty_comp_dir = '/home/ise/programs/defects4j/framework/projects/{}/modified_classes'.format(p_name)
    list_files_src = pt.walk_rec(faluty_comp_dir,[],'.src')
    list_bug_info=[]
    for file_i in list_files_src:
        d={}
        bug_number = str(file_i).split('/')[-1].split('.')[0]
        d['bug_ID'] = bug_number
        d['project'] = p_name
        with open(file_i,'r+') as f:
            lines = f.readlines()
        for line in lines:
            line = line.replace('\n','')
            list_bug_info.append({'bug_ID':bug_number, 'project':p_name, 'class':line})
    return list_bug_info


def get_package_name(name):
    res = '.'.join(str(name).split('.')[:-1])
    return res


def get_package_name_appche(name):
    res = '.'.join(str(name).split('.')[4:-1])
    # print(res)
    return res


class D4J_tool:
    '''
    this class is a wrapper for Defect4j framework
    '''

    def __init__(self, out_dir, project, bug_range, time_b, csv_fp_path, info_d,
                 scope_p='all', d4j_path='/home/ise/programs/defects4j/framework/bin/defects4j', rep=2, mode='U'):
        self.root_d4j = d4j_path
        self.root_framework_defect4j = '/'.join(str(d4j_path).split('/')[:-2])
        self.bugs = bug_range
        self.p_name = project
        self.rep = rep
        self.df_SHA = None
        self.modified_class = []
        self.bug_date = 'NULL'
        self.mode = mode
        self.lower_bug_id = -1
        self.upper_bug_id = -1
        self.list_times = None
        self.info = info_d
        self.FP_dico = None
        self.out_root = out_dir
        self.scope = scope_p
        self.csv_fp = csv_fp_path
        self.out = None
        self.time_budget = time_b

    def main_process(self, path=None):
        if path is None:
            if self.root_d4j[-1] == '/':
                self.root_d4j = self.root_d4j[:-1]
            self.out = self.make_out_dir(self.out_root)
        else:
            self.out = path
        self.get_bug_rang_id()
        self.get_map_dir()
        self.make__csv()
        self.generate_test()
        out_list = self.get_all_tests()
        self.run_tests(out_list)

    def test_process(self, path_p):
        '''
        This function re_test all directories that hasn't been test yet

        '''
        self.out = path_p
        out_list = self.get_all_tests()
        new_out_list = []
        for item in out_list:
            p_bug_dir = self.get_bug_id_dir_path(item['path'])
            bol = self.test_dir_exsit(p_bug_dir)
            if bol:
                continue
            new_out_list.append(item)
        out_list = new_out_list
        if len(out_list) == 0:
            return
        self.run_tests(out_list)

    def analysis_existing_test_suite(self, path_to_dir):
        dico_list = []
        project_name = str(path_to_dir).split('/')[-1]
        bug_dirs = pt.walk_rec(path_to_dir, [], '', False, lv=-1)
        for bug_dir_i in bug_dirs:
            bug_id = str(bug_dir_i).split('/')[-1]
            p_path = '{}/{}/evosuite-branch'.format(bug_dir_i, project_name)
            print p_path
            all_test = pt.walk_rec(p_path, [], '', False, lv=-1)
            for test_dir in all_test:
                name_rep = str(test_dir).split('/')[-1]
                # os.system("rm {0}/*.bz2".format(test_dir))
                # tar_command ='tar -cvjSf {0}/{1}-{2}f-evosuite-branch.{3}.tar.bz2 {0}/*'.format(test_dir,project_name,bug_id,name_rep)
                # print tar_command
                # os.system(tar_command)
                rel_path = test_dir
                test_out = pt.mkdir_system('{}/'.format(test_dir), 'TEST_results_B_{}'.format(bug_id))
                dico_list.append(
                    {'log': test_out, 'output': test_out, 'project': project_name, 'path': rel_path, 'version': bug_id})
                self.run_tests(dico_list)
                dico_list = []

    def get_map_dir(self, defect_lib='/home/ise/programs/defects4j/framework/projects'):
        if os.path.isfile('{}/{}/dir_map.csv'.format(defect_lib, self.p_name)):
            df = pd.read_csv('{}/{}/dir_map.csv'.format(defect_lib, self.p_name), names=['SHA_ID', 'class', 'tests'])
            self.df_SHA = df
        else:
            self.df_SHA = None

    def make_out_dir(self, dir_path, index=None):
        '''
        crate the relevant bug dir
        '''
        localtime = time.asctime(time.localtime(time.time()))
        localtime = str(localtime).replace(":", "_")
        localtime = str(localtime).replace(" ", "_")
        if index is None:
            dir_name = "OUT_{0}_D_{1}".format(self.p_name, str(localtime))
        else:
            dir_name = "P_{0}_{1}_D_{2}".format(self.p_name, str(index), str(localtime))
        full_dis = bg.mkdir_Os(dir_path, dir_name)
        if full_dis == 'null':
            print('cant make dir')
            exit(1)
        return full_dis

    def make__csv(self):
        if self.info['M'] == 'FP':
            args_input = "py. -p {0} -o {1} \
            -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b {2} -l 1\
            -u 100 -f True -t info -r {3} -z {2} ".format(self.p_name, self.info['i'], self.time_budget, self.bugs)
            if self.info['C'] == '1':
                main_wrapper(args_input)
            self.FP_dico = info_dir_to_csv_dict(self.info['i'])
        else:
            bol = self.get_faulty_classes()
            return bol

    def get_build_path_by_project(self):
        '''
        project that dont have dir_map.csv , the path wehere the java src files and java test files
        '''
        src = ''
        test = ''
        if self.p_name == 'Time':
            src = 'src/main/java'
            test = 'src/test/java'
        elif self.p_name == 'Chart':
            src = 'source'
            test = 'source'
        elif self.p_name == 'Clousre':
            src = 'src'
            test = 'test'

        return src, test

    def get_row_sha_df(self, sha_id):
        df = self.df_SHA
        if df is None:
            return self.get_build_path_by_project()
        df_res = df.loc[df['SHA_ID'] == sha_id]
        if len(df_res) == 0:
            return None, None
        elif len(df_res) == 1:
            return df_res['class'].tolist()[0], df_res['tests'].tolist()[0]
        else:
            raise Exception("get_row_sha_df function found more than one value [Error]")

    def get_faulty_classes(self):
        self.write_log(self.out, self.scope, 'scope')
        for id in range(self.lower_bug_id, self.upper_bug_id + 1):
            self.modified_class = []
            str_c = "/home/ise/programs/defects4j/framework/bin/defects4j info -p  {1} -b {0}".format(id,
                                                                                                      self.p_name)
            result = subprocess.check_output(str_c, shell=True)
            print '#' * 200
            print result

            x = result.find("List of modified sources:")
            date_index = result.find("Revision date (fixed version):")
            stoper = result.find("Root cause in triggering tests")

            sha_str = "Revision ID (fixed version):\n"
            sha_str_size = len(sha_str)
            x_sha_id_start = result.find(sha_str)

            x_sha_id_end = result.find("Revision date (fixed version):")

            x_sha = result[x_sha_id_start + sha_str_size:x_sha_id_end].replace('-', "").replace('\n', '').replace(' ',
                                                                                                                  '')
            ID_SHA = x_sha

            class_path, tset_path = self.get_row_sha_df(ID_SHA)
            if class_path is None:
                print ID_SHA
                self.write_log(self.out, 'cant find {} in dir_map.csv BUG_ID: {} {}'.format(ID_SHA, id, self.p_name),
                               name='miss_SHA')
                return False
            data_time = result[date_index + len("Revision date (fixed version):"):stoper].replace('-', "")
            try:
                data_time = data_time.replace('\n', "").split()[0]
            except Exception:
                print "[EError] in Date"
                data_time = '20120101'
            year = data_time[:4]
            month = data_time[4:6]
            day = data_time[-2:]
            str_data_bug = "{}_{}_{}".format(year, month, day)
            y = result[x + len("List of modified sources:"):].replace("-", "").replace(" ", "").split('\n')
            for y1 in y:
                if len(y1) > 1:
                    print y1
                    self.modified_class.append(y1)
            if len(self.modified_class) > 1:
                print ""
            print '#' * 200
            self.bug_date = str_data_bug
            self.get_all_java_class(id, class_path, tset_path)
            self.write_faulty(self.out, "bug_{}".format(id), self.modified_class)

    def get_all_java_class(self, id, class_path, test_path):
        out_fix = pt.mkdir_system(self.out, 'fixed', True)
        str_command = self.root_d4j + ' checkout -p {1} -v {0}"f" -w {2}/'.format(id, self.p_name, out_fix)
        print '[OS] {}'.format(str_command)
        os.system(str_command)
        java_class = pt.walk_rec("{}/{}".format(out_fix, class_path), [], '.java')
        package_class = []
        start_package = 'org'
        if self.p_name == 'Closure':
            start_package = 'com'
        for item in java_class:
            if item[-5:] != '.java':
                continue
            pack = pt.path_to_package(start_package, item, -1 * len('.java'))
            package_class.append(pack)
        package_class = self.filter_by_scope(package_class, id)
        self.write_faulty(self.out, "class_{}".format(id), package_class)
        os_rm_dir(out_fix)

    def get_relevent_classs(self, id):
        '''
        get the revent classes -A flag in run_evosuite.pl
        '''
        with open("{}/projects/{}/loaded_classes/{}.src".format(
                self.root_framework_defect4j, self.p_name, id), 'r') as f_src:
            lines = f_src.readlines()
            return lines

    def filter_by_name(self, list_candidates, prefix=True):
        '''
        filter by the scope the project classes
        '''
        result_klass = []
        modified_package = []
        for item_i in self.modified_class:
            modified_package.append('.'.join(str(item_i).split('.')[:-1]))
        for klass in list_candidates:
            for item in modified_package:
                if prefix:
                    if str(klass).startswith(item):
                        result_klass.append(klass)
                        continue
                else:
                    if '.'.join(str(klass).split('.')[:-1]) == item:
                        result_klass.append(klass)
                        continue
        return result_klass

    def filter_by_scope(self, list_classes, id):
        '''
        in which scope to generate test
        :param list_classes:
        :param id:
        :return:
        '''
        if self.scope == 'project':
            return list_classes
        elif self.scope == 'target':
            return self.modified_class
        elif self.scope == 'test_trace':
            return self.get_relevent_classs(id)
        elif self.scope == 'package_only':
            return self.filter_by_name(list_classes, False)
        elif self.scope == 'package_rec':
            return self.filter_by_name(list_classes, True)
        else:
            msg = '[Error] the scope value is not defined --> [{}]\n' \
                  'project - all classes\n' \
                  'target - only the fault components\n' \
                  'test_trace - all the class in the bug trace\n' \
                  'package_only - only the fault components package\n' \
                  'package_rec - recursively the package with the fault components '.format(self.scope)
            raise Exception(msg)

    def write_faulty(self, path_out, file_name, list_item):
        out = pt.mkdir_system(path_out, 'fault_components', False)
        with open("{}/{}.txt".format(out, file_name), 'a') as f:
            for item in list_item:
                f.write(item + '\n')

    def process_str_time_budget(self, str_time):
        if str(str_time).__contains__('-'):
            arr = str(str_time).split('-')
            arr = [int(x) for x in arr]
            return arr
        else:
            return [int(str_time)]

    def get_bug_rang_id(self):
        num_of_bugs = project_dict[self.p_name]["num_bugs"]
        self.list_times = self.process_str_time_budget(self.time_budget)
        if str(self.bugs).__contains__('-'):
            lower_bug_id = int(str(self.bugs).split('-')[0])
            upper_bug_id = int(str(self.bugs).split('-')[1])
        else:
            lower_bug_id = int(str(self.bugs))
            upper_bug_id = int(str(self.bugs))
        if int(upper_bug_id) > int(num_of_bugs):
            upper_bug_id = int(num_of_bugs)
        if lower_bug_id > upper_bug_id:
            lower_bug_id = upper_bug_id
        self.lower_bug_id = lower_bug_id
        self.upper_bug_id = upper_bug_id

    def generate_test(self):
        print '----- generate tests phase -----'
        d4j_dir_bin = '/'.join(str(self.root_d4j).split('/')[:-1])
        for i in range(self.lower_bug_id, self.upper_bug_id + 1):
            property_info = 'B_{}_M_{}'.format(i, self.mode)
            out_dir_bug = self.make_out_dir(self.out, property_info)
            for time_bud in self.list_times:
                for rep_it in range(self.rep):
                    out_folder = pt.mkdir_system(out_dir_bug, 't={}'.format(time_bud), False)
                    targe_file = "{}/fault_components/class_{}.txt".format(self.out, i).replace('//', '/')

                    evosuite_command = '{0}/run_evosuite.pl -p {1} -v {2}f -n {3}' \
                                       ' -o {4} -b {5} -c branch -m {7} -u {6}'.format(d4j_dir_bin,
                                                                                       self.p_name, str(i), rep_it,
                                                                                       out_folder,
                                                                                       time_bud, targe_file,
                                                                                       self.mode)
                    print "[OS] {}".format(evosuite_command)
                    process = Popen(shlex.split(evosuite_command), stdout=PIPE, stderr=PIPE)
                    stdout, stderr = process.communicate()
                    self.write_log(out_folder, evosuite_command, 'evosuite_command.log')
                    self.write_log(out_folder, stdout, 'evosuite_stdout.log')
                    self.write_log(out_folder, stderr, 'evosuite_stderr.log')

    def get_all_tests(self):
        '''
        collect all test tar that generated in the relevant dir
        :return:
        '''
        dir = self.out
        all_tat_files = pt.walk_rec(dir, [], '.tar')
        list_tar = []
        for item in all_tat_files:
            name = str(item).split('/')[-1]
            p_path = '/'.join((str(item).split('/')[:-1]))
            rep_index = str(item).split('/')[-2]
            array = str(name).split('.')
            name_project = array[0].split('-')[0]
            version = array[0].split('-')[1][:-1]
            search_criteria = array[0].split('-')[3]
            list_tar.append({'f_name': name, 'path': p_path, 'project': name_project, 'version': version,
                             'search_criteria': search_criteria, 'rep': rep_index})
        return list_tar

    def get_bug_id_dir_path(self, path):
        arr_folder_name = str(path).split('/')
        ctr = 0
        for name in arr_folder_name:
            if str(name).startswith('P_'):
                break
            ctr += 1
        return '/'.join(arr_folder_name[:ctr + 1])

    def test_dir_exsit(self, path):
        res = pt.walk_rec(path, [], 'Test_P', False, lv=-2)
        if len(res) > 0:
            return True
        return False

    def run_tests(self, list_test_tar):
        '''
        /home/ise/programs/defects4j/framework/bin/run_bug_detection.pl
        -d ~/Desktop/d4j_framework/test s/Math/evosuite-branch/0/ -p Math -v 3f -o ~/Desktop/d4j_framework/out/ -D

        sudo cpan -i DBD::CSV
        '''
        print "---test phase----"
        d4j_dir_bin = '/'.join(str(self.root_d4j).split('/')[:-1])
        for item in list_test_tar:
            if 'output' not in item:
                dir_out_bug_i = '/'.join(str(item['path']).split('/')[:-3])
                out_test_dir = pt.mkdir_system(dir_out_bug_i, 'Test_P_{}_ID_{}'.format(self.p_name,
                                                                                       str(time.time() % 1000).split(
                                                                                           '.')[0]))
            else:
                dir_out_bug_i = item['log']
                out_test_dir = item['output']
            command_test = '{0}/run_bug_detection.pl -d {1}/ -p {2} -v {3}f -o {4} -D'.format(d4j_dir_bin,
                                                                                              item['path'],
                                                                                              item['project'],
                                                                                              item['version'],
                                                                                              out_test_dir)
            print "[OS] {}".format(command_test)
            process = Popen(shlex.split(command_test), stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            self.write_log(dir_out_bug_i, command_test, 'testing_commands.log')
            self.write_log(dir_out_bug_i, stdout, 'testing_stdout.log')
            self.write_log(dir_out_bug_i, stderr, 'testing_stderr.log')

    def write_log(self, father_dir, info, name='missing_pred_class'):
        '''
        write to log dir
        '''
        dir_p = pt.mkdir_system(father_dir, 'loging', False)
        with open("{}/{}".format(dir_p, '{}.txt'.format(name)), 'a') as f:
            f.write(info)
            f.write('\n')


def os_rm_dir(path):
    string_command = 'rm -r {}'.format(path)
    print "[OS] {}".format(string_command)
    process = Popen(shlex.split(string_command), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print "stderr:\n{}".format(stderr)
    print "stdout:\n{}".format(stdout)


def wrapper_get_all_results_D4j(root):
    all_OUT = pt.walk_rec(root, [], "OUT", False)
    for x_path in all_OUT:
        get_all_results_D4j(x_path)


def get_all_results_D4j(root_path, out=None, name='results_D4j'):
    '''
    going over all the folders and collecting the results to a csv
    :param root_path:
    :return:
    '''
    if out is None:
        out = root_path
    list_dict = []
    folders = pt.walk_rec(root_path, [], 'P_', False, lv=-2)
    for f_folder in folders:
        d = {}
        bug_id = str(f_folder).split('/')[-1].split('_')[3]
        created = '-'.join(str(f_folder).split('/')[-1].split('_')[4:])
        time_b = str(f_folder).split('/')[-1].split('_')[3]
        d['bug_id'] = bug_id
        d['time_budget'] = time_b
        d['created'] = created
        test_dir = pt.walk_rec(f_folder, [], 'Test_', False, lv=-2)
        if len(test_dir) == 1:
            # time_budget = str(test_dir[0]).split('/')[-1].split('_')[6]
            out_file_l = pt.walk_rec(test_dir[0], [], 'bug_detection', lv=-1)
            if len(out_file_l) == 1:
                out_file = out_file_l[0]
            else:
                continue
            df_tmp = pd.read_csv(out_file)
            for ky, val in d.iteritems():
                df_tmp[ky] = val
        else:
            continue
        list_dict.append(df_tmp)
    if len(list_dict) > 1:
        result = pd.concat(list_dict)
    else:
        print '[Error] noting found at path: {}'.format(root_path)
        return
    if out[-1] == '/':
        result.to_csv('{}{}.csv'.format(out, name))
    else:
        result.to_csv('{}/{}.csv'.format(out, name))


def init_testing_pahse(root_p, replace_new_str=None, replace_old_str=None):
    all_command_test = pt.walk_rec(root_p, [], 'testing_commands.log.txt')
    for command_i_file in all_command_test:
        with open(command_i_file, 'r') as f:
            command_i = f.readlines()
            for command_j in command_i:
                if replace_new_str != None:
                    command_j = str(command_j).replace(replace_old_str, replace_new_str)
                if len(command_j) < 1:
                    continue
                command_j = command_j.replace('//', '/')
                print "[OS] {}".format(command_j)
                os.system(command_j)


def get_results_junit(root_p, out=None, name='result_df'):
    print root_p
    if root_p[-1]=='/':
        root_p=root_p[:-1]
    if out is None:
        out = '/'.join(str(root_p).split('/')[:-1])
    dir_name = str(root_p).split('/')[-1]
    father_dir = str(root_p).split('/')[-2]
    scope_const = None
    if father_dir == 'oracle':
        scope_const = 'target'
    name = "{}__{}".format(dir_name,father_dir)
    list_df = []
    list_df_class = []
    all_bugs_dir = pt.walk_rec(root_p, [], 'P_', False, lv=-3)
    for bug_folder in all_bugs_dir:
        OUT_dir = "{}".format('/'.join(str(bug_folder).split('/')[:-1]))
        if scope_const is None:
            res_scope = read_scope_test_gen(OUT_dir)
        else:
            res_scope = scope_const
        time_folders = pt.walk_rec(bug_folder, [], 't=', False, lv=-1)
        bug_id = str(bug_folder).split('/')[-1].split('_')[3]
        mode_gen = str(bug_folder).split('/')[-1].split('_')[5]
        for time_dir in time_folders:
            time_budget = str(time_dir).split('/')[-1].split('=')[1]
            test_dir = pt.walk_rec(time_dir, [], 'Test_', False, lv=-1)
            for item in test_dir:
                if os.path.isfile("{}/bug_detection".format(item)):
                    d = {}
                    d['scope'] = res_scope
                    d['bug_id'] = bug_id
                    d['gen_mode'] = mode_gen
                    d['time_budget'] = time_budget
                    res = get_deff("{}/bug_detection_log".format(item))
                    df_tmp = pd.read_csv("{}/bug_detection".format(item))
                    for ky, val in d.iteritems():
                        df_tmp[ky] = val
                    d_class_tmp = get_fp_time_b(time_dir)
                    if len(res) > 0:
                        df_tmp['buggy_test_case_fail (diff)'] = res['bug']['tests']
                        df_tmp['fixed_test_case_fail (diff)'] = res['fix']['tests']
                        df_tmp['kill_binary'] = df_tmp.apply(binary_kill, axis=1)

                        # df_tmp['buggy_diff'] = res['bug']['diff']
                        # df_tmp['fixed_diff'] = res['fix']['diff']
                    for ky in d_class_tmp.keys():
                        d_class = {}
                        d_class['bug_id'] = bug_id
                        d_class['gen_mode'] = mode_gen
                        d_class['time_budget'] = time_budget
                        d_class['class'] = ky
                        d_class['time_gen'] = d_class_tmp[ky]
                        list_df_class.append(d_class)
                    list_df.append(df_tmp)
    if len(list_df) == 0:
        print "[Error] no results"
        return
    result = pd.concat(list_df)
    df = pd.DataFrame(list_df_class)
    if len(df) == 0:
        bol = False
    else:
        bol = True
    if out[-1] == '/':
        result.to_csv('{}{}.csv'.format(out, name))
        if bol:
            df.to_csv('{}{}_{}.csv'.format(out, 'class_allocation', name))
    else:
        result.to_csv('{}/{}.csv'.format(out, name))
        if bol:
            df.to_csv('{}/{}_{}.csv'.format(out, 'class_allocation', name))


def binary_kill(row,fix_col='fixed_test_case_fail (diff)',buggy_col='buggy_test_case_fail (diff)'):
    '''
    help to crate DataFrame killing col
    '''
    if row[fix_col] == '-':
        fix=0
    else:
        fix=1
    if row[buggy_col] == '-':
        buggy=0
    else:
        buggy=1
    if buggy==1 and fix==0:
        return 1
    else:
        return 0



def get_deff(dir_path):
    '''
    getting the diff between the result of the junit, the buggy version and the fix version
    :param dir_path:
    :return:
    '''
    log_files = pt.walk_rec(dir_path, [], 'trigger.log')
    d = {}
    if len(log_files) == 2:
        for file_i in log_files:
            if str(file_i).split('.')[0].__contains__('f'):
                d['fix'] = {'path': file_i}
            elif str(file_i).split('.')[0].__contains__('b'):
                d['bug'] = {'path': file_i}
            else:
                raise Exception("[Error] the log file is not in the correct format -> {}".format(file_i))
    else:
        return d
    diff_bug, diff_fix = diff_function(d['bug']['path'], d['fix']['path'])
    d['bug']['diff'] = diff_bug
    d['fix']['diff'] = diff_fix
    d['fix']['tests'] = ':'.join(get_regex_res(diff_fix, 'test\d+'))
    d['bug']['tests'] = ':'.join(get_regex_res(diff_bug, 'test\d+'))
    d['bug']['class'] = ':'.join(get_regex_res(diff_bug,'---.+ESTest',4))
    d['fix']['class'] = ':'.join(get_regex_res(diff_fix,'^---.+ESTest',4))
    if len(d['fix']['tests']) == 0:
        d['fix']['tests']='-'
    if len(d['bug']['tests']) == 0:
        d['bug']['tests'] = '-'
    return d


def get_regex_res(string_search, pattern,cut=0):
    tmp = re.compile(r'{}'.format(pattern)).search(string_search)
    arr = []
    if tmp is not None:
        for tuple in tmp.regs:
            arr.append(string_search[tuple[0]:tuple[1]])
    if cut == 0:
        return arr
    else:
        arr = [x[cut:] for x in arr]
    if len(arr) == 0 :
        return ['-']
    return arr


def diff_function(file_one, file_two):
    '''
    This is very inefficient, especially for large files !!! FIX IT !!!
    :return:
    '''
    doc2 = open(file_two, 'r')
    doc1 = open(file_one, 'r')

    f2 = [x for x in doc2.readlines()]
    f1 = [x for x in doc1.readlines()]

    f1 = [x for x in f1 if str(x).startswith('\tat') is False]
    f2 = [x for x in f2 if str(x).startswith('\tat') is False]

    diff1 = [line for line in f1 if line not in f2]  # lines present only in f1
    diff2 = [line for line in f2 if line not in f1]  # lines present only in f2



    if len(diff1) == 0:
        diff1 = '-'
    else:
        diff1 = '\n'.join(diff1)
        diff1 = diff1.replace(',', '|')
    if len(diff2) == 0:
        diff2 = '-'
    else:
        diff2 = '\n'.join(diff2)
        diff2 = diff2.replace(',', '|')
    doc2.close()
    doc1.close()

    return diff1, diff2


def get_fp_time_b(p):
    d = {}
    if ("{}/loging/evosuite_stdout.log.txt".format(p)):
        with open("{}/loging/evosuite_stdout.log.txt".format(p), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line[0] == '<' and line[-2] == '>':
                    arr = str(line[1:-2]).split(',')
                    d[arr[0]] = arr[1]
    return d


def parser_args(arg):
    '''

    helps to split the args to dict
    :param arg: string args
    :return: dict
    '''
    usage = '-p project name\n' \
            '-o out dir\n' \
            '-e Evosuite path\n' \
            '-b time budget\n' \
            '-l Lower bound time budget\n' \
            '-u Upper bound time budget\n' \
            '-t target class/package/all/project\n' \
            '-c clean flaky test [T/F]\n' \
            '-d use defect4j framework\n' \
            '-k the csv fp file or U for uniform\n' \
            '-r range for bug ids e.g. x-y | x<=y and x,y int\n' \
            '-z to what time budgets to make a predection CSV e.g. 4;5;6\n' \
            '-i dir folder where the FP CSV\n' \
            '-C crate the info dir or not e.g. 1/0\n' \
            '-M mode of the allocation [FP/U]\n' \
            '-T Test again all the dir\n ' \
            '-F Fix\n' \
            '-P pass for sudo\n'
    dico_args = {}
    array = arg
    i = 1
    while i < len(array):
        if str(array[i]).startswith('-'):
            key = array[i][1:]
            i += 1
            val = array[i]
            dico_args[key] = val
            i += 1
        else:
            msg = "the symbol {} is not a valid flag".format(array[i])
            print(msg)
            print(usage)
            raise Exception('[Error] in parsing Args')
    return dico_args


def replace_script(d4j_path):
    '''
    retplcae the scrip pl TODO: change the harcoded path repo ATG
    '''
    if d4j_path[-1] != '/':
        d4j_path = d4j_path + '/'
    comaand_rm = 'rm {}run_evosuite.pl'.format(d4j_path)
    print "[OS] {}".format(comaand_rm)
    cwd = '/home/ise/eran/repo/ATG'
    comaand_cp = 'cp {}/D4J/script/run_evosuite.pl {}'.format(cwd, d4j_path)
    print "[OS] {}".format(comaand_cp)
    os.system(comaand_rm)
    os.system(comaand_cp)


def init_main():
    # string_std_in='file.py -i /home/ise/eran/D4J/info/ -M U -C 0 -d /home/ise/programs/defects4j/framework/bin -b 2 -r 1-1 -o /home/ise/eran/D4j/out/ -t target -p Chart -k U'
    # sys.argv = str(string_std_in).split()
    dico_args = parser_args(sys.argv)
    replace_script(dico_args['d'])
    if 'T' in dico_args:
        init_testing_pahse(dico_args['T'])
    elif 'R' in dico_args:
        all_dir_OUT = pt.walk_rec(dico_args['R'], [], 'OUT', False, lv=-2)
        for dir_OUT in all_dir_OUT:
            get_results_junit(dir_OUT)
    else:
        obj_d4j = D4J_tool(out_dir=dico_args['o'], project=dico_args['p'], bug_range=dico_args['r'],
                           time_b=dico_args['b'],
                           csv_fp_path=dico_args['k'], scope_p=dico_args['t'], info_d=dico_args)
        obj_d4j.main_process()
    exit()


def rm_dir_by_name(root, name=None):
    if name is None:
        name = 'fixed'
    all_res = pt.walk_rec(root, [], name, False)
    for x in all_res:
        final_command = 'rm -r -f {}'.format(x)
        process = Popen(shlex.split(final_command), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print "----stdout----"
        print stdout
        print "----stderr----"
        print stderr


def info_dir_to_csv_dict(root):
    '''
    make form the folder dict with the FP csv path
    :param root:
    :return:
    '''
    d = {}
    all_dirs = pt.walk_rec(root, [], 'P_', False, lv=-1)
    for dir in all_dirs:
        name = str(dir).split('/')[-1]
        bug_id = str(name).split('_')[3]
        all_csvs = pt.walk_rec(dir, [], '.csv')
        ALL_csv = [x for x in all_csvs if str(x).split('/')[-1].__contains__('All_')]
        d_budget_all = {}
        d_budget_pack = {}
        for item_all in ALL_csv:
            time_budget = str(item_all).split('/')[-1].split('=')[1].split('.')[0][:-1]
            d_budget_all[time_budget] = item_all
        PACK_csv = [x for x in all_csvs if str(x).split('/')[-1].__contains__('Pack_')]
        for item_pack in PACK_csv:
            time_budget = str(item_pack).split('/')[-1].split('=')[1].split('.')[0]
            d_budget_pack[time_budget] = item_pack
        d[bug_id] = {'ALL': d_budget_all, 'PACK': d_budget_pack}
    return d


def get_faulty_comp(project_name='Math', out_dir='/home/ise/MATH/Defect4J'):
    '''
    make a CSV with all the faulty comp
    :param project_name:
    :param out_dir:
    :return:
    '''
    num_of_bug = project_dict[project_name]['num_bugs']
    list_of_d = []
    for i in range(1, num_of_bug, 1):
        object_bug = Bug_4j(project_name, i, {'t': 'info', 'p': project_name}, out_dir)
        print object_bug.modified_class
        for modify in object_bug.modified_class:
            pack = '.'.join(str(modify).split('.')[:-1])
            list_of_d.append({'package': pack, 'bug_ID': i, 'CUT': modify, 'faulty': 1})
    df = pd.DataFrame(list_of_d)
    df.to_csv("{}/{}_faulty_comp.csv".format(out_dir, project_name))
    exit()


def test_process(root_dir='P_Lang_B_36_Sun_Aug__5_22_23_19_2018'):
    name = str(root_dir).split('/')[-1]
    project_name = str(name).split('_')[1]
    bug_ID = str(name).split('_')[3]
    bug_object = Bug_4j(project_name, bug_ID, info_args=None, root_dir=root_dir)
    print 'done'


def get_problamtic_dirs(root_path):
    list_dirs = pt.walk_rec(root_path, [], 'P_', False, lv=-2)
    no_log = []
    yes_log = []
    fix_list = []
    for item_dir in list_dirs:
        if os.path.isdir('{}/Evo_Test'.format(item_dir)):
            fix_list.appqend(item_dir)
            continue
        else:
            if os.path.isdir('{}/log'.format(item_dir)):
                yes_log.append(item_dir)
            else:
                no_log.append(item_dir)
    res = []
    res.extend(yes_log)
    res.extend(no_log)
    return res


def re_gen_broken_test(csv_path='/home/ise/eran/D4j/oracle/log.csv'):
    path_rel = '/'.join(str(csv_path).split('/')[:-1])
    list_command = []
    df = pd.read_csv(csv_path, index_col=0)
    print len(df)
    df = df[df['msg'] != '[good]']
    if len(df) == 0:
        print "[py] no error test"
    else:
        df['command'] = df.apply(bla, scope='package_only', axis=1)
        df.to_csv('{}/log_broken.csv'.format(path_rel))
        list_command = df['command'].tolist()
    with open("{}/D4j_broken_test.sh".format(path_rel), 'w+') as f:
        f.write('#!/usr/bin/env bash\n')
        f.write('\nATG="/home/ise/eran/repo/ATG/"\n\n')
        for item in list_command:
            f.write('{}\n\n'.format(item))


def fix_error_no_gen_test(path_to_file):
    df = pd.read_csv(path_to_file, index_col=0)
    path_rel = '/'.join(str(path_to_file).split('/')[:-1])
    print list(df)
    df['command'] = df.apply(bla, scope='package_only', axis=1)
    list_command = df['command'].tolist()
    with open("{}/D4j_script_no_gen.sh".format(path_rel), 'w+') as f:
        f.write('#!/usr/bin/env bash\n')
        f.write('\nATG="/home/ise/eran/repo/ATG/"\n\n')
        for item in list_command:
            f.write('{}\n\n'.format(item))


def bla(row, scope):
    time = str(row['time_budget'])
    proj = str(row['project'])
    id_bug = str(row['bug_ID'])
    command = 'sudo env "PATH=$PATH" python /home/ise/eran/repo/ATG/defects_lib.py d4j -i /home/ise/eran/D4J/info/ -M U -C 0 -d /home/ise/programs/defects4j/framework/bin -b {0} -r {1}-{1} -o /home/ise/eran/D4j/out/ -t {3} -p {2} -k U'.format(
        time, id_bug, proj, scope)
    return command


def get_results(root='/home/ise/eran/eran_D4j'):
    '''
    this function get the results out of the maven framework d4j after the (fixer_maven-function) process
    '''
    dirs = pt.walk_rec(root, [], 'csvs', False, lv=-3)
    df_big = None
    list_emmpty = []
    if len(dirs) == 0:
        print "didnt fine any csvs in path {}".format(root)
    for dir_csv in dirs:
        print dir_csv
        files_csv = pt.walk_rec(dir_csv, [], '.csv')
        if len(files_csv) > 1:
            df_fix = pd.read_csv("{}/fix_TEST.csv".format(dir_csv), index_col=0)
            df_fix.rename(columns={'class_err': 'fix_class_err', 'class_fail': 'fix_class_fail', 'err': 'fix_err',
                                   'fail': 'fix_fail'}, inplace=True)
            df_buggy = pd.read_csv("{}/buggy_TEST.csv".format(dir_csv), index_col=0)
            df_buggy.rename(
                columns={'class_err': 'buggy_class_err', 'class_fail': 'buggy_class_fail', 'err': 'buggy_err',
                         'fail': 'buggy_fail'}, inplace=True)
            d = {"path": dir_csv}
            is_empty = False
            if len(df_fix) == 0:
                is_empty = True
                d["is_fix_empty"] = 1
            if len(df_buggy) == 0:
                d["is_buggy_empty"] = 1
                is_empty = True
            if is_empty:
                list_emmpty.append(d)
                continue
            del df_fix['bug']
            del df_buggy['bug']

            df_merg = df_buggy.merge(df_fix, on=['bug_ID', 'time_budget', 'project', 'name'], how='outer')

            df_merg.to_csv('{}/merge.csv'.format(dir_csv))
            if df_big is None:
                df_big = df_merg
            else:
                df_big = pd.concat([df_big, df_merg])
    if df_big is not None:
        df_big.to_csv('{}/all_df_merg.csv'.format(root))
    if len(list_emmpty) > 0:
        df_empty = pd.DataFrame(list_emmpty)
        df_empty.to_csv('{}/is__empty.csv'.format(root))
    exit(0)


def copytree(src, dst, symlinks=False, ignore=None):
    import shutil
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def read_scope_test_gen(out_dir):
    '''
    read the scope that the test was generted in the out dir loging dir scope.txt
    '''
    lines = None
    if os.path.isfile('{}/loging/scope.txt'.format(out_dir)):
        with open('{}/loging/scope.txt'.format(out_dir), 'r+') as f:
            lines = f.readlines()
            lines = lines[0]
    if lines[-1]=='\n':
        lines=lines[:-1]
    return lines


def wrapper_make_oracle_target_folder(root_package, out_dir_root, copy=True, debug=True):
    if out_dir_root[-1] == '/':
        out_dir_root = out_dir_root[:-1]
    d_list = []
    print "[py] starting to copy dir-tree ...."
    if copy:
        copytree(root_package, out_dir_root)
    print "[py] done copy"
    log_dir_gen = pt.mkdir_system(out_dir_root, 'log_generated_tests', True)
    file_out = pt.walk_rec(out_dir_root, [], 'OUT', False, -2)
    for out_dir in file_out:
        if debug:
            print "[Debug] {}".format(out_dir)
        dir_info = None
        scope_gen = read_scope_test_gen(out_dir)
        project_name = str(out_dir).split('/')[-1].split('_')[1]
        if os.path.isdir('{}/fault_components'.format(out_dir)):
            dir_info = '{}/fault_components'.format(out_dir)
        else:
            raise Exception('No dir info: fault_components in path : {}'.format(out_dir))
        list_bug_dir = pt.walk_rec(out_dir, [], 'P_', False, lv=-1)
        for bug_dir in list_bug_dir:
            if debug:
                print "[Debug] {}".format(bug_dir)

            # ram all TEST folder in the bug_dir
            list_test = pt.walk_rec(bug_dir, [], 'Test', False, lv=-2)
            command_rm_test = 'rm -r '
            for dir_test in list_test:
                print "[OS] {}{}/*".format(command_rm_test, dir_test)
                os.system('{}{}/*'.format(command_rm_test, dir_test))
            BUG_ID = str(bug_dir).split('/')[-1].split('_')[3]
            tar_files = pt.walk_rec(bug_dir, [], 'tar.bz2')
            for tar_file in tar_files:
                it_number = str(tar_file).split('/')[-1].split('.')[1]
                out = '/'.join(str(tar_file).split('/')[:-1])
                time_budget = str(tar_file).split('t=')[1].split('/')[0]
                d = {'project': project_name, 'bug_ID': BUG_ID, 'time_budget': time_budget, 'iteration': it_number}
                bol, msg, faulty, gen_dico = unzip_get_the_faulty_components(BUG_ID, project_name, tar_file, dir_info,
                                                                             out, rm=True)
                d['msg'] = msg
                d['boolean'] = bol
                d['faulty'] = faulty
                d['scope'] = scope_gen
                d['actual_scope_size'] = add_actual_scope_size(BUG_ID, dir_info)
                d['generated tests'] = len(gen_dico)
                path_log = log_gen_test(log_dir_gen, gen_dico.keys(),
                                        "{}_{}_{}".format(project_name, BUG_ID, it_number))
                d['log_test_path'] = path_log
                d_list.append(d)
    df = pd.DataFrame(d_list)
    df.to_csv('{}/log.csv'.format(out_dir_root))
    re_gen_broken_test('{}/log.csv'.format(out_dir_root))
    name_new_dir = str(out_dir_root).split('/')[-1]
    name_old_dir = out_dir_root.split('/')[-1]
    init_testing_pahse(out_dir_root, name_new_dir, 'out')
    return


def log_gen_test(path, list_item, name):
    with open("{}/{}".format(path, '{}.log'.format(name)), 'a') as f:
        for item in list_item:
            f.write(item)
            f.write('\n')
    return "{}/{}".format(path, '{}.log'.format(name))


def unzip_get_the_faulty_components(bug_id, project_name, path_zip_file, fault_dir_info, path_out, rm=False,
                                    debug=True):
    '''
    :param bug_id: the bug ID
    :param project_name:  project name
    :param path_zip_file: path to the zip file, where all Evosuite TESTs
    :param fault_dir_info: where can find the info bug_ids folder
    :param path_out: where to write the test
    :param debug:
    :return:  False or True (indeicated if the function invoke in a good what) msg (info what go wrong) modify_class
    , generated_tests ky_package:[Test,_Test_scaffolding]
    '''
    modified_classes = []
    zip_name = str(path_zip_file).split('/')[-1]
    max_bug_id = project_dict[project_name]['num_bugs']
    if int(bug_id) > max_bug_id:
        msg = "[Error] the max bug id in " \
              "project: {} is {} ---> bug_id:{}".format(project_name, max_bug_id, bug_id)
        print msg
        return False, msg, None, None
    if os.path.isfile('{}/bug_{}.txt'.format(fault_dir_info, bug_id)) is False:
        msg = "[Error] missing bug_{}.txt file in {}".format(bug_id, fault_dir_info)
        print msg
        return False, msg, None, None
    with open('{}/bug_{}.txt'.format(fault_dir_info, bug_id), 'r+') as f_bug:
        for line in f_bug:
            modified_classes.append(line[:-1])
    if len(modified_classes) < 1:
        msg = "[Error] the modified_classes is empty file: {} ".format('{}/bug_{}.txt'.format(bug_id))
        print msg
        return False, msg, modified_classes, None
    if debug:
        print "[Debug] modified_classe:= {}".format(modified_classes)
    return extract_tar(path_zip_file, path_out, filter_only=modified_classes, f_name=zip_name, del_tar=rm,
                       p_name=project_name)


def GET_test_generated(path_tests, p_name):
    dico_package_test = {}
    suffix = '_ESTest.java'
    prefix_package = project_dict[p_name]['prefix']
    size_suffix = len(suffix)
    suffix_2 = '_ESTest_scaffolding.java'
    size_suffix_2 = len(suffix_2)
    tests_res_l = pt.walk_rec(path_tests, [], '.java')
    for file_java in tests_res_l:
        java_name = str(file_java).split('/')[-1]
        if java_name.__contains__('scaffolding'):
            package = pt.path_to_package(prefix_package, file_java, -size_suffix_2)
        else:
            package = pt.path_to_package(prefix_package, file_java, -size_suffix)
        if package in dico_package_test:
            dico_package_test[package].append(file_java)
        else:
            dico_package_test[package] = [file_java]
    return dico_package_test


def extract_tar(path_in, path_out, f_name, p_name ,format_file='bz2', filter_only=None, compress=True, del_tar=False,
                ):
    '''
    this function heandel the process of extracting the zip files
    '''
    import tarfile
    bol = True
    msg = 'null'
    tar = tarfile.open("{}".format(path_in), "r:{}".format(format_file))
    tar.extractall(path_out)
    tar.close()
    dico_test = GET_test_generated(path_out, p_name)
    if filter_only is not None:
        ctr_rm = 0
        for key_pack in dico_test.keys():
            list_path_test = dico_test[key_pack]
            if key_pack in filter_only:
                continue
            else:
                for path_test_i in list_path_test:
                    ctr_rm += 1
                    command_rm = 'rm {}'.format(path_test_i)
                    print "[OS] {}".format(command_rm)
                    os.system(command_rm)
        if ctr_rm == len(dico_test.keys()) * 2:
            msg = '[Error] all java file deleted --> {}'.format(path_in)
            print msg
            return False, msg, filter_only, dico_test
        x = float((len(dico_test.keys()) * 2) - ctr_rm) / 2.0
        if x == float(len(filter_only)):
            bol = True
            msg = '[good]'
        else:
            bol = False
            msg = '[Error] not all modified_classes generated'
    if del_tar:
        command_rm = 'rm {}'.format(path_in)
        print '[OS] {}'.format(command_rm)
        os.system(command_rm)
    if compress:
        dir_compress = pt.walk_rec(path_out, [], '', False, lv=-1)
        if len(dir_compress) == 1:
            target = dir_compress[0]
            with tarfile.open("{}/{}".format(path_out, f_name), "w|{}".format(format_file)) as tar:
                tar.add(path_out, arcname='.')
    return bol, msg, filter_only, dico_test


def add_actual_scope_size(bug_id, path_dir, scope='package_only'):
    '''
    add to a dataframe the number of scope that need to be generated
    '''
    lines = None
    if scope == 'package_only' or scope == 'package_rec':
        with open('{}/class_{}.txt'.format(path_dir, bug_id), 'r+') as f:
            lines = f.readlines()
        if lines is not None:
            return len(lines)
    elif scope == 'target':
        with open('{}/bug_{}.txt'.format(path_dir, bug_id), 'r+') as f:
            lines = f.readlines()
        if lines is not None:
            return len(lines)
    return None


def main_parser():
    if len(sys.argv) == 1:
        print "--- no args given ---"
        return
    if sys.argv[1] == 'fixer':
        fixer_maven(sys.argv[2])
    elif sys.argv[1] == 'merg':
        get_results()
    elif sys.argv[1]=='T':
        if str(sys.argv[2]).__contains__('oracle'):
            init_testing_pahse(sys.argv[2],'oracle')
    elif sys.argv[1] == 'res':
        if sys.argv[2] == 'all':
            res_dir_oracle = pt.walk_rec('/home/ise/eran/D4j/oracle',[],'',False,lv=-1)
            res_dir_out = pt.walk_rec('/home/ise/eran/D4j/out',[],'',False,lv=-1)
            res_dir_oracle = [x for x in res_dir_oracle if str(x).split('/')[-1].__contains__('_') is False]
            res_dir_out  = [x for x in res_dir_out if str(x).split('/')[-1].__contains__('_') is False]
            all = res_dir_oracle + res_dir_out
            for path in all :
                get_results_junit(path)
        else:
            get_results_junit(sys.argv[2])
    elif sys.argv[1] == 'd4j':
        sys.argv = sys.argv[1:]
        init_main()
    elif sys.argv[1] == 'oracle':
        if len(sys.argv) == 2:
            p_path ='/home/ise/eran/D4j/out'
        else:
            p_path = sys.argv[2]
        path_rel = '/'.join(str(p_path).split('/')[:-1])
        out_dir_oracle = pt.mkdir_system(path_rel, 'oracle', True)
        wrapper_make_oracle_target_folder(p_path, out_dir_oracle)
    elif sys.argv[1] == 'not_gen':
        fix_error_no_gen_test(sys.argv[2])
    elif sys.argv[1] == 'mvn_target':
        project_name = sys.argv[2]
        make_target_mvn_framework(p_name=project_name)
    elif sys.argv[1] == 'd4j_mvn':
        sys.argv = sys.argv[1:]
        main_wrapper()
    elif sys.argv[1] == 're_test':
        if len(sys.argv) > 2:
            ver_path = sys.argv[2]
        else:
            ver_path = '/home/ise/eran/D4j/out'
        re_test_OUT_dirs(ver_path)
    elif sys.argv[1] == 'change_evo':
        ver = sys.argv[2]
        util_d4j.change_runtime_and_gen_jars(ver)
    else:
        print "undfiend command [d4j_mvn / d4j / fixer ] "


def re_test_OUT_dirs(root_father_out):
    out_dirs_list = pt.walk_rec(root_father_out, [], 'OUT_', False, lv=-2)
    dico_parm = {'r': '', 'b': '', 'k': '', 't': ''}
    for out_dir in out_dirs_list:
        p_name = str(out_dir).split('/')[-1].split('_')[1]
        dico_parm['o'] = out_dir
        dico_parm['p'] = p_name
        obj_d4j = D4J_tool(out_dir=dico_parm['o'], project=dico_parm['p'], bug_range=dico_parm['r'],
                           time_b=dico_parm['b'],
                           csv_fp_path=dico_parm['k'], scope_p=dico_parm['t'], info_d=dico_parm)
        obj_d4j.test_process(out_dir)


if __name__ == "__main__":
    '''
    # sudo env "PATH=$PATH" python
    '''
    before_op()
    out = '/home/ise/eran/D4j/oracle/P_Chart_B_4_M_U_D_Mon_Aug_20_01_02_31_2018/t=5/Chart/evosuite-branch/0'
    faulty_dir = '/home/ise/eran/D4j/out/OUT_Chart_D_Mon_Aug_20_01_02_16_2018/fault_components'
    zip = '/home/ise/eran/D4j/out/OUT_Chart_D_Mon_Aug_20_01_02_16_2018/P_Chart_B_4_M_U_D_Mon_Aug_20_01_02_31_2018/t=5/Chart/evosuite-branch/0/Chart-4f-evosuite-branch.0.tar.bz2'

    args = "py. -p Mockito -o /home/ise/Desktop/defect4j_exmple/ex2/ \
            -e /home/ise/eran/evosuite/jar/evosuite-1.0.5.jar -b 5 -l 1\
            -u 100 -f True -t info -r 1-555 -z 2;4;6;10;20;50 "

    p_path = '/home/ise/eran/D4j/OUT_Time_D_Sat_Jul_21_17_54_36_2018'
    p_path = '/home/ise/Desktop/d4j_framework/out/OUT_Time_D_Sat_Jul_21_17_59_42_2018'
    p_path = '/home/ise/eran/eran_D4j'
    # get_problamtic_dirs(p_path)
    #
    # get_faulty_comp()
    #
    # get_results_junit()
    # wrapper_get_all_results_D4j('/home/ise/Desktop/d4j_framework/out/')
    ### make_uniform_package_dict()

    # args = 'pp d4j -i /home/ise/eran/D4J/info/ -M U -C 0 -d /home/ise/programs/defects4j/framework/bin -b 2 -r 100-100 -o /home/ise/eran/D4j/out/ -t package_only -p Closure -k U'
    #args = 'py res all'
    #sys.argv=args.split()
    main_parser()
    # fixer_maven(p_path)
    # main_wrapper(args)
    exit()

    # init_main()
    # test_process()
    # get_FP_csv_by_ID("/home/ise/Desktop/defect4j_exmple/ex2")
    # check_FP_prediction_vs_reality('Math')
    # path_test = '/home/ise/Desktop/defect4j_exmple/d4j_csv/'
    # memreg_all_df(path_test)
    # exit()
    # get_statistic(path_test)
    ########################
    # analysis_dir(path_test)
    # exit()
    ##################
