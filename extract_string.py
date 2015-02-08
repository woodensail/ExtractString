import json
import zipfile
import os
import re


def parse(t):
    size = (t[8] << 8) + t[9]
    index = 10
    count = 1
    out = []
    pool = [0] * size
    indexlist = [0] * size
    while count < size:
        if 8 == t[index]:
            out += [(t[index + 1] << 8) + t[index + 2]]
            index += 3
        elif 1 == t[index]:
            length = (t[index + 1] << 8) + t[index + 2]
            pool[count] = t[index + 3:index + 3 + length:].decode('UTF-8')
            indexlist[count] = index
            index += length + 3
        elif 7 == t[index]:
            index += 3
        elif 5 == t[index] or 6 == t[index]:
            index += 9
        else:
            index += 5
        count += 1
    return [{'str': pool[i], 'poolindex': i} for i in out]
    # return [{'str': pool[i], 'index': indexlist[i], 'poolindex': i} for i in out]


def replace(t, data):
    data = {i.get('poolindex'): i for i in data}
    size = (t[8] << 8) + t[9]
    index = 10
    count = 1
    last_index = 0
    out = b''
    while count < size:
        if 8 == t[index]:
            index += 3
        elif 1 == t[index]:
            current = data.get(count)
            if current:
                code = current.get('str').encode('UTF-8')
                n_lengtn = len(code)
                out += t[last_index:index + 1:]
                last_index = index + 3 + (t[index + 1] << 8) + t[index + 2]
                _len = bytearray(2)
                _len[0] = n_lengtn // 256
                _len[1] = n_lengtn % 256
                out += bytes(_len)
                out += code
            length = (t[index + 1] << 8) + t[index + 2]
            index += length + 3
        elif 7 == t[index]:
            index += 3
        elif 5 == t[index] or 6 == t[index]:
            index += 9
        else:
            index += 5
        count += 1
    out += t[last_index::]
    return out


def read():
    file = input('请输入汉化文件完整路径，如(E:\\test\\jar.txt)。\n无异常处理，乱输后果自负。\n')
    z = zipfile.ZipFile(file, 'r')
    myfilelist = z.namelist()
    out = {}
    for name in myfilelist:
        if 0 < name.find('.class'):
            parsed = parse(z.read(name))
            if parsed:
                out[name] = parsed
    file = input('请输入汉化文件完整路径，如(E:\\test\\jar.txt)。\n无异常处理，乱输后果自负。\n')
    check_file(file)
    with open(file, 'w', encoding='UTF-8') as f:
        f.write(json.dumps(out, indent=4, sort_keys=True, ensure_ascii=False))
    print('文本信息提取完毕，修改该文件后重新写回原jar包即可。')
    z.close()


def write():
    file = input('请输入jar包完整路径，如(E:\\test\\starfarer_obf.jar)。\n无异常处理，乱输后果自负。\n')
    txt_file = input('请输入汉化文件完整路径，如(E:\\test\\chinese.txt)。\n无异常处理，乱输后果自负。\n')
    z = zipfile.ZipFile(file, 'r')
    zz = zipfile.ZipFile(check_file(file + r'.new'), 'w')
    chinese = open(txt_file, 'r', encoding='UTF-8')
    myfilelist = z.namelist()
    all = json.load(chinese)
    # for name in all:
    for name in myfilelist:
        _before = z.read(name)
        if all.get(name):
            _before = replace(_before, all.get(name))
        zz.writestr(name, _before)
    z.close()
    zz.close()
    chinese.close()
    print('文本信息写回完毕。')


def check_file(file_name):
    file_dir = re.findall(r'.+(?=\\[^\\]*$)', file_name)[0]
    i = 0
    bk = file_name
    while os.path.exists(bk):
        i += 1
        bk = file_name + '.' + str(i) + '.bk'
    if i:
        os.rename(file_name, bk)
    elif not os.path.exists(file_dir):
        os.makedirs(file_dir)
    return file_name


if __name__ == '__main__':
    in_str = input('请输入指令\n1:读jar包\n2:写回jar包\n')
    if '1' == in_str:
        read()
    elif '2' == in_str:
        write()
    input('按任意键退出')