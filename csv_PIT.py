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


def get_all_dir(root_p,name=None):
    if name is None:
        walker=pit_render_test.walker(root_p)
        classes_list = walker.walk("org",False,0)
        print "class_list = ",classes_list
    else :
        walker=pit_render_test.walker(root_p)
        classes_list = walker.walk(name,False,-1)
        print "class_list = ",classes_list
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


def _data_df(list_data,time=''):
    time_b =time
    df_list=[]
    error_dir=0
    names_list=["class","method","line"]
    for item in list_data:
        csvs = item['csv']
        #print "name= ",item['name']
        names_list.append(item['name'])
        if len(csvs) > 0 :
            df = pd.read_csv(csvs[0],names = ["class-suffix", "class", "mutation-type", "method","line",item['name']+'_'+time_b,"test"])
            df.drop(df.columns[[0,len(list(df))-1]], axis=1, inplace=True)
           # df.set_index(["class","method","line"], inplace=True)
            #df.reset_index(level=['class','mutation-type','method','line'],inplace=True)
            #if len(df) == 47163 :
            df_list.append(df)
            #else:
            #    error_dir+=1
            #    print item['name']
            #    #del_error_files(item['dir'])
    print 'error_dir=',error_dir
    result = merge_df(df_list)
    return result

#def del_error_files(path_err):
#    os.system('rm -r '+path_err)

def merge_df(list_df,bol=True):
    for df in list_df:
        df.drop_duplicates(keep=False,inplace=True)
    df_all = list_df[0]
    ctr = 0
    print 'szie=',len(list_df)
    while ctr<len(list_df):
        if ctr == 0 :
            ctr += 1
            continue
        print 'df_all.shape = ', df_all.shape
        if bol:
            df_all = pd.merge(df_all, list_df[ctr], how='inner',on=['index',"class","mutation-type","method","line"])
        else:
            df_all = pd.merge(df_all, list_df[ctr], how='inner',on=["class","mutation-type","method","line"])  # "class", "mutation-type", "method",
        ctr += 1
    return df_all


def merge_all_mutation_df(root_p,name=None,time = None):
    if name is None:
        all_dir= get_all_dir(root_p)
    else:
        all_dir = get_all_dir(root_p,name)
    for d in all_dir:
        print d,'\n'
    dict_mut=make_dcit(all_dir)
    dfs = _data_df(dict_mut,time)
    print list(dfs)
    return  dfs


def write_to_csv(dest_path ,df):
    df.to_csv(dest_path, encoding='utf-8')

def mean_all(df,bol=True):    #[ KILLED , NO_COVERAGE ,SURVIVED ,TIMED_OUT , RUN_ERROR
    if bol:
        list_name = list(df)[5:]
    else:
        list_name = list(df)[4:]
    for name  in arr_sign:
        df[name+'_sum'] = (df[list_name] == name).sum(axis=1)
    string = '_sum'
    my_new_list = [x + string for x in arr_sign]
    df['total'] = df[my_new_list].sum(axis=1)
    for it in my_new_list:
        df[it[:-3]+"mean"] = (df[it].astype(float))/df['total']
        df[it[:-3] + "mean_norm"] = (df[it].astype(float)) / df['total']
    return df



def mean_all_FPU(df):    #[ KILLED , NO_COVERAGE ,SURVIVED ,TIMED_OUT , RUN_ERROR
    list_name = list(df)
    list_name.remove('class')
    list_name.remove('mutation-type')
    list_name.remove('method')
    list_name.remove('line')
    fp=[]
    u=[]
    for item in list_name:
        if str(item).__contains__('FP'):
            fp.append(item)
        else:
            u.append(item)
    if len(fp)>0:
        df=get_mean_df(df,fp,'FP')
    if len(u)>0:
        df=get_mean_df(df, u, 'U')
    return df

