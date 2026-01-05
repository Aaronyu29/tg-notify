# 实时价格监控器使用指南

## 功能说明

这是一个结合 WebSocket 实时数据和 Alert Generator 规则系统的监控器，可以：

- ✅ 实时监听 Binance 永续合约价格
- ✅ 根据配置文件中的规则自动检测暴涨暴跌
- ✅ 自动发送告警到 FWAlert
- ✅ 支持多个时间窗口和阈值
- ✅ 防止重复告警（冷却机制）

## 快速开始

### 1. 配置告警规则

编辑 `monitor_config.py` 文件：

```python
ALERT_RULES = [
    # 5分钟暴涨 30%
    {
        "name": "5分钟暴涨30%",
        "window_minutes": 5,
        "threshold": 30.0,
        "direction": "up",      # up=暴涨, down=暴跌
        "priority": "high"      # normal/high/critical
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

### 2. 配置 FWAlert URL

在 `.env` 文件中添加：

```bash
FWALERT_URL=https://fwalert.com/your-webhook-id
```

### 3. 运行监控器

```bash
# 使用配置文件版本（推荐）
python realtime_monitor_v2.py

# 或使用简单版本（固定 5 分钟窗口）
python realtime_monitor.py
```

## 配置说明

### monitor_config.py

```python
# 采样间隔（秒）- 建议 60 秒
SAMPLE_INTERVAL = 60

# 告警冷却时间（秒）- 防止同一币种频繁告警
ALERT_COOLDOWN = 900  # 15分钟

# Top N 显示数量
TOP_N_DISPLAY = 5
```

### 规则配置参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `name` | 规则名称 | "5分钟暴涨30%" |
| `window_minutes` | 时间窗口（分钟） | 5, 10, 15, 30 |
| `threshold` | 阈值（百分比） | 30.0, 50.0 |
| `direction` | 方向 | "up"（暴涨）或 "down"（暴跌） |
| `priority` | 优先级 | "normal", "high", "critical" |

## 使用示例

### 示例 1: 监控 5 分钟暴涨暴跌 30%

```python
ALERT_RULES = [
    {
        "name": "5分钟暴涨30%",
        "window_minutes": 5,
        "threshold": 30.0,
        "direction": "up",
        "priority": "high"
    },
    {
        "name": "5分钟暴跌30%",
        "window_minutes": 5,
        "threshold": 30.0,
        "direction": "down",
        "priority": "high"
    },
]
```

### 示例 2: 多时间窗口监控

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

    # 15分钟暴涨 50%
    {
        "name": "15分钟暴涨50%",
        "window_minutes": 15,
        "threshold": 50.0,
        "direction": "up",
        "priority": "critical"
    },

    # 10分钟暴跌 20%
    {
        "name": "10分钟暴跌20%",
        "window_minutes": 10,
        "threshold": 20.0,
        "direction": "down",
        "priority": "high"
    },
]
```

### 示例 3: 不同优先级

```python
ALERT_RULES = [
    # 普通告警
    {
        "name": "15分钟涨20%",
        "window_minutes": 15,
        "threshold": 20.0,
        "direction": "up",
        "priority": "normal"
    },

    # 高优先级
    {
        "name": "10分钟涨30%",
        "window_minutes": 10,
        "threshold": 30.0,
        "direction": "up",
        "priority": "high"
    },

    # 紧急告警
    {
        "name": "5分钟涨50%",
        "window_minutes": 5,
        "threshold": 50.0,
        "direction": "up",
        "priority": "critical"
    },
]
```

## 运行效果

启动后会看到：

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
      🚀 BNBUSDT: +1.45%
      🚀 SOLUSDT: +3.21%
      📉 ADAUSDT: -0.95%
  ✅ 暂无币种触发告警阈值
```

当检测到暴涨暴跌时：

```
[ALERT] BNBUSDT: +35.20% - 5分钟暴涨30%
  🚨 已发送 1 条告警
```

## 告警消息格式

发送到 FWAlert 的消息格式：

```
🚀 BNBUSDT 5分钟暴涨30%
涨跌幅: +35.20%
当前价格: $650.5
5分钟前: $481.2
检测时间: 21:35:00
```

## 文件说明

| 文件 | 说明 |------|
| `realtime_monitor.py` | 简单版本，固定 5 分钟窗口 |
| `realtime_monitor_v2.py` | 配置文件版本（推荐） |
| `monitor_config.py` | 配置文件 |
| `alert_generator.py` | 告警生成器核心 |

## 工作原理

1. **WebSocket 连接**: 连接到 Binance WebSocket，实时接收所有 USDT 永续合约价格
2. **定时采样**: 每 60 秒采样一次当前价格，保存到历史队列
3. **规则检查**: 每次采样后，检查所有币种是否满足配置的规则
4. **发送告警**: 满足条件时，通过 alert_generator 发送到 FWAlert
5. **冷却机制**: 同一币种同一规则在 15 分钟内只告警一次

## 注意事项

1. **历史数据积累**: 需要等待足够的历史数据才能开始检测（例如 5 分钟窗口需要等待 6 分钟）
2. **采样间隔**: 建议设置为 60 秒，太短会增加计算负担，太长会降低精度
3. **冷却时间**: 防止同一币种频繁告警，建议设置为 15 分钟
4. **网络连接**: 需要稳定的网络连接，断线会自动重连

## 故障排查

### 未收到告警

1. 检查 `FWALERT_URL` 是否正确配置
2. 检查规则阈值是否设置过高
3. 查看控制台是否有 `[ALERT]` 日志
4. 确认历史数据已积累足够

### WebSocket 断线

- 程序会自动重连，等待 5 秒后重试
- 检查网络连接是否稳定

### 告警过多

- 调高阈值
n- 减少规则数量

## 高级用法

### 结合 Telegram 通知

修改 `alert_generator.py`，在发送 FWAlert 的同时发送 Telegram：

```python
from notify_client import notify

# 在 send_alert 方法中添加
notify(
    title=f"价格告警",
    message=message,
    channel="price",
    priority="high"
)
```

### 自定义过滤

在 `_handle_message` 方法中添加过滤逻辑：

```python
# 只监控特定币种
WATCH_LIST = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

if symbol not in WATCH_LIST:
    continue
```

## 性能优化

- 默认监控所有 USDT 永续合约（约 200+ 个）
- 内存占用约 50-100MB
- CPU 占用很低（< 5%）
- 建议在服务器上长期运行

## License

MIT
