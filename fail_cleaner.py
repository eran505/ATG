import pit_render_test
import xml.etree.ElementTree
import os

class Cleaner:
    def __init__(self, Path_mvn ,_remove=False,Clean_Fail=True,Clean_Error=True,test_out = 'target/surefire-reports/'):
        self.out_path = self.mod_path(Path_mvn)
        self.mvn_path = self.mod_path(Path_mvn)
        self.remove_whole = _remove
        self.clean_fail = Clean_Fail
        self.clean_error = Clean_Error
        self.test_dir = test_out
        self.const_src_test = "src/test/java/"



    def fit(self):
        arr = self.get_outputs_test(False)
        res = []
        if arr is None:
            print "no path found arr in function fit"
            return
        for xml in arr :
            res.append(self.pars_xml(xml))
        #os.chdir(self.mvn_path)
        #os.system("mvn clean test")



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
            os.system("mvn clean test")
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
        #print "parsing xml...."
        err={}
        fail={}
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
        if len(fail) or len(err) > 0:
            self.del_test_cases(fail,err)
        return err,fail

    def _fix_del(self,p,lis_del):
        list_to_remove=[]
        ctr = 0
        d={}
        to_del=[]
        for it in lis_del:
            val, bol = self.intTryParse(it[4:])
            if bol is False:
                print "[Error] cant parss in fix the test case {} , in {}".format(it,p)
                exit()
            to_del.append(val)
        size = 0
        counter=-1
        with open(p, 'r') as myfile:
            data = myfile.read()
            arr=str(data).split('\n')
            size = len(arr)
            for x in arr :
                counter+=1
                if x.__contains__("@Test"):
                    d[ctr] = counter
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
            range_end = d[intger+1]
            arr=arr[:range_start] + arr[range_end:]
        cla = str(p).split('/')
        pp= "/home/ise/Desktop/out/"+cla[-1]
        text_file = open(p, "w")
        text_file.write('\n'.join(arr))
        text_file.close()


    def del_test_cases(self,del_dico,del_err_d):
        print "#"*200
        print "del_d = ",del_dico
        print "#" * 200
        if len(del_dico) == 0 :
            del_dico=del_err_d
            del_err_d={}
        absolute_path = self.mvn_path+self.const_src_test
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

if __name__ == "__main__":
    #/home/ise/eran/flaky  /home/ise/Desktop/
    obj = Cleaner("/home/ise/eran/flaky/commons-math3-3.5-src")
    obj.fit()

    exit()
    args = sys.argv
    if len(args) == 2 :
        obj = Cleaner(args[1])
        obj.fit()
    else:
        print "No Path was given !!"