def get_mean_df(df,list_col,name_mode):
    for name  in arr_sign:
        df[name+'_sum_'+name_mode] = (df[list_col] == name).sum(axis=1)
    for name  in arr_sign:
        df[name+'_AVG_'+name_mode] = ( (df[list_col] == name).sum(axis=1) ) / len(list_col)
    string = '_sum_'+name_mode
    df[name_mode]=len(list_col)
    #my_new_list = [x + string for x in arr_sign]
    #df['total'] = df[my_new_list].sum(axis=1)
    #for it in my_new_list:
    #    df[it[:-3]+"mean_"+name_mode] = (df[it].astype(float))/df['total']
    #    df[it[:-3] + "mean_norm"+name_mode] = (df[it].astype(float)) / df['total']
    return df

def name_ext(p):
    print p
    arr = str(p).split('/')
    if len(arr[-1])>2:
        return  arr[-1]
    else :
        return arr[-2]

def get_data_df_by_name(list_data):
    df_list=[]
    result = ""
    error_dir=0
    names_list=["class","method","line"]
    for item in list_data:
        if item['csv'] is None:
            continue
        csvs = item['csv']
        rec_name = "{0}_t={1}_i={2}".format(item['mode'],item['budget'],item['it'])
        names_list.append(rec_name)
        if len(csvs) > 0 :
            df = pd.read_csv(csvs,names = ["class-suffix", "class", "mutation-type", "method","line",rec_name,"test"])
            #df['index']=df.set_index(["class","method","line"], inplace=True)
            df.drop(df.columns[[0,len(list(df))-1]], axis=1, inplace=True)
            if df.empty:
                continue
            print "df_size = ",df.shape
            df_list.append(df)
            print 'li: ',list(df)
    if len(df_list) > 0:
        result = merge_df(df_list,False)
    else:
        result =None
    return result

def get_all_class_by_name(path_root,out_path=None):
    if path_root[-1] != '/':
        path_root = path_root + '/'
    if out_path is None:
        out_path=path_root+'out/'
        if os.path.isdir(out_path) is False:
            os.mkdir(out_path)
    if out_path[-1] != '/':
        out_path = out_path + '/'
    dict_package_prefix=dict()
    walker=pit_render_test.walker(path_root)
    classes_list = walker.walk('ALL', False, 1,False)
    print classes_list
    for class_item in classes_list:
        walker = pit_render_test.walker(path_root+'/'+class_item+'/commons-math3-3.5-src/target/pit-reports/')
        classes_list = walker.walk('org.apache.commons.math',False)
        d = {}
        for item in classes_list:
            name = str(item).split('/')[-1]
            if os.path.exists(item+'/mutations.csv'):
                d[name]=item+'/mutations.csv'
            else:
                d[name]=None
        dict_package_prefix[class_item] = d
    dico = merge_dict_by_class(dict_package_prefix)
    res_dataframe={}
    for ky in dico :
        #if not str(ky).__contains__("org.apache.commons.math3.linear"):
        #    continue
        tmp = get_data_df_by_name(dict(dico[ky]).values())
        if tmp is None:
            continue
        print ky
        print 'tmp shape = ',tmp.shape
        df_to_csv=mean_all_FPU(tmp)
        print 'writing ',ky,' size = ',df_to_csv.shape
        write_to_csv(out_path+ky+'.csv',df_to_csv)
        print 'Done !!!! ', ky, ' size = ', df_to_csv.shape
    #for k in res_dataframe :
    #    if res_dataframe[k] is None:
    #        continue
    #    write_to_csv(out_path+k+'.csv',res_dataframe[k])



    print "done"
def merge_dict_by_class(dict_dir):
    dict_class={}
    for key in dict_dir:
        for second_key in dict_dir[key]:
            time,it,mode = extract_it_time(key)
            if second_key in dict_class:
                dict_class[second_key][key] = {'name':second_key,'csv':dict_dir[key][second_key],'budget':time, 'mode':mode , 'it':it }
            else:
                dict_class[second_key]={}
                dict_class[second_key][key] = {'name':second_key,'csv': dict_dir[key][second_key], 'budget': time, 'mode': mode, 'it': it}
    return dict_class



