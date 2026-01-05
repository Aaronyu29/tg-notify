# Alert Generator 快速开始

根据你的需求创建的告警生成器，可以根据自定义规则生成 curl 请求并发送到 FWAlert。

## 配置

1. 复制 `.env.example` 为 `.env`
2. 在 `.env` 中配置你的 FWAlert URL：

```bash
FWALERT_URL=https://fwalert.com/96a-b4-4c8f-bdbc-9f298598ead7
```

## 快速使用

### 方式 1: 使用预定义规则

```python
from alert_generator import AlertGenerator, create_price_surge_rule

# 创建生成器
generator = AlertGenerator()

# 添加规则：BNB 涨幅超过 30% 时告警
generator.add_rule(create_price_surge_rule("BNB", 30.0))

# 检查数据
data = {
    "symbol": "BNB",
    "price": 650.5,
    "change_percent": 35.2
}

# 自动检查并发送告警
results = generator.check_and_alert(data)
```

这会自动生成并发送如下 curl 请求：

```bash
curl --location 'https://fwalert.com/96a-b4-4c8f-bdbc-9f298598ead7' \
--header 'Content-Type: application/json' \
--data '{
    "message": "BNB 价格在过去五分钟涨了 35.2%，请及时关注"
}'
```

### 方式 2: 自定义规则

```python
from alert_generator import AlertGenerator, AlertRule

generator = AlertGenerator()

# 自定义规则
rule = AlertRule(
    name="custom_alert",
    condition=lambda data: data.get("value") > 100,
    message_template="检测到异常：{value}",
    priority="high"
)

generator.add_rule(rule)

# 使用
data = {"value": 150}
generator.check_and_alert(data)
```

## 预定义规则

```python
from alert_generator import (
    create_price_surge_rule,      # 价格暴涨
    create_price_drop_rule,        # 价格暴跌
    create_price_threshold_rule,   # 价格阈值
    create_volume_spike_rule       # 交易量激增
)

generator = AlertGenerator()

# BNB 涨幅超过 30%
generator.add_rule(create_price_surge_rule("BNB", 30.0))

# BTC 跌幅超过 10%
generator.add_rule(create_price_drop_rule("BTC", 10.0))

# ETH破 4000
generator.add_rule(create_price_threshold_rule("ETH", 4000, "above"))

# BNB 交易量超过平均值 5 倍
generator.add_rule(create_volume_spike_rule("BNB", 5.0))
```

## 测试

运行内置测试：

```bash
python alert_generator.py
```

运行示例：

```bash
python examples/alert_generator_example.py
```

## 生成 curl 命令

如果你只想生成 curl 命令而不发送：

```python
generator = AlertGenerator()
message = "BNB 价格在过去五分钟涨了 30%，请及时关注"
curl_cmd = generator.generate_curl_command(message)
print(curl_cmd)
```

## 完整文档

查看 [ALERT_GENERATOR_GUIDE.md](./ALERT_GENERATOR_GUIDE.md) 获取完整文档和更多示例。

## 文件说明

- `alert_generator.py` - 核心代码
- `ALERT_GENERATOR_GUIDE.md` - 完整使用指南
- `examples/alert_generator_example.py` - 使用示例
- `.env.example` - 配置模板（已添加 FWALERT_URL）

## 与现有系统集成

可以同时使用 FWAlert 和 Telegram 通知：

```python
from alert_generator import AlertGenerator, create_price_surge_rule
from notify_client import notify

generator = AlertGenerator()
generator.add_rule(create_price_surge_rule("BNB", 30.0))

data = {"symbol": "BNB", "change_percent": 35.2, "price": 650.5}
results = generator.check_and_alert(data)

到 Telegram
if results["triggered_rules"]:
    for rule in results["triggered_rules"]:
        notify(
            title=f"告警: {rule['rule']}",
            message=rule['message'],
            channel="alert",
            priority=rule['priority']
        )
```
