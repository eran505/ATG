import os.path


class tester_gen:

    def __init__(self,inverment,config_file_path,root_path,dist_path):
        self.root = root_path
        self.out_dist = dist_path
        self.config_path = config_file_path
        self.builder = inverment
        self.dict_config=None

    def read_config_file(self):
        '''
        Evosuite config file:
        time_each_class: time in seconds > 0
        replication: number > 0
        src: where is the source file
        project: project name
        :return:
        '''
        if os.path.isfile(self.config_path) is False:
            msg = '[Error] the path to the config file is not vaild --> {}'.format(self.config_path)
            raise Exception(msg)
        d={}
        with open(self.config_path,'r') as file_conf:
            lines = file_conf.readlines()
            for line in lines:
                if len(line) < 1:
                    continue
                if line.__contains__(':='):
                    arr_tmp = line.split(':=')
                    d[arr_tmp[0]]=arr_tmp[1]
        self.dict_config = d