def init_clac_v2(arr_path,out,name=None):
    ctr=0
    arr_dfs = []
    acc = {}
    for path in arr_path :
        name_dir = name_ext(path)
        ctr += 1
        #dfs = merge_all_mutation_df(path+'pit-reports/')
        if name is None:
            dfs = merge_all_mutation_df(path+'commons-math3-3.5-src/target/pit-reports/')
        else:
            dfs = merge_all_mutation_df(path+'commons-math3-3.5-src/target/pit-reports/',name,name_dir)
        acc[name_dir]=dfs
    print dfs.shape
    size =  len(list(dfs))
    res_df = merge_df(acc.values())
    #mean_all(dfs)
    arr_dfs.append({'id':ctr , 'data':dfs})
    #write_to_csv(path+'PIT_'+str(name_dir)+str(size)+'.csv', dfs)
    if name is None:
        write_to_csv(out + 'PIT_' + str(name_dir) +"_s="+str(size) + '.csv', dfs)
    else:
        write_to_csv(out + 'PIT_' + str(name_dir)+str("_c="+name) + '.csv', dfs)
    #delet_csv(path)
    return arr_dfs



def init_clac(arr_path,out,name=None):
    ctr=0
    arr_dfs = []
    for path in arr_path :
        name_dir = name_ext(path)
        ctr += 1
        #dfs = merge_all_mutation_df(path+'pit-reports/')
        if name is None:
            dfs = merge_all_mutation_df(path+'commons-math3-3.5-src/target/pit-reports/')
        else:
            dfs = merge_all_mutation_df(path+'commons-math3-3.5-src/target/pit-reports/',name,name_dir)

        print dfs.shape
        size =  len(list(dfs))
        if name is None:
            mean_all(dfs)
        arr_dfs.append({'id':ctr , 'data':dfs})
        #write_to_csv(path+'PIT_'+str(name_dir)+str(size)+'.csv', dfs)
        if name is None:
            write_to_csv(out + 'PIT_' + str(name_dir) +"_s="+str(size) + '.csv', dfs)
        else:
            write_to_csv(out + 'PIT_' + str(name_dir)+str("_c="+name) + '.csv', dfs)
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


def info_input(path_info):  #/home/eran/Desktop/testing/new_test
    with open(path_info) as f:
        content = f.readlines()
        a = [x for x in content if x != '\n']
        for x in a:
            x = x.replace('\n',"")
            if x.__contains__('\n'):
                print x
            arr = x.split(" ")
            arr=arr[1:]
            main_pars(arr)

def by_class(path,out,class_name):
    ctr=0
    arr_dfs = []
    for path in path :
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




def extract_it_time(str_name_dir):
    it_index = str_name_dir.find('_it=') #3
    time_index = str_name_dir.find('_t=') #2
    mode_index = str_name_dir.find('ALL_')
    mode = str_name_dir[mode_index +4:mode_index +6]
    time_budget =  str_name_dir[time_index+3:it_index]
    it = str_name_dir[it_index+4:]
    return time_budget,it,mode


def get_sum_df(p_path):
    walker = pit_render_test.walker(p_path)
    classes_list = walker.walk('.csv')
    d={}
    for csv_p in classes_list:
        name_class = str(csv_p).split('/')[-1][:-4]
        d[name_class] = csv_p
        d[name_class] = pd.read_csv(csv_p)
    return d

def mkdir_os(dir_name,root_path):
    if root_path[-1] != '/':
        root_path=root_path+'/'
    if os.path.isdir(root_path+dir_name):
        return root_path+dir_name+'/'
    else:
        os.mkdir(root_path+dir_name)
        return root_path + dir_name + '/'

def insert_to_big(df,dico_class_df,budget):
    for ky in dico_class_df:
        xx= list(dico_class_df[ky])
        if not 'class' in xx :
            print "bugbug"
            continue
        dico_class_df[ky].set_index(["class","mutation-type","method", "line"],drop=True,inplace=True)
        dictionary = dico_class_df[ky].to_dict(orient="index")
        for ky_s in dictionary:
            if ky_s in df:
                if 'KILLED_AVG_FP' in dictionary[ky_s]:
                    df[ky_s][budget+"_FP"] = dictionary[ky_s]['KILLED_AVG_FP']
                if 'KILLED_AVG_U' in dictionary[ky_s]:
                    df[ky_s][budget + "_U"] = dictionary[ky_s]['KILLED_AVG_U']
            else:
                df[ky_s]={'ID':ky_s , budget+"_FP":0 , budget+'_U':0}
                if 'KILLED_AVG_FP' in dictionary[ky_s]:
                    df[ky_s][budget+"_FP"] = dictionary[ky_s]['KILLED_AVG_FP']
                if 'KILLED_AVG_U' in dictionary[ky_s]:
                    df[ky_s][budget + "_U"] = dictionary[ky_s]['KILLED_AVG_U']






