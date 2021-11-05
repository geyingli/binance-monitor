# 包含数据的读写相关程序

import os
import time
from binance import instance

import utils


# 币安所有已上线币种 (不包括稳定币/看涨币/看跌币等币种，顺序不定)
COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "NEOUSDT", "LTCUSDT", "QTUMUSDT", "ADAUSDT", "XRPUSDT", "EOSUSDT", "TUSDUSDT", "IOTAUSDT", "XLMUSDT", "ONTUSDT", "TRXUSDT", "ETCUSDT", "ICXUSDT", "NULSUSDT", "VETUSDT", "LINKUSDT", "WAVESUSDT", "BTTUSDT", "ONGUSDT", "HOTUSDT", "ZILUSDT", "ZRXUSDT", "FETUSDT", "BATUSDT", "XMRUSDT", "ZECUSDT", "IOSTUSDT", "CELRUSDT", "DASHUSDT", "NANOUSDT", "OMGUSDT", "THETAUSDT", "ENJUSDT", "MITHUSDT", "MATICUSDT", "ATOMUSDT", "TFUELUSDT", "ONEUSDT", "FTMUSDT", "ALGOUSDT", "GTOUSDT", "DOGEUSDT", "DUSKUSDT", "ANKRUSDT", "WINUSDT", "COSUSDT", "COCOSUSDT", "MTLUSDT", "TOMOUSDT", "PERLUSDT", "DENTUSDT", "MFTUSDT", "KEYUSDT", "DOCKUSDT", "WANUSDT", "FUNUSDT", "CVCUSDT", "CHZUSDT", "BANDUSDT", "BUSDUSDT", "BEAMUSDT", "XTZUSDT", "RENUSDT", "RVNUSDT", "HBARUSDT", "NKNUSDT", "STXUSDT", "KAVAUSDT", "ARPAUSDT", "IOTXUSDT", "RLCUSDT", "CTXCUSDT", "BCHUSDT", "TROYUSDT", "VITEUSDT", "FTTUSDT", "EURUSDT", "OGNUSDT", "DREPUSDT",
    "TCTUSDT", "WRXUSDT", "BTSUSDT", "LSKUSDT", "BNTUSDT", "LTOUSDT", "AIONUSDT", "MBLUSDT", "COTIUSDT", "STPTUSDT", "WTCUSDT", "DATAUSDT", "SOLUSDT", "CTSIUSDT", "HIVEUSDT", "CHRUSDT", "GXSUSDT", "ARDRUSDT", "MDTUSDT", "STMXUSDT", "KNCUSDT", "REPUSDT", "LRCUSDT", "PNTUSDT", "COMPUSDT", "SCUSDT", "ZENUSDT", "SNXUSDT", "VTHOUSDT", "DGBUSDT", "GBPUSDT", "SXPUSDT", "MKRUSDT", "DCRUSDT", "STORJUSDT", "MANAUSDT", "AUDUSDT", "YFIUSDT", "BALUSDT", "BLZUSDT", "IRISUSDT", "KMDUSDT", "JSTUSDT", "SRMUSDT", "ANTUSDT", "CRVUSDT", "SANDUSDT", "OCEANUSDT", "NMRUSDT", "DOTUSDT", "LUNAUSDT", "RSRUSDT", "WNXMUSDT", "TRBUSDT", "BZRXUSDT", "SUSHIUSDT", "YFIIUSDT", "KSMUSDT", "EGLDUSDT", "DIAUSDT", "RUNEUSDT", "FIOUSDT", "UMAUSDT", "BELUSDT", "WINGUSDT", "UNIUSDT", "NBSUSDT", "OXTUSDT", "SUNUSDT", "AVAXUSDT", "HNTUSDT", "FLMUSDT", "ORNUSDT", "UTKUSDT", "XVSUSDT", "ALPHAUSDT", "AAVEUSDT", "NEARUSDT", "FILUSDT", "INJUSDT", "AUDIOUSDT", "CTKUSDT", "AKROUSDT",
    "AXSUSDT", "HARDUSDT", "DNTUSDT", "STRAXUSDT", "UNFIUSDT", "ROSEUSDT", "AVAUSDT", "XEMUSDT", "SKLUSDT", "SUSDUSDT", "GRTUSDT", "JUVUSDT", "PSGUSDT", "1INCHUSDT", "REEFUSDT", "OGUSDT", "ATMUSDT", "ASRUSDT", "CELOUSDT", "RIFUSDT", "BTCSTUSDT", "TRUUSDT", "CKBUSDT", "TWTUSDT", "FIROUSDT", "LITUSDT", "SFPUSDT", "DODOUSDT", "CAKEUSDT", "ACMUSDT", "BADGERUSDT", "FISUSDT", "OMUSDT", "PONDUSDT", "DEGOUSDT", "ALICEUSDT", "LINAUSDT", "PERPUSDT", "RAMPUSDT", "SUPERUSDT", "CFXUSDT", "EPSUSDT", "AUTOUSDT", "TKOUSDT", "PUNDIXUSDT", "TLMUSDT", "BTGUSDT", "MIRUSDT", "BARUSDT", "FORTHUSDT", "BAKEUSDT", "BURGERUSDT", "SLPUSDT", "SHIBUSDT", "ICPUSDT", "ARUSDT", "POLSUSDT", "MDXUSDT", "MASKUSDT", "LPTUSDT", "NUUSDT", "XVGUSDT", "ATAUSDT", "GTCUSDT", "TORNUSDT", "KEEPUSDT", "ERNUSDT", "KLAYUSDT", "PHAUSDT", "BONDUSDT", "MLNUSDT", "DEXEUSDT", "C98USDT", "CLVUSDT", "QNTUSDT", "FLOWUSDT", "TVKUSDT", "MINAUSDT", "RAYUSDT", "FARMUSDT", "ALPACAUSDT", "QUICKUSDT",
    "MBOXUSDT", "FORUSDT", "REQUSDT", "GHSTUSDT", "WAXPUSDT", "TRIBEUSDT", "GNOUSDT", "XECUSDT", "ELFUSDT", "DYDXUSDT", "POLYUSDT", "IDEXUSDT", "VIDTUSDT", "GALAUSDT", "ILVUSDT", "YGGUSDT", "SYSUSDT", "DFUSDT", "FIDAUSDT", "FRONTUSDT", "CVPUSDT", "AGLDUSDT", "RADUSDT", "BETAUSDT", "RAREUSDT", "LAZIOUSDT", "CHESSUSDT", "ADXUSDT", "AUCTIONUSDT",
]

