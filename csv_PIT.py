import os ,sys,re
import pandas as pd
import numpy as np
import csv


import pit_render_test

arr_sign = [ 'KILLED' , 'NO_COVERAGE' ,'SURVIVED' ,'TIMED_OUT' , 'RUN_ERROR' ]

def get_csv_summary(root_p):
    walker=pit_render_test.walker(root_p)
    classes_list = walker.walk("csv")
    return classes_list


def get_all_dir(root_p):
    walker=pit_render_test.walker(root_p)
    classes_list = walker.walk("org",False,0)
    return classes_list

def get_name_CUT(root_p):
    walker=pit_render_test.walker(root_p)
    list_p = walker.walk("html")
    size = len('<h2>Tests examined</h2><ul>*</ul>')
    name = []
    for page in list_p:
        with open(page, 'r') as myfile:
            data = myfile.read()
            data = data.replace('\n','')
            tmp = re.findall('<h2>Tests examined</h2><ul>.*?</ul>',data)
            if tmp == None:
                continue
            if len(tmp)>0 and len(tmp[0])>size:
                name.append(tmp[0][31:-20])
                break
    if len(name) == 0:
        raise Exception("problem with the ", root_p)
    size=len(name[0])
    res_name = name[0][:size/2]
    return res_name


def get_name(path):
    walker=pit_render_test.walker(path)
    name ='null'
    list_p = walker.walk("csv")
    if len(list_p)>0:
        val_s = 'ESTest'
        csv_file = csv.reader(open(path+'/mutations.csv', "rb"), delimiter=",")
        for row in csv_file:
            if str(row[6]).__contains__(val_s) is True:
                name = row[6]
                break
    return name[:len(name)/2]

def make_dcit(all_dir):
    all_data=[]
    for dir in all_dir:
        arr = str(dir).split('/')
        if len(str(arr[len(arr)-1])) < 20 :
            name_class = get_name(dir)
        else :
            name_class = arr[len(arr)-1]
       # name_class = get_name_CUT(dir)
        csv = get_csv_summary(dir)
        d={'name':name_class , 'csv':csv , 'dir':dir }
        all_data.append(d)
    print 'data_size=',len(all_data)
    return all_data


def _data_df(list_data):
    df_list=[]
    error_dir=0
    names_list=["class","method","line"]
    for item in list_data:
        csvs = item['csv']
        #print "name= ",item['name']
        names_list.append(item['name'])
        if len(csvs) > 0 :
            df = pd.read_csv(csvs[0],names = ["class-suffix", "class", "mutation-type", "method","line",item['name'],"test"])
            df.drop(df.columns[[0,len(list(df))-1]], axis=1, inplace=True)
            #df.set_index(["class","method","line"], inplace=True)
            df.reset_index(level=['class','mutation-type','method','line'],inplace=True)
            if len(df) == 47163 :
                df_list.append(df)
            else:
                error_dir+=1
                print item['name']
                del_error_files(item['dir'])
    print 'error_dir=',error_dir
    result = merge_df(df_list)
    return result

def del_error_files(path_err):
    os.system('rm -r '+path_err)

def merge_df(list_df):
    df_all = list_df[0]
    ctr = 0
    while ctr<len(list_df):
        if ctr == 0 :
            ctr += 1
            continue
        df_all = pd.merge(df_all, list_df[ctr], how='inner',on=['index',"class","mutation-type","method","line"])
        ctr += 1
    return df_all


def merge_all_mutation_df(root_p):
    print 'root=',root_p
    all_dir= get_all_dir(root_p)
    dict_mut=make_dcit(all_dir)
    dfs = _data_df(dict_mut)
    print list(dfs)
    return  dfs


def write_to_csv(dest_path ,df):
    df.to_csv(dest_path, encoding='utf-8')

def mean_all(df):    #[ KILLED , NO_COVERAGE ,SURVIVED ,TIMED_OUT , RUN_ERROR
    list_name = list(df)[5:]
    for name  in arr_sign:
        df[name+'_sum'] = (df[list_name] == name).sum(axis=1)
    string = '_sum'
    my_new_list = [x + string for x in arr_sign]
    df['total'] = df[my_new_list].sum(axis=1)
    for it in my_new_list:
        df[it[:-3]+"mean"] = (df[it].astype(float))/df['total']
        df[it[:-3] + "mean_norm"] = (df[it].astype(float)) / df['total']

def name_ext(p):
    print p
    arr = str(p).split('/')
    if len(arr[-1])>2:
        return  arr[-1]
    else :
        return arr[-2]

def delet_csv(root_p):
    walker=pit_render_test.walker(root_p)
    list_p = walker.walk("mutations.csv")
    for csv_f in list_p:
        if str(csv_f).__contains__('org.apache.commons') is True :
            os.system("rm "+csv_f)

