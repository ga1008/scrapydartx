#!/usr/bin/env python
import re
import os
import sys

from twisted.scripts.twistd import run
from os.path import join, dirname
from sys import argv
import scrapydartx


def main():
    _update_config_file()
    argv[1:1] = ['-n', '-y', join(dirname(scrapydartx.__file__), 'txapp.py')]
    run()


def _update_config_file():
    base_path = os.path.realpath(scrapydartx.__file__).replace('__init__.py', 'default_scrapyd.conf')
    f = open(base_path, 'r')
    default_conf = f.readlines()
    f.close()
    default_conf_str = ''.join(default_conf)
    show_lis = list()
    show_lis.append(_re_find_from_conf(default_conf, '^Terminator.+'))
    show_lis.append(_re_find_from_conf(default_conf, '^database_type.+'))
    show_lis.append(_re_find_from_conf(default_conf, '^mysql_host.+'))
    show_lis.append(_re_find_from_conf(default_conf, '^mysql_port.+'))
    show_lis.append(_re_find_from_conf(default_conf, '^mysql_user.+'))
    show_lis.append(_re_find_from_conf(default_conf, '^mysql_password.+'))
    show_lis.append(_re_find_from_conf(default_conf, '^mysql_db.+'))
    show_lis.append(_re_find_from_conf(default_conf, '^clear_up_database_when_start.+'))
    print('The default settings are as follows: ')
    for i, st in enumerate(show_lis):
        print(i, st)
    print('Select the serial number of the option you want to change, separate with ","')
    print('example: 1,2,4')
    print('what it means? https://shimo.im/docs/9VZttqLE0xgbnxVg/read')
    update_nums = input('(let it empty to set as default): ')
    if update_nums:
        try:
            num_lis = [int(x.strip(' ')) for x in update_nums.split(',')]
        except ValueError:
            print('wrong input! ')
            sys.exit(0)
        for num in num_lis:
            option = show_lis[num].split(':')[0].strip(' ')
            set_op = input('{}: '.format(option))
            default_conf_str = re.sub(r'(?P<asd>\s{} += +).+\n'.format(option), r'\g<asd>{}\n'.format(set_op), default_conf_str)
        print('set compete, saving to default_scrapyd.conf ...')
        os.remove(base_path)
        wf = open(base_path, 'w')
        wf.write(default_conf_str)
        wf.flush()
        wf.close()


def _re_find_from_conf(lis, re_str):
    temp = [x for x in lis if re.findall(re_str, x)][0].strip('\n') if [x for x in lis if re.findall(re_str, x)] else None
    temp = temp.replace('=', ':') if temp is not None else None
    return temp


if __name__ == '__main__':
    main()
