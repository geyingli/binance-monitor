# 模拟交易，回测及跟踪真实行情

import os
import pprint
import pygame
import matplotlib.pyplot as plt

from abc import abstractmethod
from bayes_opt import BayesianOptimization

import data_loader
import utils

LONG_FRICTION = 0.001    # 0.1%做多手续费
SHORT_FRICTION = 0.001    # 0.1%做空手续费
SLIDING_FRICTION = 0.001    # 滑价比例
INTRERST_RATE = 0.14    # 借款年利率


class Account:
    """账户管理"""
    pass


class MockAccount(Account):
    """模拟账户"""

    def __init__(self, init_balance=10000, basic_currency="USDT"):
        self.init_balance = init_balance    # 初始余额
        self.basic_currency = basic_currency    # 基础货币(一键平仓时将自动将资产出售为该货币)
        self.initialize()

    def initialize(self):
        """初始化账户"""
        self.account_info = {
            "assets": {
                self.basic_currency: {
                    "position": "LONG",
                    "price": 1.0,
                    "limit_profit_price": None,
                    "limit_loss_price": None,
                    "quantity": self.init_balance,
                    "value": self.init_balance,
                },
            },
            "value": self.init_balance,
        }

        self.lost_connection = False    # 是否断开网络连接
        self.last_prices = {}    # 最新的全局价格

    def update(self, tic, prices):
        """更新各项数据，包括自动触发止盈止损，及利息扣除"""

        # 处理最新数据
        self.last_prices = {}
        for symbol_info in prices:

            # 更新价格
            symbol = symbol_info["symbol"]
            price = symbol_info["price"]
            self.last_prices[symbol] = price

            # 更新账户信息
            asset = symbol.replace(self.basic_currency, "")
            if asset not in self.account_info["assets"]:
                continue
            self.account_info["assets"][asset]["price"] = price
            self.account_info["assets"][asset]["value"] = self.account_info["assets"][asset]["quantity"] * price
        self.account_info["value"] = sum([self.account_info["assets"][asset]["value"] for asset in self.account_info["assets"]])

        # 自动触发
        for asset in list(self.account_info["assets"].keys()):
            if asset == self.basic_currency:
                continue
            symbol = asset + self.basic_currency
            price = self.last_prices[symbol]
            position = self.account_info["assets"][asset]["position"]
            limit_profit_price = self.account_info["assets"][asset]["limit_profit_price"]
            limit_loss_price = self.account_info["assets"][asset]["limit_loss_price"]

            # 止盈
            if limit_profit_price and ((position == "LONG" and price >= limit_profit_price) or (position == "SHORT" and price <= limit_profit_price)):
                self.close(symbol, limit_profit_price, 1.0)
                continue

            # 止损
            if limit_loss_price and ((position == "LONG" and price <= limit_loss_price) or (position == "SHORT" and price >= limit_loss_price)):
                self.close(symbol, limit_loss_price, 1.0)
                continue

            # 利息扣除
            if position == "SHORT":
                interest = INTRERST_RATE / 365 / 24 / 60 * self.account_info["assets"][asset]["value"]
                if self.account_info["assets"][self.basic_currency]["value"] > interest:
                    self.account_info["assets"][self.basic_currency]["quantity"] -= interest
                    self.account_info["assets"][self.basic_currency]["value"] -= interest
                else:
                    value = interest / (1 - LONG_FRICTION)
                    self.account_info["assets"][asset]["quantity"] *= (self.account_info["assets"][asset]["value"] - value) / self.account_info["assets"][asset]["value"]
                    self.account_info["assets"][asset]["value"] -= value

    def long(self, symbol, quantity=None, value=None, limit_price=None, limit_profit_ratio=None, limit_loss_ratio=None):
        """做多"""

        if quantity is not None or value is None:
            return
        if value is None:
            if self.basic_currency not in self.account_info["assets"]:
                return
            value = self.account_info["assets"][self.basic_currency]["value"]
            if value < 10:
                return
        if limit_price is None:
            trading_price = self.last_prices[symbol] * (1 + SLIDING_FRICTION)
        else:
            trading_price = limit_price
        trading_value = value * (1 - LONG_FRICTION)
        trading_quantity = trading_value / trading_price

        asset = symbol.replace(self.basic_currency, "")
        if asset not in self.account_info["assets"]:
            self.account_info["assets"][self.basic_currency]["quantity"] -= value
            self.account_info["assets"][self.basic_currency]["value"] -= value
            self.account_info["assets"][asset] = {
                    "position": "LONG",
                    "price": trading_price,
                    "limit_profit_price": None,
                    "limit_loss_price": None,
                    "quantity": trading_quantity,
                    "value": trading_value,
            }
        elif self.account_info["assets"][asset]["position"] == "SHORT":
            if self.account_info["assets"][asset]["value"] < trading_value:
                compl_quantity = self.account_info["assets"][asset]["quantity"]
                compl_value = self.account_info["assets"][asset]["value"]
                self.account_info["assets"][self.basic_currency]["quantity"] += compl_value
                self.account_info["assets"][self.basic_currency]["value"] += compl_value
                self.account_info["assets"][asset]["position"] = "LONG"
                self.account_info["assets"][self.basic_currency]["quantity"] -= value - compl_value
                self.account_info["assets"][self.basic_currency]["value"] -= value - compl_value
                self.account_info["assets"][asset]["quantity"] = trading_quantity - compl_quantity
                self.account_info["assets"][asset]["value"] = trading_value - compl_value
            elif self.account_info["assets"][asset]["value"] > trading_value:
                self.account_info["assets"][asset]["quantity"] -= trading_quantity
                self.account_info["assets"][asset]["value"] -= value
                self.account_info["assets"][self.basic_currency]["quantity"] += trading_value
                self.account_info["assets"][self.basic_currency]["value"] += trading_value
            else:
                self.account_info["assets"].pop(asset)
                self.account_info["assets"][self.basic_currency]["quantity"] += trading_value
                self.account_info["assets"][self.basic_currency]["value"] += trading_value
        else:
            self.account_info["assets"][self.basic_currency]["quantity"] -= value
            self.account_info["assets"][self.basic_currency]["value"] -= value
            self.account_info["assets"][asset]["quantity"] += trading_quantity
            self.account_info["assets"][asset]["quantity"] += trading_value

        if limit_profit_ratio is not None:
            self.account_info["assets"][asset]["limit_profit_price"] = trading_price * (1 + limit_profit_ratio)
        if limit_loss_ratio is not None:
            self.account_info["assets"][asset]["limit_loss_price"] = trading_price * (1 - limit_loss_ratio)

    def short(self, symbol, quantity=None, value=None, limit_price=None, limit_profit_ratio=None, limit_loss_ratio=None):
        """做空"""

        if quantity is not None or value is None:
            return
        if value is None:
            if self.basic_currency not in self.account_info["assets"]:
                return
            value = self.account_info["assets"][self.basic_currency]["value"]
            if value < 10:
                return
        if limit_price is None:
            trading_price = self.last_prices[symbol] * (1 - SLIDING_FRICTION)
        else:
            trading_price = limit_price
        trading_value = value * (1 - SHORT_FRICTION)
        trading_quantity = trading_value / trading_price

        asset = symbol.replace(self.basic_currency, "")
        if asset not in self.account_info["assets"]:
            self.account_info["assets"][self.basic_currency]["quantity"] -= value
            self.account_info["assets"][self.basic_currency]["value"] -= value
            self.account_info["assets"][asset] = {
                    "position": "SHORT",
                    "price": trading_price,
                    "quantity": trading_quantity,
                    "value": trading_value,
            }
        elif self.account_info["assets"][asset]["position"] == "LONG":
            if self.account_info["assets"][asset]["value"] < trading_value:
                compl_quantity = self.account_info["assets"][asset]["quantity"]
                compl_value = self.account_info["assets"][asset]["value"]
                self.account_info["assets"][self.basic_currency]["quantity"] += compl_value
                self.account_info["assets"][self.basic_currency]["value"] += compl_value
                self.account_info["assets"][asset]["position"] = "SHORT"
                self.account_info["assets"][self.basic_currency]["quantity"] -= value - compl_value
                self.account_info["assets"][self.basic_currency]["value"] -= value - compl_value
                self.account_info["assets"][asset]["quantity"] = trading_quantity - compl_quantity
                self.account_info["assets"][asset]["value"] = trading_value - compl_value
            elif self.account_info["assets"][asset]["value"] > trading_value:
                self.account_info["assets"][asset]["quantity"] -= trading_quantity
                self.account_info["assets"][asset]["value"] -= value
                self.account_info["assets"][self.basic_currency]["quantity"] += trading_value
                self.account_info["assets"][self.basic_currency]["value"] += trading_value
            else:
                self.account_info["assets"].pop(asset)
                self.account_info["assets"][self.basic_currency]["quantity"] += trading_value
                self.account_info["assets"][self.basic_currency]["value"] += trading_value
        else:
            self.account_info["assets"][self.basic_currency]["quantity"] -= value
            self.account_info["assets"][self.basic_currency]["value"] -= value
            self.account_info["assets"][asset]["quantity"] += trading_quantity
            self.account_info["assets"][asset]["quantity"] += trading_value

        if limit_profit_ratio is not None:
            self.account_info["assets"][asset]["limit_profit_price"] = trading_price * (1 - limit_profit_ratio)
        if limit_loss_ratio is not None:
            self.account_info["assets"][asset]["limit_loss_price"] = trading_price * (1 + limit_loss_ratio)

    def close(self, symbol, limit_price=None, percentage=1.0):
        """平仓"""
        asset = symbol.replace(self.basic_currency, "")
        value = self.account_info["assets"][asset]["value"] * percentage

        position = self.account_info["assets"][asset]["position"]
        if position == "LONG":
            if limit_price is None:
                trading_price = self.account_info["assets"][asset]["price"] * (1 + SLIDING_FRICTION)
            else:
                trading_price = limit_price
            trading_value = value * (1 - SHORT_FRICTION)
        else:
            if limit_price is None:
                trading_price = self.account_info["assets"][asset]["price"] * (1 - SLIDING_FRICTION)
            else:
                trading_price = limit_price
            trading_value = value * (1 - LONG_FRICTION)
        trading_quantity = trading_value / trading_price

        if percentage == 1.0:
            self.account_info["assets"].pop(asset)
        else:
            self.account_info["assets"][asset]["value"] -= value
            self.account_info["assets"][asset]["quantity"] -= trading_quantity
        self.account_info["assets"][self.basic_currency]["quantity"] += trading_value
        self.account_info["assets"][self.basic_currency]["value"] += trading_value

    def close_all(self):
        """无条件全部平仓"""
        for asset in list(self.account_info["assets"].keys()):
            if asset == self.basic_currency:
                continue
            symbol = asset + self.basic_currency
            self.close(symbol)


