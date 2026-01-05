# TG Notify - 币种价格监控与告警系统

## 📁 项目结构

```
tg-notify/
├── monitor/                    # ⭐ 主监控程序目录（主要使用）
│   ├── realtime_monitor_v2.py # 主监控程序
│   ├── monitor_config.py      # 配置文件
│   ├── start_monitor.bat      # 启动脚本
│   ├── logger.py              # 日志模块
│   ├── alert_generator.py     # 告警模块
│   ├── chinese_converter.py   # 中文转换
│   ├── .env                   # 环境变量
│   ├── logs/                  # 日志目录
│   └── README.md              # 使用说明
│
├── test_alert.py              # 测试程序
├── view_logs.py               # 日志查看工具
├── LOG_USAGE.md               # 日志使用说明
├── TOP_MOVERS_UPDATE.md       # 涨跌幅榜说明
└── LOG_IMPLEMENTATION_SUMMARY.md  # 实现总结
```

## 🚀 快速开始

### 1. 进入主程序目录
```bash
cd monitor
```

### 2. 启动监控程序

**Windows 用户（推荐）：**
双击 `monitor/start_monitor.bat`

**命令行启动：**
```bash
cd monitor
python realtime_monitor_v2.py
```

## ⚙️ 配置

所有配置都在 `monitor/monitor_config.py` 中：

```python
# 告警规则
ALERT_RULES = [
    {
        "name": "5分钟暴涨15%",
        "window_minutes": 5,
        "threshold": 15.0,
        "direction": "up",
        "priority": "high"
    },
]

# 采样间隔
SAMPLE_INTERVAL = 60  # 60秒

# 告警冷却
ALERT_COOLDOWN = 900  # 15分钟

# 显示数量
TOP_N_DISPLAY = 5  # Top 5
```

## 📊 功能特性

### 实时监控
- ✅ 监控所有 Binance USDT 永续合约
- ✅ 每分钟采样价格
- ✅ 自动计算涨跌幅
- ✅ 触发告警自动通知

### 日志系统
- ✅ 自动记录到文件
- ✅ 每小时轮转
- ✅ 保留24小时
- ✅ 控制台彩色输出

### 涨跌幅榜
- ✅ 涨幅榜 Top 5
- ✅ 跌幅榜 Top 5
- ✅ 显示价格变化

### 告警通知
- ✅ 发送到 FWAlert
- ✅ JSON 格式
- ✅ 中文数字
- ✅ 防止刷屏（冷却机制）

## 📝 查看日志

```bash
# 查看当前日志
notepad monitor\logs\monitor.log

# 使用日志查看工具
python view_logs.py
```

## 📚 文档

- **`monitor/README.md`** - 主程序使用说明 ⭐
- **`LOG_USAGE.md`** - 日志系统详细说明
- **`TOP_MOVERS_UPDATE.md`** - 涨跌幅榜功能说明
- **`LOG_IMPLEMENTATION_SUMMARY.md`** - 技术实现总结

## 🎯 告警格式

```json
{
    "upOrDown": "正百分之十五点三二",
    "symbol": "BTC",
    "currentPrice": "四万五千六百点五零美元",
    "beforePrice": "三万九千五百点零零美元"
}
```

## 🔧 依赖安装

```bash
pip install websockets requests python-dotenv
```

## ⚠️ 注意事项

1. **主程序在 `monitor/` 目录** - 所有操作都在这个目录进行
2. **不要关闭终端** - 关闭后程序停止
3. **电脑不要休眠** - 休眠会暂停程序
4. **配置 .env 文件** - 设置 FWALERT_URL

## 📞 常见问题

### Q: 如何修改告警阈值？
A: 编辑 `monitor/monitor_config.py`，修改 `threshold` 值。

### Q: 如何查看历史日志？
A: 日志保存在 `monitor/logs/monitor.log`，或使用 `python view_logs.py`。

### Q: 程序可以一直运行吗？
A: 可以，只要不关闭终端窗口且电脑不休眠。

### Q: 如何停止程序？
A: 在终端按 `Ctrl+C`。

## 🎉 开始使用

```bash
# 1. 进入主程序目录
cd monitor

# 2. 配置环境变量（如果还没配置）
# 编辑 .env 文件，设置 FWALERT_URL

# 3. 启动程序
python realtime_monitor_v2.py

# 或双击 start_monitor.bat
```

---

**当前版本特性：**
- ✅ 实时价格监控
- ✅ 自动告警通知
- ✅ 日志记录系统
- ✅ 涨跌幅榜显示
- ✅ 自动重连机制
- ✅ 防刷屏冷却

**推荐配置：**
- 时间窗口：5分钟
- 告警阈值：±15%
- 采样间隔：60秒
- 告警冷却：15分钟
