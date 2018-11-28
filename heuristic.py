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

    ###df = df.head(6)  # TODO: remove it !!!!

    print 'len(df):\t{}'.format(len(df))
    df['out_dir'] = df.apply(gatther_info_make_dir, out=src_dir, list_info=list_jar_info, axis=1)
    util_d4j.run_tests(list_jar_info)
    jar_making_process(src_dir)
    os.chdir(src_dir)
    util_d4j.rm_dir_by_name(src_dir, 'debug_dir')
    util_d4j.rm_dir_by_name(src_dir, 'out_test')
    mk_call_graph_raw_data(src_dir)
    mk_call_graph_df(src_dir)


def making_pred(p_name='Lang',out='/home/ise/eran/JARS' ,root_jat_dir='/home/ise/eran/JARS/JARS_D4J',
                csv_FP='/home/ise/eran/repo/ATG/D4J/FP',k=4,alpha=0.99999,beta=0.0001,debug=True):
    df = pd.read_csv("{0}/{1}/{1}.csv".format(csv_FP, p_name), index_col=0)
    print "df size:\t{}".format(len(df))
    print df.dtypes
    res_list=[]
    res = pt.walk_rec(root_jat_dir, [], 'df_coverage.csv')
    for item in res:
        print item
        p_name_i = str(item).split('/')[-2].split('_')[1]
        b_time = str(item).split('/')[-2].split('_')[5]
        bug_id = str(item).split('/')[-2].split('_')[3]
        index_test = str(item).split('/')[-2].split('_')[7]
        date_time= '_'.join(str(item).split('/')[-2].split('_')[9:])
        df_coverage = pd.read_csv(item, index_col=0)
        df_loc = find_loc_componenets(p_name_i, bug_id)

        # TODO: give zero to --> df_coverage instead of skip this bug_ID
        if len(df_coverage) == 0:
            continue

        # extracting only the Test component
        df_coverage = filter_coverage_data(df_coverage)
        if debug:
            out_debug = pt.mkdir_system("{}/debug".format(root_jat_dir),str(item).split('/')[-2])
        print list(df_coverage)
        print "----{}----".format(bug_id)
        df_filter = df.loc[df['bug_ID'] == int(bug_id)]
        print "df size:\t{}".format(len(df_filter))
        dict_test_picked = heuristic_process(df_filter, df_coverage, df_loc,k,alpha,beta,debug_dir=out_debug,f_name="{}_B_{}_K".format(p_name,bug_id))

        for test_i_key in dict_test_picked.keys():
            if dict_test_picked[test_i_key]['pick']==0:
                continue
            kill_sum,all_rep = get_rep_kill_out_raw_by_name(test_i_key,df_filter )
            index_test_pick = dict_test_picked[test_i_key]['index']
            res_list.append({'bug_ID':bug_id,'project':p_name_i,'time_budget':b_time,'k':k,
                         'alpha':alpha,'beta':beta,'test_picked':test_i_key,'index_gen_suite':index_test,
                             "index_pick_test":index_test_pick ,"date_time":date_time,'sum_detected':kill_sum,
                             'count_detected':all_rep})
    df_final = pd.DataFrame(res_list)
    df_final.to_csv('{}/heuristic_{}_V_max_LOC.csv'.format(out,p_name))

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

#######################################heuristic_process###################################################
def heuristic_process(df_data, df_coverage, df_loc_componenet, k=2, alpha=0.7,beta=0.01
                      ,f_name='tmp',debug_dir='/home/ise/eran/JARS/debug',debug=True):
    list_test = df_coverage['test'].unique()
    print list_test
    if len(list_test)==0:
        return None
    list_comp = df_coverage['component'].unique()
    print list_comp
    print "num_of_test:\t", len(list_test)
    d_set_picked = {}
    print df_coverage.dtypes
    # g = df_coverage.groupby('test')['score'].sum().reset_index(name='score_sum')
    pivot_data_df = df_coverage.pivot(index='test', columns='component', values='score').fillna(0)
    for item_test in list_test:
        d_set_picked[item_test] = {'pick': 0}
    if k > len(list_test):
        k = len(list_test)
    for i in range(k):
        df_res = compute_heuristic(d_set_picked, pivot_data_df, df_data, df_loc_componenet)
        df_res['rank'] = df_res['val_fp']*alpha+df_res['val_coverage']*(1-alpha)+beta*df_res['val_loc']
        df_res
        test_picked = df_res['test'].iloc[df_res['rank'].argmax()]
        if debug:
            df_res.to_csv('{}/{}_{}.csv'.format(debug_dir,f_name,i))
        d_set_picked[test_picked]['pick']=1
        d_set_picked[test_picked]['index'] = i
    return d_set_picked

def compute_heuristic(d_pick, pivot_data, df_raw_data, df_loc_comp):
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
        cur_vec = to_binary_vec(cur_vec)
        vector_picked = to_binary_vec(vector_picked)

        res = minus_vec(cur_vec, vector_picked)
        coverage_sum = np.sum(res)
        # end coverage
        # compute LOC
        cur_vec_filter = cur_data.loc[cur_data.values > 0]
        list_all_comp = cur_vec_filter.index.tolist()
        data_df_filter = df_loc_comp.loc[df_loc_comp['name'].isin(list_all_comp)]

        sum_loc = data_df_filter['LOC'].sum()
        # end loc
        d_list.append({'test': item_test, 'val_coverage': coverage_sum,
                       'val_loc': sum_loc, 'val_fp': sum_fp})
    df_res = pd.DataFrame(d_list)
    if len(df_res) == 0:
        return None
    # norm all the val colounms
    for loc in ['val_fp','val_coverage','val_loc']:
        if loc == 'val_fp':                         # TODO: FIX IT !!!
            continue
        df_res = call_g.min_max_noramlizer(df_res,loc,min_new_arg=0.01,max_new_arg=1)
    return df_res


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


def find_loc_componenets(p_name, bug_id, is_norm=True, path_LOC_dir='/home/ise/eran/LOC'):
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
    csv_p = '/home/ise/eran/JARS/all_H.csv'.format(p_name)
    df = pd.read_csv(csv_p,index_col=0)
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
    hyper_parm_key = "A_{}_B_{}".format(alpha,beta)
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
        manger(args[2], args[3], filter_time_b=[70,90,50])
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
    print "\t"
    sys.argv = ['', 'pred']
    main_parser()
