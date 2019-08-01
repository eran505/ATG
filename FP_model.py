import os

from anaconda_project.test.test_prepare import test_prepare_some_env_var_already_set

import pit_render_test as pt
from scipy.io import arff
from io import StringIO
import numpy as np
from sklearn.preprocessing import LabelEncoder
import pandas as pd
from scipy.io.arff import loadarff
import xgboost as xgb
from sklearn.metrics import auc, accuracy_score, confusion_matrix, roc_curve,mean_squared_error, precision_recall_curve, \
    average_precision_score, mean_absolute_error, f1_score,roc_auc_score,precision_score,recall_score

import matplotlib.pyplot as plt
from sklearn.utils.fixes import signature
from sklearn import cross_validation
from sklearn.model_selection import GridSearchCV
import matplotlib.pylab as plt
from matplotlib.pylab import rcParams
from matplotlib import pyplot
from sklearn.model_selection import StratifiedShuffleSplit

rcParams['figure.figsize'] = 12, 4
from sklearn import metrics

target = 'hasBug'

name_fig=None

def main_func(test_arff, train_arff, valid_set, target_col='hasBug', under_sample=False, cross_proj=False,over_sample=1,conf=True):
    # load arff to pandas DataFrame
    raw_data = loadarff(train_arff)
    train_df = pd.DataFrame(raw_data[0])
    raw_tets = loadarff(test_arff)
    test_df = pd.DataFrame(raw_tets[0])

    print (train_df[target].value_counts())
    #return None, None, None, None
    # cross_project_adding bugs:
    df_fault = None
    if cross_proj:
        df_fault = add_samples_from_other_project(p=0.1)
        df_fault['train'] = 2

    # merge two DataSets
    valid_df = None
    if valid_set is not None:
        print "valid_set:\t",valid_set
        arff_valid = loadarff(valid_set)
        valid_df = pd.DataFrame(arff_valid[0])
        valid_df['train'] = 3

    train_df['train'] = 1
    test_df['train'] = 0
    df_list = []
    for df in [train_df, test_df, df_fault, valid_df]:
        if df is not None:
            df_list.append(df)
    df_combined = pd.concat(df_list)

    # convert the target to --> binary
    df_combined = converting_target(df_combined)

    # look for categorical col
    cols_cat = categorical_features_look(df_combined)
    # one hot the catagorial features
    df_combined = one_hot_convertor(cols_cat, df_combined)

    d_DF = get_train_test_set(df_combined)
    train_df = d_DF[1]
    del d_DF[1]

    # Remove col with the same values
    train_df, cols_del = remove_col_same_val(train_df)
    if train_df is None:
        return None, None, None, None
    print "del size cols_del = {}".format(len(cols_del))
    # drop also cols from the test set, valid set ....
    for ky in d_DF.keys():
        val_df = d_DF[ky]
        if val_df is not None:
            val_df = val_df.drop(cols_del, axis=1)
            d_DF[ky]=val_df


    test_df = d_DF[0]
    cross_df = d_DF[2]
    valid_df = d_DF[3]
    if cross_proj:
        train_df = pd.concat([train_df, cross_df])
    print "the number of col with the same value are: {}".format(len(cols_del))
    print "num of features that are left: {}".format(len(list(train_df)) - 1)

    if under_sample:
        train_df = Random_under_sampling(train_df)
    if over_sample > 0:
        train_df = Random_over_sampling(train_df, target_ratio=over_sample)
    # imbalanced data
    # Train Proportion:
    target_ratio = print_Proportion(train_df, 'Train')
    val = print_Proportion(test_df, 'TEST')
    if val == -1:
        test_df = None

    if valid_df is not None:
        val = print_Proportion(valid_df, 'Validtion')
        if val == -1:
            valid_df = None
        else:
            valid_df = valid_df.reset_index(drop=True)
            if test_df is None:
                test_df = valid_df.copy(deep=True)
                valid_df = None
                print "[Warning] the validtion set is now the test set !!!!!"

    if test_df is None:
        return None,None,None,None

    # reset the index
    train_df = train_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    return train_df, test_df, target_ratio, valid_df


