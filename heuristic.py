import pandas as pd
import os
import sys
import pit_render_test as pt
import util_defects4j as util_d4j
import numpy as np
import call_G_util as call_g


def scan_all_test_jar(path_target, file_name='jar_test_df', out=None):
    """
    scanning all jar files on root directory
    :rtype: object
    """
    results_out = pt.walk_rec(path_target, [], '.tar.bz2')
    d_info = []
    for item in results_out:
        arr_rel_path = str(item).split('/')
        test_index = arr_rel_path[-2]
        fitness_evolution = arr_rel_path[-3]
        time_budget = arr_rel_path[-5].split('=')[1]
        project_name = arr_rel_path[-6].split('_')[1]
        bug_id = arr_rel_path[-6].split('_')[3]
        date = '_'.join(arr_rel_path[-6].split('_')[4:])
        d = {'JAR_path': item, 'Test_index': test_index, 'Fitness_Evosutie': fitness_evolution,
             'time_budget': time_budget, 'Project_Name': project_name,
             'bug_ID': bug_id, 'Date': date}
        d_info.append(d)
    df = pd.DataFrame(d_info)
    if out is not None:
        df.to_csv('{}/{}.csv'.format(out, file_name))
    return df


def manger(root_dir, out_dir, filter_time_b=None):
    """
    manage the process
    """
    if os.path.isdir(root_dir) is False:
        msg = "[Error] the dir path is not a valid one --> {}".format(root_dir)
        raise Exception(msg)
    src_dir = pt.mkdir_system(out_dir, 'JARS_D4J')
    df = scan_all_test_jar(root_dir, out=src_dir)
    list_jar_info = []
    df['time_budget'] = df['time_budget'].astype(int)
    print df.dtypes
    if filter_time_b is not None:
        df = df.loc[df['time_budget'].isin(filter_time_b)]
    df = df.reset_index()
    df.set_index(np.arange(len(df.index)), inplace=True)
    df.drop_duplicates(inplace=False)
    print 'len(df):\t{}'.format(len(df))
    df['out_dir'] = df.apply(gatther_info_make_dir, out=src_dir, list_info=list_jar_info, axis=1)
    util_d4j.run_tests(list_jar_info)
    jar_making_process(src_dir)
    os.chdir(src_dir)
    util_d4j.rm_dir_by_name(src_dir, 'debug_dir')
    util_d4j.rm_dir_by_name(src_dir, 'out_test')
    mk_call_graph_raw_data(src_dir)
    mk_call_graph_df(src_dir)


def making_pred(p_name='Lang',out='/home/ise/eran/JARS' ,root_jat_dir='/home/ise/eran/JARS/JARS_D4J',dis_factor=0.01,
                csv_FP='/home/ise/eran/repo/ATG/D4J/FP',k=4,alpha=0.009,beta=0.0001,loc='LOC',gama=0.1,debug=True):
    df = pd.read_csv("{0}/{1}/{1}.csv".format(csv_FP, p_name), index_col=0)
    print "df size:\t{}".format(len(df))
    print df.dtypes
    if debug:
        out_root_debug = pt.mkdir_system(out,"debug_A_{}_B_{}_loc_{}_ds_{}".format(
                alpha,beta,loc,dis_factor))
    res_list=[]
    res = pt.walk_rec(root_jat_dir, [], 'P_',False,lv=-1)
    for item in res:
        print item
        p_name_i = str(item).split('/')[-1].split('_')[1]
        b_time = str(item).split('/')[-1].split('_')[5]
        bug_id = str(item).split('/')[-1].split('_')[3]
        index_test = str(item).split('/')[-1].split('_')[7]
        date_time= '_'.join(str(item).split('/')[-1].split('_')[9:])
        df_loc = find_loc_componenets(p_name_i, bug_id)


        if debug:
            out_debug = pt.mkdir_system(out_root_debug,str(item).split('/')[-1])
        print "----{}----".format(bug_id)
        df_filter = df.loc[df['bug_ID'] == int(bug_id)]
        print "df size:\t{}".format(len(df_filter))
        dict_test_picked = heuristic_process(df_filter, item, df_loc,k,gama=gama,loc=loc,
                                             alpha=alpha,beta=beta,debug_dir=out_debug,discount_factor=dis_factor,
                                             f_name="{}_B_{}_K".format(p_name,bug_id))

        if dict_test_picked is None:
            continue

        for test_i_key in dict_test_picked.keys():
            if dict_test_picked[test_i_key]['pick']==0:
                continue
            kill_sum,all_rep = get_rep_kill_out_raw_by_name(test_i_key,df_filter )
            index_test_pick = dict_test_picked[test_i_key]['index']
            res_list.append({'bug_ID':bug_id,'project':p_name_i,'time_budget':b_time,'k':k,"discount_factor":dis_factor,
                         'alpha':alpha,'beta':beta,'test_picked':test_i_key,'index_gen_suite':index_test,'loc_mode':loc,
                             "index_pick_test":index_test_pick ,"date_time":date_time,'sum_detected':kill_sum,
                             'count_detected':all_rep})
    df_final = pd.DataFrame(res_list)
    df_final.to_csv('{}/heuristic_P_{}_A_{}_B_{}_loc {}_Dfact_{}.csv'.format(out,p_name,alpha,beta,loc,dis_factor))

