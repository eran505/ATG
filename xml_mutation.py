import time,os,sys
import pit_render_test
import xml.etree.ElementTree
import pandas as pd
import hashlib


def mkdir_system(path_root,name,is_del=True):
    if path_root is None:
        raise Exception("[Error] passing a None path --> {}".format(path_root))
    if path_root[-1]!='/':
        path_root=path_root+'/'
    if os.path.isdir("{}{}".format(path_root,name)):
        if is_del:
            os.system('rm -r {}{}'.format(path_root,name))
        else:
            print "{}{} is already exist".format(path_root,name)
            return '{}{}'.format(path_root, name)
    os.system('mkdir {}{}'.format(path_root,name))
    return '{}{}'.format(path_root,name)


def flush_csv(out_path_dir, xml_df, name_file):
    if xml_df is None:
        return
    ##print "{}/{}.csv".format(out_path_dir, name_file)
    xml_df.to_csv("{}/{}.csv".format(out_path_dir,name_file))

def get_all_xml(path,root_path_project,mod):
    d_class={}
    print "-"*30
    print path
    cols=['ID','mutatedClass']
    err={}
    index_df=pd.DataFrame(columns=cols)
    err_name={}
    out_path_dir = mkdir_system(path,'class',is_del=True)
    out_path_index = mkdir_system(path, 'index', is_del=True)
    list_xml=pit_render_test.walk(root_path_project,'mutations.xml')
    if list_xml is None:
        print "[Error] no mutations xmls found in the following path --> {}".format(root_path_project)
        return {}
    all = len(list_xml)
    #x_list =[]
    #for x in list_xml:
    #    if str(x).__contains__('SphericalCoordinat'):
    #        x_list.append(x)
    #list_xml= x_list

    for x_xml in list_xml:
        print all
        all=all-1
        if len(x_xml)<1:
            continue
        name_file = str(x_xml).split('/')[-2]
        #print "name: ",name_file
        xml_df,test_name = pars_xml_to_csv(x_xml,mod)

        #bulid the index data-frame

        if xml_df is None:
            #d_class[name_file] = None
            print "empty xml file in class: {}".format(name_file)
            continue
        index_df = pd.concat([xml_df[cols],index_df])
        if test_name is not None and test_name != name_file:
            print "[Error] {} != {}".format(name_file,test_name)
            err_name[test_name] = name_file
            err[test_name]=xml_df
            continue
        flush_csv(out_path_dir,xml_df,name_file)
        d_class[name_file]=xml_df
    print err_name
    for key in  err.keys():
        xml_df = err[key]
        name_file = key
        flush_csv(out_path_dir,xml_df,name_file)
        d_class[name_file]=xml_df
    flush_csv(out_path_index,index_df,'index_er')
    return d_class


def rm_file(path):
    os.system('rm {}'.format(path))

def pars_xml_to_csv(path_xml,mod):
    test_name =None
    list_xml=[] #the dict that will become to DataFrame
    if os.path.isfile(path_xml) is False:
        raise "[Error] no file in the path --> {}".format(path_xml)
    try:
        root_node = xml.etree.ElementTree.parse(path_xml).getroot() #get the root xml

    except (Exception, ArithmeticError) as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print (message)
        rm_file(path_xml)
        return None,None

    ctr=0
    hash = hashlib.sha1()
    for item in root_node._children:
        d_i={}
        ctr=ctr+1
        if len(item.attrib)>0:
            d_i['status'] = item.attrib['status'] #{'status': 'KILLED', 'detected': 'true'}
            d_i['detected'] = item.attrib['detected']
        else:
            raise "[Error] no attribute to item number:{} path xml: {}".format(ctr,path_xml)
        for attribute in item._children:
            tag=attribute.tag
            text = attribute.text
            d_i[tag]=text
        col = ['description','lineNumber','methodDescription','mutatedClass',
               'mutatedMethod','mutator','sourceFile']
        str_hash=''
        for c in col:
            str_hash+=str(d_i[c])
        hash.update(str_hash)
        d_i['ID'] = hash.hexdigest()
        test_name_tmp = d_i['killingTest']
        if mod == 'rev':
            if test_name_tmp is not None and test_name is None:
                test_name = str(test_name_tmp).split('_ESTest')[0]
        else:
            test_name_tmp = d_i['mutatedClass']
            if test_name_tmp is not None and test_name is None:
                if str(test_name_tmp).startswith('org.'):
                    test_name = str(test_name_tmp)
        list_xml.append(d_i)
    df=pd.DataFrame(list_xml)
    return df,test_name

