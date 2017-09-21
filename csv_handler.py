



import  pit_render_test

def main_csv(path_csv) :
    print "strating .."
    walker=pit_render_test.walker(path_csv)
    list_mut = walker.walk("mutations.csv")
    list_fp = walker.walk("FP_budget_time.csv")


if len(sys.argv) == 2 :
    path_csv = sys.argv[1]
    main_csv(path_csv)
else:
    print 'Usage :\n-p [path] '
    print pd




'''''''''''
list = get_all_csv(str_path)
list.sort(key=lambda x: x.size, reverse=True)
res=join_data_frame(list)
res.to_csv("/home/eran/Desktop/evo_result/res.csv", sep='\t', encoding='utf-8')
'''''