def aggregate_time_budget(root_path):
    dict_package_prefix = dict()
    walker = pit_render_test.walker(root_path)
    classes_list = walker.walk('_t=', False, 0)
    classes_list = [x+'/pit_test/' for x in classes_list]
    print classes_list
    time = ''
    d={}
    last=len("/pit_test/")+1
    for p_path in classes_list:
        y = str(p_path).find("t=")
        if y > 0 :
            time = p_path[y+2:-last]
            d[p_path] = time
        else:
            d[p_path] = None
        get_all_class_by_name(p_path)
    classes_list = [x + 'out/' for x in classes_list]
    time_arr = d.values()
    time_arr_fp = [str(x)+"_budget_FP" for x in time_arr]
    time_arr_u = [str(x) + "_budget_U" for x in time_arr]
    print classes_list
    all_c = ['class']+time_arr_fp + time_arr_u
    df_big_d = {}
    list_end={}
    for i in range(len(classes_list)):
        tmp_dico = get_sum_df(classes_list[i])
        insert_to_big(df_big_d,tmp_dico, d[classes_list[i][:-4]] )
        #merge_df_sum_by_class(tmp_dico,list_end,d[classes_list[i][:-4]])
    df_big = pd.DataFrame(df_big_d.values())
    list_colo = list(df_big)
    _list10 = [x for x in list_colo if str(x).__contains__("10") ]
    _list30 = [x for x in list_colo if str(x).__contains__("30") ]
    _list60 = [x for x in list_colo if str(x).__contains__("60") ]
    _list90 = [x for x in list_colo if str(x).__contains__("90") ]
    _df10 = df_big.copy(deep=True)
    _df30 = df_big.copy(deep=True)
    _df60 = df_big.copy(deep=True)
    _df90 = df_big.copy(deep=True)
    for col0 in _list10:
        _df10 = _df10[np.isfinite(_df10[col0])]
    for col1 in _list30:
        _df30 = _df30[np.isfinite(_df30[col1])]
    for col2 in _list60:
        _df60 = _df60[np.isfinite(_df60[col2])]
    for col3 in _list90:
        _df90 = _df90[np.isfinite(_df90[col3])]

    path_out = mkdir_os('fin_out',root_path)
    write_to_csv(path_out+'big.csv',df_big)
    write_to_csv(path_out + 'df10.csv', _df10)
    write_to_csv(path_out + 'df30.csv', _df30)
    write_to_csv(path_out + 'df60.csv', _df60)
    write_to_csv(path_out + 'df90.csv', _df90)
    #for key_class in list_end :
    #    write_to_csv(path_out+key_class+'.csv',list_end[key_class])
    #return list_end

def cal_df_sum(df):
    list_col_1 = list(df)
    list_col = [x for x in list_col_1 if x.__contains__("AVG")]
    #u_num = 0
    #fp_num = 0
    #if "U" in list_col_1:
    #    if (df['U'].count)>0:
    #        u_num= df['U'][0]
    #    else:
    #        u_num=0
    #if "FP" in list_col_1:
    #    if (df['FP'].count)>0:
    #        fp_num = df['FP'][0]
    #    else:
    #        fp_num  = 0

    d_total = {}

    fp=[0,0]
    u=[0,0]
    for x in list_col:
        if x.__contains__("FP"):
            if x.__contains__("KILL"):
                fp[0]=df[x].sum()
            else:
                fp[1]+=df[x].sum()
        else:
            if x.__contains__("U"):
                if x.__contains__("KILL"):
                    u[0] = df[x].sum()
                else:
                    u[1] += df[x].sum()
    return fp,u

