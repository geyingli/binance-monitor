## 介绍量化

本仓库提供了基于币安 (Binance) 的二级市场舆情系统，可以根据自己的需求设定各类告警提示

## 代码结构

- binance.py - 与币安API交互
- data_loader.py - 数据相关的读写
- monitor.py - 监控的核心方法实现
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
    "API Key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "Secret Key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

通过 `python3 monitor.py` 指令运行监控程序。稍等历史价量数据下载完成后，可以看到类似于以下的打印信息：

```
开始执行价量监控...
2021年11月2日 12:25:00 >>> ANKRUSDT, $0.1610, 7分钟内价格上涨5%
2021年11月2日 12:30:00 >>> SUPERUSDT, $1.202, 交易量突增
2021年11月2日 12:39:00 >>> ANKRUSDT, $0.1615, 9分钟内价格上涨5%
```

## 未来计划

增加数据分析脚本，从数据中获取更丰富的insight
