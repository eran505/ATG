import sys,csv
import pit_render_test
import pandas as pd
import numpy as np

def get_time_from_path(str_path,prefix):
    pos_time_bud=str(str_path).find(prefix)
    if pos_time_bud < 0 :
        return ""
    index = pos_time_bud + len(prefix)
    acc=""
    while index < len(str_path) :
        if str_path[index] == "_" or str_path[index]=='/':
            break
        acc = acc + str_path[index]
        index+=1
    return acc

def mereg_df(list_df,key):
    if len(list_df)>1:
        df_merge = list_df[0]
        for i in range(1,len(list_df)):
            df_merge=df_merge.merge(list_df[i], on=key, how='outer')
        return df_merge
    elif len(list_df) == 1 :
        return list_df
    else:
        raise Exception("Error in mereg_df function with key="+key)

def analyse_budget(root_path_csv,out_path_name):
    print "starting...."
    walker = pit_render_test.walker(root_path_csv)
    list_csv= walker.walk("statistics.csv")
    list_df = []
    list_dic_df={}
    #df_ans = pd.DataFrame()
    for item in list_csv:
        time_str = get_time_from_path(str(item),"_t=")
        df_item = pd.read_csv(str(item))
        #print list(df_item)
        df_item_budget = pd.DataFrame(df_item[[' TARGET_CLASS','Total_Time']])
        df_item_budget['Total_Time_'+time_str] = df_item_budget['Total_Time']
        del df_item_budget['Total_Time']

        if time_str in list_dic_df:
            list_dic_df[time_str].append(df_item_budget)
            df_ans = pd.DataFrame(df_item_budget[' TARGET_CLASS'].copy())
        else:
            list_dic_df[time_str] = [df_item_budget]
        list_df.append(df_item_budget)
    print "done"
    list_fin_df=[]

    if len(list_dic_df)>1:
        for key in list_dic_df.keys():
            budget_df_i=mereg_df(list_dic_df[key],' TARGET_CLASS')
            list_col = list(budget_df_i)
            print key
           # print budget_df_i
            list_col.remove(' TARGET_CLASS')
            budget_df_i["mean_"+key] = budget_df_i[list_col].mean(axis=1)
            df_ans = df_ans.merge(budget_df_i[[' TARGET_CLASS',"mean_"+key]], on=' TARGET_CLASS', how='outer')
            #df_ans["mean_"+key] = budget_df_i["mean_"+key].copy()

        df_ans.to_csv(out_path_name, encoding='utf-8', index=False)


def clean_path_math(p,sufix='.class',prefix='/org/'):
    p_str = str(p)
    if len(p)<1:
        return 'null-str'
    val = p_str.find(prefix)
    val_end = p_str.find(sufix)
    if val == -1 :
        return 'null-org'
    ans = p_str[val+1:val_end]
    ans = ans.replace('/','.')
    return  ans

def origin_java(root_path_java):
    walker = pit_render_test.walker(root_path_java)
    list_java = walker.walk(".class",True,-1)
    filter_java = [klass for klass in list_java if not str(klass).__contains__("$")]
    list_java = []
    for x in filter_java :
        list_java.append(clean_path_math(x))
    return list_java



class ProjectCase:
    def __init__(self,path,or_list):
        self._path = path
        self.origin_list = or_list
        self.time = -1
        self.it=-1
        self.mode = 'null'
        self.dict = self.pre_process()
        self.analysis()
    def pre_process(self):
        dict_res = {}
        str_path = str(self._path)
        sufix= str_path.find("_it=")
        prefix=str_path.find("ALL_")+4
        arr= str_path[prefix:sufix].split("__t=")
        self.time = arr[1]
        self.mode = arr[0]
        sufix= str_path.find("_it=")+4
        self.it = str_path[sufix:]
        for x in self.origin_list:
            dict_res[x]={"generate":0}
        return dict_res

    def analysis(self):
        walker = pit_render_test.walker(self._path)
        list_java = walker.walk("ESTest.java")
        list_txt = walker.walk("ESTest.txt")
        list_class = walker.walk("ESTest.class")
        list_java,list_txt,list_class = self.list_clean(list_java,list_txt,list_class)
        for klass in list_java :
            if klass[0][:-7] in self.dict:
                self.dict[klass[0][:-7]]={"generate":1 ,"un_compile":1 , "report":0 }
        for comp_klass in list_class:
            if  comp_klass[0][:-7] in self.dict:
                tmp = self.dict[comp_klass[0][:-7] ]
                tmp["compile"] = 1
                tmp["un_compile"]=0
            else:
                raise Exception("[Exception] file in txt but not in java: ",comp_klass[0])
        for txt_f in list_txt:
            if txt_f[0][:-7] in self.dict:
                tmp = self.dict[txt_f[0][:-7] ]
                tmp["p"] = txt_f[1]
                tmp["report"] = 1
            else:
                raise Exception("[Exception] file in txt but not in java: ",txt_f[0])
        self.read_txt()
        return self.dict
    def list_clean(self,list_java,list_txt,list_class):
        new_list_java=[]
        new_list_txt=[]
        new_class_list=[]
        for z in list_class:
            new_class_list.append([clean_path_math(z, ".class"), z])
        for x in list_java:
            new_list_java.append([clean_path_math(x,".java"),x])
        for y in list_txt:
            new_list_txt.append([clean_path_math(y,".txt","/org."),y])
        return  new_list_java,new_list_txt,new_class_list
    def read_txt(self):
        for var in self.dict.values():
            if "un_compile" in var and var["report"]==1 :
                p = var["p"]
                del var["p"]
                with open(p) as f:
                    lines = f.readlines()
                    if len(lines ) > 2:
                        run, Failures, Errors, Skipped = self.get_info(lines[3])
                        var["run"]=int(run)
                        var["Failures"]=int(Failures)
                        var["Errors"] =int(Errors)
                        var["Skipped"] =int(Skipped)
    def get_info(self,info_str):
        arr = info_str.split(',')
        if len(arr )>3:
            b_run = arr[0].find(": ")+2
            b_Failures = arr[1].find(": ")+2
            b_Errors = arr[2].find(": ")+2
            b_Skipped = arr[3].find(": ")+2
            run = arr[0][b_run:]
            Failures=arr[1][b_Failures:]
            Errors = arr[2][b_Errors:]
            Skipped = arr[3][b_Skipped:]
            return run,Failures,Errors,Skipped
        raise Exception("prass" ,info_str)