def get_rep_kill_out_raw_by_name(name,df):
    comp_name = str(name).split('_EST')[0]
    print list(df)
    df_filter = df.loc[df['TEST'] == comp_name]
    if len(df_filter )==0:
        raise Exception('The test is missing from the raw DataFrame --> {}'.format(name))
    if len(df_filter)==1:
        return df_filter['sum_detected'].sum(),df_filter['count_detected'].sum()
    else:
        raise Exception('more then one result in function [get_rep_kill_out_raw_by_name] ')
def filter_coverage_data(df, filter='_ESTest', col='component'):
    '''
    remove Test
    '''
    print list(df)
    print len(df)
    df = df[~df[col].str.contains(filter)]
    print len(df)
    return df

def minus_vec(v1,v2):
    res = np.subtract(v1,v2)
    np.place(res, res < 0, [0])
    return res

def to_binary_vec(vec):
    np.place(vec, vec > 0, [1])
    return vec



def make_coverage_matrix(dir_i='/home/ise/Desktop/new',debug_dir='/tmp',matrix_mode='BFS',is_file=True,debug=False,gama=0.1,dis_factor=0.01):
    '''
    Return MATRIX and unique test list and unique components list

    MATRIX-->
    index = test
    columns = component
    value = score

    LIST --> [name_1 ... name_n]

    :matrix_mode= BFS / step_10 / simple_path / LOC

    '''
    dir_name_i = str(dir_i).split('/')[-1]
    p_name_i = dir_name_i.split('_')[1]
    b_time = dir_name_i.split('_')[5]
    bug_id = dir_name_i.split('_')[3]
    index_test = dir_name_i.split('_')[7]
    date_time = '_'.join(dir_name_i.split('_')[9:])
    df_loc = find_loc_componenets(p_name_i, bug_id)
    df_bfs = pd.read_csv("{}/df_coverage_BFS.csv".format(dir_i),index_col=0)
    df_adj_matrixs = pd.read_csv('{}/df_coverage_step_1.csv'.format(dir_i),index_col=0)
    if len(df_bfs) == 0 :
        return None,None,None
    print df_bfs.dtypes

    if bug_id == '44':
        print ""
    if debug:
        print "df_bfs:\t",list(df_bfs)
        print "df_adj_matrixs:\t",list(df_adj_matrixs)

    test_comp_list = df_bfs['test_component'].unique()
    src_comp_list  = df_bfs['src_component'].unique()

    # save time and re_genrate all the tree struct again
    if is_file == True:
        if os.path.isfile("{}/tree_df.csv".format(dir_i)):
            df_in = pd.read_csv("{}/tree_df.csv".format(dir_i), index_col=0)
            test_comp_list = check_any_miss_tests(debug_dir,df_in, test_comp_list, bug_id, b_time, p_name_i, date_time, index_test)
            return make_matrix_score(df_in,gama=gama,dis_factor=dis_factor),test_comp_list, src_comp_list

    list_res = []
    for test_comp in test_comp_list:

        # cut the Dataframe to the given test name and remove all inf entry
        filter =  df_bfs.loc[df_bfs['test_component']==test_comp]
        filter = filter.loc[filter['depth'] < np.inf]
        filter.sort_values("depth", inplace=True)
        print test_comp,"\t",len(filter)
        # make a dict out of the Data_Frame
        list_depth = filter.to_dict('records')
        # a level dict, to know each edge to look up for
        d_level={}
        if debug:
            print "TEST:--->{}".format(test_comp)

        d_level[1.0]=[test_comp]
        for item in list_depth:
            cur_depth = item['depth'] +1
            if cur_depth not in d_level:
                d_level[cur_depth] = []
            d_level[cur_depth].append(item['src_component'])
        if debug:
            for ky in d_level.keys():
                print "{}:{}".format(ky, d_level[ky])
        # list_ky are all the unique level number list
        list_ky = d_level.keys()
        # for each level look for the next level edge and assign the number of edge
        d_edge={}
        d_edge[test_comp]=1
        for i in range(len(list_ky)):
            if i + 1 >= len(list_ky):
                break
            else:
                list_comp_i = d_level[list_ky[i]]
                list_comp_i_1 = d_level[list_ky[i + 1]]
                if debug:
                    print "list_comp_i_1 = {}".format(list_comp_i_1)
                for comp_i in list_comp_i:
                    cut_df = df_adj_matrixs.loc[df_adj_matrixs['component'] == comp_i]

                    if comp_i == 'org.apache.commons.lang3.text.translate.CharSequenceTranslator':
                        print cut_df['test']

                    for comp_j in list_comp_i_1:
                        res_df = cut_df.loc[cut_df['test'] == comp_j]
                        if len(res_df) == 1:
                            edge_num =  res_df['score'].sum()
                            if comp_j not in d_edge:
                                d_edge[comp_j]=[]
                            try:
                                father_edge = np.sum(d_edge[comp_i])
                            except Exception as e:
                                father_edge = 0
                                print "{}\t---->\t{}".format(comp_i,comp_j)
                            d_edge[comp_j].append(edge_num*father_edge)
                            list_res.append({"test_component":test_comp,
                                             "component_father":comp_i,
                                             "component_son":comp_j,
                                             "depth":list_ky[i],
                                             "edge":edge_num,
                                             "path":np.sum(d_edge[comp_j])})
                        else:
                            continue
    df = pd.DataFrame(list_res)
    df.to_csv("{}/tree_df.csv".format(dir_i))

    #check if some tests are empty if yes log them down:
    #
    test_comp_list = check_any_miss_tests(debug_dir,df,test_comp_list,bug_id,b_time,p_name_i,date_time,index_test)
    # end

    return make_matrix_score(df,gama=gama,dis_factor=dis_factor),test_comp_list,src_comp_list