def print_Proportion(df, name):
    print ("{} Proportion:".format(name))
    print ("---------------")
    target_count = df[target].value_counts()
    print('Class valid ({}):\t{}'.format(name, target_count[0]))
    if len(target_count) == 1:
        return -1
    print('Class bug ({}):\t{}'.format(name, target_count[1]))
    target_ratio = float(target_count[0]) / float(target_count[1])
    print('Proportion ({}):\t{}'.format(name, round(float(target_count[1]) / float(target_count[0]), 8), ': 1'))
    print ("ratio ({}): {}".format(name, target_ratio))
    return target_ratio


def add_samples_from_other_project(p_path=r'/home/ise/bug_miner/XGB/MATH_BUGS.csv', p=0.10):
    if p_path.endswith('.csv'):
        df_all_bugs = pd.read_csv(p_path)
    else:
        res_arff = pt.walk_rec(p_path, [], '.arff')
        df_list = []
        for item in res_arff:
            raw_data = loadarff(item)
            df = pd.DataFrame(raw_data[0])
            print len(df)
            df = df.loc[df[target] == 'bugged']
            df_list.append(df)
        df_all_bugs = pd.concat(df_list)
        print "df_all_bugs: {}".format(len(df_all_bugs))
        df_all_bugs.to_csv("/home/ise/bug_miner/XGB/MATH_BUGS.csv")
    print df_all_bugs.shape
    frac_df = df_all_bugs.sample(frac=p, axis=0)
    print frac_df.shape
    return df_all_bugs


def reacall_precision(y_test, y_score,ploting=True,my_graph=True,full_out=False):
    average_precision = average_precision_score(y_test, y_score)

    print('Average precision-recall score: {0:0.2f}'.format(
        average_precision))



    precision, recall, thresholds = precision_recall_curve(y_test, y_score)
    # print "--- precision_recall_curve ------"
    # print "precision: {}".format(precision)
    # print "recall: {}".format(recall)

    # In matplotlib < 1.5, plt.fill_between does not have a 'step' argument
    if ploting is False:
        if full_out:
            return precision, recall, thresholds,average_precision
        else:
            return average_precision

    if my_graph:
        plt.plot(thresholds, precision[:-1], 'b--', label='precision')
        plt.plot(thresholds, recall[:-1], 'g--', label='recall')
        plt.xlabel('Threshold')
        plt.legend(loc='upper left')
        plt.ylim([0, 1])
        plt.savefig('/home/ise/bug_miner/XGB/fig/{}.png'.format(name_fig))
        plt.close()
    else:
        step_kwargs = ({'step': 'post'}
                   if 'step' in signature(plt.fill_between).parameters
                   else {})
        plt.step(recall, precision, color='b', alpha=0.2,
             where='post')
        plt.fill_between(recall, precision, alpha=0.2, color='b', **step_kwargs)

        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.ylim([0.0, 1.05])
        plt.xlim([0.0, 1.0])
        plt.title('2-class Precision-Recall curve: AP={0:0.2f}'.format(
        average_precision))
    return average_precision


def data_frame_x_y(df, target='hasBug'):
    X_train = df.drop([target], axis=1)
    y_train = df[target].values
    return X_train, y_train


def Random_under_sampling(df_train, col_target='hasBug', target_ratio=0.90):
    # Divide by class
    count_class_0, count_class_1 = df_train[col_target].value_counts()
    df_class_0 = df_train[df_train[col_target] == 0]
    df_class_1 = df_train[df_train[col_target] == 1]
    sampel_num = len(df_class_0) * target_ratio
    df_class_0_under = df_class_0.sample(int(sampel_num))
    df_test_under = pd.concat([df_class_0_under, df_class_1], axis=0)

    print('Random under-sampling:')
    print(df_test_under[col_target].value_counts())
    return df_test_under

