import os ,sys,re
import pandas as pd
import numpy as np
import csv
import random as rand
from scipy.io.matlab.miobase import arr_dtype_number

import pit_render_test

class bugger:
    def __init__(self, result_path , pred_path):
        self.dcit = None
        self.seq = None
        self.result_path = result_path
        self.pred_path = pred_path
        print list(self.df)
        self.sort_list()
        self.seed = rand.randint(1, 99)
        self.random_object = rand.seed(self.seed)
        self.init_rand()
        self.data_freq = self.group_class()

    def group_class(self):  #TODO: Make ID:class  -> [bugID,FP,UNI]
        csv_file = csv.reader(open(self.result_path, "rb"), delimiter=",")
        for row in csv_file:
            print 'TOd|o|'


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
            list_d[acc]=[{"class":row[0] , "time":row[1],"pred":row[2] }]
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
        print val
        if val in self.seq :
            tmp=self.dcit[val]
        else:
            x = self.n_search(self.seq,val)
            tmp = self.dcit[x]
        bug = tmp[0]['class']
        pred = tmp[0]['pred']
        print bug,' p=',pred


def init_main():
    print "starting.."
    bugger_obj = bugger('/home/eran/Desktop/package_MATH_t=20/all.csv','/home/eran/thesis/test_gen/experiment/t20/FP_budget_time.csv')
    print bugger_obj.data_freq
    for i in range(1):
        bugger_obj.get_bUG()

if __name__ == "__main__":
    init_main()