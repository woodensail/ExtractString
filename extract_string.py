import json
import zipfile
import os
import re
import configparser
from urllib import request, parse


def parse_class(t, cn=None, array=False):
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
            count += 1
        else:
            index += 5
        count += 1

    if cn:
        return1 = [pool[i] for i in out]
        return2 = parse_class(cn, array=True)
        return {return1[i]: return2[i] for i in range(len(return1))}
    elif array:
        return [pool[i] for i in out]
    else:
        return {pool[i]: pool[i] for i in out}
        # return [{'str': pool[i], 'index': indexlist[i], 'poolindex': i} for i in out]


def replace(t, data_array):
    size = (t[8] << 8) + t[9]
    index = 10
    count = 1
    utf = []
    indexlist = [0] * size
    pool = [0] * size
    while count < size:
        if 8 == t[index]:
            utf += [(t[index + 1] << 8) + t[index + 2]]
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
            count += 1
        else:
            index += 5
        count += 1

    data = {}
    data_array.reverse()
    for i in data_array:
        data.update(i)
    out = b''
    last_index = 0
    utf.sort()
    for i in utf:
        if data[pool[i]]:
            c_index = indexlist[i]
            code = data[pool[i]].encode('UTF-8')
            n_lengtn = len(code)
            out += t[last_index:c_index + 1:]
            last_index = c_index + 3 + (t[c_index + 1] << 8) + t[c_index + 2]
            _len = bytearray(2)
            _len[0] = n_lengtn // 256
            _len[1] = n_lengtn % 256
            out += bytes(_len)
            out += code
    out += t[last_index::]

    return out


def read(item):
    file = item.path_jar
    z = zipfile.ZipFile(file, 'r')
    z_c = None
    if os.path.exists(file + '.cn'):
        z_c = zipfile.ZipFile(file + '.cn', 'r')
    myfilelist = z.namelist()
    out = {}
    for name in myfilelist:
        if 0 < name.find('.class'):
            if z_c:
                parsed = parse_class(z.read(name), cn=z_c.read(name))
            else:
                parsed = parse_class(z.read(name))
            if parsed:
                out[name] = parsed
    file = check_file(item.path_txt)
    # conf = configparser.ConfigParser()
    # for i in sorted(out.keys()):
    # conf.add_section(i)
    # for j in out[i]:
    # print(j.get('poolindex'),j.get('str'))
    # conf.set(i, str(j.get('poolindex')), re.sub(r'%',r'%%',j.get('str')))
    # trans([j for i in out for j in out[i]])
    with open(file, 'w', encoding='UTF-8') as f:
        f.write(json.dumps(out, indent=4, sort_keys=True, ensure_ascii=False))
    input('文本信息提取完毕，修改该文件后重新写回原jar包即可。')
    z.close()


def write(item):
    file = item.path_jar
    txt_file = item.path_txt
    z = zipfile.ZipFile(file, 'r')
    all_file = item.path_all
    zz = zipfile.ZipFile(check_file(file + r'.new'), 'w')
    txt = open(txt_file, 'r', encoding='UTF-8')
    all_data = {}
    if all_file and os.path.exists(all_file):
        all_data = json.load(open(all_file, 'r', encoding='UTF-8'))
    myfilelist = z.namelist()
    txt_data = json.load(txt)
    regex = {re.compile(i): all_data[i] for i in all_data}
    for name in myfilelist:
        _before = z.read(name)
        if txt_data.get(name):
            _before = replace(_before, [txt_data.get(name)] + [regex[i] for i in regex if i.findall(name)])
        zz.writestr(name, _before)
    z.close()
    zz.close()
    txt.close()
    input('文本信息写回完毕。')


def update(item):
    pass
    

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


def read_cfg():
    conf = configparser.ConfigParser()
    if not os.path.exists("config.ini"):
        create_cfg()
    conf.read("config.ini", encoding='Utf-8')
    return Item({i[0]: i[1] for i in conf.items('Options')})


def change_cfg(msg, opt):
    value = input(msg)
    print(value)
    conf = configparser.ConfigParser()
    conf.read("config.ini", encoding='Utf-8')
    conf.set('Options', opt, value)
    with open("config.ini", 'w', encoding='UTF-8') as f:
        conf.write(f)


def create_cfg():
    conf = configparser.ConfigParser()
    conf.add_section('Options')
    conf.set('Options', 'path_jar', 'temp.jar')
    conf.set('Options', 'path_txt', 'str.txt')
    conf.set('Options', 'path_all', 'all.txt')
    with open("config.ini", 'w', encoding='UTF-8') as f:
        conf.write(f)


def trans(data):
    base = 'http://fanyi.baidu.com/v2transapi?from=en&to=zh&transtype=trans&simple_means_flag=3'
    base = 'http://openapi.baidu.com/public/2.0/bmt/translate'
    page = request.urlopen(base, parse.urlencode(
        {'client_id': 'GdaG95GYEEuCsR1PErPKD5s2', 'q': '\n'.join(data[:10:]), 'from': 'en', 'to': 'zh',
         'transtype': 'trans',
         'simple_means_flag': '3'}).encode(encoding='UTF8')).read().decode()
    # cn = re.findall('"dst":"([^"]*)"', page)
    print(json.loads(page))


class Item:
    def __init__(self, opt_dict):
        self.path_jar = opt_dict.get('path_jar')
        self.path_txt = opt_dict.get('path_txt')
        self.path_all = opt_dict.get('path_all')


if __name__ == '__main__':
    while 1:
        os.system('cls')
        _item = read_cfg()
        in_str = input('''请输入指令
1:读jar包
2:写回jar包
3:更改jar包地址，目前为：%s
4:更改txt文件地址，目前为：%s
5:更改all.txt文件地址，目前为：%s
''' % (_item.path_jar, _item.path_txt, _item.path_all))
        if '1' == in_str:
            read(_item)
        elif '2' == in_str:
            write(_item)
        elif '3' == in_str:
            change_cfg('请输入jar包地址:\n', 'path_jar')
        elif '4' == in_str:
            change_cfg('请输入txt文件地址:\n', 'path_txt')
        elif '5' == in_str:
            change_cfg('请输入all.txt文件地址:\n', 'path_all')
        else:
            break