def Random_over_sampling(df_train, col_target='hasBug', target_ratio=0.90):
    # Divide by class
    print('Random over-sampling:')
    print ("Before:")
    print (df_train[col_target].value_counts())
    count_class_0, count_class_1 = df_train[col_target].value_counts()
    df_class_0 = df_train[df_train[col_target] == 0]
    df_class_1 = df_train[df_train[col_target] == 1]
    sampel_num = len(df_class_1) * target_ratio
    df_class_1_over = df_class_1.sample(int(sampel_num),replace=True)
    df_test_over = pd.concat([df_class_1_over,df_class_1,df_class_0], axis=0)

    print ("AFTER over-sampling:")
    print(df_test_over[col_target].value_counts())
    return df_test_over


def get_train_test_set(combained_dataframe, col='train'):
    d_DF = {}
    for i in [0, 1, 2, 3]:
        DF_i = combained_dataframe[combained_dataframe[col] == i]
        if len(DF_i) > 0:
            DF_i = DF_i.drop([col], axis=1)
        else:
            DF_i = None
        d_DF[i] = DF_i
    return d_DF


def Nan_finder(train_df):
    '''
    Checking for NaN values and removing constant features in the training data
    '''
    print("Total Train Features with NaN Values = " + str(train_df.columns[train_df.isnull().sum() != 0].size))
    if (train_df.columns[train_df.isnull().sum() != 0].size):
        print("Features with NaN => {}".format(list(train_df.columns[train_df.isnull().sum() != 0])))
        train_df[train_df.columns[train_df.isnull().sum() != 0]].isnull().sum().sort_values(ascending=False)


def one_hot_convertor(nonnumeric_columns, df):
    le = LabelEncoder()
    for feature in nonnumeric_columns:
        df[feature] = le.fit_transform(df[feature])
    return df


def categorical_features_look(df):
    col_all = list(df)
    cols = df.select_dtypes([np.number]).columns
    col_cat = []
    for item in col_all:
        if item in cols:
            continue
        # print item
        # print df[item].value_counts()
        col_cat.append(item)
    if len(col_cat) == 0:
        return None
    return col_cat


def remove_col_same_val(df):
    nunique = df.apply(pd.Series.nunique)
    cols_to_drop = nunique[nunique == 1].index
    if 'hasBug' in cols_to_drop:
        return None, None
    df.drop(cols_to_drop, axis=1, inplace=True)
    return df, cols_to_drop


def converting_target(df):
    idxDict = {'valid': 0, 'bugged': 1}
    df['hasBug'] = df['hasBug'].map(idxDict)
    # print df['hasBug'].value_counts()
    df["hasBug"] = pd.to_numeric(df["hasBug"])
    return df


def helper_get_arrf_fiels(p_path='/home/ise/bug_miner/commons-lang1432698/FP/all_lang', mode='most', validtion=True):
    d_tags = {}
    res = pt.walk_rec(p_path, [], '_{}'.format(mode), False)
    arff_path, pred_1_path = None, None
    for item in res:
        if str(item).endswith('arff_{}'.format(mode)):
            arff_path = item
        elif str(item).endswith('pred_1_{}'.format(mode)):
            pred_1_path = item
    res_minor = pt.walk_rec(pred_1_path, [], '', False, lv=-1)
    res_models = pt.walk_rec(arff_path, [], '.arff')
    for item in res_minor:
        name = '_'.join(str(item).split('/')[-1].split('_')[1:])
        index_sort = str(item).split('/')[-1].split('_')[0]
        files_res = pt.walk_rec(item, [], '')
        d_tags[name] = {'sort_index': index_sort}
        d_tags[name]['model'] = None
        for file_i in files_res:
            if str(file_i).endswith('.csv'):
                d_tags[name]['name'] = file_i
            elif str(file_i).endswith(".arff"):
                d_tags[name]['test'] = file_i
    for item_arff in res_models:
        name = str(item_arff).split('/')[-1].split('.')[0]
        if name in d_tags:
            d_tags[name]['model'] = item_arff
        else:
            d_tags[name] = {'model': item_arff, 'test': None, 'name': None, 'sort_index': None}

    # find validation set:
    keys_list = d_tags.keys()
    keys_list = [[x, int(d_tags[x]['sort_index'])] for x in keys_list]
    keys_list_sorted = sorted(keys_list, key=lambda tup: tup[1])
    print keys_list
    only_key_sort = [x[0] for x in keys_list_sorted]
    for ky in d_tags.keys():
        index = only_key_sort.index(ky)
        if index < len(keys_list_sorted) - 1:
            ky_son = keys_list_sorted[index + 1][0]
            d_tags[ky]['validation_set'] = d_tags[ky_son]['test']
        else:
            d_tags[ky]['validation_set'] = None
    manger(d_tags)

