import os ,sys,re
import pandas as pd
import numpy as np
import csv
import random as rand

import pit_render_test

class bugger:
    def __init__(self, result_path , pred_path,path_out,p_index=None):
        self.dcit = None
        self.seq = None
        self.col_name = ["ID,"]
        self.out = path_out
        self.result_path = result_path
        self.df_FP=None
        self.out_p=None
        self.df_index = None
        self.fp_index_path = p_index
        self.pred_path = pred_path
        self.read_csv_FP()
        self.df_bugs=None
        self.d_packages= None
        self.result_data = []
        self.err_not_found= {}
        self.init_dfs()
    def touch_file(self,path_out,total,ch):
        with open('{}err_not_found_{}.txt'.format(path_out,ch), 'wb') as fp:
            summ=0
            for k, v in self.err_not_found.items():
                fp.write(str(k) + ' >>> ' + str(v) + '\n\n')
                summ+=v
            fp.write("sum_not found = {}".format(summ) + '\n\n')
            fp.write("total= {}".format(total) + '\n\n')
            fp.write("parentage = {}".format(float(summ)/float(total)) + '\n\n')
            fp.close()

    def pars_csv_by_bugID(self):
        df_bugs = pd.read_csv(self.result_path)
        print list(df_bugs)
        df_bugs['class'] = df_bugs['ID'].apply(self.get_id)
        df_bugs = df_bugs.loc[:, ~df_bugs.columns.str.contains('^Unnamed')]
        print df_bugs.shape
        df_bugs = df_bugs.merge(self.df_FP,on='class')
        self.df_bugs = df_bugs
        #df_bugs.to_csv("/home/eran/Desktop/out/tmp.csv", sep='\t')
        print df_bugs.shape
        print list(df_bugs)

    def read_csv_FP(self):
        self.df_FP=pd.read_csv(self.pred_path,header=None,names=["class","probability"])

    def bug_generator(self,draws=10,rand='FP'):
        d_choices = self.df_FP['class'].values
        size_d_choices  = len(d_choices)
        if rand == 'U':
            d_probs = np.empty(size_d_choices)
            val = float(1)/float(size_d_choices)
            d_probs.fill(val)
        else:
            d_probs = self.df_FP['probability'].values
        res_arr =  np.random.choice(d_choices, draws, p=d_probs)
        print res_arr
        return res_arr

    def bug_generator_packages(self,mode,rand_mode='FP',draws=4,out='/home/ise/Desktop/out_package/'):
        packages_dfs = {}
        for ky_pack in self.d_packages.keys():
            size_len = len(self.d_packages[ky_pack])
            list_class =  self.d_packages[ky_pack]['class'].tolist()
            print "self.df_FP: {}".format(len(self.df_FP))
            df_fp_filter = self.df_FP.loc[self.df_FP['class'].isin(list_class)]
            print "df_fp_filter : {}".format(len(df_fp_filter))
            d_choices = df_fp_filter['class'].values
            size_d_choices = len(d_choices)
            if rand_mode == 'U':
                d_probs = np.empty(size_d_choices)
                val = float(1) / float(size_d_choices)
                d_probs.fill(val)
            else:
                d_probs = df_fp_filter['probability'].values
            sum_val = d_probs.sum()
            d_probs = [x/sum_val for x in d_probs ]
            res_arr = np.random.choice(d_choices, draws, p=d_probs)
            df_ky = self.get_bug_DataFrame_V1(res_arr,mode)
            packages_dfs[ky_pack]=df_ky
        out_path = self.out
        for key in packages_dfs:
            flush_csv(out_path,packages_dfs[key],key)



    def get_id(self,x):
        arr=str(x).split(',')
        if str(arr[0]).__contains__("org"):
            return arr[0][1:]
        else:
            raise Exception("no org.apache.commons.math3.X in the following {}".format(x))
    def group_class(self):  #TODO: Make ID:class  -> [bugID,FP,UNI]
        csv_file = csv.reader(open(self.result_path, "rb"), delimiter=",")
        ctr =0
        d={}
        d_list=[]
        for row in csv_file:
            if row[1] in d :
                arr = d[row[1]]
                arr.append({'fp':row[6],'ID':row[0],'uni':row[5]  })
            else:
                d[row[1]] = [{'fp':row[6],'ID':row[0] , 'uni':row[5] }]
        return d


    def get_relevant_ids(self,class_name):
        df_part = self.df_index.loc[self.df_index['class'] == class_name]
        print "len: {}".format( len(df_part))
        df_res = pd.merge(df_part,self.df_bugs,on=['ID'])
        #flush_csv(self.out_p,df_res,class_name)
        return df_res

    def get_bug_DataFrame_V1(self,arr,draws=1,char='',tot=0):
        all_bugs = None
        for klass in arr:
            id_df = self.get_relevant_ids(klass)
            size_cur = int(len(id_df))
            if size_cur == 0 :
                print "[Error] class has no ID mutations: {} ".format(klass)
                continue
            if draws < len(id_df):
                chosen_idx = np.random.choice(size_cur, replace=False, size=draws)
                df_trimmed = id_df.iloc[chosen_idx]
            else:
                df_trimmed = id_df
            if all_bugs is None:
                all_bugs=df_trimmed
            else:
                all_bugs = pd.concat([all_bugs, df_trimmed])
        return all_bugs



    def get_bugs_DataFrame(self,arr,draws=1,char='',tot=0):
        cols = list(self.df_bugs)

        df = pd.DataFrame(columns=cols)
        for klass in arr:
            df_part = self.df_bugs.loc[self.df_bugs['class'] == klass]
           # print df_part['class']
            size_part_df = len(df_part.index)
            if size_part_df == 0 :
                print "class not foud {}".format(klass)
                if klass in self.err_not_found:
                    self.err_not_found[klass] +=1
                else:
                    self.err_not_found[klass] = 1
                continue
            arr_elements = df_part['ID'].values
            print size_part_df
            np_prob= np.empty(size_part_df)
            np_prob.fill(float(1)/float(size_part_df))
            res = np.random.choice(arr_elements, draws, p=np_prob)
            for x  in res:
                tmp_df = df_part.loc[df_part['ID'] == x]
                df = df.append(tmp_df)
                #print df
        self.get_plot(df,char)

        out_str = "{}bugs_seed_{}_{}.csv".format(self.out,self.seed,char)
        df.to_csv(out_str)

        self.touch_file(self.out,tot,char)

    def get_plot(self,df,ch,mod='Avg'): # Avg or Sum
        list_val = list(df)
        list_val_U = [x for x in list_val if str(x).__contains__('U') and str(x).__contains__(mod)]
        list_val_FP = [x for x in list_val if str(x).__contains__('FP') and str(x).__contains__(mod) ]
        d=[]
        time_u = []
        time_fp = []
        for x in list_val_U:
            time_val = str(x).split('_')[0]
            time_val = time_val[2:]
            time_u.append(time_val)

        for x in list_val_FP:
            time_val = str(x).split('_')[0]
            time_val = time_val[2:]
            time_fp.append(time_val)

        all_time = time_u + time_fp
        all_time = list(set(all_time))

        for t in all_time:
            val_u = -1.0
            val_fp = -1.0
            for col in list_val_U :
                if str(col).__contains__("t={}_".format(t)):
                    val_u = df[col].mean()
                    break
            for col_i in list_val_FP :
                if str(col_i).__contains__("t={}_".format(t)):
                    val_fp = df[col_i].mean()
                    break
            d.append({'time':t, 'FP':val_fp , 'U':val_u})
        df_finall = pd.DataFrame(d)
        if self.out_p[-1]=='/':
            df_finall.to_csv(self.out+'{}_fin_{}.csv'.format(mod,ch))
        else:
            df_finall.to_csv(self.out + '/{}_fin_{}.csv'.format(mod, ch))

    def sort_list(self):
        list_d={}
        csv_file = csv.reader(open(self.pred_path, "rb"), delimiter=",")
        acc=0
        ctr=0
        for row in csv_file:
            ctr+=1
            acc+=float(row[1])
            if float(row[2]) < 1 :
                continue
            list_d[acc]=[{"class":row[0] , "time":row[2],"pred":row[1]  }]
        self.dcit=list_d
        self.seq = sorted(self.dcit.keys())

    def binary_search(self,seq,value):
        if len(seq) == 0:
            return False
        if len(seq) == 1 :
            return seq[0]
        else:
            mid = len(seq) / 2
            if value == seq[mid]:
                return value
            elif value < seq[mid]:
                return self.binary_search(seq[:mid], value)
            elif value > seq[mid]:
                return self.binary_search(seq[mid + 1:], value)

    def n_search(self,seq,value):
        ans =-1
        for x in seq:
            if value > x :
                continue
            else:
                ans = x
                break;
        return ans

    def uniform_bugs(self):
        val = self.random_object.random()
        val = val * len(self.data_freq)
        val = int(val)
        list_keys = self.data_freq.keys()
        bug = list_keys[val]
        fin_bug_arr = self.data_freq[bug]
        size = len(fin_bug_arr)
        res_num = self.random_object.randint(0, size - 1)
        bugg = fin_bug_arr[res_num]
        bugg['pred_bug'] = 1/len(self.data_freq.values())
        self.result_data.append(bugg)
        return

    def get_bUG(self):
        ctr = 0
        while True:
            ctr=+1
            val = self.random_object.random()
            val = val * self.seq[-1]
            if val in self.seq :
                tmp=self.dcit[val]
            else:
                x = self.n_search(self.seq,val)
                tmp = self.dcit[x]
            bug = tmp[0]['class']
            pred = tmp[0]['pred']
            if bug in self.data_freq :
                fin_bug_arr = self.data_freq[bug]
                size = len(fin_bug_arr)
                res_num = self.random_object.randint(0, size-1)
                bugg = fin_bug_arr[res_num]
                bugg['pred_bug'] = pred
                self.result_data.append(bugg)
                return
            if ctr > 100 :
                print "error: in get_bUG"
                exit(1)
                return

    def make_bugs(self,rounds=10,mod="fp"):
        if mod == "fp":
            for i in range(rounds):
                self.get_bUG()
        else :
            for i in range(rounds):
               self.uniform_bugs()
        df = pd.DataFrame(self.result_data,columns=["ID", "pred_bug", "fp", "uni"])
        df['kill_fp'] = np.where(df['fp'].astype(float) > 0, "1", "0")
        df['kill_uni'] = np.where(df['uni'].astype(float) > 0, '1', '0')
        df['only_uni'] = np.where(( df['kill_uni'].astype(float) == 1) & (df['kill_fp'].astype(float)==0) , '1', '0')
        df['only_fp'] = np.where((df['kill_uni'].astype(float) == 0) & (df['kill_fp'].astype(float) == 1), '1', '0')
        df['both'] = np.where((df['kill_uni'].astype(float) == 1 )& (df['kill_fp'].astype(float) == 1), '1', '0')
        df['none'] = np.where((df['kill_uni'].astype(float) == 0) & (df['kill_fp'].astype(float) == 0), '1', '0')
        sum_none = df['none'].astype(int).sum()
        sum_both = df['both'].astype(int).sum()
        sum_only_fp =  df['only_fp'].astype(int).sum()
        sum_only_uni = df['only_uni'].astype(int).sum()
        sum_fp = df['kill_fp'].astype(int).sum()
        sum_uni = df['kill_uni'].astype(int).sum()



        d={ 'none':sum_none , 'both':sum_both , 'only_fp':sum_only_fp , 'only_uni':sum_only_uni , 'fp':sum_fp , 'uni':sum_uni}
        df_sum = pd.DataFrame([d])
        df_sum.to_csv(self.out+'sum_seed_'+str(self.seed)+'.csv',encoding='utf-8', index=False)
        df.to_csv(self.out+'bug_seed_'+str(self.seed)+'.csv',encoding='utf-8', index=False)

    def init_dfs(self):
        self.init_index()
        p = self.result_path
        arr = str(p).split('/')[:-1]
        self.out_p = '/'.join(arr)
        self.df_bugs=pd.read_csv(self.result_path,index_col=0)

    def package_separation(self,num,mod):  ## for package analysis !!!!!
        d_package = {}
        if self.df_index is None:
            print "No index DataFrame is available"
            return None
        self.df_index['package']=self.df_index['class'].apply(lambda x: '.'.join(str(x).split('.')[:-1]))
        all_package_list=self.df_index['package'].unique()
        for pack in all_package_list:
            d_package[pack]=self.df_index.loc[self.df_index['package'] == pack]
        self.d_packages = d_package
        res_data = self.bug_generator_packages(num,mod)


    def init_index(self):
        if self.fp_index_path is None:
            p = self.result_path
            arr = str(p).split('/')[:-1]
            root_p = '/'.join(arr)
            bol=get_ID_index_table(root_p)
            if bol:
                df_index = pd.read_csv("{}/indexer.csv".format(root_p),index_col=0)
            else:
                print "[Error ] No index csv in :{}".format(root_p)
                raise Exception("no index")
        else:
            df_index = pd.read_csv("{}".format(self.fp_index_path), index_col=0)
        self.df_index = df_index
        ###############################
        df_fp = self.df_FP
        print list(df_fp)
        print 'size:{}'.format(df_fp.shape)
        result_df = pd.merge(df_fp,df_index,on=['class'])
        flush_csv('/home/ise/eran/random',result_df,'fp_index')
        print list(df_index )
        print 'size:{}'.format(df_index.shape)

