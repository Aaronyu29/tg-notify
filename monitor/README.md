# 币种价格监控器

## 📁 目录说明

这是主要的监控程序目录，包含所有运行所需的核心文件。

## 📄 文件说明

### 核心文件
- **`realtime_monitor_v2.py`** - 主监控程序（⭐ 主要文件）
- **`monitor_config.py`** - 监控配置文件（⭐ 主要文件）
- **`start_monitor.bat`** - Windows 启动脚本（双击运行）

### 依赖文件
- **`logger.py`** - 日志记录模块
- **`alert_generator.py`** - 告警发送模块
- **`chinese_converter.py`** - 中文转换模块
- **`.env`** - 环境变量配置（包含 FWAlert URL）

## 🚀 快速开始

### 方法1：使用启动脚本（推荐）
双击 `start_monitor.bat` 即可启动监控程序。

### 方法2：命令行启动
```bash
cd monitor
python realtime_monitor_v2.py
```

## ⚙️ 配置说明

### 修改告警规则
编辑 `monitor_config.py`：

```python
ALERT_RULES = [
    {
        "name": "5分钟暴涨15%",
        "window_minutes": 5,      # 时间窗口（分钟）
        "threshold": 15.0,        # 阈值（百分比）
        "direction": "up",        # up=暴涨, down=暴跌
        "priority": "high"        # 优先级

### 修改采样间隔
```python
SAMPLE_INTERVAL = 60  # 60秒采样一次
```

### 修改告警冷却时间
```python
ALERT_COOLDOWN = 900  # 15分钟内同一币种不重复告警
```

### 修改显示数量
```python
TOP_N_DISPLAY = 5  # 显示涨跌幅 Top 5
```

## 📊 监控功能

### 实时监控
- ✅ 监控所有 Binance USDT 永续合约
- ✅ 每分钟采样一次价格
- ✅ 自动计算涨跌幅
- ✅ 触发告警自动发送通知

### 日志记录
- ✅ 所有运行信息记录到 `logs/monitor.log`
- ✅ 自动轮转，保留24小时
- ✅ 控制台彩色输出

### 涨跌幅榜
- ✅ 涨幅榜 Top 5
- ✅ 跌幅榜 Top 5
- ✅ 显示当前价格和历史价格

## 📝 日志查看

日志文件位置：`logs/monitor.log`

查看方式：
```bash
# 方法1：直接打开文件
notepad logs\monitor.log

# 方法2：使用查看工具（需要在上级目录）
cd ..
python view_logs.py
```

## 🔧 故障排查

### 程序无法启动
1. 检查是否安装了依赖：`pip install websockets requests python-dotenv`
2. 检查 `.env` 文件是否存在且配置正确

### 没有收到告警
1. 检查 `.env` 中的 `FWALERT_URL` 是否配置正确
2. 检查网络连接是否正常
3. 检查告警阈值是否设置过高

### WebSocket 频繁断开
- 这是正常现象，程序会自动重连
- 如果持续断开，检查网络连接

## 📈 使用建议

### 阈值设置建议
- **激进策略**：10% - 捕捉更多机会（告警较多）
- **平衡策略**：15% - 当前设置（推荐）
- **保守策略**：20% - 只关注极端波动（告警较少）

### 长期运行建议
1. 保持终端窗口打开
2. 设置电脑不休眠
3. 定期查看日志文件
4. 监控磁盘空间（日志占用）

## 🎯 告警示例

当币种满足条件时，会收到如下格式的告警：

```json
{
    "upOrDown": "正百分之十五点三二",
    "symbol": "BTC",
    "currentPrice": "四万五千六百点五零美元",
    "beforePrice": "三万九千五百点零零美元"
}
```

## 📞 支持

如有问题，请查看：
- `LOG_USAGE.md` - 日志系统使用说明
- `TOP_MOVERS_UPDATE.md` - 涨跌幅榜说明
- `LOG_IMPLEMENTATION_SUMMARY.md` - 实现总结

## ⚠️ 注意事项

1. **不要关闭终端窗口** - 关闭后程序会停止
2. **电脑休眠会暂停程序** - 建议设置不休眠
3. **日志文件包含敏感信息** - 请妥善保管
4. **网络断开会自动重连** - 无需手动干预

---

**当前配置：**
- 时间窗口：5分钟
- 告警阈值：±15%
- 采样间隔：60秒
- 告警冷却：15分钟
- 显示数量：Top 5