def manger(d_tags):
    '''
    the main function that start to test the Data
    '''
    global name_fig
    l_d=[]
    for ky in d_tags:
        d_param = get_dict_pram('/home/ise/bug_miner/XGB/conf/conf.csv')
        continue_falg=0
        print "**" * 100
        print "TAG:\t{}".format(ky)
        if d_tags[ky]['model'] is None or d_tags[ky]['test'] is None:
            continue
        for ky_p in d_param.keys():
            valid_set = d_tags[ky]['validation_set']
            cur_parm = d_param[ky_p]
            id_conf = cur_parm['ID_conf']
            over_sample_int = cur_parm['over_sample']
            del cur_parm['ID_conf']
            del cur_parm['over_sample']
            name_fig = "P_{}_CONF_{}".format(ky,id_conf)
            train_df, test_df, target_ratio,valid_set = main_func(d_tags[ky]['test'], d_tags[ky]['model'], valid_set,over_sample=over_sample_int)
            if train_df is None:
                break
            d_res,top_ten = my_func_xgb(train_df, test_df, target_ratio,valid_set,param_dict=cur_parm)
            d_res['TAG']=ky
            d_res['Conf'] = id_conf
            if valid_set is None:
                d_res['validation_set'] = False
            else:
                d_res['validation_set'] = True
            top_ten = ["{}={}".format(x[0],x[1]) for x in top_ten]
            d_res['top_ten']=" | ".join(top_ten)
            l_d.append(d_res)
    df=pd.DataFrame(l_d)
    df.to_csv('/home/ise/bug_miner/XGB/res/tmp.csv')


def get_dict_pram(path_p_conf='/home/ise/bug_miner/XGB/conf/conf.csv'):
    df_conf = pd.read_csv(path_p_conf)
    dict_df = df_conf.to_dict('index')
    return dict_df

def eval(model, test_y, test_x, train_x, train_y, classifier=False,sk_learn =True,DM_train=None,DM_test=None):
    if sk_learn is False:
        # Predict training set:
        dtrain_predictions = model.predict(DM_train)

        # Predict Test set:
        test_predictions = model.predict(DM_test)
    else:
        # Predict training set:
        dtrain_predictions = model.predict(train_x)

        # Predict Test set:
        test_predictions = model.predict(test_x)

    # classifier:
    if classifier:
        test_predictions_prob = model.predict_proba(test_x)[:, 1]

    # Print model report:
    # results on Train Set:

    df_y_train = pd.DataFrame(data=train_y)

    df_y_train['pred'] = dtrain_predictions
    print "df_y_train size: ", len(df_y_train)
    # df_y_train['actual'] = train_y
    df_y_train['name'] = df_y_train[target].apply(lambda x: 'valid' if x == 0 else 'bug')
    df_y_train.to_csv('/home/ise/bug_miner/XGB/csv_res/TRAIN/{}_TRAIN.csv'.format(name_fig))
    df_bug_train = df_y_train[df_y_train['name'] == 'bug']
    df_valid_train = df_y_train[df_y_train['name'] == 'valid']

    mse_valid_train = mean_squared_error(df_valid_train[target], df_valid_train['pred'])
    mse_buggy_train = mean_squared_error(df_bug_train[target], df_bug_train['pred'])
    # f1_s = f1_score(df_bug_train[target], df_bug_train['pred'])

    print "TRAIN:\t bug   MSE = {}".format(((mse_buggy_train)))
    print "TRAIN:\t valid MSE = {}".format(((mse_valid_train)))
    # print "TRAIN F1 score = {}".format(f1_s)


    # ROC-AUC

    print "_" * 50

    # results on Test Set:
    df_y = pd.DataFrame(data=test_predictions, columns=['test_predictions'])
    df_y[target] = test_y
    df_y['name'] = df_y[target].apply(lambda x: 'valid' if x == 0 else 'bug')
    df_bug = df_y[df_y['name'] == 'bug']
    df_valid = df_y[df_y['name'] == 'valid']

    df_y.to_csv('/home/ise/bug_miner/XGB/csv_res/TEST/{}_TEST.csv'.format(name_fig))

    mse_valid_test = mean_squared_error(df_valid[target], df_valid['test_predictions'])
    mse_buggy_test = mean_squared_error(df_bug[target], df_bug['test_predictions'])
    # f1_s = f1_score(df_bug[target], df_bug['test_predictions'])

    print "TEST:\t bug   MSE = {}".format(((mse_buggy_test)))
    print "TEST:\t valid MSE = {}".format(((mse_valid_test)))
    # print "TEST F1 score = {}".format(f1_s)

    Avg_PR = reacall_precision(test_y, test_predictions)
    d_res = {'Avg_PR_TEST':Avg_PR,'Train_mse_valid':mse_valid_train,'Train_mse_buggy':mse_buggy_train,
             "TEST_mse_buggy":mse_buggy_test,'TEST_mse_valid':mse_valid_test}
    return d_res

