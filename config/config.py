#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-
# Author: ver007
# Description: config.py python2.7
# License: Apache Licence 
# CreateTime: 2018/6/26 : 下午4:19
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def load_config(path):
    config_file = open(BASE_DIR + "/" + path, "r")
    config_str = ""
    while True:
        line = config_file.readline()
        if line == "":
            break
        config_str += line
    return json.loads(config_str, encoding="utf8")


conf = {"root": BASE_DIR, "rules": load_config("resource/finger.json"), "match": load_config("resource/work_rule.json"),
        "suffix": load_config("resource/file_suffix.json"), "host_suffix": load_config("resource/host_suffix.json")}
# rules = load_config("resource/finger.json")
# rules = load_config("resource/finger.json")
