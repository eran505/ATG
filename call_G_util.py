import pit_render_test
import os.path
import igraph as ig


class Call_g:
    def __init__(self, path_file):
        self.data_path = path_file
        self.class_graph = {}
        self.method_graph = {}
        self.G_method = ig.Graph()
        self.G_class = ig.Graph()

    def init_G(self):
        self.G_class['name']

    def read_and_process(self):
        """
        process and read the data from the given file
        :return: None
        """
        remove_pattrens = ['ESTest_scaffolding', 'junit.Assert','org.evosuite']
        lookup_pattren = []
        if os.path.isfile(self.data_path) is False:
            err_msg = "[Error] invalid path: {} ".format(self.data_path)
            raise Exception(err_msg)
        with open(self.data_path, 'r+') as f:
            arr_data = f.readlines()

        if len(arr_data) == 0:
            err_msg = "[Error] empty file, no data to process: {} ".format(self.data_path)
            raise Exception(err_msg)
        pat_prefix = '.'.join(arr_data[0].split()[0].split(':')[1].split('.')[:-1])
        lookup_pattren.append(pat_prefix)
        for line in arr_data:
            flag = 0
            for pat in remove_pattrens:
                if str(line).__contains__(pat):
                    print pat
                    flag = 1
                    break
            if flag == 1:
                continue
            for match_p in lookup_pattren:
                if str(line).split()[1].__contains__(match_p):
                    print line
                    self.process_data(line)


        method_graph = self.G_method
        class_graph = self.G_class

        class_graph.vs["label"] = [str(name).split('.')[-1] for name in class_graph.vs["name"]]
        color_dict={True:'blue', False:'green'}
        class_graph.vs["color"] = [color_dict[indctor] for indctor in class_graph.vs["is_test"]]
        layout = class_graph.layout("kk")
        ig.plot(class_graph, layout=layout)

    def process_data(self, line_data):
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
        if symbol == 'M':
            print "----method----"
            method_name = klass.split(':')[1]
            class_name = klass.split(':')[0]
            invoked_class = str(call_class).split(':')[0][3:]
            prop_invok = call_class[1]
            invoked_method = str(call_class).split(':')[1]
            inv_method, inv_args = self.get_args_method(invoked_method)
            print "{}:{} --> ({}){}:{}( {} )".format(class_name, method_name,
                                                     prop_invok, invoked_class, inv_method, inv_args)
            src_name = '{}:{}'.format(class_name, method_name)
            target_name = '{}:{}'.format(invoked_class, inv_method)
            self.add_node('method', {'name': src_name, 'is_test': True})
            self.add_node('method', {'name': target_name, 'is_test': False})
            self.add_edge(src_name, target_name)

            src_name=class_name
            target_name=invoked_class
            self.add_node('class', {'name': src_name, 'is_test': True})
            self.add_node('class', {'name': target_name, 'is_test': False})
            self.add_edge(src_name, target_name,'class')

        elif symbol == 'C':
            print '---class---'
            print "{}-->{}".format(klass, call_class)
            self.add_node('class', {'name': klass, 'is_test': True})
            self.add_node('class', {'name': call_class, 'is_test': False})
            self.add_edge(klass, call_class,'class')
        else:
            print 'error: {}'.format(symbol)
            raise Exception("error")

    def add_node(self, label, args_dico):
        if label == 'class':
            graph_g = self.G_class
        else:
            graph_g = self.G_method
        node_name = args_dico['name']
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

    def add_edge(self, source_name, target_name, label='method'):
        G = None
        if label == 'method':
            G = self.G_method
        else:
            G = self.G_class
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


if __name__ == "__main__":
    #g_test()
    print "in"
    #graph_obj = Call_g('/home/ise/Desktop/call_G/common_lang_test_callG.txt')
    #graph_obj.read_and_process()
