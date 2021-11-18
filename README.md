## 介绍

本仓库提供了基于币安 (Binance) 的二级市场行情系统，可以根据自己的需求修改代码，设定各类告警提示

## 代码结构

- binance.py - 与币安API交互
- data_loader.py - 数据相关的读写
- monitor.py - 监控的核心方法实现
- analyze.py - 基于历史数据进行数据分析
- utils.py - 通用函数
- alarm.mp3 - 监控提示音，可以使用同名的其他mp3文件代替

## 使用说明

下载本仓库：

```shell
git clone https://github.com/geyingli/binance-monitor.git
cd binance-monitor
```

前往[币安官网](https://www.binance.com/zh-CN)注册账号，在API管理页面获取API Key和Secret Key，在本目录下新建 `api.conf` 文件并按如下格式填写 (json规范)：

```json
{
    "API Key": "XXX",
    "Secret Key": "XXX"
}
```

通过 `python3 monitor.py` 指令运行监控程序。稍等历史价量数据下载完成后，可以看到类似于以下的打印信息：

```
开始执行价量监控...
2021年11月5日 21:22:55 --- 价格指数, 0.999
2021年11月5日 21:30:00 >>> ONTUSDT, $1.154, 交易额突增27.7倍 ($52万)
2021年11月5日 21:33:12 --- 价格指数, 0.999
2021年11月5日 21:43:21 --- 价格指数, 1.002
2021年11月5日 21:44:00 >>> NEARUSDT, $10.86, 交易额突增53.3倍 ($161万)
2021年11月5日 21:54:03 --- 价格指数, 1.001
2021年11月5日 22:04:30 --- 价格指数, 1.000
2021年11月5日 22:13:00 >>> LRCUSDT, $1.307, 8分钟内价格上涨5.1%
2021年11月5日 22:15:19 --- 价格指数, 0.999
2021年11月5日 22:25:52 --- 价格指数, 0.999
2021年11月5日 22:36:51 --- 价格指数, 0.995
2021年11月5日 22:37:00 >>> LRCUSDT, $1.335, 6分钟内价格上涨5.2%
2021年11月5日 22:42:00 >>> XTZUSDT, $6.71, 交易额突增13.6倍 ($45万)
```

\*\*注\*\* 本仓库实现了在检测到BTC大跌时 (10分钟内下跌幅度超过1%)，自动一键平仓，如需取消该设定请前往`monitor.py`注释相关代码

## 数据分析

分享一些我们在数据分析上获取的有意思的观察

#### 价格变动 (以天为周期)

我们取了头部的几十个币种，按每分钟价格涨跌百分比绘制了如下图形。可以看出，北京时间14~19点价格走势普遍偏弱 (因为这个时间美国人在睡觉?)，而晚上23点和早上5点则是涨幅分布更密集的时间

![price_change_by_day](./refs/price_change_by_day.png)

#### 价格变动 (以周为周期)

同样，我们从周一到周天的粒度对涨幅进行统计，可以看出，周五是上涨最多见的一天，跌幅第一则以周日最为显著

![price_change_by_weekday](./refs/price_change_by_weekday.png)

#### 交易额变动 (以天为周期)

下午15点开始到凌晨1点是交易额最高的一段时间

![volume_by_day](./refs/volume_by_day.png)

#### 交易额变动 (以周为周期)

从周一到周日的视角，周六和周日的交易额最低，而周三的平均交易额最高

![volume_by_weekday](./refs/volume_by_weekday.png)