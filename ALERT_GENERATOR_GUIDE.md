# Alert Generator 使用指南

## 简介

`alert_generator.py` 是一个灵活的告警生成器，可以根据自定义规则检查数据并自动发送告警到 FWAlert webhook。

## 快速开始

### 1. 配置环境变量

在 `.env` 文件中添加你的 FWAlert webhook URL：

```bash
FWALERT_URL=https://fwalert.com/your-webhook-id
```

### 2. 基本使用

```python
from alert_generator import AlertGenerator, AlertRule

# 创建告警生成器
generator = AlertGenerator()

# 定义规则：BNB 涨幅超过 30%
rule = AlertRule(
    name="BNB_surge",
    condition=lambda data: data.get("symbol") == "BNB" and data.get("change_percent", 0) > 30,
    message_template="BNB 价格在过去五分钟涨了 {change_percent:.1f}%，请及时关注",
    priority="high"
)

# 添加规则
generator.add_rule(rule)

# 检查数据并发送告警
data = {
    "symbol": "BNB",
    "price": 650.5,
    "change_percent": 35.2
}

results = generator.check_and_alert(data)
```

## 预定义规则

### 价格暴涨规则

```python
from alert_generator import create_price_surge_rule

# BNB 涨幅超过 30% 时告警
rule = create_price_surge_rule("BNB", 30.0)
generator.add_rule(rule)
```

### 价格暴跌规则

```python
from alert_generator import create_price_drop_rule

# BTC 跌幅超过 10% 时告警
rule = create_price_drop_rule("BTC", 10.0)
generator.add_rule(rule)
```

### 价格阈值规则

```python
from alert_generator import create_price_threshold_rule

# ETH 价格突破 4000 时告警
rule = create_price_threshold_rule("ETH", 4000, "above")
generator.add_rule(rule)

# BTC 价格跌破 40000 时告警
rule = create_price_threshold_rule("BTC", 40000, "below")
generator.add_rule(rule)
```

### 交易量激增规则

```python
from alert_generator import create_volume_spike_rule

# 交易量超过平均值 5 倍时告警
rule = create_volume_spike_rule("BNB", 5.0)
generator.add_rule(rule)
```

## 自定义规则

### 创建自定义规则

```python
from alert_generator import AlertRule

# 示例：大额转账告警
large_transfer_rule = AlertRule(
    name="large_transfer",
    condition=lambda data: data.get("amount", 0) > 1000000,
    message_template="检测到大额转账：{amount:,.2f} USDT，地址：{address}",
    priority="high"
)

generator.add_rule(large_transfer_rule)

# 使用
data = {
    "amount": 1500000,
    "address": "0x1234...5678"
}
generator.check_and_alert(data)
```

### 复杂条件规则

```python
# 示例：多条件组合
def complex_condition(data):
    # 价格上涨且交易量激增
    price_up = data.get("change_percent", 0) > 10
    volume_high = data.get("volume_ratio", 0) > 3
    return price_up and volume_high

complex_rule = AlertRule(
    name="price_volume_surge",
    condition=complex_condition,
    message_template="{symbol} 价格上涨 {change_percent:.1f}% 且交易量激增 {volume_ratio:.1f} 倍",
    priority="high"
)

generator.add_rule(complex_rule)
```

## 完整示例：加密货币监控

```python
from alert_generator import (
    AlertGenerator,
    create_price_surge_rule,
    create_price_drop_rule,
    create_price_threshold_rule,
    create_volume_spike_rule
)

# 初始化
generator = AlertGenerator()

# 添加多个规则
generator.add_rule(create_price_surge_rule("BNB", 30.0))
generator.add_rule(create_price_drop_rule("BTC", 10.0))
generator.add_rule(create_price_threshold_rule("ETH", 4000, "above"))
generator.add_rule(create_volume_spike_rule("BNB", 5.0))

# 模拟实时数据检查
def monitor_price(symbol, price, change_percent, volume_ratio):
    data = {
        "symbol": symbol,
        "price": price,
        "change_percent": change_percent,
        "volume_ratio": volume_ratio
    }

    results = generator.check_and_alert(data)

    if results["triggered_rules"]:
        print(f"触发了 {len(results['triggered_rules'])} 条规则")
        for rule in results["triggered_rules"]:
            print(f"  - {rule['rule']}: {rule['message']}")
    else:
        print("未触发任何规则")

# 使用
monitor_price("BNB", 650.5, 35.2, 3.5)
```

