import os,re,sys

class walker:
    def __init__(self, root):
        self._root = root

    def walk(self,rec="", file_t=True, lv=-1, full=True):
        size = 0
        ctr = 0
        class_list = []
        if lv == -1:
            lv = float('inf')
        for path, subdirs, files in os.walk(self._root):
            if lv < ctr:
                break
            ctr += 1
            if file_t:
                for name in files:
                    tmp = re.compile(rec).search(name)
                    if tmp == None:
                        continue
                    size += 1
                    if full:
                        class_list.append(os.path.join(path, name))
                    else:
                        class_list.append(str(name))
            else:
                for name in subdirs:
                    tmp = re.compile(rec).search(name)
                    if tmp == None:
                        continue
                    size += 1
                    if full:
                        class_list.append(os.path.join(path, name))
                    else:
                        class_list.append(str(name))
        return class_list


def walk(root,rec="",file_t=True,lv=-1,full=True) :
    size=0
    ctr=0
    class_list = []
    if lv == -1:
        lv=float('inf')
    for path, subdirs, files in os.walk(root):
        if lv < ctr:
            break
        ctr+=1
        if file_t :
            for name in files:
                tmp = re.compile(rec).search(name)
                if tmp == None:
                    continue
                size += 1
                if full:
                    class_list.append(os.path.join(path, name))
                else:
                    class_list.append(str(name))
        else:
            for name in subdirs:
                tmp = re.compile(rec).search(name)
                if tmp == None:
                    continue
                size += 1
                if full:
                    class_list.append(os.path.join(path, name))
                else:
                    class_list.append(str(name))
    return class_list


def fix_bug_tests(root):
    all_test= walk(root,"ESTest.java")
    for cut in all_test:
        with open(cut, 'r') as myfile:
            data = myfile.read().replace('separateClassLoader = true', 'separateClassLoader = false')
        text_file = open(cut, "w")
        text_file.write(data)
        text_file.close()
    print "done !"


def main(sys):
    if len(sys.argv) > 1 :
        root = sys.argv[1]
        fix_bug_tests(root)


if __name__ == "__main__":
    main(sys)
