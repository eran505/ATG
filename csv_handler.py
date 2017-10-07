


import sys,os
import  pit_render_test

def copy_pacakge(dir,out):
    if os.path.exists(dir+"/commons-math3-3.5-src/target/pit-reports/"):
        os.system("cp -r "+dir+"/commons-math3-3.5-src/target/pit-reports/"+" "+out)

def copy_mutation(dir,out):
    walker=pit_render_test.walker(dir)
    list_dir = walker.walk("ALL",False,-1)
    os.system("cp "+dir+"/FP_budget_time.csv "+out)
    for dir in list_dir :
        name_dir = str(dir).split("/")[-1]
        if os.path.exists(out+name_dir):
            os.system("rm -r " +out+name_dir)
        os.makedirs(out+name_dir)
        copy_pacakge(dir,out+name_dir+"/")


def main_csv(path_csv) :
    if os.path.exists(path_csv+"data_mutation"):
        os.system("rm -r "+path_csv+"data_mutation")
    os.makedirs(path_csv+"data_mutation")
    walker=pit_render_test.walker(path_csv)
    list_dir = walker.walk("09",False,0)
    out = path_csv +"data_mutation/"
    for dir in list_dir :
        name_dir = str(dir).split("/")[-1]
        if os.path.exists(out+name_dir):
            os.system("rm -r " +out+name_dir)
        os.makedirs(out+name_dir)
        copy_mutation(dir,out+name_dir+"/")

    print "done !"
def main_info(path_p):
    all
    with open(path_p) as f:
        content = f.readlines()
        a = [x for x in content if x != '\n']
        for x in a:

            arr = x.split(" ")
            arr=arr[:2]
            print arr


def init_script():
    #sys.argv = ["p","info","/home/eran/Desktop/testing/new_test/info.txt"]
    if len(sys.argv) == 3 :
        mode = sys.argv[1]
        if mode == 'info':
            main_info(sys.argv[2])
        elif mode == "csv":
            main_csv(sys.argv[2])
        else :
            print('error no mode ')
    else:
        print 'Usage : -csv [path] '

if __name__ == "__main__":
    init_script()





'''''''''''
list = get_all_csv(str_path)
list.sort(key=lambda x: x.size, reverse=True)
res=join_data_frame(list)
res.to_csv("/home/eran/Desktop/evo_result/res.csv", sep='\t', encoding='utf-8')
'''''