## 生成 curl 命令

如果你想手动执行或调试，可以生成 curl 命令：

```python
message = "BNB 价格在过去五分钟涨了 30%，请及时关注"
curl_cmd = generator.generate_curl_command(message)
print(curl_cmd)
```

输出：
```bash
curl --location 'https://fwalert.com/96a-b4-4c8f-bdbc-9f298598ead7' \
--header 'Content-Type: application/json' \
--data '{
    "message": "BNB 价格在过去五分钟涨了 30%，请及时关注"
}'
```

## 与现有通知系统集成

如果你想同时使用 FWAlert 和 Telegram 通知：

```python
from alert_generator import AlertGenerator
from notify_client import notify

generator = AlertGenerator()

# 添加规则
generator.add_rule(create_price_surge_rule("BNB", 30.0))

# 检查数据
data = {"symbol": "BNB", "change_percent": 35.2, "price": 650.5}
results = generator.check_and_alert(data)

# 同时发送到 Telegram
if results["triggered_rules"]:
    for rule in results["triggered_rules"]:
        notify(
            title=f"告警: {rule['rule']}",
            message=rule['message'],
            channel="alert",
            priority=rule['priority']
        )
```

## 定时监控示例

```python
import time
from alert_generator import AlertGenerator, create_price_surge_rule

generator = AlertGenerator()
generator.add_rule(create_price_surge_rule("BNB", 30.0))

def fetch_price_data():
    """从交易所 API 获取价格数据（示例）"""
    # 这里应该调用实际的 API
    return {
        "symbol": "BNB",
        "price": 650.5,
        "change_percent": 35.2,
        "volume_ratio": 3.5
    }

# 每 5 分钟检查一次
while True:
    data = fetch_price_data()
    generator.check_and_alert(data)
    time.sleep(300)  # 5 分钟
```

## API 参考

### AlertRule

```python
AlertRule(
    name: str,                                    # 规则名称
    condition: Callable[[Dict], bool],            # 判断函数
    message_template: str,                        # 消息模板
    priority: str = "normal"                      # 优先级
)
```

### AlertGenerator

```python
AlertGenerator(fwalert_url: str = None)           # 初始化

add_rule(rule: AlertRule)                         # 添加规则

check_and_alert(data: Dict) -> Dict               # 检查并发送告警

send_alert(message: str) -> bool                  # 发送单条告警

generate_curl_command(message: str) -> str        # 生成 curl 命令
```

## 测试

运行测试：

```bash
python alert_generator.py
```

这会运行内置的测试用例，展示各种规则的使用。

## 注意事项

1. **环境变量配置**：确保在 `.env` 中正确配置 `FWALERT_URL`
2. **消息模板**：使用 `{key}` 格式引用数据字典中的值
3. **异常处理**：规则检查失败不会中断程序，会打印错误信息
4. **优先级**：支持 `normal`、`high`、`critical` 三个级别

## 故障排查

### 告警未发送

1. 检查 `FWALERT_URL` 是否正确配置
2. 检查网络连接
3. 查看控制台错误信息

### 规则未触发

1. 打印数据字典，确认字段名称正确
2. 测试 condition 函数是否返回预期结果
3. 检查数据类型是否匹配

### 消息格式错误

1. 确保消息模板中的 `{key}` 在数据字典中存在
2. 使用格式化选项，如 `{price:.2f}` 保留两位小数

## License

MIT