def rev_analysis_by_package(p_path,data_path=None,d_class=None):
    '''make csv by packages
    by dictionary object or by path csv dir
    '''
    out_path_dir = mkdir_system(p_path,'package',is_del=False)
    d={}
    cur_d=d_class
    d_class_local = {}
    if data_path is not None:
        list_csvs = pit_render_test.walk(data_path,'.csv')
        for csv_item in list_csvs:
            name = str(csv_item).split('/')[-1][:-4]
            df = pd.read_csv(csv_item)
            d_class_local[name]=df
        cur_d=d_class_local
    print "in"
    for key in cur_d.keys():
        xml_df = cur_d[key]
        if xml_df is not None:
            package_prefix = str(key).split('.')[:-1]
            package_prefix= '.'.join(package_prefix)
            if package_prefix not in d:
                d[package_prefix]={}
            d[package_prefix][key]=xml_df
    print "done"
    merge_dfs(d,out_path_dir)

def merge_dfs(dico,out_path):
    d_fin={}
    res_df=None
    for ky in dico.keys():
        sub_dico_df = dico[ky]
        ctr=0
        first_len = -1
        print '-'*10
        for ky_sub in sub_dico_df.keys():
            sub_dico_df[ky_sub].rename(columns={'status':'{}'.format(ky_sub)}, inplace=True)
            tmp_df = sub_dico_df[ky_sub][['ID','mutatedClass','mutatedMethod','lineNumber',ky_sub]]
            if ctr == 0 :
                res_df = tmp_df
                ctr+=1
                print res_df.shape
                first_len = len(res_df)
                continue
            res_df = pd.merge(res_df,tmp_df,how='outer',on=['ID','mutatedClass','mutatedMethod','lineNumber'])
            print res_df.shape
            if len(res_df) != first_len:
                raise Exception('The merge process didnt work well on package {} the class:{} is differ'.format(ky,ky_sub))
        d_fin[ky]=res_df
    for ky_i in d_fin.keys():
        flush_csv(out_path,d_fin[ky_i],ky_i)

def main_func(root_p,mod):
    out_path_dir = mkdir_system(root_p,'csvs',is_del=True)
    dict_classes = get_all_xml(out_path_dir,root_p,mod)
    if mod == 'rev':
        rev_analysis_by_package(out_path_dir,d_class=dict_classes)
    #rev_analysis_by_package(out_path_dir,data_path='/home/ise/eran/xml/02_23_17_34_26_t=60_/pit_test/ALL_U_t=60_it=0_/commons-math3-3.5-src/csvs/class')

def get_projects(p_root_path,mod='rev'):
    list_project = pit_render_test.walk(p_root_path,'commons',False)
    list_project = pit_render_test.walk_rec(p_root_path,[],'commons-',False,-4)
    #list_project = ['/home/ise/eran/xml/02_23_17_34_26_t=60_/pit_test/ALL_U_t=60_it=0_/commons-math3-3.5-src','/home/ise/eran/xml/02_23_17_34_26_t=60_/pit_test/ALL_FP_t=60_it=0_/commons-math3-3.5-src']
    #list_project=[x for x in list_project if str(x).__contains__('t=20')]
    for x in list_project:
        main_func(x,mod)
    if mod!='rev':
        wrapper_class_analysis(p_root_path)
        make_big_csv(p_root_path)
        add_all_big(p_root_path)

def merge_all_csvs(root_path):
    print ''
    csvs_class=pit_render_test.walk(root_path,'csvs',False)
    dico_paths={}
    for item_p in csvs_class:
        if item_p[-1] == '/':
            item_p=item_p[:-1]
        if os.path.isdir("{}/class".format(item_p)) is False:
            print "[Error]  {}/class is not exist".format(item_p)
            continue
        classes_name=pit_render_test.walk("{}/class".format(item_p),'.csv')
        for klass in classes_name:
            name = str(klass).split('/')[-1][:-4]
            if name not in dico_paths:
                dico_paths[name]=[]
            dico_paths[name].append(klass)
    return dico_paths