def modelfit(xgb_model, dtrain, predictors, dtest, param, is_sklearn, vaild_set):
    if len(predictors) != len(set(predictors)):
        raise ValueError('feature_names must be unique')
    # Fit the algorithm on the data
    xtrain_data = xgb.DMatrix(np.asmatrix(dtrain[predictors]), label=dtrain[target].values)
    xtest_data = xgb.DMatrix(np.asmatrix(dtest[predictors]), label=dtest[target].values)
    if is_sklearn is False:
        xvlidt = xgb.DMatrix(vaild_set[predictors].values, label=vaild_set[target].values)
        evallist = [(xvlidt, 'eval'), (xtrain_data, 'train')]
        xgb_model = xgb.train(param,xtrain_data,param['early_stopping_rounds'],evals=evallist,feval=pr_auc_metric)
    else:
        bst = xgb_model.fit(dtrain[predictors], dtrain[target], verbose=True ,eval_set=vaild_set, eval_metric=pr_auc_metric)



    if vaild_set is not None and is_sklearn==False:
        print "xgb_model.best_iteration  = {}".format(xgb_model.best_iteration )
        print "xgb_model.best_ntree_limit = {}".format(xgb_model.best_ntree_limit)
        res = eval(xgb_model, dtest[target], dtest[predictors], dtrain[predictors], dtrain[target],
             sk_learn=is_sklearn,DM_test=xtest_data,DM_train=xtrain_data)
    else:
        # eval the model
        res = eval(xgb_model, dtest[target], dtest[predictors], dtrain[predictors], dtrain[target])

    top_ten_f =save_topn_features(xgb_model, topn=30,is_sklearn=is_sklearn)
    return res,top_ten_f

def save_topn_features(alg, fname="XGB_topn_features.txt", topn=-1,is_sklearn=False):
    if is_sklearn is True:
        x_list = get_importance_feature(alg)
    else:
        x_list = get_importance_feature_xgb(alg)
    return x_list

def my_func_xgb(train, test, ratio_target=1, validtion_set=None, sklearn=False,param_dict=None):
    # Choose all predictors except target & IDcols
    mode_sklearn=True
    predictors = [x for x in train.columns if x not in [target]]
    if param_dict is None:
        param_dict_Regressor = {'max_depth': 3, 'silent': 1, 'objective': 'binary:logistic', 'n_estimators': 500,
                            "min_child_weight": 1, 'gamma': 0.001, "subsample": 0.7, "colsample_bytree": 0.6,
                            'nthread': 4,
                            'eval_metric': 'aucpr', "scale_pos_weight": ratio_target, "early_stopping_rounds": 20}
    else:
        if param_dict['scale_pos_weight']  == 0 :
            param_dict['scale_pos_weight'] = ratio_target

        param_dict_Regressor = param_dict

    eval_set_tuple = None
    if validtion_set is not None and sklearn is True:
        eval_set_tuple = [(train[predictors],train[target]),(validtion_set[predictors], validtion_set[target])]
    elif validtion_set is not None and sklearn is False:
        eval_set_tuple = validtion_set
        mode_sklearn = False

    xgb1 = xgb.XGBRegressor(**param_dict_Regressor)

    d_res,top_ten = modelfit(xgb1, train, predictors, test, param=param_dict_Regressor, is_sklearn = mode_sklearn, vaild_set=eval_set_tuple)

    return d_res,top_ten