class Strategy:
    """策略基类，实现一些基础方法"""

    # 贝叶斯优化，超参数及边界
    BAYSIAN_OPT_BOUNDS = {}

    def __init__(self):
        self.output_dir = None
        self.init_balance = None

    def update_params(self, **kwargs):
        """更新参数"""
        for arg, value in kwargs.items():
            self.__setattr__(arg, value)

    def baysian_optimize(self):
        """贝叶斯优化，自动寻找最优超参数"""

        def f(**kwargs):
            self.update_params(**kwargs)
            return self.back_test()[0]    # 第一个元素作为优化项
        optimizer = BayesianOptimization(
            f=f,
            pbounds=self.BAYSIAN_OPT_BOUNDS,
            random_state=1,
        )
        try:
            optimizer.maximize(init_points=5, n_iter=20)
            return None, optimizer.max
        except Exception as e:
            return "贝叶斯优化失败: %s" % e, None

    @abstractmethod
    def back_test(self, *args, **kwargs):
        """回测"""
        raise NotImplementedError()

    @abstractmethod
    def implement(self, *args, **kwargs):
        """执行策略"""
        raise NotImplementedError()


class Momentum(Strategy):
    """对价量进行监控，跟随突增交易趋势"""

    # 贝叶斯优化，超参数及边界
    BAYSIAN_OPT_BOUNDS = {
        "volume_break_out_ratio": (10, 30),
        "limit_profit_ratio": (0.1, 0.5),
        "limit_loss_ratio": (0.1, 0.1),
    }

    def __init__(
        self,
        symbol,                                 # 资产名称
        tics,                                   # 时间戳
        prices,                                 # 价格
        volumes,                                # 交易额
        basic_currency="USDT",                  # 以美元为基准的稳定币
        volume_break_out_thresh=1000000,        # 超出多少交易额认定为有效交易额突增
        volume_break_out_ratio=10,               # 超出均交易额多大比例认为交易额突增
        volume_per_asset=0.10,                  # 每种资产的初始持仓比例
        limit_profit_ratio=0.20,                 # 盈利多少倍，进行止盈
        limit_loss_ratio=0.10,                   # 亏损多少倍，进行止损
    ):
        self.asset = symbol.replace(basic_currency, "")
        self.symbol = symbol
        self.basic_currency = basic_currency
        self.tics = tics
        self.prices = prices
        self.volumes = volumes
        self.volume_break_out_thresh = volume_break_out_thresh
        self.volume_break_out_ratio = volume_break_out_ratio
        self.volume_per_asset = volume_per_asset
        self.limit_profit_ratio = limit_profit_ratio
        self.limit_loss_ratio = limit_loss_ratio

        self.ma_7m_price = data_loader.get_moving_average(prices, "7m")[-1]    # 7分钟滑动平均价
        self.ma_7h_price = data_loader.get_moving_average(prices, "7h")[-1]    # 7小时滑动平均价
        self.ma_7h_volume = data_loader.get_moving_average(volumes, "7h")[-1]    # 7日滑动平均交易额
        self.ma_7d_price = data_loader.get_moving_average(prices, "7d")[-1]    # 7日滑动平均价
        self.ma_7d_volume = data_loader.get_moving_average(volumes, "7d")[-1]    # 7日滑动平均交易额

    def update(self, tic, price, volume):
        """更新最新数据"""
        self.ma_7m_price += price / 7 - self.prices[-7] / 7
        self.ma_7h_price += price / 420 - self.prices[-420] / 420
        self.ma_7h_volume += volume / 420 - self.volumes[-420] / 420
        self.ma_7d_price += price / 10080 - self.prices[-10080] / 10080
        self.ma_7d_volume += volume / 10080 - self.volumes[-10080] / 10080
        self.tics.append(tic)
        self.prices.append(price)
        self.volumes.append(volume)
        self.tics.pop(0)
        self.prices.pop(0)
        self.volumes.pop(0)

    def implement(self, lag):
        """执行监控，同类提示每10分钟最多一次"""

        global last_close_all

        # 平多：一定时间内BTC价格下跌1%
        if self.symbol == "BTC" + self.basic_currency:
            for i in range(1, 10):
                if self.prices[-1] > self.prices[-1-i] * 0.99:
                    continue
                context = "%s分钟内价格下跌%.1f%%" % (
                    i,
                    (1 - self.prices[-1] / self.prices[-1-i]) * 100,
                )
                self.close_all(context)
                last_close_all = self.tics[-1]
                return

        # 数据延期不高
        if lag > 2:
            return

        # 账户拥有足额稳定币
        balance = 0
        if self.basic_currency in account.account_info["assets"]:
            balance = account.account_info["assets"][self.basic_currency]["value"]    # 可交易稳定币余额
        trading_volume = max(account.account_info["value"] * self.volume_per_asset, 1000)    # 开仓金额
        if balance < trading_volume:
            return

        # 账户当前不持有该币种
        if self.asset in account.account_info["assets"] and account.account_info["assets"][self.asset]["value"] > 10:
            return

        # 距离上一次BTC快速下跌不足6小时
        # if self.tics[-1] - last_close_all < 6 * 60 * 60 * data_loader.TIMESTAMP_UNIT:
        #     return

        # 做多：突破7天/7小时均交易额一定倍数，且在50万美元以上；价格大于7天/7小时/7分钟均价
        if (self.volumes[-1] > self.ma_7d_volume * self.volume_break_out_ratio and self.volumes[-1] > self.ma_7h_volume * self.volume_break_out_ratio) and \
                (self.prices[-1] > self.ma_7d_price and self.prices[-1] > self.ma_7h_price and self.prices[-1] > self.ma_7m_price) and self.volumes[-1] > self.volume_break_out_thresh:
            context = "交易额突增%.1f倍 ($%d万)" % (
                self.volumes[-1] / self.ma_7h_volume - 1,
                int(self.volumes[-1]/10000),
            )
            self.long(context, trading_volume)
            return

        # 做多：一定时间内价格上涨5%
        for i in range(1, 10):
            if self.prices[-1] < self.prices[-1-i] * 1.05:
                continue
            context = "%s分钟内价格上涨%.1f%%" % (
                i,
                (self.prices[-1] / self.prices[-1-i] - 1) * 100,
            )
            self.long(context, trading_volume)
            return

    def long(self, context, trading_volume):
        """做多"""
        print("%s >>> %s, $%s, %s, 做多 ($%.1f)" % (
            utils.tic2time(self.tics[-1]),
            self.symbol,
            utils.standardize(self.prices[-1]),
            context,
            trading_volume,
        ))
        account.long(self.symbol, value=trading_volume, limit_profit_ratio=self.limit_profit_ratio, limit_loss_ratio=self.limit_loss_ratio)
        if not isinstance(account, MockAccount):
            pygame.mixer.music.play()    # 播放提示音

    def short(self, context, trading_volume):
        """做空"""
        print("%s >>> %s, $%s, %s, 做空 ($%.1f)" % (
            utils.tic2time(self.tics[-1]),
            self.symbol,
            utils.standardize(self.prices[-1]),
            context,
            trading_volume,
        ))
        account.short(self.symbol, value=trading_volume, limit_profit_ratio=self.limit_profit_ratio, limit_loss_ratio=self.limit_loss_ratio)
        if not isinstance(account, MockAccount):
            pygame.mixer.music.play()    # 播放提示音

    def close_all(self, context):
        """无条件全部平仓"""
        print("%s >>> %s, $%s, %s, 全部平仓" % (
            utils.tic2time(self.tics[-1]),
            self.symbol,
            utils.standardize(self.prices[-1]),
            context,
        ))
        account.close_all()
        if not isinstance(account, MockAccount):
            pygame.mixer.music.play()    # 播放提示音