def merge_df_sum_by_class(df1_d,d_end,time_b):
    columns = ['Budget', 'FP_kill', 'U_kill', 'FP_Survived', 'U_Survived']
    for ky in df1_d :
        if ky in d_end:
            df_tmp = d_end[ky]
            fp, u = cal_df_sum(df1_d[ky])
            list_res = [time_b, fp[0], u[0], fp[1], u[1]]
            df_tmp.loc[len(df_tmp)] = list_res
            d_end[ky] = df_tmp
        else:
            df_sumup = pd.DataFrame(columns=columns)
            fp,u = cal_df_sum(df1_d[ky])
            list_res = [time_b,fp[0],u[0],fp[1],u[1]]
            df_sumup.loc[len(df_sumup)] = list_res
            d_end[ky] = df_sumup


def main_pars(arr):
    if len(arr) > 2 :
        mod = arr[1]
        if mod == "fin" :
            die_p = arr[2]  # '/home/eran/thesis/test_gen/experiment/t30_distr/pit_res/'
            fpcsv = arr[3]  # '/home/eran/thesis/test_gen/experiment/t30_distr/pit_res/FP_budget_time.csv'
            uni = arr[4]  # '30'
            clac_by_package(die_p, fpcsv, uni)
        elif mod=='all':
            dico = init_clac(  arr[2] ,arr[3],'org.apache.commons.math3.linear.PreconditionedIterativeLinearSolver')
        elif mod == 'arg':
            aggregate_time_budget(arr[2])
        elif mod =='class':
            if len(arr) > 3 :
                dico = get_all_class_by_name(  arr[2] , arr[3])
            else:
                dico = get_all_class_by_name(arr[2])
    else :
        # fin_mereg("/home/ise/eran/idel/geometry_pac/")  # data_mutation #new_FP
        print "[Error] ----no args------"
        exit(0)



########################3
def get_data_df_by_name_v1(list_data):
    df_list=[]
    result = ""
    error_dir=0
    names_list=["class","method","line"]
    for item in list_data:
        if item['csv'] is None:
            continue
        csvs = item['csv']
        rec_name = "{0}_t={1}_i={2}".format(item['mode'],item['budget'],item['it'])
        names_list.append(rec_name)
        if len(csvs) > 0 :
            df = pd.read_csv(csvs,names = ["class-suffix", "class", "mutation-type", "method","line",rec_name,"test"])
            #df['index']=df.set_index(["class","method","line"], inplace=True)
            df.drop(df.columns[[0,len(list(df))-1]], axis=1, inplace=True)
            if df.empty:
                continue
            print "df_size = ",df.shape
            df_list.append(df)
            print 'li: ',list(df)
    if len(df_list) > 0:
        result = merge_df(df_list,False)
    else:
        result =None
    return result

#####################

if __name__ == "__main__":
    #get_data_df_by_name_v1([{'csv':'/home/eran/Desktop/xxx/mutations_fp1.csv','mode':'FP','budget':10,"it":1},
    #                        {'csv':'/home/eran/Desktop/xxx/mutations_fp2.csv','mode':'FP','budget':10,"it":2},
    #                        {'csv':'/home/eran/Desktop/xxx/mutations_u1.csv','mode':'U','budget':10,"it":1},
    #                        {'csv': '/home/eran/Desktop/xxx/mutations_u2.csv', 'mode': 'U', 'budget': 10, "it": 2}])
    #exit()
    arr=sys.argv
    #arr = ['py','arg','/home/eran/Desktop/exm/']
    if len(arr) == 2:
        if arr[1] == 'f':
            fin_mereg("/home/ise/eran/idel/geometry_pac/")  # data_mutation #new_FP
            exit(0)
        exit(0)
    #arr_p = "py all /home/ise/eran/idel/geometry_pac/09_28_20_01_35_t=70_/pit_test/ALL_FP__t=70_it=0/ /home/ise/eran/idel/geometry_pac/09_28_20_01_35_t=70_/pit_test/report_pit/"
    #arr= arr_p.split(" ")
    main_pars(arr)