MINUTE = 1    # 基础数据单位
HOUR = 60
DAY = 60 * 24
MONTH = 60 * 24 * 30
YEAR = 60 * 24 * 365
TIMESTAMP_UNIT = 1000


class Data:
    """读取数据文件，生成数据结构体"""

    def __init__(self, file):

        print("从`%s`读取数据..." % file)
        tics = []
        prices = []
        volumes = []

        with open(file) as f:
            for line in f:
                line = line[:-1].split("\t")

                # 获取当前价格及交易量
                # 0: 1609294920000,        开盘时间
                # 1: "27685.07000000",     开盘价
                # 2: "27690.00000000",     最高价
                # 3: "27660.62000000",     最低价
                # 4: "27683.34000000",     收盘价(当前K线未结束的即为最新价)
                # 5: "52.11377900",        成交量
                # 6: 1609294979999,        收盘时间
                # 7: "1442353.58329190",   成交额
                # 8: 1149,                 成交笔数
                # 9: "21.07290400",        主动买入成交量
                # 10: "583235.27944325",    主动买入成交额
                # 11: "0" ]                 请忽略该参数
                tic = int(line[0])
                price = float(line[4])
                volume = float(line[7])

                tics.append(tic)
                prices.append(price)
                volumes.append(volume)

        self.tics = tics
        self.prices = prices
        self.volumes = volumes


