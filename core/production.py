#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-
# Author: ver007
# Description: production.py python2.7
# License: Apache Licence
# CreateTime: 2018/6/26 : 下午11:16
import time

from config.config import conf


class Production(object):
    """
    任务生产
    """

    def __init__(self, target, config):
        self.target = target
        self.re_rules = set()
        self.rules = config.get("match")
        self.suffix = config.get("suffix")
        self.host_suffix = config.get("host_suffix")
        self.path_handle()

    def path_handle(self):
        """
        字典生成器
        """
        for key in self.rules:
            rule = self.rules.get(key)
            if key == "time":
                for f in rule:
                    if "format" in f:
                        for_mat = f.get("format")
                        for_mat = for_mat.replace("yyyy", "%Y").replace("mm", "%m").replace("dd", "%d")
                        for i in range(1, 7):
                            self.re_rules.add(time.strftime(for_mat, time.localtime(time.time() - 86400 * i)))
            if key == "host":
                for r in rule:
                    _target = ""
                    if "replace" in r:
                        _rule = r.get("replace")
                        _tmp = _rule.split("|")
                        _target = self.target.replace(_tmp[0], _tmp[1] if _tmp[1] != "*" else " ")
                    elif "delete" in r:
                        _rule = r.get("delete")
                        _tmp = _rule.split("|")
                        _target = self.delete(self.target, _tmp)
                    self.re_rules.add(_target)

        rule = self.rules.get("adding")
        target = list(self.re_rules)
        for r in rule:
            _target = ""
            for t in target:
                _rule = r.get("adding")
                _tmp = _rule.split("|")
                if _tmp[0] != "": _target = _tmp[0] + t
                if _tmp[1] != "": _target = t + _tmp[1]
                self.re_rules.add(_target)

        rule = self.rules.get("common")
        for r in rule:
            self.re_rules.add(r)
        rule = self.rules.get("range")
        for r in rule:
            [s, e] = r.split("|")
            if s == "1": [self.re_rules.add(str(i)) for i in range(int(s), int(e) + 1)]
            if s == "a": [self.re_rules.add(chr(i + ord('A')).lower()) for i in xrange(26)]

        self.suffix_handle(self.re_rules)

        rule = self.rules.get("alone")
        for r in rule:
            self.re_rules.add(r)

    def suffix_handle(self, rules):
        """
        字典后缀处理
        :param rules:
        """
        re_rules = set()
        _path = list(rules)
        for _target in _path:
            if _target == "": continue
            for suffix in self.suffix:
                re_rules.add(_target + suffix)
        self.re_rules = re_rules

    def getWorkPath(self):
        """
        URI路径获取
        :return:
        """
        return self.re_rules

    def delete(self, target, rule):
        """
        字典删除处理
        :param target:
        :param rule:
        :return:
        """
        _prefix, _suffix = rule[0], rule[1]
        suffix = self.getSuffix(target) or ""
        if _prefix == "prefix":
            _target = target[:0 - len(suffix)].split(".")[-1] + suffix
            if _suffix == "suffix":
                _target = _target[:0 - len(suffix)]
            return _target
        if _prefix == "suffix":
            return target[:0 - len(suffix)]

    def getSuffix(self, host):
        """
        获取后缀
        :param host:
        :return:
        """
        for suffix in self.host_suffix:
            if host.endswith(suffix):
                return "." + suffix


if __name__ == '__main__':
    p = Production("www.asd.com", conf)
    print p.getWorkPath()
