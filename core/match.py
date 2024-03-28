#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-
# Author: ver007
# Description: match.py python2.7
# License: Apache Licence 
# CreateTime: 2018/6/26 : 下午3:51
import re

from bean.rule import Rule


class MatchHandel(object):
    """
    文件头字节匹配
    """

    rules = None

    def __init__(self, rules):
        self.rules = []
        for rule_str in rules:
            self.rules.append(Rule(rule_str))

    def match(self, header, body):
        """
        HTTP头匹配
        :param header: HTTP 头
        :param body: HTTP 主体信息
        :return:
        """
        if header.get("Content-Length") is None or body is None: return None
        for rule in self.rules:
            if self._march(rule, header, body):
                return rule.getName()
        return None

    def _march(self, rule, header, body):
        """
        匹配实现
        :param rule: 用于匹配的规则
        :param header: HTTP 头类型
        :param body: HTTP 主体内容
        :return:
        """
        try:
            for r in rule.getRegex():
                if isinstance(r, tuple):
                    columns, regex = r
                    if regex.search(header.get(columns) or ""): return True
                else:
                    if r.search(body.encode("hex")): return True
        except Exception, e:
            pass
        return False