def get_moving_average(prices, interval):
    """获取移动平均价

    prices: e.g. [121 123 125 124 120]
    target_prices: 头部不满足长度要求的为None，其余皆有值 e.g. [None, None, 123, 124, 123]
    """
    # print("计算%s滑动平均价" % interval)

    # 单位数据量
    unit = int(interval[:-1])
    if interval[-1] == "h":
        unit *= 60
    elif interval[-1] == "d":
        unit *= 60 * 24

    mean_price = 0
    target_prices = []
    for i in range(len(prices)):
        if i < unit - 1:    # 未达数量要求
            mean_price += prices[i] / unit
            target_prices.append(None)
        elif i == unit - 1:    # 刚达数量要求
            mean_price += prices[i] / unit
            target_prices.append(mean_price)
        else:    # 达到数量要求
            mean_price -= prices[i - unit] / unit    # 丢弃头
            mean_price += prices[i] / unit    # 添加尾
            target_prices.append(mean_price)
    return target_prices


def update_data_all(verbosity=1):
    """更新所有数据"""

    utils.mkdir("data")

    # 遍历所有目标币种，以分钟为单位读取和更新数据
    for i, coin in enumerate(COINS):
        if verbosity:
            print("%s (%d/%d)" % (coin, i + 1, len(COINS)))
        data_loader(coin, "1m", "data/%s.1m.data" % coin, verbosity)


def data_loader(symbol, interval, file, verbosity=1):
    """加载新币种，或更新新数据"""

    # 新文件从七天前开始取数据，已有文件则继续累积数据
    last_timestamp = get_last_timestamp(file)
    if last_timestamp:
        init_timestamp = last_timestamp + 60 * TIMESTAMP_UNIT
    else:
        init_timestamp = int(time.time() - 7 * 24 * 60 * 60) * TIMESTAMP_UNIT

    # 获取最新数据
    latest_data = get_latest_data(symbol, interval, init_timestamp, verbosity)
    if not isinstance(latest_data, list):
        raise ValueError("download data fail: %s" % symbol)
    with open(file, "a", encoding="utf-8") as f:
        for item in latest_data:
            f.write("%s\n" % "\t".join(list(map(str, item))))


def get_latest_data(symbol, interval, init_timestamp, verbosity=1):
    """获得最新的区间数据"""

    # 根据间隔计算时间戳区间
    if interval == "1m":
        timestamp_interval = 500 * 60 * TIMESTAMP_UNIT  # 500条，每条间隔1分钟
    else:
        raise ValueError("unsupported interval: %s", interval)

    last = -1
    start_timestamp = init_timestamp
    now_timestamp = int(time.time() * TIMESTAMP_UNIT)  # 现在
    if now_timestamp < init_timestamp + 60 + TIMESTAMP_UNIT:    # 时间太近
        return []
    latest_data = []

    while True:
        now = time.time()

        # 睡眠，避免频繁请求
        if now - last < 0.5:
            time.sleep(0.5 - now + last)
            continue

        # 获取数据
        end_timestamp = start_timestamp + timestamp_interval - 1
        data = instance.get_prices(symbol, interval, start_timestamp, end_timestamp)
        if isinstance(data, dict) and "code" in data:
            raise ValueError(data["%s" % data])
        elif data is None:    # 网络问题等造成失败，重试
            continue
        latest_data += data

        # 计算并打印当前进度
        process = (start_timestamp + timestamp_interval - init_timestamp) / (now_timestamp - init_timestamp) * 100
        process = min(process, 100)
        if process < 0:
            process = 100
        if verbosity:
            print("[%.2f%%]" % process)

        # 进入下一次批数据
        last = time.time()
        start_timestamp += timestamp_interval
        if start_timestamp > now_timestamp:    # 结束
            break

    return latest_data


def get_last_timestamp(file):
    """从已有数据中获取最后一次记录的时间戳"""

    if not os.path.exists(file):
        return None

    # 读取最后一行
    last_line = ""
    with open(file, encoding="utf-8") as f:
        while True:
            line = f.readline()
            if not line:
                break
            last_line = line

    # 最后一行的第一个元素，即为时间戳
    if last_line:
        return int(last_line.strip().split("\t")[0])
    return None


if __name__ == "__main__":
    update_data_all()