def read_and_mereg(dico,out_path):
    col=['ID','status']
    out_dir = pit_render_test.mkdir_system(out_path,'out_xml',True)
    for ky in dico:
        list_df=[]
        for p_csv in dico[ky]:
            name_col = None
            for x in str(p_csv).split('/'):
                if str(x).__contains__('ALL'):
                    name_col=x
                    time_b = str(x).split('_')[-3]
                    break
            if name_col is None:
                str_err = "[Error] something wrong with the path {} no ALL dir ".format(p_csv)
                raise Exception("{}".format(str_err))
            df = pd.read_csv(p_csv,index_col=0)
            df=df[col]
            df.rename(columns={'status': '{}'.format(name_col)}, inplace=True)
            list_df.append(df)
        if len(list_df)>0:
            m_df = list_df[0]
            for item in list_df[1:]:
                m_df=pd.merge(m_df,item,on=['ID'])
        print "ky:{} size_df:{}".format(ky,m_df.shape)
        #m_df['killed'] = m_df.apply(sublst, axis=1)
        target_fp = [x for x in list(m_df) if str(x).__contains__('FP')]
        target_u = [x for x in list(m_df) if str(x).__contains__('U')]
        aggregation(m_df,target_fp,'FP',time_b)
        aggregation(m_df, target_u,'U',time_b)
        flush_csv(out_dir,m_df,ky)

def aggregation(m_df,cols,mode,time_budget):
    size_target = len(cols)
    m_df['{}_KILL_Sum_{}'.format(time_budget,mode)] = m_df[cols].apply(lambda row: my_test(row, cols), axis=1)
    m_df['{}_KILL_Avg_{}'.format(time_budget,mode)] = m_df['{}_KILL_Sum_{}'.format(time_budget,mode)] / size_target

def make_big_csv(root_p):
    list_p = pit_render_test.walk(root_p,'out_xml',False)
    for p in list_p:
        print p
        cols = ['ID', 'KILL_Avg_FP', 'KILL_Sum_FP', 'KILL_Avg_U', 'KILL_Sum_U' ]
        time_b = str(p).split('/')[-2].split('_')[-2]
        for j in range(1,len(cols)):
            cols[j]="{}_{}".format(time_b,cols[j])
        acc = 0
        name = str(p).split('/')[-2].split('_')[-2]
        csv_lists= pit_render_test.walk(p,'.csv')
        big_df = pd.DataFrame(columns=cols)
        p = p[:-8]
        for csv_item in csv_lists:
            print "csv_item =",csv_item
            df = pd.read_csv(csv_item,index_col=0)
            df=df[cols]
            acc+=int(len(df))
            big_df = pd.concat([big_df,df])
            if acc != int(len(big_df)):
                print "acc: {} big: {}".format(acc,int(len(big_df)))
            #print "[Good] big_df size: ", len(big_df)
            flush_csv(p,big_df,'big_df_{}'.format(name))
        print 'done'


def add_all_big(root_p):
    list_p = pit_render_test.walk(root_p,'big_df')
    if len(list_p) > 0 :
        big_df_all = pd.read_csv(list_p[0],index_col=0)
    else:
        print "didnt find any big_df Dataframe in path:{}".format(root_p)
        return
    for p in list_p[1:]:
        df = pd.read_csv(p,index_col=0)
        big_df_all = pd.merge(big_df_all,df,on=['ID'],how='outer')
        print "all_df: {}".format(len(big_df_all))
    avg_col = ['ID']
    list_cols = list(big_df_all)
    list_cols = [x for x in list_cols if str(x).__contains__('Avg')]
    avg_col.extend(list_cols )
    df_avg = big_df_all[avg_col]
    make_graph(df_avg,avg_col,root_p)
    flush_csv(root_p, df_avg, 'big_AVG_df')
    flush_csv(root_p,big_df_all,'big_all_df')



