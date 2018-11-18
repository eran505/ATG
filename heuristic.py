import pandas as pd
import os
import sys
import pit_render_test as pt
import util_defects4j as util_d4j


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
        d= {'JAR_path': item, 'Test_index': test_index, 'Fitness_Evosutie': fitness_evolution,
                       'time_budget': time_budget, 'Project_Name': project_name,
                       'bug_ID': bug_id, 'Date': date}
        print d
        d_info.append(d)
    df = pd.DataFrame(d_info)
    if out is not None:
        df.to_csv('{}/{}.csv'.format(out, file_name))
    return df


def manger(root_dir, out_dir,filter_time_b=None):
    """
    manage the process
    """
    if os.path.isdir(root_dir) is False:
        msg = "[Error] the dir path is not a valid one --> {}".format(root_dir)
        raise Exception(msg)
    src_dir = pt.mkdir_system(out_dir, 'JARS_D4J')
    df = scan_all_test_jar(root_dir, out=src_dir)
    list_jar_info = []
    if filter_time_b is not None:
        if isinstance(filter_time_b , list):
            df = df.loc[df['time_budget'].isin(filter_time_b)]
        else:
            df = df.loc[df['time_budget'] == filter_time_b]
    df.reset_index(inplace=True)
    df['out_dir'] = df.apply(gatther_info_make_dir, out=src_dir, list_info=list_jar_info, axis=1)
    util_d4j.run_tests(list_jar_info)


def gatther_info_make_dir(row, out, list_info):
    bug_id = row['bug_ID']
    proj_name = row['Project_Name']
    test_index = row['Test_index']
    time_b = row['time_budget']
    name = 'P_{}_B_{}_T_{}_I_{}'.format(proj_name, bug_id, time_b, test_index)
    out_dir_i = pt.mkdir_system(out, name)
    arr_dir_name = ['debug_dir', 'log', 'out_test']
    for dir_name in arr_dir_name:
        pt.mkdir_system(out_dir_i, dir_name)
    list_info.append({'project': proj_name, 'output': "{}/out_test".format(out_dir_i),
                      'log': "{}/log".format(out_dir_i), 'tmp_dir': "{}/debug_dir".format(out_dir_i),
                      'path': row['JAR_path'], 'version': bug_id})
    return out_dir_i


def main_parser():
    args = sys.argv
    if args[1] == 'jar':
        manger(args[2], args[3],60)


if __name__ == '__main__':
    print "\t"
    main_parser()
