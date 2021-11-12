# 本页的实现参考了：https://github.com/hengxuZ/binance-quantization，感谢hengxuZ提供的优质代码

import os
import requests
import time
import json
import hmac
import pprint
import hashlib
import urllib

import utils


class BinanceAPI:
    """通过币安API获取信息，详见：
    https://github.com/binance/binance-spot-api-docs/blob/master/README_CN.md
    """

    BASE_URL = "https://www.binance.com/api/v3"
    FUTURE_URL = "https://fapi.binance.com"
    PUBLIC_URL = "https://www.binance.com/exchange/public/product"

    def __init__(self, key, secret, verbosity=0):
        self.key = key    # API Key
        self.secret = secret    # Secret Key
        self.verbosity = verbosity

        self.last_fail_tic = -1    # 上一次报错时间戳 (避免报错信息刷屏，距离上一次报错太近则不报错)
        self.lost_connection = False    # 是否断开网络连接

    def get_ping(self):
        """检测是否与服务器连接成功

        returns: {}
        """

        url = "%s/ping" % self.BASE_URL
        params = {}

        # 请求
        try:
            return self._request_without_sign(url, params)
        except Exception as e:
            return self._process_error(e)

    def get_time(self):
        """获取服务器时间戳

        returns: {'serverTime': 1635406440050}
        """

        url = "%s/time" % self.BASE_URL
        params = {}

        # 请求
        try:
            return self._request_without_sign(url, params)
        except Exception as e:
            return self._process_error(e)

    def get_price(self, symbol=None):
        """获取资产现价

        returns: {
            "symbol": "LTCBTC",
            "price": "4.00000200"
        }
        """

        url = "%s/ticker/price" % self.BASE_URL
        params = {}
        if symbol:
            params["symbol"] = symbol

        # 请求
        try:
            return self._request_without_sign(url, params)
        except Exception as e:
            return self._process_error(e)

    def get_price_change(self, symbol, interval="24hr"):
        """获取资产区间交易信息

        returns: {
            "symbol": "BNBBTC",
            "priceChange": "-94.99999800",
            "priceChangePercent": "-95.960",
            "weightedAvgPrice": "0.29628482",
            "prevClosePrice": "0.10002000",
            "lastPrice": "4.00000200",
            "lastQty": "200.00000000",
            "bidPrice": "4.00000000",
            "askPrice": "4.00000200",
            "openPrice": "99.00000000",
            "highPrice": "100.00000000",
            "lowPrice": "0.10000000",
            "volume": "8913.30000000",
            "quoteVolume": "15.30000000",
            "openTime": 1499783499040,
            "closeTime": 1499869899040,
            "firstId": 28385,   // 首笔成交id
            "lastId": 28460,    // 末笔成交id
            "count": 76         // 成交笔数
        }
        """

        url = "%s/ticker/%s" % (self.BASE_URL, interval)
        params = {"symbol": symbol}

        # 请求
        try:
            return self._request_without_sign(url, params)
        except Exception as e:
            return self._process_error(e)

    def get_ticker_bookticker(self, symbol):
        """获取资产挂单价

        returns: {
          "symbol": "LTCBTC",
          "bidPrice": "4.00000000",//最优买单价
          "bidQty": "431.00000000",//挂单量
          "askPrice": "4.00000200",//最优卖单价
          "askQty": "9.00000000"//挂单量
        }
        """

        url = "%s/ticker/bookTicker" % self.BASE_URL
        params = {"symbol": symbol}

        # 请求
        try:
            return self._request_without_sign(url, params)
        except Exception as e:
            return self._process_error(e)

    def get_prices(self, symbol, interval="1m", startTime=None, endTime=None):
        """获取区间价格

        returns: [
            [
                1499040000000,      // 开盘时间
                "0.01634790",       // 开盘价
                "0.80000000",       // 最高价
                "0.01575800",       // 最低价
                "0.01577100",       // 收盘价(当前K线未结束的即为最新价)
                "148976.11427815",  // 成交量
                1499644799999,      // 收盘时间
                "2434.19055334",    // 成交额
                308,                // 成交笔数
                "1756.87402397",    // 主动买入成交量
                "28.46694368",      // 主动买入成交额
                "17928899.62484339" // 请忽略该参数
            ],
            ...
        ]
        """

        url = "%s/klines" % self.BASE_URL
        params = None
        if startTime is None:
            params = {"symbol": symbol, "interval": interval}
        else:
            params = {"symbol": symbol, "interval": interval, "startTime": startTime, "endTime": endTime}

        # 请求
        try:
            return self._request_without_sign(url, params)
        except Exception as e:
            return self._process_error(e)

    def get_historical_trades(self, symbol, limit=500, startTime=None, endTime=None):
        """获取历史交易

        returns: [
            {
                "a": 26129,         // 归集成交ID
                "p": "0.01633102",  // 成交价
                "q": "4.70443515",  // 成交量
                "f": 27781,         // 被归集的首个成交ID
                "l": 27781,         // 被归集的末个成交ID
                "T": 1498793709153, // 成交时间
                "m": true,          // 是否为主动卖出单
                "M": true           // 是否为最优撮合单(可忽略，目前总为最优撮合)
            },
            ...
        ]
        """

        url = "%s/aggTrades" % self.BASE_URL
        params = {"symbol": symbol, "limit": limit}
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime

        # 请求
        try:
            return self._request_without_sign(url, params)
        except Exception as e:
            return self._process_error(e)

    def get_account(self):
        """获取账户信息

        returns: {
            "balances": [
                {
                    "asset": "BTC",
                    "free": "4723846.89208129",
                    "locked": "0.00000000"
                },
                {
                    "asset": "LTC",
                    "free": "4763368.68006011",
                    "locked": "0.00000000"
                },
                ...
            ],
            'canDeposit': True,
            'canTrade': True,
            'canWithdraw': True,
            'permissions': ['SPOT', 'LEVERAGED'],   # 权限
            'buyerCommission': 0,                   # 现货买入手续费
            'sellerCommission': 0,                  # 现货售出手续费
            'makerCommission': 10,                  # 合约挂单手续费
            'takerCommission': 10,                  # 合约接单手续费
            'updateTime': 1635407407595,            # 时间戳
        }
        """

        url = "%s/account" % self.BASE_URL
        params = {"recvWindow": 5000, "timestamp": int(1000 * time.time())}

        # 请求
        try:
            return self._request_with_sign(url, params)
        except Exception as e:
            return self._process_error(e)

    def get_account_value(self):
        """获取账户剩余价值

        returns: {
            'assets': {
                'AUDIO': {'perc': '11.64%', 'price': 2.604, 'value': 168.2},
                'AXS': {'perc': '10.68%', 'price': 145.85, 'value': 154.4},
                'BAT': {'perc': '17.18%', 'price': 1.3298, 'value': 248.4},
                'GALA': {'perc': '12.10%', 'price': 0.10894, 'value': 174.8},
                'MANA': {'perc': '27.15%', 'price': 3.7773, 'value': 392.4},
                'USDT': {'perc': '20.92%', 'price': 1.0, 'value': 302.4},
            },
            'value': 1445.636287122,
        }
        """

        # 获取持仓信息
        account = self.get_account()
        if account is None:
            return

        # 获取价格
        prices = {}
        for market in self.get_price():
            symbol = market["symbol"]
            price = market["price"]
            prices[symbol] = float(price)

        # 整理资产信息
        assets = {}
        for asset in account["balances"]:
            name = asset["asset"]
            quantity = float(asset["free"]) + float(asset["locked"])
            if quantity > 0:
                price = 1.0
                if "USD" not in name:
                    price = prices[name + "USDT"]
                assets[name] = {
                    "price": price,
                    "value": price * quantity,
                }
        total_value = sum([v["value"] for _, v in assets.items()])
        for asset in list(assets.keys()):
            if assets[asset]["value"] < 10:    # 小额资产不予显示
                assets.pop(asset)
                continue
            assets[asset]["fraction"] = "%.2f%%" % (assets[asset]["value"] / total_value * 100)
            assets[asset]["value"] = float(utils.standardize(assets[asset]["value"]))
        data = {
            "value": float("%.1f" % total_value),
            "assets": assets,
        }

        return data

    def trade(self, symbol, quantity=None, value=None, side="BUY/SELL", limit_price=None):
        """现货交易 (这个函数有问题，待排查，暂时无法执行)"""

        if quantity is None and value is None:
            print("FAIL: quantity/value cannot be NONE together")
            return
        elif quantity is not None and value is not None:
            print("FAIL: quantity/value cannot be not NONE together")
            return

        url = "%s/order" % self.BASE_URL
        params = {"timestamp": int(1000 * time.time())}

        if limit_price is not None:    # 限价委托
            params["type"] = "LIMIT"
            params["price"] = "%.8f" % limit_price
            params["timeInForce"] = "GTC"
        else:
            params["type"] = "MARKET"

        params["symbol"] = symbol
        params["side"] = side
        params["quantity"] = "%.8f" % quantity

        # 请求
        try:
            return self._request_with_sign(url, params)
        except Exception as e:
            if time.time() - self.last_fail_tic > 60:
                print("FAIL: %s" % e)
            self.last_fail_tic = time.time()
            return

    def _request_with_sign(self, url, params):
        """带有签名的HTTP请求"""

        params = self._sign(params)
        query = urllib.parse.urlencode(params)
        header = {"X-MBX-APIKEY": self.key}
        url = "%s?%s" % (url, query)
        if self.verbosity:
            print("REQUEST: ", url)

        # 请求
        data = requests.get(url, headers=header, timeout=180, verify=True)
        try:
            d = data.json()
            if self.lost_connection:
                print("网络已恢复")
                self.lost_connection = False
            return d
        except Exception:
            return "FAIL: " + data.content.decode('utf-8')

    def _request_without_sign(self, url, params):
        """不带签名的HTTP请求"""
        query = urllib.parse.urlencode(params)
        url = "%s?%s" % (url, query)
        if self.verbosity:
            print("REQUEST: ", url)

        # 请求
        data = requests.get(url, timeout=180, verify=True)
        try:
            d = data.json()
            if self.lost_connection:
                print("网络已恢复")
                self.lost_connection = False
            return d
        except Exception:
            return "FAIL: " + data.content.decode('utf-8')

    def _sign(self, params):
        """签名

        returns: {
            'signature': '7d4c72a87cdcc88ce4d8ec22d1384085e0092498fb1a6563767672fc7d5cd5ad',
        }
        """

        data = params.copy()

        h = urllib.parse.urlencode(data)
        b = bytearray()
        b.extend(self.secret.encode())
        signature = hmac.new(b, msg=h.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()
        data["signature"] = signature

        return data

    def _process_error(self, e):
        """处理报错"""
        if time.time() - self.last_fail_tic > 60:
            print("FAIL: %s" % e)
            if ("%s" % e).startswith("HTTPSConnectionPool"):
                print("网络连接失败")
                self.lost_connection = True
        self.last_fail_tic = time.time()


# 读取API配置
if not os.path.exists("api.conf"):
    raise FileNotFoundError("未找到`./api.conf`文件，请遵循README提示操作")
with open("api.conf", encoding="utf-8") as f:
    api_conf = json.load(f)
    instance = BinanceAPI(
        api_conf["API Key"],
        api_conf["Secret Key"],
    )


if __name__ == "__main__":

    # pprint.pprint(instance.get_ping())    # 检测是否与服务器连接成功
    # pprint.pprint(instance.get_time())    # 获取服务器时间戳
    # pprint.pprint(instance.get_price())    # 获取所有资产价格
    # pprint.pprint(instance.get_price("BTCUSDT"))    # 获取指定资产价格
    # pprint.pprint(instance.get_prices("BTCUSDT", interval="1h", startTime=None, endTime=None))    # 获取价格区间
    # pprint.pprint(instance.get_price_change("BTCUSDT", interval="24hr"))    # 获取价格区间变动
    # pprint.pprint(instance.get_account())    # 获取账户信息
    # pprint.pprint(instance.get_account_value())    # 获取账户价值
    # pprint.pprint(instance.trade("BTCUSDT", quantity=1.0, side="BUY", limit_price=None))    # 现货交易 (暂时无法执行)

    # 定期打印账户价值
    while True:
        print(utils.tic2time(time.time()))
        pprint.pprint(instance.get_account_value())    # 获取账户价值
        time.sleep(60)
