# 价格阈值报警功能使用指南

## 功能概述

价格阈值报警功能允许你监控指定币种的价格，当价格突破或跌破设定的阈值时，自动发送报警消息到 fwalert。

## 核心特性

### 1. 灵活配置
- 支持多个币种同时监控
- 支持"突破"和"跌破"两种方向
- 可自定义报警优先级

### 2. 智能防重复
- **触发状态记录**：首次触发后立即报警，价格在阈值附近波动不会重复报警
- **状态自动重置**：价格恢复到阈值另一侧后，重置触发状态，允许下次触发
- **冷却时间机制**：即使价格反复跨越阈值，也会有冷却期（默认1小时）

### 3. 实时监控
- 基于 WebSocket 实时价格数据
- 每30秒检查一次（与采样间隔一致）
- 与涨跌幅监控并行运行

## 配置方法

### 1. 配置 Webhook（可选）

如果你想让价格阈值报警发送到不同的 webhook，编辑 `monitor/.env` 文件：

```bash
# 默认 webhook（用于涨跌幅报警）
FWALERT_URL=https://fwalert.com/your-default-webhook-id

# 价格阈值报警专用 webhook（可选）
PRICE_THRESHOLD_WEBHOOK_URL=https://fwalert.com/your-threshold-webhook-id
```

**说明：**
- 如果不配置 `PRICE_THRESHOLD_WEBHOOK_URL`，价格阈值报警会使用默认的 `FWALERT_URL`
- 如果配置了 `PRICE_THRESHOLD_WEBHOOK_URL`，价格阈值报警会发送到独立的 webhook
- 这样可以将不同类型的报警分开处理

### 2. 编辑配置文件

打开 `monitor/monitor_config.py`，找到 `PRICE_THRESHOLD_RULES` 配置：

```python
PRICE_THRESHOLD_RULES = [
    # BNB 跌破 800
    {
        "symbol": "BNBUSDT",
        "threshold": 800.0,
        "direction": "below",
        "priority": "high"
    },

    # BTC 突破 100000
    {
        "symbol": "BTCUSDT",
        "threshold": 100000.0,
        "direction": "above",
        "priority": "high"
    },

    # ETH 跌破 3000
    {
        "symbol": "ETHUSDT",
        "threshold": 3000.0,
        "direction": "below",
        "priority": "high"
    },
]
```

### 2. 配置参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `symbol` | 币种符号（必须以USDT结尾） | `"BNBUSDT"`, `"BTCUSDT"` |
| `threshold` | 阈值价格 | `800.0`, `100000.0` |
| `direction` | 方向：`"above"` 突破，`"below"` 跌破 | `"below"`, `"above"` |
| `priority` | 优先级：`"normal"`, `"high"`, `"critical"` | `"high"` |

### 3. 调整冷却时间

如果需要修改冷却时间，编辑配置文件中的：

```python
# 价格阈值报警冷却时间（秒）
PRICE_THRESHOLD_COOLDOWN = 3600  # 1小时
```

## 报警逻辑详解

### 触发机制

```
价格 > 阈值 → 触发 "above" 规则
价格 < 阈值 → 触发 "below" 规则
```

### 防重复逻辑

```
1. 首次触发：
   价格跌破 800 → 立即报警 ✓ → 标记为"已触发"

2. 价格在阈值附近波动：
   价格 795 → 不报警（已触发）
   价格 798 → 不报警（已触发）
   价格 792 → 不报警（已触发）

3. 价格恢复：
   价格 805 → 重置触发状态

4. 再次触发：
   价格跌破 800 → 检查冷却时间
   - 如果距离上次报警 < 1小时 → 不报警
   - 如果距离上次报警 >= 1小时 → 报警 ✓
```

### 报警消息格式

发送到 fwalert 的 JSON 格式：

```json
{
    "type": "price_threshold",
    "symbol": "BNB",
    "direction": "跌破",
    "threshold": "八百",
    "currentPrice": "七百九十五点五"
}
```

## 使用示例

### 示例 1：监控 BNB 跌破 800

```python
{
    "symbol": "BNBUSDT",
    "threshold": 800.0,
    "direction": "below",
    "priority": "high"
}
```

**场景：**
- BNB 价格从 850 跌到 795
- 系统检测到价格 < 800
- 发送报警：`BNB 跌破 800，当前价格 795`

### 示例 2：监控 BTC 突破 100000

```python
{
    "symbol": "BTCUSDT",
    "threshold": 100000.0,
    "direction": "above",
    "priority": "critical"
}
```

**场景：**
- BTC 价格从 98000 涨到 100500
- 系统检测到价格 > 100000
- 发送报警：`BTC 突破 100000，当前价格 100500`

### 示例 3：同时监控多个阈值

```python
PRICE_THRESHOLD_RULES = [
    # BNB 的两个阈值
    {
        "symbol": "BNBUSDT",
        "threshold": 800.0,
        "direction": "below",
        "priority": "high"
    },
    {
        "symbol": "BNBUSDT",
        "threshold": 1000.0,
        "direction": "above",
        "priority": "high"
    },
]
```

