# 价格阈值配置示例

## 快速开始

复制以下配置到 `monitor_config.py` 的 `PRICE_THRESHOLD_RULES` 中：

```python
PRICE_THRESHOLD_RULES = [
    # BNB 跌破 800
    {
        "symbol": "BNBUSDT",
        "threshold": 800.0,
        "direction": "below",
        "priority": "high"
    },
]
```

## 常用配置模板

### 1. 主流币种监控

```python
PRICE_THRESHOLD_RULES = [
    # BTC 关键价位
    {
        "symbol": "BTCUSDT",
        "threshold": 100000.0,
        "direction": "above",
        "priority": "high"
    },
    {
        "symbol": "BTCUSDT",
        "threshold": 90000.0,
        "direction": "below",
        "priority": "high"
    },

    # ETH 关键价位
    {
        "symbol": "ETHUSDT",
        "threshold": 4000.0,
        "direction": "above",
        "priority": "high"
    },
    {
        "symbol": "ETHUSDT",
        "threshold": 3000.0,
        "direction": "below",
        "priority": "high"
    },

    # BNB 关键价位
    {
        "symbol": "BNBUSDT",
        "threshold": 800.0,
        "direction": "below",
        "priority": "high"
    },
]
```

### 2. 风险控制监控（清算价附近）

```python
PRICE_THRESHOLD_RULES = [
    # 接近清算价 - 紧急告警
    {
        "symbol": "BTCUSDT",
        "threshold": 85000.0,
        "direction": "below",
        "priority": "critical"
    },

    # 预警价位 - 高优先级
    {
        "symbol": "BTCUSDT",
        "threshold": 88000.0,
        "direction": "below",
        "priority": "high"
    },

    # 安全价位 - 普通告警
    {
        "symbol": "BTCUSDT",
        "threshold": 90000.0,
        "direction": "below",
        "priority": "normal"
    },
]
```

### 3. 突破监控（技术分析）

```python
PRICE_THRESHOLD_RULES = [
    # 突破前高
    {
        "symbol": "BTCUSDT",
        "threshold": 105000.0,
        "direction": "above",
        "priority": "high"
    },

    # 突破整数关口
    {
        "symbol": "ETHUSDT",
        "threshold": 5000.0,
        "direction": "above",
        "priority": "high"
    },

    # 突破阻力位
    {
        "symbol": "BNBUSDT",
        "threshold": 1000.0,
        "direction": "above",
        "priority": "high"
    },
]
```

### 4. 双向监控（区间突破）

```python
PRICE_THRESHOLD_RULES = [
    # BTC 区间上沿
    {
        "symbol": "BTCUSDT",
        "threshold": 105000.0,
        "direction": "above",
        "priority": "high"
    },

    # BTC 区间下沿
    {
        "symbol": "BTCUSDT",
        "threshold": 95000.0,
        "direction": "below",
        "priority": "high"
    },
]
```

### 5. 山寨币监控

```python
PRICE_THRESHOLD_RULES = [
    # SOL
    {
        "symbol": "SOLUSDT",
        "threshold": 200.0,
        "direction": "above",
        "priority": "high"
    },

    # AVAX
    {
        "symbol": "AVAXUSDT",
        "threshold": 50.0,
        "direction": "above",
        "priority": "high"
    },

    # MATIC
    {
        "symbol": "MATICUSDT",
        "threshold": 1.0,
        "direction": "above",
        "priority": "normal"
    },
]
```

## 冷却时间配置

```python
# 高频监控（适合短线交易）
PRICE_THRESHOLD_COOLDOWN = 900  # 15分钟

# 中频监控（适合日内交易）
PRICE_THRESHOLD_COOLDOWN = 3600  # 1小时

# 低频监控（适合长线持仓）
PRICE_THRESHOLD_COOLDOWN = 14400  # 4小时
```

## 完整配置示例

```python
# ========== 价格阈值报警配置 ==========

PRICE_THRESHOLD_RULES = [
    # BTC 多级监控
    {
        "symbol": "BTCUSDT",
        "threshold": 110000.0,
        "direction": "above",
        "priority": "high"
    },
    {
        "symbol": "BTCUSDT",
        "threshold": 100000.0,
        "direction": "above",
        "priority": "high"
    },
    {
        "symbol": "BTCUSDT",
        "threshold": 90000.0,
        "direction": "below",
        "priority": "high"
    },
    {
        "symbol": "BTCUSDT",
        "threshold": 85000.0,
        "direction": "below",
        "priority": "critical"
    },

    # ETH 关键价位
    {
        "symbol": "ETHUSDT",
        "threshold": 4000.0,
        "direction": "above",
        "priority": "high"
    },
    {
        "symbol": "ETHUSDT",
        "threshold": 3000.0,
        "direction": "below",
        "priority": "high"
    },

    # BNB 监控
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

# 冷却时间：1小时
PRICE_THRESHOLD_COOLDOWN = 3600
```

## 注意事项

1. **币种符号格式**：必须以 `USDT` 结尾，如 `BTCUSDT`、`ETHUSDT`
2. **阈值设置**：建议设置在关键技术位，避免过于接近当前价格
3. **优先级选择**：
   - `critical`：极其重要（如清算价）
   - `high`：重要关注（如支撑/阻力）
   - `normal`：一般关注
4. **冷却时间**：根据交易频率调整，避免过度报警
5. **规则数量**：建议不超过 20 个，保持配置简洁

## 测试配置

修改配置后，运行测试脚本验证：

```bash
cd monitor
python test_price_threshold.py
```