def check_any_miss_tests(debug_dir,df,test_comp_list,bug_id,b_time,p_name_i,date_time,index_test):
    list_test_df = df['test_component'].unique()
    empty=[]
    for test_i in test_comp_list:
        if test_i in list_test_df:
            continue
        else:
            empty.append(test_i)
    if len(empty)>0:
        with open('{}/miss_tests.csv'.format(debug_dir),'a') as f:
            for elm in empty:
                f.write("{},{},{},{},{},{}\n".format(bug_id,b_time,p_name_i,date_time,index_test,elm))
    test_comp_list = list_test_df
    return test_comp_list


def make_matrix_score(df=None,dis_factor=0.01,path_to_df='/home/ise/Desktop/new/P_Lang_B_57_T_60_I_0_D_15_21_37_56_2018/tree_df.csv',gama=0.1):
    '''
    making the pivot table matrix and compute the score by the score = A^depth*number_path
    '''

    if df is None:
        df = pd.read_csv('{}'.format(path_to_df),index_col=0)

    df['score'] = df['path'] * np.power(dis_factor,df['depth'])

    print df['score'][:5]
    print list(df)
    df.rename(columns={'component_son': 'component', 'test_component': 'test'}, inplace=True)
    pivot_data_df = df.reset_index().pivot_table(index='test', columns='component', values='score').fillna(0)
    return pivot_data_df


def matrix_step_10(dir):
    '''
    making a pivot table out of the 10 step matrix
    :param dir:
    :return:
    '''
    df_coverage = pd.read_csv("{}/df_coverage_step_10.csv".format(dir),index_col=0)
    # extracting only the Test component
    if len(df_coverage) == 0:
        return None
    df_coverage = filter_coverage_data(df_coverage)
    list_test = df_coverage['test'].unique()
    print list_test
    list_comp = df_coverage['component'].unique()
    print list_comp
    print "num_of_test:\t", len(list_test)
    print df_coverage.dtypes
    # g = df_coverage.groupby('test')['score'].sum().reset_index(name='score_sum')
    pivot_data_df = df_coverage.pivot(index='test', columns='component', values='score').fillna(0)
    return pivot_data_df , list_test,list_comp