def

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
    print "done"
    return True


def collctor(path,name_file):
    out_path = '/'.join(str(path).split('/')[:-1])
    list_dico = []
    csv_list = pit_render_test.walk(path,'.csv')
    for item_csv in csv_list:
        name  = str(item_csv).split('/')[-1][:-4]
        df = pd.read_csv(item_csv,index_col=0)
        list_cols = list(df)
        list_cols = [x for x in list_cols if str(x).__contains__('t=')]
        d={'package':name}
        for col in list_cols:
            d[col]=df[col].mean()
        list_dico.append(d)
    ans_df = pd.DataFrame(list_dico)
    flush_csv(out_path,ans_df,name_file)

def flush_csv(out_path_dir, xml_df, name_file):
    if xml_df is None:
        return
    ##print "{}/{}.csv".format(out_path_dir, name_file)
    xml_df.to_csv("{}/{}.csv".format(out_path_dir,name_file))

def init_main():
    #collctor('/home/ise/eran/random/LANG/tran_FP','FP_summery')
    #collctor('/home/ise/eran/random/LANG/tran_U', 'U_summery')
    #exit()
    print "starting.."
    for mod in ['FP','U']:
        num=5000
        ch_i = 1
        #get_ID_index_table('/home/ise/tran')
        out_path = pit_render_test.mkdir_system('/home/ise/Desktop/tmp/LANG','tran_{}'.format(mod),False)
        p_path = '/home/ise/eran/lang/big_all_df.csv'
        p_index = '/home/ise/eran/lang/indexer.csv'
        csv_fp_file='/home/ise/eran/repo/ATG/csv/FP_budget_time_lang.csv'
        #csv_fp_file = '/home/ise/eran/repo/ATG/csv/FP_budget_time_math.csv'
        bugger_obj = bugger(p_path,csv_fp_file,out_path,p_index)
        #bugger_obj.package_separation(num,mod)
        #continue
        arr= bugger_obj.bug_generator(num,mod)
        df = bugger_obj.get_bug_DataFrame_V1(arr,ch_i,mod,num)
        bugger_obj.get_plot(df,ch_i)
        bugger_obj.get_plot(df,ch_i,'Sum')
        flush_csv(out_path,df,'n_{}_mod_{}'.format(num,mod))
    exit()



if __name__ == "__main__":
    init_main()