def get_top_traded_pairs(models, n=50):
    """获取头部交易对"""
    items = [(symbol, models[symbol].ma_7d_volume) for symbol in models]
    items.sort(key=lambda x: x[1], reverse=True)
    top = [item[0] for item in items][:n]
    top = {item: 1 for item in top}
    return top


if __name__ == "__main__":

    start_timestamp = utils.time2tic(2021, 2, 23, 18, 0, 0) * data_loader.TIMESTAMP_UNIT
    end_timestamp = utils.time2tic(2021, 10, 23, 17, 59, 59) * data_loader.TIMESTAMP_UNIT
    basic_currency = "USDT"
    data_dir = ".backup/data"

    print("为所有币种创建模型...")
    models = {}
    data_iterators = {}
    for symbol in data_loader.COINS:
        file = "%s/%s.1m.data" % (data_dir, symbol)
        if not os.path.exists(file):
            continue
        data = data_loader.Data(file)    # 读取历史数据
        if data.tics[0] > start_timestamp:    # 第一条数据在开始时间以后
            continue
        t = -1
        for i in range(len(data.tics)):
            if data.tics[i] == start_timestamp:
                t = i
                break
        if t == -1:    # 无有效数据
            continue
        data.tics = data.tics[t:]
        data.prices = data.prices[t:]
        data.volumes = data.volumes[t:]
        if len(data.prices) < data_loader.DAY * 7:    # 数据不满足监控条件（需要计算滑动平均价/交易额）
            continue

        # 创建模型
        models[symbol] = Momentum(
            symbol,
            data.tics[:data_loader.DAY * 7 + 1],
            data.prices[:data_loader.DAY * 7 + 1],
            data.volumes[:data_loader.DAY * 7 + 1],
            basic_currency=basic_currency,
            volume_break_out_thresh=1000000,
            volume_break_out_ratio=10,
            volume_per_asset=0.1,
            limit_profit_ratio=0.1,
            limit_loss_ratio=0.1,
        )

        # 记录最新时间戳、价格
        tic = data.tics[data_loader.DAY * 7]
        price = data.prices[data_loader.DAY * 7]
        if symbol == "BTC" + basic_currency:
            btc_price = price

        # 创建数据迭代器，模拟获取未来数据
        data_iterators[symbol] = [
            data.tics[data_loader.DAY * 7 + 1:],
            data.prices[data_loader.DAY * 7 + 1:],
            data.volumes[data_loader.DAY * 7 + 1:],
        ]

    print("初始化模拟账户...")
    account = MockAccount(
        init_balance=btc_price,    # 方便作图，对比收益
        basic_currency=basic_currency,
    )

    print("开始执行策略...")
    pygame.mixer.init()
    pygame.mixer.music.load("refs/alarm.mp3")
    stop = False
    top = {}
    last_cal_top = -1
    last_record = -1
    last_draw = tic
    last_close_all = -1
    hold = {}
    mock_times = []
    mock_benchmark = []
    mock_values = []
    mock_values_window = []
    while True:

        # 更新模型数据
        price_list = []
        for symbol in list(models.keys()):
            model = models[symbol]
            if len(data_iterators[symbol][0]) == 0:    # 数据未下载完全/币已从交易所下线
                models.pop(symbol)
                if symbol in top:
                    top.pop(symbol)
                continue
            tic = int(data_iterators[symbol][0].pop(0))
            price = float(data_iterators[symbol][1].pop(0))
            volume = float(data_iterators[symbol][2].pop(0))
            if tic >= end_timestamp:
                print("模拟结束")
                stop = True
                break
            if symbol == "BTC" + basic_currency:
                btc_price = price
            price_list.append({
                "symbol": symbol,
                "price": price,
            })
            model.update(
                tic=tic,
                price=price,
                volume=volume,
            )
        if stop or len(models) == 0:
            break

        # 更新账户状态
        account.update(tic, price_list)
        pprint.pprint(account.account_info)
        print(utils.tic2time(tic))

        # 下跌过快则全部平仓
        # mock_values_window.append(account.account_info["value"])
        # if len(mock_values_window) > 5:
        #     mock_values_window.pop(0)
        # for i in range(1, len(mock_values_window)):
        #     if mock_values_window[-1] > mock_values_window[-1-i] * 0.98:
        #         continue
        #     account.close_all()
        #     break

        # 记录持仓，时间过久则卖出
        for asset in list(account.account_info["assets"].keys()):
            if asset == basic_currency:
                continue
            if asset not in hold:
                hold[asset] = 0
            hold[asset] += 1
            if hold[asset] > 3 * data_loader.DAY:    # 3天一次
                account.close(asset + basic_currency)
        for asset in list(hold.keys()):
            if asset not in account.account_info["assets"]:    # 已平仓
                hold.pop(asset)

        # 更新头部列表
        if tic - last_cal_top > 3 * 60 * 60 * data_loader.TIMESTAMP_UNIT:    # 3小时一次
            top = get_top_traded_pairs(models, n=50)
            last_cal_top = tic

        # 执行策略
        for symbol in top:
            models[symbol].implement(lag=0)

        # 记录价格变动
        if tic - last_record > 2 * 60 * 60 * data_loader.TIMESTAMP_UNIT:    # 2小时一次
            mock_times.append(utils.tic2time(tic))
            mock_benchmark.append(btc_price)
            mock_values.append(account.account_info["value"])
            last_record = tic

        # 作图
        if tic - last_draw > 1 * 24 * 60 * 60 * data_loader.TIMESTAMP_UNIT:    # 1天一次
            plt.figure()
            plt.plot(mock_times, mock_benchmark, color="black")
            plt.plot(mock_times, mock_values, color="orange")
            plt.savefig("mock.png")
            last_draw = tic

    # 作图
    plt.figure()
    plt.plot(mock_times, mock_benchmark, color="black")
    plt.plot(mock_times, mock_values, color="orange")
    plt.savefig("mock.png")
