import time,os,sys
import pit_render_test
import xml.etree.ElementTree
import pandas as pd
import hashlib


def mkdir_system(path_root,name,is_del=True):
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

def get_all_xml(root_path):
    out_path_dir = mkdir_system(root_path,'out_csv',is_del=True)
    list_xml=pit_render_test.walk(root_path,'mutations.xml')
    for x_xml in list_xml:
        name_file = str(x_xml).split('/')[-2]
        print "name: ",name_file
        xml_df = pars_xml_to_csv(x_xml)
        flush_csv(out_path_dir,xml_df,name_file)

def rm_file(path):
    os.system('rm {}'.format(path))

def pars_xml_to_csv(path_xml):
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
        return None

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
        col = ['description','index','lineNumber','methodDescription','mutatedClass',
               'mutatedMethod','mutator','sourceFile']
        str_hash=''
        for c in col:
            str_hash+=str(d_i[c])
        hash.update(str_hash)
        d_i['ID'] = hash.hexdigest()
        list_xml.append(d_i)
    df=pd.DataFrame(list_xml)
    return df

if __name__ == "__main__":
    #prefix = ['org.apache.commons.math3.geometry.hull.ConvexHullGenerator','org.apache.commons.math3.analysis.differentiation.JacobianFunction','org.apache.commons.math3.util.FastMath']
    #p_ex_path = '/home/ise/eran/rev/02_26_13_27_45_t=30_/pit_test/ALL_U_t=30_it=0_/commons-math3-3.5-src/target/pit-reports/' \
    #            '{}/mutations.xml'.format(prefix[0])
    #pars_xml_to_csv(p_ex_path)
    get_all_xml('/home/ise/eran/rev/02_26_13_27_45_t=30_/pit_test/ALL_U_t=30_it=0_/commons-math3-3.5-src')