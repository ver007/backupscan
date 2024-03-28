#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-
# Author: ver007
# Description: scanwork.py python2.7
# License: Apache Licence 
# CreateTime: 2018/6/26 : 下午4:49
import time
import zlib
import urllib
import urlparse

from socket import *
from AnsiColor import *
from threadpool import *
from match import MatchHandel
from production import Production

_https = False
try:
    import ssl

    _https = True
except ImportError:
    print "import ssl error"
    pass


class ScanBackup(object):
    """
    扫描备份
    """

    def __init__(self, target, option, config):
        self.timeout = None
        self.status = False
        self.option = option
        self.target = target
        self.matchHandel = MatchHandel(config.get("rules"))
        self.host, self.port, self.main_path = self.host_parse(target)
        self.output_path = config.get("root") + "/" + target.replace(":", "-") + ".txt"
        self.output_file = open(self.output_path, "a")
        prod = Production(self.host, config)
        self.paths = prod.getWorkPath()
        self.path_num = len(self.paths)
        self._Error_ = None
        self.getErr404Page()
        # self.getNormalPage()
        self.requests = makeRequests(self.do_something, self.paths, self.print_result, self.handle_exception)

    def getErr404Page(self):
        """
        获取错误页面关键字
        """
        stime = time.time()
        self._Error_ = self.do_something("get_404_page")
        etime = time.time()
        if (etime - stime) > 3: self.timeout = 1

    # def getNormalPage(self):
    #     s, b, h = self.do_something("")
    #     self.status = (s != "200" or s == "404")

    def host_parse(self, target):
        """
        host 解析
        :param target:
        :return:
        """
        if not target.startswith("http"): target = "http://" + target
        url = urlparse.urlparse(target)
        host_port = url.netloc or url.path
        host = host_port.split(":")[0]
        port = host_port.split(":")[1] if ":" in host_port else "80"
        path = url.path or "/"
        return host, port, path

    def do_something(self, path):
        """
        识别rdp服务
        :param path: 请求地址路径
        :return:
        """

        get_str = 'GET %s%s HTTP/1.1\r\n' \
                  'Host: %s:%s\r\n' \
                  'Connection: close\r\n' \
                  'Accept-Encoding: gzip, deflate\r\n' \
                  'User-Agent: Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                  'Chrome/44.0.2403.125 Safari/537.36\r\n' \
                  'Accept: */*\r\n\r\n' % (self.main_path, urllib.quote(path).replace("%5f", "/"), self.host, self.port)

        conn, version, status, reason, length, html, headers = None, "", "", "", 0, "", {}
        try:
            conn = self.sockHttp(self.host, self.port, self.timeout or self.option.get("timeout"))
            if conn is None: return status, html, headers
            conn.send(get_str)
            recv_data, byte_num = "", 0
            while True:
                recv_data += conn.recv(100)
                byte_num += 100
                if recv_data.find("\r\n\r\n") >= 0:
                    recv_data += conn.recv(100)
                    break
                if byte_num > 1000: break

            line = recv_data.split("\r\n")[0]
            try:
                [version, status, reason] = line.split(None, 2)
            except ValueError:
                try:
                    [version, status] = line.split(None, 1)
                    reason = ""
                except ValueError:
                    version = ""

            index = recv_data.find("\r\n\r\n")
            if index >= 0:
                header = recv_data[0:index]
                recv_data = recv_data[index + 4:]
                header_lines = header.split("\r\n")
                status_line = header_lines[0]
                for line in header_lines[1:]:
                    line = line.strip("\r\n")
                    if len(line) == 0:
                        continue
                    colonIndex = line.find(":")
                    fieldName = line[:colonIndex]
                    fieldValue = line[colonIndex + 1:].strip()
                    headers[fieldName] = fieldValue
            else:
                return status, html, length

            if 'Content-Encoding' in headers and 'gzip' in headers['Content-Encoding']:
                html = zlib.decompress(recv_data, 16 + zlib.MAX_WBITS)
            else:
                html = recv_data

            return status, html, headers

        except socket.error as e:
            if e[0] in (10060, 'timed out') or str(e) == "[Errno 35] Resource temporarily unavailable":
                return status, html, headers
        except Exception, e:
            return status, html, headers
        finally:
            if conn: conn.close()

    def print_result(self, request, result):
        try:
            url = self.main_path + urllib.quote(request.args[0]).replace("%5f", "/")
            status, body, headers = result
            self.path_num -= 1
            _status, _body, _headers = self.match_error(result)
            if _status and _body and _headers:
                Print_E_line(self.path_num, (result[0] or "404") + " " + self.target + url)
            else:
                type_name = self.matchHandel.match(headers, body)
                if type_name is not None:
                    self.output_file.writelines(self.target + url + "\n")
                    Print_(result[0] + " " + hexdump(body) + self.target + url + " Length: " + str(
                        headers.get("Content-Length", "0")) + " Type: " + type_name)
                else:
                    Print_E_line(self.path_num, (result[0] or "404") + " " + self.target + url)
        except Exception, e:
            pass

    def match_error(self, result):
        """
        匹配错误页面
        :param result:
        :return:
        """
        status1, body1, headers1 = result
        status2, body2, headers2 = self._Error_
        _status, _body, _headers = [False] * 3
        if status1 == status2: _status = True
        if body1 == body2: _body = True
        if headers1 == headers2: _headers = True
        return _status, _body, _headers

    def handle_exception(self, request, exc_info):
        """
        处理线程池工作异常
        :param request:
        :param exc_info:
        :return:
        """
        if not isinstance(exc_info, tuple):
            raise SystemExit
        Print_E("请求发生异常 #%s: %s" % (request.requestID, exc_info))

    def start(self):
        main = ThreadPool(self.option.get("thread"))

        for req in self.requests:
            main.putRequest(req)

        while not self.status:
            try:
                time.sleep(0.5)
                main.poll()

            except NoResultsPending:
                print "\n"
                Print_B("**** 扫描结束无结果!")
                break
            except KeyboardInterrupt:
                print "\n"
                print "1: 结束任务"
                print "2: 进入下一任务"
                print "3: 继续当前任务\n"
                i = raw_input("请输入下一步编号 > ")
                workNum = len(main.workers)
                if i.strip() == "1":
                    main.dismissWorkers(workNum)
                    self.status = True
                    break
                elif i == "2":
                    # main.dismissWorkers(workNum)
                    break
                elif i == "3":
                    continue

        if main.dismissedWorkers:
            print "\n"
            Print_B(self.target + " 扫描结束，退出工作线程...")
            main.joinAllDismissedWorkers()

        self.output_file.close()

    def sockHttp(self, host, port, timeout=3):
        """
        Sock Https 请调用后调用结束
        :param host:
        :param port:
        :param timeout:
        :return:
        """
        socketObj = socket(AF_INET, SOCK_STREAM)
        try:
            if port == 443:
                if not _https:
                    raise Exception("Not support SSL")
                try:
                    socketObj = ssl.wrap_socket(socketObj, ssl_version=ssl.PROTOCOL_TLSv1)
                except ssl.SSLError:
                    socketObj = ssl.wrap_socket(socketObj, ssl_version=ssl.PROTOL_SSLv23)

            socketObj.settimeout(timeout)
            socketObj.connect((host, int(port)))
            return socketObj
        except IOError, e:
            return None