def init_clac(arr_path,out):
    ctr=0
    arr_dfs = []
    for path in arr_path :
        name_dir = name_ext(path)
        ctr += 1
        #dfs = merge_all_mutation_df(path+'pit-reports/')
        dfs = merge_all_mutation_df(path+'commons-math3-3.5-src/target/pit-reports/')
        print dfs.shape
        size =  len(list(dfs))
        mean_all(dfs)
        arr_dfs.append({'id':ctr , 'data':dfs})
        #write_to_csv(path+'PIT_'+str(name_dir)+str(size)+'.csv', dfs)
        write_to_csv(out + 'PIT_' + str(name_dir) +"_s="+str(size) + '.csv', dfs)
        #delet_csv(path)
    return arr_dfs


def fin_sum(dict_df_list):
    new_df = dict_df_list[0]['data'][['index',"class","method","line"]].copy()
    total_sum=0.0
    for item in dict_df_list :
        total_sum+= item['data']['total']
        new_df['total_sum'] = total_sum
    for label in  arr_sign :
        new_df[label+'_W_mean']=0.0
        for item in dict_df_list:
            new_df[label+'_W_mean']+=item['data'][label+'_mean']*(item['data']['total']/new_df['total_sum'])
    return new_df



def tmp_csv_fin(path_p):

    walker=pit_render_test.walker(path_p)
    list_p = walker.walk(".csv")
    df_reg=[]
    df_FP=[]
    for p in list_p:
        if str(p).__contains__('FP.csv') is True:
            df_FP.append(pd.read_csv(p))
        else :
            df_reg.append(pd.read_csv(p))
    new_df = df_FP[0][['index',"class","method","line"]].copy()
    counter = 0
    for df in df_FP:
        if counter == 0 :
            new_df['kill_R_FP'] = np.where(df['KILLED_sum'] > 0, 1, 0)
            new_df['total_FP'] = df['total']
        else:
            new_df['total_FP']+=df['total']
            new_df['kill_R_FP'] += np.where(df['KILLED_sum'] > 0 , 1 , 0)
        for leb in arr_sign:
            if counter == 0:
                new_df[leb + '_FP'] = df[leb + '_sum']
            else:
                new_df[leb+'_FP']+=df[leb+'_sum']
        counter+=1
        counter=0
        for df in df_reg:
            if counter == 0:
                new_df['kill_R_uni'] = np.where(df['KILLED_sum'] > 0, 1, 0)
                new_df['total_uni'] = df['total']
            else:
                new_df['total_uni'] += df['total']
                new_df['kill_R_uni'] += np.where(df['KILLED_sum'] > 0, 1, 0)
            for leb in arr_sign:
                if counter == 0:
                    new_df[leb + '_uni'] = df[leb + '_sum']
                else:
                    new_df[leb + '_FP'] += df[leb + '_sum']
            counter += 1
    write_to_csv('/home/eran/Desktop/fin.csv',new_df)
    return  new_df




