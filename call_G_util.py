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
                self.add_node('method', {'name': src_name, 'is_test': klass_is_test})
                self.add_node('method', {'name': target_name, 'is_test': call_class_is_test})
                self.add_edge(src_name, target_name,is_dup=dup)

            src_name=class_name
            target_name=invoked_class
            self.add_node('class', {'name': src_name, 'is_test': klass_is_test})
            self.add_node('class', {'name': target_name, 'is_test': call_class_is_test})

            self.add_edge(src_name, target_name,'class',is_dup=dup)

        elif symbol == 'C':
            print '---class---'
            print "{}-->{}".format(klass, call_class)
            self.add_node('class', {'name': klass, 'is_test': klass_is_test})
            self.add_node('class', {'name': call_class, 'is_test': call_class_is_test})
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

    def add_node(self, label, args_dico):

        if label == 'class':
            graph_g = self.G_class
        else:
            graph_g = self.G_method
        node_name = args_dico['name']
        args_dico['name'] = self.clean_text(node_name)
        try:
            node = graph_g.vs.find(name=node_name)
        except ValueError:
            node = None
        except NameError:
            node = None
        if node is None:
            graph_g.add_vertex(**args_dico)
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

    def coverage_matrix(self,step=10,normalize=False,debug=False):
        '''
        making a coverage matrix
        :param step: matrix ^ step
        :param out_df: path for DataFrame
        :param debug: print process consol
        :return: None
        '''
        coverage_dico={}  # type: Dict[Any, Dict[Any, ndarray]]
        g = self.G_class
        if debug:
            print "is_directed = {} ".format(g.is_directed())
        matrix = g.get_adjacency()
        matrix = matrix.data
        test_index={}
        component_index={}
        for node in g.vs:
            if node["is_test"]:
                test_index[node.index]=node['name']
            else:
                component_index[node.index]=node['name']
        if debug:
            print test_index
            print component_index
        adjacency_matrix = np.matrix(matrix)
        adjacency_matrix = adjacency_matrix.astype(float)
        adjacency_matrix_steps = self.matrixMul_rec(adjacency_matrix,step)
        list_dict=[]
        for index_evo in test_index.keys() :
            tmp = adjacency_matrix_steps[:,index_evo]
            if debug:
                print "adjacency_matrix_10_step.shape={}".format(adjacency_matrix_steps.shape)
            i = 0
            d_item={}
            for n in tmp :
                totalsum = np.sum(n)
                if totalsum>0:
                    if debug:
                        print g.vs[i]['name']
                    d_item[g.vs[i]['name']]=totalsum
                    list_dict.append({'test':g.vs[index_evo]['name'], 'component':g.vs[i]['name'],'score':totalsum })
                i+=1
            coverage_dico[g.vs[index_evo]['name']]=d_item

        self.matrix_cover=coverage_dico
        self.cover_df=pd.DataFrame(list_dict)
        print self.cover_df.dtypes
        if normalize:
            min_score = self.cover_df['score'].min()
            max_score = self.cover_df['score'].max()
            max_minus_min = float(max_score - min_score)
            new_max=10000000
            new_min=1
            self.cover_df['score'] = self.cover_df['score'].apply(lambda x :(float(x-min_score)/(max_minus_min))*(new_max-new_min)+new_min)
        if debug:
            print "------"*100
            for key in coverage_dico.keys():
                print "\t{}".format(key)
                for ky_sec in  coverage_dico[key].keys():
                    print "{}:{}".format(ky_sec,coverage_dico[key][ky_sec])
        self.cover_df.to_csv('{}/df_coverage.csv'.format(self.out_dir_data))
        return coverage_dico


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
    path_file = '/home/ise/Desktop/new/zzz/lang_57.txt'
    out = '/home/ise/Desktop/new/zzz'
    graph_obj = Call_g(path_file,out)
    graph_obj.read_and_process(False)
    print "--"*60,'Q',"--"*60
    graph_obj.coverage_matrix()
    #print graph_obj.G_class.adjacent(target_vs)