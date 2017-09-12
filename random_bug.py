import os ,sys,re
import pandas as pd
import numpy as np
import csv
import random as rand
from scipy.io.matlab.miobase import arr_dtype_number

import pit_render_test

class bugger:
    def __init__(self, result_path , pred_path,path_out):
        self.dcit = None
        self.seq = None
        self.out = path_out
        self.result_path = result_path
        self.pred_path = pred_path
        self.sort_list()
        self.seed = rand.randint(1, 99)
        self.random_object = rand.seed(self.seed)
        self.init_rand()
        self.data_freq = self.group_class()
        self.result_data = []

    def group_class(self):  #TODO: Make ID:class  -> [bugID,FP,UNI]
        csv_file = csv.reader(open(self.result_path, "rb"), delimiter=",")
        ctr =0
        d={}
        for row in csv_file:
            if row[1] in d :
                arr = d[row[1]]
                arr.append({'fp':row[6],'ID':row[0],'uni':row[5]  })
            else:
                d[row[1]] = [{'fp':row[6],'ID':row[0] , 'uni':row[5] }]
        return d



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
            acc+=float(row[2])
            if float(row[1]) < 1 :
                continue
            list_d[acc]=[{"class":row[0] , "time":row[1],"pred":row[2]  }]
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

    def get_bUG(self):
        val = self.random_object.random()
        val = val * self.seq[-1]
        if val in self.seq :
            tmp=self.dcit[val]
        else:
            x = self.n_search(self.seq,val)
            tmp = self.dcit[x]
        bug = tmp[0]['class']
        pred = tmp[0]['pred']
        if bug in self.data_freq is False :
            return
        fin_bug_arr = self.data_freq[bug]
        size = len(fin_bug_arr)
        res_num = self.random_object.randint(0, size-1)
        bugg = fin_bug_arr[res_num]
        bugg['pred_bug'] = pred
        self.result_data.append(bugg)

    def make_bugs(self,rounds=100):
        for i in range(rounds):
            self.get_bUG()
        df = pd.DataFrame(self.result_data)
        df['win'] = np.where(df['uni'] > df[], 1, 0)
        df.reindex(columns=["ID","pred_bug","fp","uni"])
        df.to_csv(self.out+'bug_seed_'+str(self.seed)+'.csv',encoding='utf-8', index=False)




def init_main():
    print "starting.."
    bugger_obj = bugger('/home/eran/Desktop/package_MATH_t=20/all.csv','/home/eran/thesis/test_gen/experiment/t20/FP_budget_time.csv','/home/eran/Desktop/bug/')
    bugger_obj.make_bugs()

if __name__ == "__main__":
    init_main()