def clac_by_package(dir_path,path_fp_budget,uni_time):
    walker=pit_render_test.walker(dir_path)
    list_p = walker.walk(".csv")
    arr_uni = []
    arr_fp = []
    for p in list_p:
        if str(p).__contains__('_U_'):
            arr_uni.append(pd.read_csv(p))
        elif str(p).__contains__('_FP_'):
            arr_fp.append(pd.read_csv(p))
    max_num=0
    max_obj=None
    if len(arr_uni)>0:
        for m in arr_uni:
            if len(list(m))>max_num:
                max_obj=m
                max_num = len(list(m))
    elif len(arr_fp)>0 :
        for m in arr_fp:
            if len(list(m))>max_num:
                max_obj=m
                max_num = len(list(m))
    else:
        print ("BAD_Args: no FP or UNI is found")
        exit(0)
    tmper = max_obj
    new_df = tmper[['index',"class","mutation-type","method", "line"]].copy()
    all_df = tmper[['index', "class", "mutation-type", "method", "line"]].copy()
    budget_df = pd.read_csv(path_fp_budget,names = ["class", "pred","time"])
    new_df = pd.merge(new_df, budget_df, how='left', on=["class"])
    new_df['uni_budget'] = uni_time
    new_df['FP_budget'] = np.where(new_df['time'] > int(uni_time), uni_time, new_df['time'])
    #new_df['pred_bug'] = new_df['time'] / float(uni_time)
    del new_df['time']
    list_name = list(tmper)
    res = [k for k in list_name if 'org' in k]
    dict_list=[]
    all_df['UNI'] = 0
    all_df['FP'] = 0
    size_uni = len(arr_uni)
    size_fp = len(arr_fp)

    for k in res:
        ctr_uni = []
        ctr_fp = []
        new_df['UNI'] = 0
        new_df['FP'] = 0
        for df_uni in arr_uni:
            if k in df_uni.columns:
                ctr_uni.append(df_uni)
                continue
        for df_fp in arr_fp:
            if k in df_fp.columns:
                ctr_fp.append(df_fp)
                continue
        if len(ctr_fp)> 0 :
            for df_fp in ctr_fp:
                new_df['FP'] += np.where(df_fp[k] == 'KILLED', 1 , 0)
        if len(ctr_uni)>0:
            for df_uni in ctr_uni:
                new_df['UNI'] += np.where(df_uni[k] == 'KILLED', 1 , 0)

        new_df['kill_fp'] = np.where( new_df['FP']>0 , 1 , 0)

        new_df['kill_uni'] = np.where(new_df['UNI']>0, 1 , 0)
        if (size_fp)>0:
            tmp_size_fp=float(len(ctr_fp))/ float(size_fp)
            new_df["test_suite_FP"] =  tmp_size_fp
        else:
            tmp_size_fp = 0
            new_df["test_suite_FP"]=tmp_size_fp
        if (size_uni)>0:
            tmp_size_u = float(len(ctr_uni))/ float(size_uni)
            new_df["test_suite_U"] = tmp_size_u
        else:
            tmp_size_u =  0
            new_df["test_suite_U"]=tmp_size_u
        dict_list.append({"package":k ,"FP":new_df['FP'].sum() ,"UNI":new_df['UNI'].sum()
                                ,"kill_fp":new_df['kill_fp'].sum() , "kill_uni":new_df['kill_uni'].sum()  ,
                              "test_suite_FP":tmp_size_fp,
                              "test_suite_U": tmp_size_u
                              })
        all_df['FP']+=new_df['FP']
        all_df['UNI'] += new_df['UNI']
        all_df['kill_fp']=new_df['kill_fp']
        all_df['kill_uni'] = new_df['kill_uni']
        new_df.to_csv(dir_path+str(k)+'.csv', encoding='utf-8', index=False)
    if len(dict_list)>0 :
        df = pd.DataFrame(dict_list, columns=dict_list[0].keys())
        df.to_csv(dir_path+'fin.csv', encoding='utf-8', index=False)
    all_df.to_csv(dir_path+'all.csv', encoding='utf-8', index=False)


def fin_mereg(path):
    walker=pit_render_test.walker(path)
    list_p = walker.walk("fin.csv")
    list_d = []
    big_dico={}
    for p in list_p:
        ISstop = True
        time_b = "null"
        if str(p).__contains__("t="):

            pos = str(p).find("t=")
            i=pos+2
            while(ISstop and i<len(str(p)) ):
                if p[i]=='_':
                    ISstop=False
                    time_b=p[pos+2:i]
                    break
                i+=1
            list_d.append({"path":p , "time":time_b})
    for item in list_d:
        csv_file = csv.reader(open(item["path"], "rb"), delimiter=",")
        for row in csv_file:
            if str(row[2]).__contains__("org"):
                item_tmp={}
                if row[2] in big_dico :
                    val = big_dico[str(row[2])]
                else:
                    big_dico[str(row[2])]=[]
                    val =  big_dico[str(row[2])]
                item_tmp["FP"] = row[0]
                item_tmp["test_suite_U"] = row[1]
                item_tmp["pacakge"] = row[2]
                item_tmp["test_suite_FP"] = row[3]
                item_tmp["kil_uni"] = row[4]
                item_tmp["kil_fp"] = row[5]
                item_tmp["uni"] = row[6]
                item_tmp["time"] = item["time"]
                val.append(item_tmp)
                big_dico[str(row[2])] = val
    for key_i in big_dico.keys() :
        df = pd.DataFrame(big_dico[key_i])
        df.to_csv(path +str(key_i) +'_fin.csv', encoding='utf-8', index=False)




if __name__ == "__main__":
    arr=sys.argv
    arr_p = "py all /home/ise/eran/idel/geometry_pac/09_28_20_01_35_t=70_/pit_test/ALL_FP__t=70_it=0/ /home/ise/eran/idel/geometry_pac/09_28_20_01_35_t=70_/pit_test/report_pit/"
    arr= arr_p.split(" ")
    if len(arr) > 2 :

        mod = arr[1]
        if mod == "fin" :
            die_p = arr[2]  # '/home/eran/thesis/test_gen/experiment/t30_distr/pit_res/'
            fpcsv = arr[3]  # '/home/eran/thesis/test_gen/experiment/t30_distr/pit_res/FP_budget_time.csv'
            uni = arr[4]  # '30'
            clac_by_package(die_p, fpcsv, uni)
        elif mod=='all':
            dico = init_clac( [ arr[2] ],arr[3])
        else:
            print "fail csv_PIT"
    else :
        #fin_mereg("/home/eran/Desktop/testing/new_test/")  # data_mutation #new_FP
        print "[Error] ----no args------"
        exit(0)

