class BigProject:
    def __init__(self,path,list_p):
        self._path = str(path)
        self._time = -1
        self.list_org = list_p
        self.proj_list = []
        self.dict_fin_all = { "Errors":0 , "report":0,"run":0 , "compile":0 , "un_compile":0 , "Skipped":0 ,"Failures":0 , "generate":0 ,"size":0 }
        self.dict_fin_FP = {}
        self.dict_fin_U = {}
        self.constractor()
        self.merge_all()
    def constractor(self):
        for x in self.list_org:
            self.dict_fin_U[x] = { "Errors":0 , "report":0, "run":0 , "compile":0 , "un_compile":0 , "Skipped":0 ,"Failures":0 , "generate":0 ,"size":0 }
            self.dict_fin_FP[x] ={ "Errors":0 ,"report":0, "run":0 , "compile":0 , "un_compile":0 , "Skipped":0 ,"Failures":0 , "generate":0 ,"size":0 }
        prefix = self._path.find("_t=")+3
        suf = self._path.find("_/pit_test")
        self._time =  self._path[prefix:suf]
        walker = pit_render_test.walker(self._path)
        list_projects = walker.walk("ALL_",False,0)
        for p in list_projects:
            tmp_obj = ProjectCase(p,self.list_org)
            self.proj_list.append(tmp_obj)
    def merge_all(self):
        if len(self.proj_list) > 1 :
            for dict_proj in self.proj_list:
                #print "T=",dict_proj.time,'M=',dict_proj.mode,"it=",dict_proj.it
                for item_dic in dict_proj.dict.keys():
                    if dict_proj.mode =='U':
                        self.mereg_dict(self.dict_fin_U[item_dic],dict_proj.dict[item_dic])
                    elif dict_proj.mode =="FP":
                        self.mereg_dict(self.dict_fin_FP[item_dic], dict_proj.dict[item_dic])
                    else :
                        raise Exception("mode = null",dict_proj._path)
                    self.mereg_dict(self.dict_fin_all, dict_proj.dict[item_dic])
    def mereg_dict(self,big_dict,dico):
        for item in dict(dico).keys():
            big_dict[item]+=dico[item]
        big_dict["size"]+=1

def analysis(root,li_org):
    walker = pit_render_test.walker(root)
    list_dir = walker.walk("t=",False,0)
    object_fin_arr = []
    for dir_p in list_dir:
        obj_main = BigProject(dir_p+"/pit_test/", li_org)
        object_fin_arr.append(obj_main)
    return object_fin_arr

def flush_data(list_obj,path):
    if len(list_obj)>1:
        li_all={}
        for budget_object in list_obj:
            time_name = budget_object._time
            li_all[time_name]=budget_object.dict_fin_all
            data_to_csv(budget_object.dict_fin_FP,path,'FP_t='+time_name,'class')
            data_to_csv(budget_object.dict_fin_U,path,'U_t='+time_name,'class')
        data_to_csv(li_all,path,'ALL','time_budget')

def data_to_csv(dico,path,name,k_name):
    li_dic = []
    for k, v in dico.iteritems():
        d = v
        d[k_name] = k
        li_dic.append(d)
    keys = li_dic[0].keys()
    with open(path+name+'.csv', 'wb') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(li_dic)

def main(math_p,dir_p,out_p):
    li = origin_java(math_p)
    li_obj = analysis(dir_p, li)
    flush_data(li_obj,out_p)
    print "done !"


if __name__ == "__main__":
    arr= sys.argv
    #arr = ["","/home/eran/thesis/test_gen/poc/commons-math3-3.5-src/target/classes/org/apache/commons/math3/fraction/",
    #       "/home/eran/Desktop/testing/new_test/","/home/eran/Desktop/mvn/"]
    print("[package_origin_dir(class file)] [input_dir] [out_dir]")
    print "[ root-csv , out_path_csv ] "
    if len(arr) == 4:
        math_p = arr[1]
        dir_p = arr[2]
        out_p=arr[3]
        main(math_p,dir_p,out_p)
    else:
        if len(arr) == 3:
            analyse_budget(arr[1],arr[2])

