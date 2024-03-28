#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-
# Author: ver007
# Description: rule.py.py python2.7
# License: Apache Licence 
# CreateTime: 2018/6/26 : 下午4:03
import re


class Rule(object):
    """
    规则对象
    """

    name = None
    regex = None

    def __init__(self, rule):
        name = rule.get("name")
        rule = rule.get("rule")
        regex = []
        for i in rule:
            _rule = i.get("rule")
            _type = i.get("type")

            if _type in ["hex", "str"]:
                _rule = re.compile(_rule.replace(" ", ""))
            elif _type == "header":
                [columns, r] = _rule.split("|")
                _rule = (columns, re.compile(r))
            regex.append(_rule)

        self.name = name
        self.regex = regex

    def getRegex(self):
        """
        获取规则
        :return:
        """
        return self.regex

    def getName(self):
        """
        获取规则名称
        :return:
        """
        return self.name

    def setRegex(self, regex):
        """
        设置规则
        :param regex:
        """
        self.regex = regex

    def setName(self, name):
        """
        设置规则名称
        :param name:
        """
        self.name = name