#######################################heuristic_process###################################################
def heuristic_process(df_data, dir_i, df_loc_componenet, k=2, alpha=0.7,beta=0.01,loc='LOC',gama=0.1,
                      discount_factor=0.01,f_name='tmp',debug_dir='/home/ise/eran/JARS/debug',debug=True):

    #pivot_data_df,list_test,list_comp = matrix_step_10(dir_i)

    pivot_data_df, list_test, list_comp = make_coverage_matrix(dir_i,debug_dir,dis_factor=discount_factor,gama=gama)

    if pivot_data_df is None:
        return None
    d_set_picked = {}
    for item_test in list_test:
        d_set_picked[item_test] = {'pick': 0}
    if k > len(list_test):
        k = len(list_test)
    for i in range(k):
        df_res = compute_heuristic(d_set_picked, pivot_data_df, df_data, df_loc_componenet,loc_mode=loc)
        df_res['rank'] = df_res['val_fp']*alpha+df_res['val_coverage']*(1-alpha)+beta*df_res['val_loc']
        test_picked = df_res['test'].iloc[df_res['rank'].argmax()]
        if debug:
            df_res.to_csv('{}/{}_{}.csv'.format(debug_dir,f_name,i))
        d_set_picked[test_picked]['pick']=1
        d_set_picked[test_picked]['index'] = i
    return d_set_picked

def compute_heuristic(d_pick, pivot_data, df_raw_data, df_loc_comp,binary=False,norm=True,loc_mode='LOC'):
    '''
    compute LOC
    compute Coverage
    compute FP
    '''
    vec_len = pivot_data.shape[1]
    picked_test = [x for x in d_pick.keys() if d_pick[x]['pick'] == 1]
    un_picked_test = [x for x in d_pick.keys() if d_pick[x]['pick'] == 0]
    print picked_test
    d_list = []
    if len(picked_test)==0:
        vector_picked=np.zeros(vec_len)
    else:
        vector_picked = pivot_data.ix[picked_test].values
    for item_test in un_picked_test:
        # fp compute
        equivalent_compnent = str(item_test).split('_EST')[0]
        df_filter_raw = df_raw_data.loc[df_raw_data['TEST'] == str(equivalent_compnent)]
        sum_fp = df_filter_raw['FP'].sum()
        # end fp
        # coverage compute
        cur_data = pivot_data.ix[item_test]
        cur_vec = cur_data.values

        #to_binary
        if binary:
            cur_vec = to_binary_vec(cur_vec)
            vector_picked = to_binary_vec(vector_picked)

        res = minus_vec(cur_vec, vector_picked)
        coverage_sum = np.sum(res)
        # end coverage
        # compute LOC
        val = 0
        if loc_mode == 'LOC':
            val = compute_LOC(cur_data, df_loc_comp, item_test, mode='LOC')
        elif loc_mode == 'simple':
            val = compute_LOC(cur_data,df_loc_comp,item_test,mode='simple')
        elif loc_mode == 'multi':
            val = compute_LOC(cur_data, df_loc_comp, item_test, mode='multi')
        sum_loc = val
        # end loc
        d_list.append({'test': item_test, 'val_coverage': coverage_sum,
                       'val_loc': sum_loc, 'val_fp': sum_fp})
    df_res = pd.DataFrame(d_list)
    if len(df_res) == 0:
        return None
    # norm all the val colounms
    if norm:
        for loc in ['val_coverage','val_loc']:
            df_res = call_g.min_max_noramlizer(df_res,loc,min_new_arg=0.01,max_new_arg=1)
    return df_res

