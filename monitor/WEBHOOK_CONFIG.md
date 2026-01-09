# Webhook 配置说明

## 概述

监控系统支持两种类型的报警，可以配置不同的 webhook 地址：

1. **涨跌幅报警**：监控币种在指定时间窗口内的涨跌幅
2. **价格阈值报警**：监控币种价格突破或跌破指定阈值

## 配置方式

### 方式 1：使用同一个 Webhook（默认）

如果你想所有报警都发送到同一个 webhook，只需配置 `FWALERT_URL`：

```bash
# monitor/.env
FWALERT_URL=https://fwalert.com/your-webhook-id
PRICE_THRESHOLD_WEBHOOK_URL=
```

**效果：**
- 涨跌幅报警 → `FWALERT_URL`
- 价格阈值报警 → `FWALERT_URL`（使用默认）

### 方式 2：使用不同的 Webhook（推荐）

如果你想将不同类型的报警分开处理，配置两个 webhook：

```bash
# monitor/.env
FWALERT_URL=https://fwalert.com/your-default-webhook-id
PRICE_THRESHOLD_WEBHOOK_URL=https://fwalert.com/your-threshold-webhook-id
```

**效果：**
- 涨跌幅报警 → `FWALERT_URL`
- 价格阈值报警 → `PRICE_THRESHOLD_WEBHOOK_URL`

## 使用场景

### 场景 1：统一处理

**适用情况：**
- 所有报警都发送到同一个 Telegram 群组
- 不需要区分报警类型

**配置：**
```bash
FWALERT_URL=https://fwalert.com/main-channel
PRICE_THRESHOLD_WEBHOOK_URL=
```

### 场景 2：分类处理（推荐）

**适用情况：**
- 涨跌幅报警发送到"市场动态"群组
- 价格阈值报警发送到"关键价位"群组
- 需要对不同类型的报警做不同处理

**配置：**
```bash
# 涨跌幅报警 → 市场动态群组
FWALERT_URL=https://fwalert.com/market-dynamics

# 价格阈值报警 → 关键价位群组
PRICE_THRESHOLD_WEBHOOK_URL=https://fwalert.com/key-levels
```

### 场景 3：优先级分离

**适用情况：**
- 涨跌幅报警（高频）发送到普通群组
- 价格阈值报警（低频、重要）发送到重要群组

**配置：**
```bash
# 涨跌幅报警 → 普通群组
FWALERT_URL=https://fwalert.com/normal-alerts

# 价格阈值报警 → 重要群组
PRICE_THRESHOLD_WEBHOOK_URL=https://fwalert.com/important-alerts
```

## 报警消息格式对比

### 涨跌幅报警 JSON

```json
{
  "upOrDown": "上涨五点二个百分点",
  "symbol": "BNB",
  "currentPrice": "八零五美元",
  "beforePrice": "七六五美元"
}
```

**特点：**
- 包含涨跌幅信息
- 包含前后价格对比
- 高频触发（每30秒检查一次）

### 价格阈值报警 JSON

```json
{
  "type": "price_threshold",
  "symbol": "BNB",
  "direction": "跌破",
  "threshold": "八零零美元",
  "currentPrice": "七九五点五美元"
}
```

**特点：**
- 包含 `type` 字段标识类型
- 包含阈值和方向信息
- 低频触发（有冷却期保护）

## 接收端处理建议

### 方式 1：根据 Webhook 区分

如果使用不同的 webhook，接收端可以根据 webhook URL 区分：

```python
# 伪代码
if webhook_url == "market-dynamics":
    # 处理涨跌幅报警
    handle_price_change_alert(data)
elif webhook_url == "key-levels":
    # 处理价格阈值报警
    handle_threshold_alert(data)
```

### 方式 2：根据 JSON 字段区分

如果使用同一个 webhook，接收端可以根据 JSON 字段区分：

```python
# 伪代码
if "type" in data and data["type"] == "price_threshold":
    # 处理价格阈值报警
    handle_threshold_alert(data)
elif "upOrDown" in data:
    # 处理涨跌幅报警
    handle_price_change_alert(data)
```

## 配置验证

### 查看启动日志

启动监控器后，查看日志确认配置：

**使用独立 webhook：**
```
✓ 价格阈值报警使用独立 Webhook: https://fwalert.com/your-threshold-webhook-id...
```

**使用默认 webhook：**
```
✓ 价格阈值报警使用默认 Webhook
```

### 测试报警发送

运行测试脚本验证配置：

```bash
cd monitor
python test_price_threshold.py
```

检查两个 webhook 是否都收到了测试消息。

## 常见问题

### Q1: 如何获取 FWAlert Webhook URL？

**答：** 访问 [FWAlert](https://fwalert.com)，创建新的 webhook 频道，复制 webhook URL。

### Q2: 可以配置多个价格阈值 webhook 吗？

**答：** 目前只支持一个价格阈值 webhook。如果需要更细粒度的控制，建议在接收端根据币种或优先级进行路由。

### Q3: 修改 webhook 配置后需要重启吗？

**答：** 是的，修改 `.env` 文件后需要重启监控器才能生效。

### Q4: webhook 配置错误会怎样？

**答：**
- 如果 webhook URL 无效，报警发送会失败
- 日志中会显示 `✗ 发送告警失败` 错误
- 监控器会继续运行，不会崩溃

### Q5: 如何临时禁用价格阈值报警？

**答：** 有两种方式：
1. 清空 `PRICE_THRESHOLD_RULES` 配置
2. 将 `PRICE_THRESHOLD_WEBHOOK_URL` 设置为无效地址（不推荐）

## 最佳实践

### 1. 使用描述性的 Webhook 名称

在 FWAlert 中创建 webhook 时，使用清晰的名称：

- ✓ `crypto-price-surge` （涨跌幅报警）
- ✓ `crypto-key-levels` （价格阈值报警）
- ✗ `webhook-1`, `test` （不清晰）

### 2. 分离高频和低频报警

```bash
# 高频报警（涨跌幅）→ 普通群组
FWALERT_URL=https://fwalert.com/high-frequency

# 低频报警（价格阈值）→ 重要群组
PRICE_THRESHOLD_WEBHOOK_URL=https://fwalert.com/low-frequency
```

### 3. 定期检查 Webhook 状态

- 定期测试 webhook 是否正常工作
- 检查 FWAlert 配额是否充足
- 监控报警发送成功率

### 4. 备份配置

```bash
# 备份 .env 文件
cp monitor/.env monitor/.env.backup
```

## 配置模板

### 模板 1：单 Webhook

```bash
# monitor/.env
FWALERT_URL=https://fwalert.com/your-webhook-id
PRICE_THRESHOLD_WEBHOOK_URL=
```

### 模板 2：双 Webhook

```bash
# monitor/.env
# 涨跌幅报警
FWALERT_URL=https://fwalert.com/price-change-alerts

# 价格阈值报警
PRICE_THRESHOLD_WEBHOOK_URL=https://fwalert.com/threshold-alerts
```

### 模板 3：开发/生产环境

```bash
# 开发环境
FWALERT_URL=https://fwalert.com/dev-alerts
PRICE_THRESHOLD_WEBHOOK_URL=https://fwalert.com/dev-threshold

# 生产环境
FWALERT_URL=https://fwalert.com/prod-alerts
PRICE_THRESHOLD_WEBHOOK_URL=https://fwalert.com/prod-threshold
```

## 更新日志

### v1.0 (2026-01-08)
- ✨ 新增价格阈值报警独立 webhook 配置
- ✅ 支持涨跌幅和价格阈值报警分离
- 📝 完善配置文档和使用说明
