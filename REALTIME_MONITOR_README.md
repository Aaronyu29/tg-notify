# 实时价格监控器 - 快速开始

## 功能

监控 Binance 永续合约价格，自动检测暴涨暴跌并发送告警到 FWAlert。

## 一分钟快速开始

### 1. 配置 FWAlert URL

在 `.env` 文件中添加：

```bash
FWALERT_URL=https://fwalert.com/your-webhook-id
```

### 2. 配置规则（可选）

编辑 `monitor_config.py`，默认规则：

```python
ALERT_RULES = [
    # 5分钟暴涨 30%
    {
        "name": "5分钟暴涨30%",
        "window_minutes": 5,
        "threshold": 30.0,
        "direction": "up",
        "priority": "high"
    },
    # 5分钟暴跌 30%
    {
        "name": "5分钟暴跌30%",
        "window_minutes": 5,
        "threshold": 30.0,
        "direction": "down",
        "priority": "high"
    },
]
```

### 3. 运行

```bash
python realtime_monitor_v2.py
```

## 告警示例

当 BNB 在 5 分钟内涨幅超过 30% 时，会自动发送：

```bash
curl --location 'https://fwalert.com/your-webhook-id' \
--header 'Content-Type: application/json' \
--data '{
    "message": "🚀 BNBUSDT 5分钟暴涨30%\n涨跌幅: +35.20%\n当前价格: $650.5\n5分钟前: $481.2\n检测时间: 21:35:00"
}'
```

## 自定义规则

### 修改阈值

```python
# 改为 20%
"threshold": 20.0,
```

### 修改时间窗口

```python
# 改为 10 分钟
"window_minutes": 10,
```

### 添加更多规则

```python
ALERT_RULES = [
    # 5分钟暴涨 30%
    {"name": "5分钟暴涨30%", "window_minutes": 5, "threshold": 30.0, "direction": "up", "priority": "high"},

    # 5分钟暴跌 30%
    {"name": "5分钟暴跌30%", "window_minutes": 5, "threshold": 30.0, "direction": "down", "priority": "high"},

    # 15分钟暴涨 50%
    {"name": "15分钟暴涨50%", "window_minutes": 15, "threshold": 50.0, "direction": "up", "priority": "critical"},

    # 10分钟暴跌 20%
    {"name": "10分钟暴跌20%", "window_minutes": 10, "threshold": 20.0, "direction": "down", "priority": "high"},
]
```

## 运行效果

```
============================================================
🔍 实时价格监控器启动
   采样间隔: 60 秒
   最大时间窗口: 5 分钟
   告警冷却: 900 秒
   规则数量: 2
============================================================

📋 加载告警规则:
  ✓ 5分钟暴涨30% (5分钟, up, high)
  ✓ 5分钟暴跌30% (5分钟, down, high)

[WS] 正在连接 Binance WebSocket...
[WS] 连接成功！

[21:30:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 采样: 245 个币种 | 历史: 6/6 分钟
  🔥 5分钟涨跌幅 Top 5:
      🚀 BTCUSDT: +2.35%
      📉 ETHUSDT: -1.82%
      🚀 BNBUSDT: +35.20% ⚠️  <- 触发告警
      🚀 SOLUSDT: +3.21%
      📉 ADAUSDT: -0.95%
  🚨 已发送 1 条告警
```

## 配置参数

在 `monitor_config.py` 中：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `SAMPLE_INTERVAL` | 60 | 采样间隔（秒） |
| `ALERT_COOLDOWN` | 900 | 告警冷却时间（秒） |
| `TOP_N_DISPLAY` | 5 | 显示 Top N |

## 文件说明

- `realtime_monitor_v2.py` - 主程序（推荐）
- `monitor_config.py` - 配置文件
- `alert_generator.py` - 告警生成器
- `REALTIME_MONITOR_GUIDE.md` - 完整文档

## 完整文档

查看 [REALTIME_MONITOR_GUIDE.md](./REALTIME_MONITOR_GUIDE.md) 获取完整文档。

## 注意事项

1. 需要等待历史数据积累（5分钟窗口需要等待 6 分钟）
2. 同一币种同一规则在 15 分钟内只告警一次
3. 需要稳定的网络连接
4. 确保 `.env` 中配置了 `FWALERT_URL`

## 停止监控

按 `Ctrl+C` 停止。