def compute_LOC(cur_data,df_loc_comp,test_name,mode='simple'):
    '''
    compute the loc val for the heuristic
    '''
    cur_vec_filter = cur_data.loc[cur_data.values > 0]
    list_all_comp = cur_vec_filter.index.tolist()
    data_df_filter = df_loc_comp.loc[df_loc_comp['name'].isin(list_all_comp)]
    if mode =='simple':
        return data_df_filter['LOC'].sum()
    elif mode=='multi':
        data_df_filter['power'] = data_df_filter['name'].apply(lambda x: cur_vec_filter[x])
        data_df_filter['score'] = data_df_filter['power']*data_df_filter['LOC']
        return data_df_filter['score'].sum()
    elif mode == 'LOC':
        data_df_filter = data_df_filter.loc[data_df_filter['name']==str(test_name).split('_EST')[0]]
        return data_df_filter['LOC'].sum()

    #########################################heuristic_process#####################################################


def jar_making_process(src_dir):
    all_project = pt.walk_rec(src_dir, [], 'V_fixed', False)
    for proj_i in all_project:
        out_i = '/'.join(str(proj_i).split('/')[:-3])
        out_dir_jar = pt.mkdir_system(out_i, 'jars_dir')
        make_jars(proj_i, out_dir_jar)


def gatther_info_make_dir(row, out, list_info):
    bug_id = row['bug_ID']
    proj_name = row['Project_Name']
    test_index = row['Test_index']
    time_b = row['time_budget']
    date = row['Date']
    date = '_'.join(str(date).split('_')[-5:])
    name = 'P_{}_B_{}_T_{}_I_{}_D_{}'.format(proj_name, bug_id, time_b, test_index, date)
    out_dir_i = pt.mkdir_system(out, name)
    arr_dir_name = ['debug_dir', 'log', 'out_test']
    for dir_name in arr_dir_name:
        pt.mkdir_system(out_dir_i, dir_name)
    list_info.append({'p_name': proj_name, 'output': "{}/out_test".format(out_dir_i),
                      'log': "{}/log".format(out_dir_i), 'tmp_dir': "{}/debug_dir".format(out_dir_i),
                      'path': row['JAR_path'], 'version': bug_id})
    return out_dir_i


def mk_call_graph_df(root_dir, name_find='call_graph_stdout.txt'):
    res = pt.walk_rec(root_dir, [], name_find)
    for item in res:
        father_dir = '/'.join(str(item).split('/')[:-3])
        graph_obj = call_g.Call_g(item, father_dir)
        graph_obj.read_and_process(False)
        graph_obj.info_graph_csv()
        graph_obj.step_matrix()
        graph_obj.adj_matrix()
        graph_obj.coverage_matrix_BFS()


def find_loc_componenets(p_name, bug_id, is_norm=False, path_LOC_dir='/home/ise/eran/LOC'):
    '''
    finding the loc in a given project name and bug_id in LOC dir
    '''
    if os.path.isdir("{}/{}".format(path_LOC_dir, p_name)) is False:
        msg = "[Error] the path is not valid one --> {} ".format("{}/{}".format(path_LOC_dir, p_name))
        print msg
        return
    path_to_csv = "{0}/{1}/LOC_{1}_{2}.csv".format(path_LOC_dir, p_name, bug_id)
    print path_to_csv
    df_loc_componenet = pd.read_csv(path_to_csv, index_col=0)
    if is_norm:
        df_loc_componenet = call_g.min_max_noramlizer(df_loc_componenet, 'LOC')
    if df_loc_componenet is None:
        raise Exception("None LOC DATAFRAME")
    return df_loc_componenet


def mk_call_graph_raw_data(root_dir, name_find='jars_dir',
                           java_caller='/home/ise/programs/java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar'):
    res = pt.walk_rec(root_dir, [], name_find, False)
    for dir_i in res:
        father_dir = '/'.join(str(dir_i).split('/')[:-1])
        jars = pt.walk_rec(dir_i, [], '.jar')
        if len(jars) != 2:
            print "[Error] in dir --> {}\nfind:\n{}".format(dir_i, jars)
            continue
        out_jars = pt.mkdir_system(father_dir, 'out_jar')
        command_java_1 = 'java -jar {} {} {} '.format(java_caller,
                                                      jars[1], father_dir)
        command_java_0 = 'java -jar {} {} {} '.format(java_caller,
                                                      jars[0], father_dir)
        util_d4j.execute_command(command_java_1, 'call_graph', out_jars)
        util_d4j.execute_command(command_java_0, 'call_graph', out_jars)


