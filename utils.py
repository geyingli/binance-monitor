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
    """标准化价格"""

    s = str(price)

    # 移除科学计数
    if "e" in s:
        base = s[:s.index("e")]
        exponent = int(s[s.index("e") + 1:])

        # 确定"点"位
        if "." in base:
            integer = base[:base.index(".")]
            decimal = base[base.index(".") + 1:]
        else:
            integer = base
            decimal = ""

        # 指数大于0
        for _ in range(abs(exponent)):
            if exponent > 0:
                if decimal:
                    integer += decimal[0]
                    decimal = decimal[1:]
                else:
                    integer += "0"
            elif exponent < 0:
                decimal = integer[-1] + decimal
                integer = integer[:-1]
                if not integer:
                    integer = "0"

        # 重组s
        s = str(int(integer))
        if decimal:
            s += "." + decimal

    # 保证非零/非点数 (有效数字) 数量在`valid`及以下
    n = 0
    on_valid = False
    after_dot = False
    for i in range(len(s)):
        if not on_valid and s[i] not in (".", "0"):    # 遇到第一个有效数
            on_valid = True
        if not after_dot and s[i] == ".":    # 遇到小数点
            after_dot = True

        if s[i] != ".":
            if on_valid:
                n += 1
            if after_dot and n == valid:
                break
    s = s[:i + 1]

    # 去尾部0
    j = len(s)
    if "." in s:
        for i in range(len(s) - 1, 1, -1):
            if s[i] != "0":
                break
            j = i
    s = s[:j]

    # 去尾部标点
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
