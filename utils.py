import os
import time
import numpy as np


def mkdir(path, clear=False):
    """创建文件夹"""

    if not os.path.exists(path):
        os.mkdir(path)

    # 清理文件夹中已有文件
    if clear:
        for file in os.listdir(path):
            os.remove(path + "/" + file)


def standardize(price, valid=4):
    """去除价格尾部的0"""

    s = str(price)
    n = 0    # 非零/有意义数字数量
    started = False
    after_dot = False
    for i in range(len(s)):
        if not started and s[i] != "." and s[i] != "0":
            started = True
        if not after_dot and s[i] == ".":
            after_dot = True

        if s[i] != ".":
            if started:
                n += 1
            if after_dot and n > valid:
                break

    s = s[:i]
    if s[-1] == ".":
        s = s[:-1]

    return s


def tic2time(tic):
    """将时间戳转换为时间"""

    if tic > 1000000000000:
        tic /= 1000

    date = time.localtime(tic)
    return "%s年%s月%s日 %02d:%02d:%02d" % (date.tm_year, date.tm_mon, date.tm_mday, date.tm_hour, date.tm_min, date.tm_sec)


def time2tic(year, month, day, hour, minute, second):
    """将时间转换为时间戳"""

    t = "%s-%s-%s %02d:%02d:%02d" % (year, month, day, hour, minute, second)
    return int(time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S")))


def get_diagnal_corr(prices):
    """获取资产价格和时间的相关性"""

    max_price = max(prices)
    min_price = min(prices)
    unit = (max_price - min_price) / len(prices)

    diagnal_prices = [max_price - j * unit for j in range(len(prices))]
    corr = abs(np.corrcoef(prices, diagnal_prices)[0, 1])
    return corr
