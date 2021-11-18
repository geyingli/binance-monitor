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

    def __init__(self, key, secret, basic_currency="USDT", verbosity=0):
        self.key = key    # API Key
        self.secret = secret    # Secret Key
        self.basic_currency = "USDT"    # 基础货币(一键平仓时将自动将资产出售为该货币)
        self.verbosity = verbosity

        self.lost_connection = False    # 是否断开网络连接

    def get_ping(self):
        """检测是否与服务器连接成功

        returns: None, {}
        """

        url = "%s/ping" % self.BASE_URL
        params = {}

        # 请求
        try:
            return None, self._get_without_sign(url, params)
        except Exception as e:
            return "服务连接失败: %s" % self._process_error(e), None

    def get_time(self):
        """获取服务器时间戳

        returns: None, {'serverTime': 1635406440050}
        """

        url = "%s/time" % self.BASE_URL
        params = {}

        # 请求
        try:
            return None, self._get_without_sign(url, params)
        except Exception as e:
            return "获取服务器时间戳失败: %s" % self._process_error(e), None

    def get_price(self, symbol=None):
        """获取资产现价

        returns: None, {
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
            return None, self._get_without_sign(url, params)
        except Exception as e:
            return "获取资产现价失败: %s" % self._process_error(e), None

    def get_price_change(self, symbol, interval="24hr"):
        """获取资产区间交易信息

        returns: None, {
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
            return None, self._get_without_sign(url, params)
        except Exception as e:
            return "获取资产区间交易信息失败: %s" % self._process_error(e), None

    def get_ticker_bookticker(self, symbol):
        """获取资产挂单价

        returns: None, {
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
            return None, self._get_without_sign(url, params)
        except Exception as e:
            return "获取资产挂单价失败: %s" % self._process_error(e), None

    def get_prices(self, symbol, interval="1m", startTime=None, endTime=None):
        """获取区间价格

        returns: None, [
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
            return None, self._get_without_sign(url, params)
        except Exception as e:
            return "获取区间价格失败: %s" % self._process_error(e), None

    def get_historical_trades(self, symbol, limit=500, startTime=None, endTime=None):
        """获取历史交易

        returns: None, [
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
            return None, self._get_without_sign(url, params)
        except Exception as e:
            return "获取历史交易失败: %s" % self._process_error(e), None

    def get_account(self):
        """获取账户信息

        returns: None, {
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
            return None, self._get_with_sign(url, params)
        except Exception as e:
            return "获取账户信息失败: %s" % self._process_error(e), None

    def get_account_value(self):
        """获取账户剩余价值

        returns: None, {
            'assets': {
                'BTC': {
                    'fraction': '1.84%',
                    'price': 60470.31,
                    'quantity': 0.00032967,
                    'value': 19.93,
                },
                'SOL': {
                    'fraction': '72.15%',
                    'price': 218.76,
                    'quantity': 3.57446,
                    'value': 781.9,
                },
                'USDT': {
                    'fraction': '25.95%',
                    'price': 1.0,
                    'quantity': 281.21525993,
                    'value': 281.2,
                }
            },
            'value': 1083.8,
        }
        """

        # 获取持仓信息
        err, account = self.get_account()
        if err is not None:
            return "获取账户信息失败: %s" % err, None

        # 获取价格
        prices = {}
        err, tmp_prices = self.get_price()
        if err is not None:
            return "获取账户信息失败: %s" % err, None
        for market in tmp_prices:
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
                    price = prices[name + self.basic_currency]
                assets[name] = {
                    "quantity": quantity,
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

        return None, data

    def buy(self, symbol, quantity=None, value=None, limit_price=None):
        """现货买入

        returns None, {
            'clientOrderId': 'WgLt8BIwOe3ya3MBiHTIzW',
            'cummulativeQuoteQty': '19.94599530',
            'executedQty': '0.00033000',
            'fills': [{'commission': '0.00000033',
                        'commissionAsset': 'BTC',
                        'price': '60442.41000000',
                        'qty': '0.00033000',
                        'tradeId': 1150128819}],
            'orderId': 8300640584,
            'orderListId': -1,
            'origQty': '0.00033000',
            'price': '0.00000000',
            'side': 'BUY',
            'status': 'FILLED',
            'symbol': 'BTCUSDT',
            'timeInForce': 'GTC',
            'transactTime': 1637201885195,
            'type': 'MARKET',
        }
        """

        if quantity is not None and value is not None:
            return "quantity/value不能同时不为空", None

        url = "%s/order" % self.BASE_URL

        # 根据账户余额获取交易额
        if value is None:
            if symbol.endswith("USDT"):
                currency = "USDT"
            elif symbol.endswith("BUSD"):
                currency = "BUSD"
            else:
                return "现货买入失败: 不支持快速交易%s，请填写quantity/value字段" % symbol, None
            err, account_info = self.get_account_value()
            if err is not None:
                return "现货买入失败: %s" % self._process_error(err), None
            if currency not in account_info["assets"]:
                return "现货买入失败: 无可用%s，请确认账户持仓" % currency, None
            value = account_info["assets"][currency]["value"]
            if value < 10:
                return "现货买入失败: %s余额需大于$10" % currency, None

        # 根据价格获取交易量
        if quantity is None:
            if limit_price is None:
                err, tmp = self.get_price(symbol)
                if err is not None:
                    return "现货买入失败: %s" % err, None
                price = float(tmp["price"])
            else:
                price = limit_price
            quantity = value / price
        quantity = utils.standardize(quantity, valid=2)

        # 限价/市价委托
        params = {
            "symbol": symbol,
            "side": "BUY",
            "quantity": quantity,
            "timestamp": int(1000 * time.time()),
            "recvWindow": 5000,
        }
        if limit_price is not None:    # 限价委托
            params["type"] = "LIMIT"
            params["timeInForce"] = "GTC"
            params["price"] = float(limit_price)
        else:
            params["type"] = "MARKET"

        # 请求
        try:
            return None, self._post_with_sign(url, params)
        except Exception as e:
            return "现货买入失败: %s" % self._process_error(e), None

    def sell(self, symbol, quantity=None, value=None, limit_price=None):
        """现货卖出

        returns None, {
            'clientOrderId': '1fneZMNyZk7KTFoZLZuFtK',
            'cummulativeQuoteQty': '30.24814000',
            'executedQty': '0.00050000',
            'fills': [{'commission': '0.03024814',
                        'commissionAsset': 'USDT',
                        'price': '60496.28000000',
                        'qty': '0.00050000',
                        'tradeId': 1150160363}],
            'orderId': 8300961476,
            'orderListId': -1,
            'origQty': '0.00050000',
            'price': '0.00000000',
            'side': 'SELL',
            'status': 'FILLED',
            'symbol': 'BTCUSDT',
            'timeInForce': 'GTC',
            'transactTime': 1637204827321,
            'type': 'MARKET',
        }
        """

        if quantity is not None and value is not None:
            return "quantity/value不能同时不为空", None

        url = "%s/order" % self.BASE_URL

        # 根据账户余额获取交易额
        if quantity is None and value is None:
            if symbol.endswith("USDT"):
                asset = symbol[:-4]
            elif symbol.endswith("BUSD"):
                asset = symbol[:-4]
            else:
                return "现货卖出失败: 不支持快速交易%s，请填写quantity/value字段" % symbol, None
            err, account_info = self.get_account_value()
            if err is not None:
                return "现货卖出失败: %s" % self._process_error(err), None
            if asset not in account_info["assets"]:
                return "现货卖出失败: 无可用%s，请确认账户持仓" % asset, None
            quantity = account_info["assets"][asset]["quantity"]
            value = account_info["assets"][asset]["value"]
            if value < 10:
                return "现货卖出失败: %s余额需大于$10" % asset, None

        # 根据价格获取交易量
        if quantity is None:
            if limit_price is None:
                err, tmp = self.get_price(symbol)
                if err is not None:
                    return "现货卖出失败: %s" % err, None
                price = float(tmp["price"])
            else:
                price = limit_price
            quantity = value / price
        quantity = utils.standardize(quantity, valid=2)

        # 限价/市价委托
        params = {
            "symbol": symbol,
            "side": "SELL",
            "quantity": quantity,
            "timestamp": int(1000 * time.time()),
            "recvWindow": 5000,
        }
        if limit_price is not None:    # 限价委托
            params["type"] = "LIMIT"
            params["timeInForce"] = "GTC"
            params["price"] = float(limit_price)
        else:
            params["type"] = "MARKET"

        # 请求
        try:
            return None, self._post_with_sign(url, params)
        except Exception as e:
            return "现货卖出失败: %s" % self._process_error(e), None

    def sell_all(self):
        """一键平仓"""

        # 获取账户持仓
        err, account_info = self.get_account_value()
        if err is not None:
            return "一键平仓失败: %s" % self._process_error(err), None

        # 逐一平仓
        info = {
            "success": {},
            "fail": {},
        }
        for asset, asset_info in account_info["assets"].items:
            if "USD" in asset:
                continue
            value = asset_info["value"]
            if value < 10:
                continue
            err, _ = self.sell(asset + self.basic_currency)
            if err is not None:
                info["fail"][asset] = {
                    "fail": err,
                    "asset_info": asset_info,
                }
            else:
                info["success"][asset] = asset_info

        if self.verbosity > 0:
            print("一键平仓")
        return None, info

    def _post_with_sign(self, url, params):
        """带有签名的HTTP请求"""

        params = self._sign(params)
        query = urllib.parse.urlencode(params)
        header = {"X-MBX-APIKEY": self.key}
        url = "%s" % url
        if self.verbosity > 1:
            print("REQUEST: ", url)
            print(query)

        # 请求
        data = requests.post(url, headers=header, data=query, timeout=180, verify=True)
        try:
            d = data.json()
            if self.lost_connection and self.verbosity > 0:
                print("网络连接已恢复")
                self.lost_connection = False
            return d
        except Exception as e:
            if self.verbosity > 1:
                print(data.content.decode("utf-8"))
            raise e

    def _get_with_sign(self, url, params):
        """带有签名的HTTP请求"""

        params = self._sign(params)
        query = urllib.parse.urlencode(params)
        header = {"X-MBX-APIKEY": self.key}
        url = "%s?%s" % (url, query)
        if self.verbosity > 1:
            print("REQUEST: ", url)

        # 请求
        data = requests.get(url, headers=header, timeout=180, verify=True)
        try:
            d = data.json()
            if self.lost_connection and self.verbosity > 0:
                print("网络连接已恢复")
                self.lost_connection = False
            return d
        except Exception as e:
            if self.verbosity > 1:
                print(data.content.decode("utf-8"))
            raise e

    def _get_without_sign(self, url, params):
        """不带签名的HTTP请求"""
        query = urllib.parse.urlencode(params)
        url = "%s?%s" % (url, query)
        if self.verbosity > 1:
            print("REQUEST: ", url)

        # 请求
        data = requests.get(url, timeout=180, verify=True)
        try:
            d = data.json()
            if self.lost_connection and self.verbosity > 0:
                print("网络连接已恢复")
                self.lost_connection = False
            return d
        except Exception as e:
            if self.verbosity > 1:
                print(data.content.decode("utf-8"))
            raise e

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

        msg = "%s" % e
        if not self.lost_connection and self.verbosity > 0:
            if (msg.startswith("HTTPSConnectionPool") or "RemoteDisconnected" in msg):
                print("网络连接失败")
            else:
                print(msg)
        self.lost_connection = True
        return msg


# 读取API配置
if not os.path.exists("api.conf"):
    raise FileNotFoundError("未找到`./api.conf`文件，请遵循README提示操作, 并注意保护隐私")
with open("api.conf", encoding="utf-8") as f:
    api_conf = json.load(f)
    instance = BinanceAPI(
        api_conf["API Key"],
        api_conf["Secret Key"],
        verbosity=0,
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
    # pprint.pprint(instance.buy("BTCUSDT", quantity=None, value=20, limit_price=None))    # 现货买入 (市价买入$20BTC)
    # pprint.pprint(instance.sell("BTCUSDT", quantity=None, value=None, limit_price=None))    # 现货卖出 (市价卖出所有BTC)

    # 定期打印账户价值
    while True:
        print(utils.tic2time(time.time()))
        err, d = instance.get_account_value()    # 获取账户剩余价值
        if err is None:
            pprint.pprint(d)
        time.sleep(60)
