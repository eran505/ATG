import os ,sys,re
import pandas as pd
import numpy as np
import csv
import random as rand

import pit_render_test

class bugger:
    def __init__(self, result_path , pred_path,path_out):
        self.dcit = None
        self.seq = None
        self.col_name = ["ID,"]
        self.out = path_out
        self.result_path = result_path
        self.df_FP=None
        self.pred_path = pred_path
        self.read_csv_FP()
        self.seed = rand.randint(1, 99)
        self.random_object = rand.seed(self.seed)
        self.init_rand()
        self.df_bugs=None
        #self.data_freq = self.group_class()
        self.result_data = []

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

    def get_bugs_DataFrame(self,arr,draws=1,char=''):
        cols = list(self.df_bugs)

        df = pd.DataFrame(columns=cols)
        for klass in arr:
            df_part = self.df_bugs.loc[self.df_bugs['class'] == klass]
           # print df_part['class']
            size_part_df = len(df_part.index)
            if size_part_df == 0 :
                print "class not foud {}".format(klass)
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

    def get_plot(self,df,ch):
        list_val = list(df)
        list_val_U = [x for x in list_val if str(x).__contains__('_U')]
        list_val_FP = [x for x in list_val if str(x).__contains__('_FP')]
        d=[]
        time_u = []
        time_fp = []
        for x in list_val_U:
            time_val = str(x).split('_')[0]
            time_u.append(time_val)

        for x in list_val_FP:
            time_val = str(x).split('_')[0]
            time_fp.append(time_val)

        all_time = time_u + time_fp
        all_time = list(set(all_time))

        for t in all_time:
            val_u = -1.0
            val_fp = -1.0
            for col in list_val_U :
                if str(col).__contains__(t):
                    val_u = df[col].mean()
            for col_i in list_val_FP :
                if str(col_i).__contains__(t):
                    val_fp = df[col_i].mean()
            d.append({'time':t, 'FP':val_fp , 'U':val_u})
        df_finall = pd.DataFrame(d)
        #df_finall.sort(['time'], inplace=True)
        df_finall.to_csv(self.out+'seed_{}_res_fin_{}.csv'.format(self.seed,ch))

    def init_rand(self):
        self.random_object = rand
        self.random_object.seed(self.seed )

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




def init_main():
    p_path = '/home/eran/Desktop/out/big.csv'
    csv_fp_file = '/home/eran/thesis/repo/ATG/csv/FP_budget_time.csv'
    out_path ='/home/eran/Desktop/out/'

    p_path = '/home/ise/Desktop/smart_out/big.csv'
    out_path = '/home/ise/Desktop/smart_out/'
    csv_fp_file='/home/ise/eran/repo/ATG/csv/FP_budget_time.csv'


    print "starting.."
    bugger_obj = bugger(p_path,csv_fp_file,out_path)
    bugger_obj.pars_csv_by_bugID()
    arr= bugger_obj.bug_generator(5000,'U')
    bugger_obj.get_bugs_DataFrame(arr,1,'U')

    #bugger_obj = bugger(p_path,csv_fp_file,out_path)
    #bugger_obj.pars_csv_by_bugID()
    #arr= bugger_obj.bug_generator(5000,'U')
    #bugger_obj.get_bugs_DataFrame(arr,1,'U')

if __name__ == "__main__":
    init_main()
