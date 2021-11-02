import os
import matplotlib.pyplot as plt
import seaborn as sns

import data_loader
import utils

sns.set(color_codes=True)


def get_price_change_by_hour(data, i):
    """获取基于小时的价格变动"""
    v = data.prices[i] / data.prices[i - 1] - 1
    time_triplet = utils.tic2time(data.tics[i]).split()[-1].split(":")
    bucket_id = time_triplet[0]
    return bucket_id, v


def get_price_change_by_weekday(data, i):
    """获取基于天的价格变动"""
    v = data.prices[i] / data.prices[i - 1] - 1
    tic = data.tics[i]

    # 基于2000年1月1日 (星期六) 计算是星期几
    week_day = ((tic / 1000 - 946656000) // (24 * 60 * 60)) % 7 + 6
    if week_day > 7:
        week_day -= 7
    bucket_id = week_day
    return bucket_id, v


def get_volume_by_hour(data, i):
    """获取基于小时的交易量变动"""
    v = data.volumes[i]
    time_triplet = utils.tic2time(data.tics[i]).split()[-1].split(":")
    bucket_id = time_triplet[0]
    return bucket_id, v


def get_volume_by_weekday(data, i):
    """获取基于天的交易量变动"""
    v = data.volumes[i]
    tic = data.tics[i]

    # 基于2000年1月1日 (星期六) 计算是星期几
    week_day = ((tic / 1000 - 946656000) // (24 * 60 * 60)) % 7 + 6
    if week_day > 7:
        week_day -= 7
    bucket_id = week_day
    return bucket_id, v


def statistics(f, data, start_timestamp, end_timestamp):
    """获取排行分布"""

    # 根据计量单位分桶
    buckets = {}
    for i in range(1, len(data.prices)):
        tic = data.tics[i]
        if tic / 1000 < start_timestamp or tic / 1000 > end_timestamp:    # 超出数据范围
            continue

        # 获取bucket_id和取值
        bucket_id, v = f(data, i)

        # 注入桶中
        if bucket_id not in buckets:
            buckets[bucket_id] = []
        buckets[bucket_id].append(v)

    # 桶数据汇总
    sorting_items = []
    for bucket_id, v in buckets.items():
        v = sum(v) / len(v)    # 取均值
        sorting_items.append((bucket_id, v))

    # 排序
    indices = {}    # bucket_id -> 排名
    sorting_items.sort(key=lambda x: x[-1], reverse=True)
    for i, (bucket_id, v) in enumerate(sorting_items):
        indices[bucket_id] = 24 - i

    # 作图
    x = list(sorted(indices.keys()))
    y = [indices[bucket_id] for bucket_id in x]
    plt.plot(x, y)
    # plt.scatter(x, y)


if __name__ == "__main__":

    # 设定数据统计初始/结尾年、月、日
    start_timestamp = utils.time2tic(2021, 7, 1, 0, 0, 0)
    end_timestamp = utils.time2tic(2021, 11, 1, 23, 59, 59)

    plt.figure()
    for symbol in data_loader.COINS[:50]:

        # 读取数据
        file = ".backup/data/%s.1m.data" % symbol
        if not os.path.exists(file):
            continue
        data = data_loader.Data(file)    # 读取历史数据
        last_timestamp = data_loader.get_last_timestamp(file)
        if not last_timestamp or last_timestamp < start_timestamp:
            continue

        # statistics(get_price_change_by_hour, data, start_timestamp, end_timestamp)    # 价格变动分布 (天)
        # statistics(get_price_change_by_weekday, data, start_timestamp, end_timestamp)    # 价格变动分布 (周)
        # statistics(get_volume_by_hour, data, start_timestamp, end_timestamp)    # 交易量分布 (天)
        statistics(get_volume_by_weekday, data, start_timestamp, end_timestamp)    # 交易量分布 (周)
    plt.show()