def make_jars(path_proj, out_dir, src_dir_compile='target/classes/org', test_dir_compile='target/gen-tests/org'):
    '''
    make a jars one for the src files one for the test files
    # jar cvf <name>.jar <target_dir>
    '''
    util_d4j.make_jar("{}/{}".format(path_proj, src_dir_compile), 'src_classes', out_dir)
    util_d4j.make_jar("{}/{}".format(path_proj, test_dir_compile), 'test_classes', out_dir)

def csv_to_dict(p_name='Lang',debug=True):
    '''
    DataFrame to python dictionary result heurisitic
    '''
    res = pt.walk_rec('/home/ise/eran/JARS',[],'heuristic',lv=-1)
    df_list=[]
    for x in res:
        df_list.append(pd.read_csv(x,index_col=0))
    df = pd.concat(df_list)
    #csv_p = '/home/ise/eran/JARS/all_H.csv'.format(p_name)
    #df = pd.read_csv(csv_p,index_col=0)
    print list(df)
    d={}
    df.apply(dict_insert,dico=d,axis=1)
    if debug:
        for ky in d:
            print "first_key: {}".format(ky)
            for ky_sec in d[ky]:
                print "\tsec_key: {}".format(ky_sec)
                print "\t\t{}".format(d[ky][ky_sec])
    return d

def dict_insert(row, dico):
    '''
    insert the row into a dict
    first key: p_<project>_I_<gen_index>_A_<alpha>_B_<beta>_D_<date_gen>
    sec key: bug_ID
    d[first_key][sec_key]= key value --> { index_pick_test:test_name}
    '''
    id_bug = row['bug_ID']
    alpha = row['alpha']
    beta = row['beta']
    date_time= row['date_time']
    k = row['k']
    project_name = row['project']
    index_pick_test = row['index_pick_test']
    test_picked = row['test_picked']
    index_gen_suite = row['index_gen_suite']
    loc_mode = row['loc_mode']
    discount_factor = row['discount_factor']
    hyper_parm_key = "A_{}_B_{}_loc_{}_ds_{}".format(alpha,beta,loc_mode,discount_factor)
    key_date = 'I_{}_D_{}'.format(index_gen_suite,date_time)
    if id_bug not in dico:
        dico[id_bug]={}
    if hyper_parm_key not in dico[id_bug]:
        dico[id_bug][hyper_parm_key]={}
    if key_date not in dico[id_bug][hyper_parm_key]:
        dico[id_bug][hyper_parm_key][key_date]={}
    dico[id_bug][hyper_parm_key][key_date][index_pick_test] = test_picked
    return True


def main_parser():
    args = sys.argv
    if len(args)<2:
        print "---No args----"
        return
    if args[1] == 'main':
        manger(args[2], args[3], filter_time_b=[65])
    if args[1] == 'jar':
        jar_making_process(args[2])
    if args[1] == 'del':
        util_d4j.rm_dir_by_name(args[2], 'debug_dir')
        util_d4j.rm_dir_by_name(args[2], 'out_test')
    if args[1] == 'loc':
        find_loc_componenets()
    if args[1] == 'pred':
        making_pred()
    if args[1] == 'csv_to_dict':
        csv_to_dict()

if __name__ == '__main__':
    print "--in--"
    #root_jat_dir='/home/ise/Desktop/new',out='/home/ise/Desktop/new/out_pred'
    #making_pred(dis_factor=0.05,alpha=0.999,loc='LOC',beta=0.00001)
    making_pred(dis_factor=0.05, alpha=1, loc='LOC', beta=0.4)
    #making_pred(dis_factor=0.05, alpha=0.5, loc='LOC', beta=1000)
    ######
    # loc : multi , LOC , simple
    ######
   # making_pred(dis_factor=0.1, alpha=0.5, loc='simple', beta=1)
   # making_pred(dis_factor=1, alpha=0.5, loc='multi', beta=1)


    #exit()
    #making_pred(root_jat_dir='/home/ise/Desktop/new',out='/home/ise/Desktop/new/out_pred'
    #            ,dis_factor=0.05,alpha=0.5,loc='multi',beta=0.5)
    #making_pred(root_jat_dir='/home/ise/Desktop/new',out='/home/ise/Desktop/new/out_pred'
    #            ,dis_factor=0.05,alpha=0.5,loc='multi',beta=0.5)
    #sys.argv = ['', 'pred']
    main_parser()
