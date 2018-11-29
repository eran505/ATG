from numpy.core.multiarray import ndarray
from typing import Dict, Any
from sklearn import preprocessing
import pit_render_test
import os.path
import igraph as ig
import numpy as np
import pandas as pd

class Call_g:
    def __init__(self, path_file,out_dir):
        self.data_path = path_file
        self.out_dir_data = out_dir
        self.class_graph = {}
        self.method_graph = {}
        self.G_method = ig.Graph()
        self.G_class = ig.Graph()
        self.matrix_cover=None
        self.cover_df=None
    def init_G(self):
        self.G_class['name']

    def read_and_process(self,print_graph =False):
        """
        process and read the data from the given file
        :return: None
        """
        remove_pattrens = ['ESTest_scaffolding', 'junit.Assert','org.evosuite','$']
        lookup_pattren = ['org.apache.commons.lang']
        if os.path.isfile(self.data_path) is False:
            err_msg = "[Error] invalid path: {} ".format(self.data_path)
            raise Exception(err_msg)
        with open(self.data_path, 'r+') as f:
            arr_data = f.readlines()
        if len(arr_data) == 0:
            err_msg = "[Error] empty file, no data to process: {} ".format(self.data_path)
            raise Exception(err_msg)
        try:
            pat_prefix = '.'.join(arr_data[0].split()[0].split(':')[1].split('.')[:-1])
            lookup_pattren.append(pat_prefix)
        except Exception as e:
            print e.message
        for line in arr_data:
            if len(line) < 1:
                continue
            flag = 0
            for pat in remove_pattrens:
                if str(line).__contains__(pat):
                    print pat
                    flag = 1
                    break
            if flag == 1:
                continue
            for match_p in lookup_pattren:
                if line.__contains__(' ') is False:
                    continue
                if str(line).split()[1].__contains__(match_p):
                    print line
                    self.process_data(line)


        method_graph = self.G_method
        class_graph = self.G_class

        '''
        the next code section is responsible for printing the graph 
        green = Src Class
        blue = Evosutie Class 
        '''

        class_graph.vs["label"] = [str(name).split('.')[-1] for name in class_graph.vs["name"]]
        color_dict={True:'blue', False:'green'}
        class_graph.vs["color"] = [color_dict[indctor] for indctor in class_graph.vs["is_test"]]
        layout = class_graph.layout("kk")
        if print_graph:
            ig.plot(class_graph, layout=layout)

    def process_data(self, line_data,method=False,dup=True):
        """
        M for invoke virtual calls
        I for invoke interface calls
        O for invoke special calls
        S for invoke static calls
        D for invoke dynamic calls
        :param line_data:
        :return:
        """
        hash_table_is_exsit={}
        symbol = line_data[0]
        line_data = line_data[2:]
        split_data = str(line_data).split()
        klass = split_data[0]
        call_class = split_data[1]
        call_class_is_test=False
        klass_is_test = False
        if call_class.__contains__('ESTest'):
            call_class_is_test=True
        if klass.__contains__('ESTest'):
            klass_is_test=True
        if symbol == 'M':

            print "----method----"
            method_name = klass.split(':')[1]
            class_name = klass.split(':')[0]
            invoked_class = str(call_class).split(':')[0][3:]
            prop_invok = call_class[1]
            invoked_method = str(call_class).split(':')[1]
            inv_method, inv_args = self.get_args_method(invoked_method)
            src_name = '{}:{}'.format(class_name, method_name)
            target_name = '{}:{}'.format(invoked_class, inv_method)

            if method:
                print "{}:{} --> ({}){}:{}( {} )".format(class_name, method_name,
                                                         prop_invok, invoked_class, inv_method, inv_args)
                self.add_node('method', {'name': src_name, 'is_test': klass_is_test},hash_table_is_exsit)
                self.add_node('method', {'name': target_name, 'is_test': call_class_is_test},hash_table_is_exsit)
                self.add_edge(src_name, target_name,is_dup=dup)

            src_name=class_name
            target_name=invoked_class
            self.add_node('class', {'name': src_name, 'is_test': klass_is_test},hash_table_is_exsit)
            self.add_node('class', {'name': target_name, 'is_test': call_class_is_test},hash_table_is_exsit)

            self.add_edge(src_name, target_name,'class',is_dup=dup)

        elif symbol == 'C':
            print '---class---'
            print "{}-->{}".format(klass, call_class)
            self.add_node('class', {'name': klass, 'is_test': klass_is_test},hash_table_is_exsit)
            self.add_node('class', {'name': call_class, 'is_test': call_class_is_test},hash_table_is_exsit)
            self.add_edge(klass, call_class,'class',is_dup=dup)
        else:
            print 'error: {}'.format(symbol)
            raise Exception("error")


    def clean_text(self,txt):
        '''
        clean classes name from the text file
        '''
        if txt[-1]==';' and txt[0]=='[':
            return txt[2:-1]
        return txt

    def add_node(self, label, args_dico,hash_table_is_existe):
        '''

        :param label: if we looking at a scope of class or methods
        :param args_dico: the info of the given node
        :param hash_table_is_existe: a map table which node are existe in the Graph
        :return:
        '''
        if label == 'class':
            graph_g = self.G_class
        else:
            graph_g = self.G_method
        args_dico['name'] = self.clean_text(args_dico['name'])
        node_name = args_dico['name']
        if node_name == 'org.apache.commons.lang.CharRange':
            print ""
        try:
            node = graph_g.vs.find(name=node_name)
        except ValueError:
            if node_name in hash_table_is_existe:
                return False
            node = None
        except NameError:
            node = None
        if node is None:
            graph_g.add_vertex(**args_dico)
            hash_table_is_existe[node_name] = True
            return True
        else:
            return False

    def add_edge(self, source_name, target_name, label='method',is_dup=False):
        source_name=self.clean_text(source_name)
        target_name=self.clean_text(target_name)
        if label == 'method':
            G = self.G_method
        else:
            G = self.G_class
        if is_dup is False:
            if G.are_connected(source_name, target_name) is False:
                G.add_edge(source_name, target_name)
        else:
            G.add_edge(source_name, target_name)

    def get_args_method(self, data):
        size = len(str(data))
        acc_args = ''
        method_name = ''
        for i in range(size):
            if data[i] != '(':
                method_name += data[i]
                continue
            else:
                i = i + 1
                while (data[i] != ')'):
                    if i == size:
                        raise Exception('Error at get_args_methods out of bound ')
                    acc_args += data[i]
                    i += 1
                if len(acc_args) == 0:
                    acc_args = 'Null'
                return method_name, acc_args

    def make_dict_index_test_and_src(self,debug=False,label='class'):
        if label == 'class':
            g = self.G_class
        else:
            g = self.G_method
        if debug:
            print "is_directed = {} ".format(g.is_directed())
        test_index = {}  # the test node in the graph
        component_index = {}  # the src node in the file
        for node in g.vs:
            if node["is_test"]:
                test_index[node.index] = node['name']
            else:
                component_index[node.index] = node['name']
        if debug:
            print test_index
            print component_index
        return test_index,component_index

    def get_tree_distance_node(self,node_id,max_dist=10,target_nodes_dict=None,mode='class'):
        '''
        get the the simple path distnace dict
        :param target_nodes_dict: d={ id (int) : name (str) }
        :return: {id_node:int,name:str,dist:int)
        '''
        dict_results_list=[]
        if mode =='class':
            g = self.G_class
        else:
            g = self.G_method
        if target_nodes_dict is None:
            list_target = None
        else:
            list_target = target_nodes_dict
        result_arr = g.shortest_paths_dijkstra(source=node_id,target=list_target)
        print result_arr
        for i in range(len(result_arr[0])):
            test_name =g.vs[node_id]['name']
            src_name = g.vs[list_target[i]]['name']
            d_tmp={'test_component':test_name,
                   'src_component':src_name,
                   'depth':result_arr[0][i]}
            dict_results_list.append(d_tmp)
        return dict_results_list


    def adj_matrix(self):
        self.step_matrix(step=1)

    def info_graph_csv(self,mode='class'):
        if mode =='class':
            g=self.G_class
        else:
            g=self.G_method
        d_l=[]
        for item in g.vs:
            d_tmp={}
            d_tmp['name'] = item['name']
            d_tmp['is_test'] = item['is_test']
            d_tmp['index'] = item.index
            d_tmp['strength'] = item.strength()
            d_tmp['pagerank'] = item.personalized_pagerank()
            d_tmp['indegree'] = item.indegree()
            d_l.append(d_tmp)
        df = pd.DataFrame(d_l)
        df.to_csv('{}/info_vertex.csv'.format(self.out_dir_data))



    def step_matrix(self,step=10,normalize=False,mode='class',debug=False):
        if mode == 'class':
            g = self.G_class
        else:
            g = self.G_method
        coverage_dico = {}  # type-> Dict[Any, Dict[Any, ndarray]]

        test_index, component_index = self.make_dict_index_test_and_src()
        matrix = g.get_adjacency()
        matrix = matrix.data
        adjacency_matrix = np.matrix(matrix)
        adjacency_matrix = adjacency_matrix.astype(float)


        if debug:
            for ky_index in test_index.keys():
                test_name = test_index[ky_index]
                print test_name
                for x in component_index.keys():
                    if component_index[x] == str(test_name).split('_ES')[0]:
                        print "{}\t{}".format(component_index[x], adjacency_matrix[x, ky_index])
                        res = max(adjacency_matrix[:, ky_index]).tolist()
                        if int(res[0][0]) != int(adjacency_matrix[x, ky_index]):
                            raise Exception(
                                "the max node distance is not the componenet - _ESTest Warining in the Call_G_util")

        adjacency_matrix_steps = self.matrixMul_rec(adjacency_matrix, step)
        list_dict = []

        list_target = test_index.keys()
        if step == 1:
            list_target.extend(component_index.keys())


        for index_evo in list_target:
            tmp = adjacency_matrix_steps[:, index_evo]
            if debug:
                print "adjacency_matrix_10_step.shape={}".format(adjacency_matrix_steps.shape)
            i = 0
            d_item = {}
            for n in tmp:
                totalsum = np.sum(n)
                if totalsum > 0:
                    if debug:
                        print g.vs[i]['name']
                    d_item[g.vs[i]['name']] = totalsum
                    list_dict.append({'test': g.vs[index_evo]['name'], 'component': g.vs[i]['name'], 'score': totalsum})
                i += 1
            coverage_dico[g.vs[index_evo]['name']] = d_item

        self.matrix_cover = coverage_dico
        self.cover_df = pd.DataFrame(list_dict)
        if debug:
            print self.cover_df.dtypes
        if normalize:
            min_score = self.cover_df['score'].min()
            max_score = self.cover_df['score'].max()
            max_minus_min = float(max_score - min_score)
            new_max = 10000000
            new_min = 1
            self.cover_df['score'] = self.cover_df['score'].apply(
                lambda x: (float(x - min_score) / (max_minus_min)) * (new_max - new_min) + new_min)

        self.cover_df.to_csv('{}/df_coverage_step_{}.csv'.format(self.out_dir_data,step))

    def coverage_matrix_BFS(self,debug=False,mode='class'):

        """
        making a coverage matrix using BFS
        :param step: matrix ^ step
        :param out_df: path for DataFrame
        :param debug: print process consol
        :return: None
        """
        if mode == 'class':
            g = self.G_class
        else:
            g = self.G_method

        test_index,component_index = self.make_dict_index_test_and_src()

        #### this section does BFS on the graph for each test node constract matrix
        all_info_list=[]
        for test_id_node_i in test_index.keys():
            test_name_node_i = test_index[test_id_node_i]
            l_result = self.get_tree_distance_node(test_id_node_i  ,target_nodes_dict=component_index.keys())
            all_info_list.extend(l_result)
        df = pd.DataFrame(all_info_list)
        self.cover_df = df
        self.cover_df.to_csv('{}/df_coverage_BFS.csv'.format(self.out_dir_data))



    def matrixMul_rec(self,a, n):
        '''
        multi matrix rec function
        '''
        if (n <= 1):
            return a
        else:
            return np.matmul(self.matrixMul_rec(a, n - 1), a)

