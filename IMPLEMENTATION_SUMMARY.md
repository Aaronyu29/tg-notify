# Alert Generator - 完成总结

## ✅ 已完成的功能

根据你的需求，我已经创建了一个完整的告警生成器系统，可以根据自定义规则生成 curl 请求并发送到 FWAlert。

## 📁 创建的文件

1. **alert_generator.py** - 核心代码文件
   - `AlertRule` 类：定义告警规则
   - `AlertGenerator` 类：管理规则和发送告警
   - 预定义规则函数：价格暴涨、暴跌、阈值、交易量激增等
   - 自动生成 curl 请求并发送

2. **ALERT_GENERATOR_GUIDE.md** - 完整使用指南
   - 详细的 API 文档
   - 各种使用场景示例
   - 故障排查指南

3. **ALERT_GENERATOR_README.md** - 快速开始文档
   - 简洁的使用说明
   - 常用示例代码

4. **examples/alert_generator_example.py** - 示例代码
   - 6 个完整的使用示例
   - 可直接运行测试

5. **更新 .env.example** - 添加了 FWALERT_URL 配置项

## 🚀 如何使用

### 1. 配置环境变量

在 `.env` 文件中添加：

```bash
FWALERT_URL=https://fwalert.com/96a-b4-4c8f-bdbc-9f298598ead7
```

### 2. 基本使用示例

```python
from alert_generator import AlertGenerator, create_price_surge_rule

# 创建生成器
generator = AlertGenerator()

# 添加规则：BNB 涨幅超过 30% 时告警
generator.add_rule(create_price_surge_rule("BNB", 30.0))

# 检查数据并自动发送告警
data = {
    "symbol": "BNB",
    "price": 650.5,
    "change_percent": 35.2
}

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

### 3. 自定义规则

```python
from alert_generator import AlertRule

rule = AlertRule(
    name="custom_alert",
    condition=lambda data: data.get("value") > 100,
    message_template="检测到异常：{value}",
    priority="high"
)

generator.add_rule(rule)
```

## 🎯 核心功能

### 1. 规则系统
- ✅ 灵活的条件判断（使用 lambda 函数）
- ✅ 消息模板支持（使用 `{key}` 格式）
- ✅ 优先级设置（normal/high/critical）

### 2. 预定义规则
- ✅ `create_price_surge_rule()` - 价格暴涨
- ✅ `create_price_drop_rule()` - 价格暴跌
- ✅ `create_price_threshold_rule()` - 价格阈值
- ✅ `create_volume_spike_rule()` - 交易量激增

### 3. 告警发送
- ✅ 自动生成 curl 请求
- ✅ 发送到 FWAlert webhook
- ✅ 错误处理和日志记录
- ✅ 支持手动生成 curl 命令

### 4. 集成能力
- ✅ 可与现有 Telegram 通知系统集成
- ✅ 支持多规则同时检查
- ✅ 返回详细的执行结果

## 📖 文档说明

### 快速开始
阅读 `ALERT_GENERATOR_README.md`

### 完整文档
阅读 `ALERT_GENERATOR_GUIDE.md`，包含：
- 详细的 API 参考
- 各种使用场景
- 自定义规则示例
- 与 Telegram 集成
- 定时监控示例
- 故障排查

### 运行示例
```bash
# 运行内置测试
python alert_generator.py

# 运行完整示例
python examples/alert_generator_example.py
```

## 🔧 测试结果

已测试所有功能：
- ✅ 规则匹配正常
- ✅ 消息格式化正常
- ✅ curl 命令生成正常
- ✅ 多规则同时触发正常
- ✅ Windows 编码问题已修复
- ✅ 错误处理正常

## 💡 使用建议

1. **配置 URL**：在 `.env` 中设置你的 FWALERT_URL
2. **测试规则**：先运行 `python alert_generator.py` 测试
3. **查看示例**：运行 `python examples/alert_generator_example.py`
4. **集成到项目**：参考文档集成到你的监控脚本中

## 📝 下一步

你可以：
1. 在 `.env` 中配置你的 FWALERT_URL
2. 根据实际需求定义自己的规则
3. 集成到现有的监控系统中
4. 结合 Telegram 通知使用

## 🎉 总结

所有功能已完成并测试通过！你现在可以：
- ✅ 定义自定义规则
- ✅ 自动生成 curl 请求
- ✅ 发送告警到 FWAlert
- ✅ 使用预定义规则快速开始
- ✅ 与现有系统集成

如有任何问题，请查看文档或运行示例代码。