def get_importance_feature_xgb(booster,importance_type='weight',max_num_features=10):
    '''
        * 'weight': the number of times a feature is used to split the data across all trees.
        * 'gain': the average gain across all splits the feature is used in.
        * 'cover': the average coverage across all splits the feature is used in.
        * 'total_gain': the total gain across all splits the feature is used in.
        * 'total_cover': the total coverage across all splits the feature is used in.
    '''
    importance= booster.get_score(importance_type='weight')
    tuples = [(k, importance[k]) for k in importance]
    if max_num_features is not None:
        tuples = sorted(tuples, key=lambda x: x[1])[-max_num_features:]
    else:
        tuples = sorted(tuples, key=lambda x: x[1])
    return tuples

def get_importance_feature(booster,importance_type='weight',max_num_features=10):

    importance = booster.get_booster().get_score(importance_type=importance_type)

    tuples = [(k, importance[k]) for k in importance]
    if max_num_features is not None:
        tuples = sorted(tuples, key=lambda x: x[1])[-max_num_features:]
    else:
        tuples = sorted(tuples, key=lambda x: x[1])
    labels, values = zip(*tuples)

    return tuples

def pr_auc_metric(y_predicted, y_true):
    return 'prc_auc', -average_precision_score(y_true.get_label(), y_predicted)


def eval_random_forest(dir_p,name_file='testing_Tree'):
    res = pt.walk_rec(dir_p, [], name_file, True)
    res = [x for x in res if str(x).endswith('.csv')]
    df_l=[]
    for itm in res:
        tag_name = str(itm).split('/')[-2]
        print(tag_name )
        print "tag_name:\t{}".format(tag_name)
        df = pd.read_csv(itm)

        df['true'] = df['actual'].apply(lambda x: 1 if  str(x) == '1:bugged' else 0 )
        if len(df['true'].value_counts()) == 1:
            continue

        df['pred'] = df['prediction'].apply(lambda x : float(1)-float(x))

        y_test = df['true'].values
        y_pred = df['pred'].values

        precision, recall, thresholds, Avg_PR = reacall_precision(y_test, y_pred,ploting=False,full_out=True)
        area = auc(recall, precision)
        roc = roc_auc_score(y_test,y_pred)


        df_bug = df[df['true'] == 1]
        df_valid = df[df['pred'] == 0]
        if len(df_bug )==0:
            continue
        mse_valid_test = mean_squared_error(df_valid['true'], df_valid['pred'])
        mse_buggy_test = mean_squared_error(df_bug['true'], df_bug['pred'])

        d_k = {}
        for k in [10, 20, 30, 100]:
            k_recall, k_precsion = metric_precsion_at_k(y_test, y_pred, k=k)
            d_k['k_{}_recall'.format(k)] = k_recall
            d_k['k_{}_precsion'.format(k)] = k_precsion

        d_out={'tag': tag_name, 'ROC': roc, 'conf': '', 'MSE_Test_Bug': mse_buggy_test,
         'MSE_Test_Valid': mse_valid_test,
         'area-PRC (buggy)': area, 'Average precision-recall score': Avg_PR}

        for d_k_key in d_k.keys():
            d_out[d_k_key]=d_k[d_k_key]

        print "TEST:\t bug   MSE = {}".format(((mse_buggy_test)))
        print "TEST:\t valid MSE = {}".format(((mse_valid_test)))
        print Avg_PR
        df_l.append(d_out)
    df_res = pd.DataFrame(df_l)
    df_res.to_csv('{}/RF_eval.csv'.format(dir_p))


