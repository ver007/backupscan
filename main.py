#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-
# Author: ver007
# Description: main.py python2.7
# License: Apache Licence 
# CreateTime: 2018/6/26 : 下午3:24

from config.config import conf
from core.scanwork import ScanBackup
from core.command import command
from core.AnsiColor import Print


def main():
    """
    主启动类
    :return:
    """
    option = command()
    for target_info in option.get("targets"):
        id = target_info.get("id")
        target = target_info.get("target")
        scanBackup = ScanBackup(target.strip(), option, conf)
        Print("TaskID <" + str(id) + "> TaskUrl <" + target.strip() + "> WorkNum <" + str(len(scanBackup.paths)) + ">")
        scanBackup.start()
        if scanBackup.status: break


if __name__ == '__main__':
    main()