## 运行监控

### 启动监控器

```bash
cd monitor
python realtime_monitor_v2.py
```

### 测试报警功能

```bash
cd monitor
python test_price_threshold.py
```

## 日志输出

### 启动时

```
✓ 价格阈值报警使用独立 Webhook: https://fwalert.com/your-threshold-webhook-id...
📋 加载价格阈值规则:
  ✓ BNBUSDT 跌破 $800.0 (high)
  ✓ BTCUSDT 突破 $100000.0 (high)
```

或者（如果未配置独立 webhook）：

```
✓ 价格阈值报警使用默认 Webhook
📋 加载价格阈值规则:
  ✓ BNBUSDT 跌破 $800.0 (high)
  ✓ BTCUSDT 突破 $100000.0 (high)
```

### 触发报警时

```
[价格阈值报警] BNBUSDT: 跌破 $800.0, 当前价格 $795.5
告警详情: {"type": "price_threshold", "symbol": "BNB", "direction": "跌破", "threshold": "八百", "currentPrice": "七百九十五点五"}
```

### 状态重置时

```
[价格阈值] BNBUSDT 价格已恢复，重置触发状态
```

### 冷却期提示

```
[价格阈值] BNBUSDT 冷却期已过，重新报警
```

## 常见问题

### Q1: 为什么价格跨越阈值后没有报警？

**可能原因：**
1. 还在冷却期内（默认1小时）
2. 价格已经触发过，且未恢复到阈值另一侧

**解决方法：**
- 检查日志中的冷却期提示
- 等待价格恢复后再次触发

### Q2: 如何减少报警频率？

**方法：**
1. 增加冷却时间：
   ```python
   PRICE_THRESHOLD_COOLDOWN = 7200  # 2小时
   ```

2. 调整阈值，避免价格频繁跨越

### Q3: 如何增加报警频率？

**方法：**
1. 减少冷却时间：
   ```python
   PRICE_THRESHOLD_COOLDOWN = 1800  # 30分钟
   ```

2. 设置多个阈值，形成阶梯式报警

### Q4: 可以监控多少个币种？

**答：** 理论上无限制，但建议：
- 常规监控：5-10 个币种
- 重点监控：1-3 个币种
- 过多会影响日志可读性

### Q5: 价格阈值和涨跌幅监控有什么区别？

| 特性 | 价格阈值监控 | 涨跌幅监控 |
|------|------------|----------|
| 触发条件 | 绝对价格 | 相对涨跌幅 |
| 适用场景 | 关键价位突破 | 短期剧烈波动 |
| 报警频率 | 较低（有冷却期） | 较高（每次波动） |
| 配置复杂度 | 简单 | 中等 |

## 最佳实践

### 1. 合理设置阈值

```python
# ✓ 好的做法：关键支撑位/阻力位
{
    "symbol": "BTCUSDT",
    "threshold": 100000.0,  # 整数关口
    "direction": "above",
    "priority": "high"
}

# ✗ 不好的做法：过于接近当前价格
{
    "symbol": "BTCUSDT",
    "threshold": 98500.0,  # 当前价格 98450
    "direction": "above",
    "priority": "high"
}
```

### 2. 优先级设置

```python
# critical: 极其重要的价位（如清算价）
{
    "symbol": "BTCUSDT",
    "threshold": 90000.0,
    "direction": "below",
    "priority": "critical"
}

# high: 重要的技术位（如支撑/阻力）
{
    "symbol": "ETHUSDT",
    "threshold": 3000.0,
    "direction": "below",
    "priority": "high"
}

# normal: 一般关注的价位
{
    "symbol": "BNBUSDT",
    "threshold": 700.0,
    "direction": "below",
    "priority": "normal"
}
```

### 3. 阶梯式监控

```python
# 为同一币种设置多个阈值
PRICE_THRESHOLD_RULES = [
    # BTC 阶梯式监控
    {"symbol": "BTCUSDT", "threshold": 95000.0, "direction": "below", "priority": "normal"},
    {"symbol": "BTCUSDT", "threshold": 90000.0, "direction": "below", "priority": "high"},
    {"symbol": "BTCUSDT", "threshold": 85000.0, "direction": "below", "priority": "critical"},
]
```

## 技术细节

### 数据来源
- Binance WebSocket API
- 实时价格更新（毫秒级延迟）

### 检查频率
- 每 30 秒检查一次（与 `SAMPLE_INTERVAL` 一致）

### 内存占用
- 每个规则约 200 字节
- 100 个规则约 20 KB

### 性能影响
- 价格阈值检查是 O(n) 复杂度，n 为规则数量
- 对主监控流程影响极小

## 更新日志

### v1.0 (2026-01-08)
- ✨ 初始版本
- ✅ 支持价格突破/跌破监控
- ✅ 智能防重复报警机制
- ✅ 冷却时间控制
- ✅ 中文数字转换