def eval_xgb_test_dir(dir_p,name_file='FP_'):
    res = pt.walk_rec(dir_p, [], name_file, True)
    res = [x for x in res if str(x).endswith('.csv')]
    df_l = []
    for itm in res:
        tag_name = '_'.join(str(itm).split('/')[-1].split('_')[-6:-3])
        conf_num=str(itm).split('/')[-1].split('_')[-2]

        print "tag_name:\t{}".format(tag_name)
        df = pd.read_csv(itm)

        y_pred = df['test_predictions'].values
        y_test = df['hasBug'].values


        precision, recall, thresholds, Avg_PR = reacall_precision(y_test, y_pred,ploting=False,full_out=True)

        area = auc(recall, precision)
        roc = roc_auc_score(y_test,y_pred)

        df_bug = df[df['hasBug'] == 1]
        df_valid = df[df['hasBug'] == 0]
        if len(df_bug) == 0:
            continue
        mse_valid_test = mean_squared_error(df_valid['hasBug'], df_valid['test_predictions'])
        mse_buggy_test = mean_squared_error(df_bug['hasBug'], df_bug['test_predictions'])


        #precsion_buggy = precision_score(df_bug['hasBug'], df_bug['test_predictions'])
        #recall_buggy = recall_score(df_bug['hasBug'], df_bug['test_predictions'])
#        F1_buggy = f1_score(df_bug['hasBug'], df_bug['test_predictions'])
        d_k={}
        for k in [10,20,30,100]:
            k_recall,k_precsion = metric_precsion_at_k(y_test,y_pred,k=k)
            d_k['k_{}_recall'.format(k)]=k_recall
            d_k['k_{}_precsion'.format(k)] = k_precsion

        print 'size buggy', len(df_bug)
        print 'size vaild', len(df_valid)
        print 'precntage vaild', float(len(df_valid))/float(len(df_bug)+len(df_valid)) *100.0
        print 'precntage buggy', float(len(df_bug))/float(len(df_bug)+len(df_valid))*100.0

        d_out = {'tag': tag_name, 'ROC': roc, 'conf': conf_num, 'MSE_Test_Bug': mse_buggy_test,'num_buggy':len(df_bug),'num_vaild':len(df_valid),'num_all':len(df_valid)+len(df_bug),
         'MSE_Test_Valid': mse_valid_test, #'F1_score':F1_buggy,'precsion_buggy':precsion_buggy,'recall_buggy':recall_buggy,
         'area-PRC (buggy)': area, 'Average precision-recall score': Avg_PR}

        for d_k_key in d_k.keys():
            d_out[d_k_key]=d_k[d_k_key]


        print "TEST:\t bug   MSE = {}".format(((mse_buggy_test)))
        print "TEST:\t valid MSE = {}".format(((mse_valid_test)))
        print Avg_PR
        df_l.append(d_out)
    df_res = pd.DataFrame(df_l)
    dir_p = '/'.join(str(dir_p).split('/')[:-1])
    df_res.to_csv('{}/eval_res.csv'.format(dir_p))


def metric_precsion_at_k(y_true,y_pred,k=20):
    col_true = pd.Series(y_true, name='true')
    col_pred= pd.Series(y_pred, name='pred')
    df = pd.concat([col_pred, col_true], axis=1)
    all_bugs =  df['true'].sum()
    df_cut = df.nlargest(k, 'pred')
    k_bug = df_cut['true'].sum()
    return float(k_bug)/float(all_bugs),float(k_bug)/float(k)

if __name__ == "__main__":
    #eval_random_forest('/home/ise/bug_miner/commons-math/FP/Random_forest')
    #eval_xgb_test_dir('/home/ise/bug_miner/commons-lang/FP/best_FP/best')
    #eval_xgb_test_dir('/home/ise/bug_miner/commons-math/FP/best_FP/best')
    eval_xgb_test_dir('/home/ise/bug_miner/commons-net/FP/best_FP/best')
    exit()
    helper_get_arrf_fiels(p_path='/home/ise/bug_miner/commons-imaging/FP/all_imaging')
    print "Done !!"
