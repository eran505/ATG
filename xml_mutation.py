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
    xml_df.to_csv("{}/{}.csv".format(out_path_dir,name_file))

def get_all_xml(path,root_path_project,mod):
    d_class={}
    err={}
    err_name={}
    out_path_dir = mkdir_system(path,'class',is_del=False)
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
        if xml_df is None:
            #d_class[name_file] = None
            print "empty xml file in class: {}".format(name_file)
            continue
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
    else:
        wrapper_class_analysis(root_p)
    #rev_analysis_by_package(out_path_dir,data_path='/home/ise/eran/xml/02_23_17_34_26_t=60_/pit_test/ALL_U_t=60_it=0_/commons-math3-3.5-src/csvs/class')

def get_projects(p_root_path,mod='rev'):
    list_project = pit_render_test.walk(p_root_path,'commons-math3-3.5-src',False)
    #list_project = ['/home/ise/eran/xml/02_23_17_34_26_t=60_/pit_test/ALL_U_t=60_it=0_/commons-math3-3.5-src','/home/ise/eran/xml/02_23_17_34_26_t=60_/pit_test/ALL_FP_t=60_it=0_/commons-math3-3.5-src']
    for x in list_project:
        main_func(x,mod)

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
        target = [x for x in list(m_df) if str(x).__contains__('ALL')]
        ##print target
        size_target = len(target)
        m_df['kill'] = m_df[target].apply(lambda row: my_test(row,target), axis=1)
        m_df['AVG_kill'] = m_df['kill']/size_target
        flush_csv(out_dir,m_df,ky)

def my_test(row,tar):
    kill =0
    for x in tar:
        if str(row[x]) == 'KILLED':
            kill+=1
    return kill


def wrapper_class_analysis(root_path):
    list_p = pit_render_test.walk(root_path,'t=',False)
    for p in list_p:
        dico = merge_all_csvs(p)
        read_and_mereg(dico,root_path)

import sys
if __name__ == "__main__":
    #wrapper_class_analysis('/home/ise/tran/02_12_18_26_28_t=9_')
    args = sys.argv
    if len(args)>2:
        get_projects(args[1])
    else:
        get_projects('/home/ise/tran/','reg') #/home/ise/eran/xml/
        pass