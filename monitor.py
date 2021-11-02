# 主程序，监控市场，提供舆情提示

import os
import time
import pygame

import data_loader
import utils


class Monitor:

    def __init__(
        self,
        symbol,                                 # 资产名称
        tics,                                   # 时间戳
        prices,                                 # 价格
        volumes,                                # 交易量
        volume_ratio=10,                        # 超出均交易量多大比例认为交易量突增
    ):
        self.symbol = symbol
        self.tics = tics
        self.prices = prices
        self.volumes = volumes
        self.volume_ratio = volume_ratio
        self.last_alarm = None    # 上一次提示内容
        self.last_alarm_tic = -1    # 上一次提示时间戳 (避免同一条信息重复提醒)

        self.ma_7m_price = data_loader.get_moving_average(prices, "7m")[-1]    # 7分钟滑动平均价
        self.ma_7h_price = data_loader.get_moving_average(prices, "7h")[-1]    # 7小时滑动平均价
        self.ma_7h_volume = data_loader.get_moving_average(volumes, "7h")[-1]    # 7日滑动平均交易量
        self.ma_7d_price = data_loader.get_moving_average(prices, "7d")[-1]    # 7日滑动平均价
        self.ma_7d_volume = data_loader.get_moving_average(volumes, "7d")[-1]    # 7日滑动平均交易量

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

    def execute(self):
        """执行监控，同类提示每10分钟最多一次"""

        tic = self.tics[-1]
        price = self.prices[-1]
        volume = self.volumes[-1]

        # 突破7天/7小时均交易量一定倍数，价格大于7天/7小时/7分钟均价
        if (volume > self.ma_7d_volume * self.volume_ratio and volume > self.ma_7h_volume * self.volume_ratio) and \
                (price > self.ma_7d_price and price > self.ma_7h_price and price > self.ma_7m_price):

            if self.last_alarm != 1 or time.time() - self.last_alarm_tic > 600 and volume > 10000:
                print("%s >>> %s, $%s, 交易量突增 ($%d万)" % (
                    utils.tic2time(tic),
                    self.symbol,
                    utils.standardize(price),
                    int(volume/10000),
                ))
                pygame.mixer.music.play()    # 播放提示音
                self.last_alarm = 1
                self.last_alarm_tic = time.time()
            return

        # 一定时间内价格上涨5%
        for i in range(1, 10):
            if price < self.prices[-1-i] * 1.05:
                continue

            if self.last_alarm != 1 or time.time() - self.last_alarm_tic > 600:
                print("%s >>> %s, $%s, %s分钟内价格上涨5%%" % (
                    utils.tic2time(tic),
                    self.symbol,
                    utils.standardize(price),
                    i,
                ))
                pygame.mixer.music.play()    # 播放提示音
                self.last_alarm = 1
                self.last_alarm_tic = time.time()
            return

        # 一定时间内价格下跌1%
        if self.symbol not in {"BTCUSDT"}:
            return
        for i in range(1, 10):
            if price > self.prices[-1-i] * 0.99:
                continue

            if self.last_alarm != -1 or time.time() - self.last_alarm_tic > 600:
                print("%s >>> %s, $%s, %s分钟内价格下跌1%%" % (
                    utils.tic2time(tic),
                    self.symbol,
                    utils.standardize(price),
                    i,
                ))
                pygame.mixer.music.play()    # 播放提示音
                self.last_alarm = -1
                self.last_alarm_tic = time.time()
            return


if __name__ == "__main__":

    print("更新所有币种最新数据...")
    data_loader.update_data_all()

    print("为所有币种创建监控...")
    monitors = {}
    last_timestamps = {}
    for coin in data_loader.COINS:
        file = "data/%s.1m.data" % coin
        if not os.path.exists(file):
            continue
        data = data_loader.Data(file)    # 读取历史数据
        if len(data.prices) < data_loader.DAY * 7:    # 数据不满足监控条件（需要计算滑动平均价/交易量）
            continue
        monitors[coin] = Monitor(    # 创建模型
            coin,
            data.tics[-data_loader.DAY*7:],
            data.prices[-data_loader.DAY*7:],
            data.volumes[-data_loader.DAY*7:],
            volume_ratio=10,
        )
        last_timestamps[coin] = data.tics[-1]

    print("计算头部交易量币种...")
    items = [(coin, monitors[coin].ma_7d_volume) for coin in monitors]
    items.sort(key=lambda x: x[1], reverse=True)
    top100 = {}
    for i, item in enumerate(items[:100]):
        coin = item[0]
        mean_volume = item[1]
        print("No.%d %s $%d" % (i + 1, coin, mean_volume))
        top100[coin] = 1

    print("开始执行价量监控...")
    pygame.mixer.init()
    pygame.mixer.music.load("refs/alarm.mp3")
    while True:

        # 监控上涨
        for coin, monitor in monitors.items():

            # 非头部100交易量币种，不参与考量
            if coin not in top100:
                continue

            # 实时更新最新数据
            time.sleep(1.5)    # 避免频繁请求币安API，低于1.5秒可能会触发币安的流量管控
            latest_data = data_loader.get_latest_data(coin, "1m", last_timestamps[coin] + 1, verbosity=0)
            if len(latest_data) == 0:    # 未能获得最新数据
                continue
            for item in latest_data:
                monitor.update(
                    tic=float(item[0]),
                    price=float(item[4]),
                    volume=float(item[7]),
                )
                monitor.execute()
            last_timestamps[coin] = int(latest_data[-1][0])