def g_test():
    g = ig.Graph()
    x = {'name': 'dd', 'age': 33}
    g.add_vertex(**x)
    #  y = g.vs.find(name="Claire")
    z = g.vs.find(name="dd")
    print "z:", z
    # print 'y:',y
    g.add_vertex(**x)
    g.add_vertex('xx')
    g.delete_vertices('xx')
    print g.vs['age']

    exit()

def min_max_noramlizer(df,col,min_new_arg=0,max_new_arg=1):
    print col
    print df[col]
    min_score = df[col].min()
    max_score = df[col].max()
    max_minus_min = float(max_score - min_score)
    if max_minus_min  == 0:
        df[col] = 0
        return df
    new_max = max_new_arg
    new_min = min_new_arg
    df[col] = df[col].apply(
        lambda x: (float(x - min_score) / (max_minus_min)) * (new_max - new_min) + new_min)
    return df

if __name__ == "__main__":
    # sudo pip install python-igraph
    print "in"
    path_file = '/home/ise/Desktop/new/P_zzz/lang_57.txt'
    out = '/home/ise/Desktop/new/P_zzz'
    graph_obj = Call_g(path_file,out)
    graph_obj.read_and_process(False)
    print "--"*60,'Q',"--"*60


    graph_obj.coverage_matrix_BFS()
    graph_obj.adj_matrix()
    graph_obj.step_matrix()
    graph_obj.info_graph_csv()