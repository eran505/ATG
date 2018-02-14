import os,sys
import pit_render_test
import fail_cleaner

def init_main(root):
    arr_sys = ['',root]
    # clean the header in the TEST file for PIT True -> False
    sys.argv = arr_sys
    pit_render_test.main(sys)
    #clean all failing test for PIT
    #fail_cleaner.get_all_project(root)
    #fail_cleaner.get_all_project(root)

    #start to make mutation testing
    comand = 'cp /home/ise/eran/repo/ATG/bash_scripts/fixer.sh {}'.format(root)
    os.system(comand)
    os.chdir(root)
    os.system("bash fixer.sh")




if __name__ == "__main__":
    arr = sys.argv
    arr = ['','/home/ise/eran/exp_littile']
    if len(arr) == 2:
        init_main(arr[1])