def make_graph(df,cols,out,action='mean'):
    list_d=[]
    d_fp = {}
    d_u={}
    all_d={}
    for x in cols:
        if x =='ID':
            continue
        mode =  str(x).split('_')[-1]
        name_budget = str(x).split('_')[0].split('=')[1]
        if mode == 'FP':
            if action == 'mean':
                d_fp[name_budget]=df[x].mean()
            elif action == 'miss':
                d_u[name_budget] = df[x].isnull().sum()
        elif mode=='U':
            if action == 'mean':
                d_u[name_budget] = df[x].mean()
            elif action == 'miss':
                d_u[name_budget] = df[x].isnull().sum()
        else:
            print mode
    for ky in d_fp.keys():
        all_d[ky]={'time_budget':ky,'FP':d_fp[ky]}
    for key in d_u.keys():
        if key in all_d:
            all_d[key]['U']=d_u[key]
        else:
            all_d[key]={'time_budget':key,'FP':0,'U':d_u[key]}
    for k in all_d:
        list_d.append(all_d[k])
    df_sum = pd.DataFrame(list_d)
    df_sum.sort_values(by=['time_budget'],inplace=True)
    flush_csv(out, df_sum, 'sum_df_{}'.format(action))



def my_test(row,tar):
    kill =0
    for x in tar:
        if str(row[x]) == 'KILLED':
            kill+=1
    return kill

def wrapper_class_analysis(root_path):
    size_p = len(str(root_path).split('/'))
    list_p = pit_render_test.walk(root_path,'t=',False)
    list_p = [x for x in list_p if len(str(x).split('/'))<size_p+1 ]
    #list_p = [x for x in list_p if str(x).__contains__('=20_')  ]
    for p in list_p:
        print p
        dico = merge_all_csvs(p)
        read_and_mereg(dico,p)


def packages_agg(path,df_index):
    out_path  = '/'.join(str(path).split('/')[:-1])
    df = pd.read_csv(path,index_col=0)
    res_df = pd.merge(df,df_index,on=['ID'],how='outer')
    res_df['package'] = res_df['class'].apply(lambda x: '.'.join(str(x).split('.')[:-1]))
    res_df_sum = res_df.groupby(['package']).sum()
    res_df_miss = res_df.groupby(['package']).apply(lambda x: x.notnull().sum())
    res_df_mean = res_df.groupby(['package']).mean()
    dir_out = pit_render_test.mkdir_system(out_path,'package_agg',True)
    flush_csv(dir_out,res_df_miss,'df_miss')
    flush_csv(dir_out, res_df_mean, 'df_mean')
    flush_csv(dir_out, res_df_sum, 'df_sum')


def get_ID_index_table(root_path):
    res = pit_render_test.walk(root_path,'index_er')
    index_df = pd.DataFrame(columns=['ID','mutatedClass'])
    if len(res)>0:
        index_df = pd.read_csv(res[0],index_col=0)
        print "size:{}".format(len(index_df))
    for csv_p in res[1:]:
        df=pd.read_csv(csv_p,index_col=0)
        index_df = pd.merge(index_df,df,on=['ID','mutatedClass'],how='outer')
        print "size:{}".format(len(index_df))
    index_df.rename(columns={'mutatedClass': '{}'.format('class')}, inplace=True)
    flush_csv(root_path,index_df,'indexer')
    return index_df

def packager(path_big,path_index): # make agg for packages TODO: fix the missing value DataFrame
    '''
     this function is analysis the data by packages

    :param path_big: the path to the big.csv file
    :param path_index: the path to the indexer.csv or path to the dir where all the index file are
    :return: csv file
    '''
    if path_index[-3:] == 'csv':
        df_index = pd.read_csv(path_index,index_col=0)
    else:
        df_index=get_ID_index_table(path_index)
    packages_agg(path_big,df_index)



import sys
if __name__ == "__main__":
    tran_p = '/home/ise/tran/'
    tran_p = '/home/ise/eran/lang/'
    tran_p='/home/ise/eran/lang/rev_exp/'
    #wrapper_class_analysis(tran_p)
    #make_big_csv(tran_p)
    #add_all_big(tran_p)
    #exit()
    args = sys.argv
    if len(args)>2:
        get_projects(args[1])
    else:
        get_projects(tran_p,'rev') #/home/ise/eran/xml/
        pass