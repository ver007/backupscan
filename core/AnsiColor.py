#!/usr/bin/python
# -*- coding: utf-8 -*-

fmt = "[***] "
fmt_w = "[***] "
fmt_e = "[!!!] "


class ansi(object):
    """
    ansi
    """
    (black, red, green, yellow, blue, magenta, cyan, grey) = range(30, 38)
    reset = '\033[0m'

    @staticmethod
    def code(fg, bg):
        return '\033[{0};{1}m'.format(bg + 10, fg)

    @staticmethod
    def wrap(text, fg=0, bg=0):
        return '{0}{1}{2}'.format(ansi.code(fg, bg), text, ansi.reset)

    @staticmethod
    def ok(text):
        """
        成功输出
        :param text: 待输出内容
        :return:
        """
        # type: (object) -> object
        text = str(text)
        return ansi.wrap(text, ansi.green)

    @staticmethod
    def warning(text):
        """
        警告输出
        :param text: 待输出内容
        :return:
        """
        return ansi.wrap(text, ansi.yellow)

    @staticmethod
    def error(text):
        return ansi.wrap(text, ansi.red)

    @staticmethod
    def blues(text):
        return ansi.wrap(text, ansi.blue)

    def __init__(self, fg, bg=0):
        self.fg = fg
        self.bg = bg

    def __call__(self, text):
        return ansi.wrap(text, self.fg, self.bg)


def Print_W(args):
    """
    warning
    :param args:
    :return:
    """
    # 线程锁开始
    print ansi.warning(fmt_w + args)


def Print_E(args):
    """
    error
    :param args:
    :return:
    """
    # 线程锁开始
    print ansi.error(fmt_e + args)


def Print_E_line(num, args):
    """
    error
    :param args:
    :return:
    """
    meg = "[ %0.6d ] " % num + args
    print "\r" + ansi.warning("%-90.110s" % meg),
    # print ansi.warning("%-80.90s" % meg)


def Print(args):
    """
    blues
    :param args:
    :return:
    """
    # 线程锁开始
    print ansi.ok(fmt + args)


def Print_(args):
    """
    blues
    :param args:
    :return:
    """
    # 线程锁开始
    print ansi.ok("\n" + fmt + args)


def Print_B(args):
    """
    blues
    :param args:
    :return:
    """
    # 线程锁开始
    print ansi.blues(fmt + args)


def hexdump(src, length=16):
    """
    文本转hex 16进制排列输出
    :param src: 源数据
    :param length: 行长度
    :return: None
    """
    result = []

    for i in xrange(0, len(src[:10]), length):
        s = src[i:i + length]
        text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.' for x in s])
        result.append(b"%s" % text)

    return "[ " + b''.join(result) + " ] "


if __name__ == '__main__':
    print ansi.ok('OK')
    print ansi.warning('WARNING')
    print ansi.error('ERROR')
    blue = ansi(ansi.blue)
    print blue('FOO')
    print ansi.blues('xxxx')
    print ansi.wrap('xxxx')
    print ansi(ansi.magenta, ansi.grey)('BAR')
    print hexdump("asdasasdafads")
