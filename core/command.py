#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-
# Author: ver007
# Description: command.py python2.7
# License: Apache Licence 
# CreateTime: 2018/6/27 : 下午5:18
import sys
import random
import argparse

from AnsiColor import ansi


def command():
    """
    :return:
    """

    parser = argparse.ArgumentParser()
    VER_INT = "1.0.0"
    parser.add_argument('-t', action='store', dest='target', help='target: "/target.txt,192.168.1.1,www.site.com"')
    parser.add_argument('-d', action='store', dest='delay', default=3, help='speed')
    parser.add_argument('-thread', action='store', dest='thread', default=10, help='scan thread num')
    parser.add_argument('-timeout', action='store', dest='timeout', default=3, help='http timeout')
    parser.add_argument('-version', action='version', version='%(prog)s ' + VER_INT)

    cmdline = parser.parse_args()

    if not cmdline.target:
        parser.print_help()
        exit()

    # 单目标
    target = cmdline.target
    target = target[7:] if target.startswith("http://") else target
    target = target[8:] if target.startswith("https://") else target
    targets = []

    # 文件
    if target.find('.txt') > -1 and target.find('://') == -1:
        try:
            with open(target) as filex:
                for url in filex.readlines():
                    url = url[7:] if url.startswith("http://") else url
                    url = url[8:] if url.startswith("https://") else url
                    targets.append({"id": random.randrange(1111, 9999, 4), "target": url.replace('\n', '')})
        except IOError as error_info:
            print ansi.error("文件无法打开: '%s'\n" % target)
            print parser.print_help()
            sys.exit()

    # 逗号相隔
    elif target.find(',') != -1:
        targetL = target.split(",")
        for url in targetL:
            targets.append({"id": random.randrange(1111, 9999, 4), "target": url})
    elif len(target) >= 5:
        targets.append({"id": random.randrange(1111, 9999, 4), "target": target})
    else:
        print parser.print_help()
        sys.exit()

    delay = cmdline.delay
    thread_num = cmdline.thread
    timeout = int(cmdline.timeout)

    option = {"thread": thread_num, "delay": delay, "timeout": timeout, "targets": targets}

    return option
