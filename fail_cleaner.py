import time

import pit_render_test
import xml.etree.ElementTree
import os,re

class Cleaner:
    def __init__(self, Path_mvn ,_remove=False,Clean_Fail=True,Clean_Error=True,test_out = 'target/surefire-reports/'):
        self.out_path = self.mod_path(Path_mvn)
        self.mvn_path = self.mod_path(Path_mvn)
        self.remove_whole = _remove
        self.clean_fail = Clean_Fail
        self.clean_error = Clean_Error
        self.test_dir = test_out
        self.const_src_test = "src/test/java/"
        self.log_unexpected = ""
        self.file_unexpected =""
        self.logs = ''
        self.max = 4

    def mkdir_logs(self):

        dir_path = ''
        if self.mvn_path[-1] == '/':
            dir_path=self.mvn_path+"logS/"
        else:
            dir_path = self.mvn_path + "/logS/"
        if os.path.isdir(dir_path):
            self.logs = dir_path
        else:
            os.system("mkdir {}".format(dir_path))
            self.logs = dir_path
        if os.path.isdir(dir_path+"unexpected/"):
            self.log_unexpected = dir_path+"unexpected/"
        else:
            os.system("mkdir {}".format(dir_path+"unexpected/"))
            self.log_unexpected = dir_path+"unexpected/"
        self.file_unexpected = "unexpected_{}.txt".format(self.get_time())
        os.system("touch {}{}".format(self.log_unexpected,self.file_unexpected))


    def get_time(self):
        localtime = time.asctime(time.localtime(time.time()))
        localtime_arr = str(localtime).split()
        localtime_arr = localtime_arr[1:]
        localtime = "_".join(localtime_arr)
        localtime = str(localtime).replace(':',"")
        print localtime
        return str(localtime)

    def fit(self):
        self.mkdir_logs()
        print "*"*70 + "New" + "*"*70
        print "mvn_path = {}".format(self.mvn_path)
        for i in range(self.max):
            print "mvn clean test "
            os.chdir(self.mvn_path)
            command = "mvn clean test >> {}out_test_{}.txt  2>&1 ".format(self.logs,self.get_time())
            print command
            os.system(command)
            arr = self.get_outputs_test(False)
            res = []
            if arr is None:
                print "no path found arr in function fit"
                return
            set_arr =set(arr)
            print "set_len:",len(set_arr)
            print "arr_len:",len(arr)
            arr = list(set_arr)
            for xml in arr :
                f,e,all = self.pars_xml(xml)
                res += all
            text_file = open(self.logs+"clear_{0}_.txt".format(self.get_time()), "w")
            if len(res) == 0 :
                text_file.write("%s\n" % "{}")
                return
            for item in res:
                text_file.write("%s\n" % item)
            text_file.close()
            if i == self.max-1:
                text_file = open(self.logs + "BUG_{0}_.txt".format(self.get_time()), "w")
                text_file.write("%s\n" % "BUG")
                text_file.close()


    def mod_path(self,path):
        if path[-1] == '/':
            return path
        else:
            path = path+'/'
            return path

    def intTryParse(self,value):
        try:
            return int(value),True
        except ValueError:
            return value, False

    def get_outputs_test(self,clean=True):
        if clean:
            os.chdir(self.mvn_path)
            os.system("mvn clean test >> out_test_start.txt  2>&1")
        if (os.path.isdir(self.mvn_path+self.test_dir)):
            all_xml = pit_render_test.walk(self.mvn_path+self.test_dir,".xml",)
            if len(all_xml) == 0 :
                print "[Error] No XML files found in {}".format(self.mvn_path+self.test_dir)
                return None
            return all_xml
        else:
            print "[Error] No directory {0} in {1}".format(self.test_dir,os.getcwd())
            return None

    def _insert_to_d(self,d,key,val):
        key_path = self._prefix_to_path(key)
        if key in d:
            d[key]['bug'].append(val)
        else:
            key_path['bug'] = [val]
            d[key]=key_path
    def _prefix_to_path(self,prefix):
        arr = str(prefix).split('.')
        class_name = arr[-1]
        path = '/'.join(arr[:-1])
        return {"class_name":class_name,"path":path+'/'}


    def pars_xml(self,path_file):
        err={}
        fail={}
        all = []
        if str(path_file).__contains__('mbeddedRungeKuttaIntegrator'):
            print ""
        root_node = xml.etree.ElementTree.parse(path_file).getroot()
        val,bol = self.intTryParse(root_node.attrib['errors'])
        if bol is False:
            print "[Error] cant parse the xml file error val input : {}".format(path_file)
        errors_num = val
        val,bol = self.intTryParse(root_node.attrib['failures'])
        if bol is False:
            print "[Error] cant parse the xml file failures val input : {}".format(path_file)
        failures_num = val
        #print "err={}  fial={} ".format(errors_num,failures_num)
        if failures_num or errors_num > 0:
            for elt in root_node.iter():
                if elt.tag == 'testcase':
                    if len(elt._children)>0:
                        for msg in elt:
                            if msg.tag == 'error':
                                self._insert_to_d(err,elt.attrib['classname'],elt.attrib['name'])
                            elif msg.tag == 'failure':
                                self._insert_to_d(fail, elt.attrib['classname'], elt.attrib['name'])
                            all.append( str(elt.attrib['classname']) +" --- "+  str(elt.attrib['name']) )
        if len(fail) or len(err) > 0:
            print "in"
            self.del_test_cases(fail,err)
        return err,fail,all

    def _del_class(self,p_path):
        scaffolding = "_ESTest_scaffolding.java"
        res = str(p_path).split('/')
        class_name_arr = res[-1].split("_")
        name = class_name_arr[0]
        name = name + scaffolding
        res[-1]=name
        scaff_path = '/'.join(res)
        if os.path.isfile(scaff_path) and os.path.isfile(p_path):
            print "scaff_path = {}".format(scaff_path)
            print "p_path = {}".format(p_path)
            os.system("rm {}".format(scaff_path))
            os.system("rm {}".format(p_path))
            return True
        else:
            print "[Error] problem with the del file class function-->"
            bol2 = os.path.isfile(scaff_path)
            bol1 = os.path.isfile(p_path)
            if bol1 is False:
                print "[Error] the file: {} is not exists in the filesystem".format(p_path)
            if bol2 is False:
                print "[Error] the file: {} is not exists in the filesystem".format(scaff_path)
            exit(-1)

    def unexpected_del(self,p):
        with open('{}{}'.format(self.log_unexpected,self.file_unexpected), 'a') as f:
            f.write("file={} date={}\n".format(p,self.get_time()))
        self._del_class(p)


    def _fix_del(self,p,lis_del):
        list_to_remove=[]
        ctr = 0
        d={}
        to_del=[]
        for it in lis_del:
            val, bol = self.intTryParse(it[4:])
            if bol is False:
                if "initializationError" == it:
                    self._del_class(p)
                    return
                else :

                    print "[Error] cant parss in fix the test case {} , in {}".format(it, p)
                    self.unexpected_del(p)
                    return
            to_del.append(val)
        size = 0
        counter=-1
        with open(p, 'r') as myfile:
            data = myfile.read()
            arr=str(data).split('\n')
            size = len(arr)
            print "S={}".format(size)
            for x in arr :
                counter+=1
                if x.__contains__("@Test"):
                    name = self.get_name_func(arr[counter+1])
                    d[name] = counter
                    ctr=name
            ctr+=1
            d[ctr]=size-2
        ''''
        k_list_size = len(d.keys())
        acc=-1
        print "d=",d
        for key in d.keys():
            acc+=1
            if acc >=k_list_size-1:
                continue
            string =  arr[d[key]+1]
            for test_case in lis_del:
                if str(test_case).__contains__(string):
                    list_to_remove.append(key)
        print "list_to_remove: ", list_to_remove
        print "lis_del: ",lis_del
        print "~"*200
        return

        '''

        sorted(to_del, reverse=True)
        to_del.sort()
        to_del = list(reversed(to_del))
        print to_del
        print d
        for intger in to_del:
            range_start  = d[intger]
            next  = self._get_next(d,intger)
            range_end = d[next]
            arr=arr[:range_start] + arr[range_end:]
        cla = str(p).split('/')
        pp= "/home/ise/Desktop/out/"+cla[-1]
        text_file = open(p, "w")
        text_file.write('\n'.join(arr))
        text_file.close()

    def _get_next(self,d,key):
        list_key = dict(d).keys()
        for k in list_key:
            if k>key:
                return k
        print "[Error] in get_next no bigger key "
        exit()

    def get_name_func(self,string_func):
        #print string_func
        acc=""
        #  public void test0()  throws Throwable  {
        res = string_func.split(" ")
        for x in res:
            if x.__contains__("test") and x.__contains__("("):
                for w in x[4:]:
                    if w in ["0","1","2","3","4","5","6","7","8","9"]:
                        acc+=w
        #print "acc={}".format(acc)
        val,bol = self.intTryParse(acc)
        if bol is False:
            print "[Error] in parsing function name cant pars to INT {}".format(string_func)
            exit()
        if len(acc)==0:
            print "[Error] in parsing function name {}".format(string_func)
            exit()
        #print "val=",val
        return val


    def del_test_cases(self,del_dico,del_err_d):
        print "#"*200
        print "del_d = ",del_dico
        print "#" * 200
        if len(del_dico) == 0 :
            del_dico=del_err_d
            del_err_d={}
        absolute_path = self.mvn_path+self.const_src_test
        print "-->del_dico=",del_dico
        for key in del_dico.keys():
            item = del_dico[key]
            p = absolute_path + item['path'] +item['class_name']+".java"
            if os.path.exists(p):

                if len(del_err_d) >  0 :
                    input = item['bug'] + del_err_d[key]['bug']
                    input = list(set(input))
                else:
                    input = item['bug']
                self._fix_del(p,input)

import sys

def get_all_project(path):
    projes = pit_render_test.walk(path,"commons-math3-3.5-src",False)
    return projes


if __name__ == "__main__":

#    args = sys.argv
    args = sys.argv
    if len(args) == 2 :
        proj_arr = get_all_project(args[1])
        for p_path in proj_arr:
            obj = Cleaner(p_path)
            obj.fit()
    else:
        print "No Path was given !!"
