import os, re, sys


class walker:
    def __init__(self, root):
        self._root = root

    def walk(self, rec="", file_t=True, lv=-1, full=True):
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


def walk(root, rec="", file_t=True, lv=-1, full=True):
    size = 0
    ctr = 0
    class_list = []
    if lv == -1:
        lv = float('inf')
    for path, subdirs, files in os.walk(root):
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


def walk_rec(root, list_res, rec="", file_t=True, lv=-800, full=True):
    if root[-1]=='/':
        root=root[:-1]
    size = 0
    ctr = 0
    class_list = list_res
    if lv == 0:
        return list_res
    lv += 1
    for path, subdirs, files in os.walk(root):
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
        for d_dir in subdirs:
            walk_rec("{}/{}".format(path, d_dir), class_list, rec, file_t, lv, full)
        break
    return class_list


def fix_bug_tests(root):
    all_test = walk(root, "ESTest.java")
    for cut in all_test:
        with open(cut, 'r') as myfile:
            data = myfile.read().replace('separateClassLoader = true', 'separateClassLoader = false')
        text_file = open(cut, "w")
        text_file.write(data)
        text_file.close()
    print "done !"


def path_to_package(first, path, cut):
    arr = []
    arr_newer=[]
    dim = 0
    while (path.find(first, dim) != -1):
        arr.append(path.find(first, dim))
        dim = path.find(first, dim) + len(first)
    if len(arr) != 1:
        for candidt in arr:
            if path[candidt-1]=='/' and path[candidt+len(first)] =='/':
                arr_newer.append(candidt)
                continue
        arr = arr_newer
        if len(arr) == 0:
            return None
        if len(arr) != 1:
            raise Exception('confilcet in path to package :', path, "with the key:", first)
    packa = path[arr[0]:]
    packa = str(packa).replace("/", '.')
    return packa[:cut]


def main(sys):
    if len(sys.argv) > 1:
        root = sys.argv[1]
        fix_bug_tests(root)


def mkdir_system(path_root, name, is_del=True):
    if path_root is None:
        raise Exception("[Error] passing a None path --> {}".format(path_root))
    if path_root[-1] != '/':
        path_root = path_root + '/'
    if os.path.isdir("{}{}".format(path_root, name)):
        if is_del:
            os.system('rm -r {}{}'.format(path_root, name))
        else:
            #print "{}{} is already exist".format(path_root, name)
            return '{}{}'.format(path_root, name)
    print '[OS] mkdir {}{}'.format(path_root, name)
    os.system('mkdir {}{}'.format(path_root, name))
    return '{}{}'.format(path_root, name)


def lcs(X, Y):
    # find the length of the strings
    m = len(X)
    n = len(Y)

    # declaring the array for storing the dp values
    L = [[None] * (n + 1) for i in xrange(m + 1)]

    """Following steps build L[m+1][n+1] in bottom up fashion
    Note: L[i][j] contains length of LCS of X[0..i-1]
    and Y[0..j-1]"""
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 or j == 0:
                L[i][j] = 0
            elif X[i - 1] == Y[j - 1]:
                L[i][j] = L[i - 1][j - 1] + 1
            else:
                L[i][j] = max(L[i - 1][j], L[i][j - 1])

    # L[m][n] contains the length of LCS of X[0..n-1] & Y[0..m-1]
    return L[m][n]


# end of function lcs

if __name__ == "__main__":
    print "--- util script ----"
    #main(sys)