# 日志系统实现总结

## ✅ 已完成的功能

### 1. 核心日志模块 (`logger.py`)
- ✅ 自动记录到文件和控制台
- ✅ 每小时自动轮转日志文件
- ✅ 自动清理超过24小时的旧日志
- ✅ 支持彩色控制台输出（不同级别不同颜色）
- ✅ 完整的异常堆栈追踪
- ✅ UTF-8 编码支持中文

### 2. 集成到监控程序 (`realtime_monitor_v2.py`)
- ✅ 所有 `print()` 替换为 `logger.info()`
- ✅ 错误信息使用 `logger.error()`
- ✅ 异常使用 `logger.exception()` 记录完整堆栈
- ✅ WebSocket 连接/断开日志
- ✅ 告警发送成功/失败日志
- ✅ 采样和价格变动日志

### 3. 日志查看工具 (`view_logs.py`)
- ✅ 查看最近24小时的所有日志
- ✅ 日志倒序显示（最新的在前）
- ✅ 显示日志总数

### 4. 文档 (`LOG_USAGE.md`)
- ✅ 完整的使用说明
- ✅ 故障排查指南
- ✅ 配置说明

## 📁 文件结构

```
tg-notify/
├── logger.py              # 日志核心模块
├── view_logs.py           # 日志查看工具
├── LOG_USAGE.md           # 使用文档
├── realtime_monitor_v2.py # 已集成日志的监控程序
└── logs/                  # 日志目录（自动创建）
    ├── monitor.log        # 当前日志
    └── monitor.log.*      # 历史日志（按小时轮转）
```

## 🎯 日志级别说明

| 级别 | 用途 | 控制台 | 文件 |
|------|------|--------|------|
| DEBUG | 调试信息（如告警详情JSON） | ❌ | ✅ |
| INFO | 普通信息（采样、连接状态） | ✅ | ✅ |
| WARNING | 警告信息 | ✅ | ✅ |
| ERROR | 错误信息（告警失败、连接断开） | ✅ | ✅ |
| CRITICAL | 严重错误 | ✅ | ✅ |

## 📊 日志内容示例

### 启动日志
```
[2026-01-05 14:30:00] [INFO] ============================================================
[2026-01-05 14:30:00] [INFO] 🔍 实时价格监控器启动
[2026-01-05 14:30:00] [INFO]    采样间隔: 60 秒
[2026-01-05 14:30:00] [INFO]    最大时间窗口: 5 分钟
```

### 正常运行日志
```
[2026-01-05 14:31:00] [INFO] [WS] 正在连接 Binance WebSocket...
[2026-01-05 14:31:01] [INFO] [WS] 连接成功！
[2026-01-05 14:32:00] [INFO] 📊 采样: 245 个币种 | 历史: 2/6 分钟
```

### 告警日志
```
[2026-01-05 14:36:00] [INFO] [ALERT] BTCUSDT: +32.50% - 5分钟暴涨30%
[2026-01-05 14:36:00] [DEBUG] 告警详情: {"upOrDown":"正百分之三十二点五零",...}
```

### 错误日志
```
[2026-01-05 14:40:00] [ERROR] [WS] 连接断开: Connection closed
[2026-01-05 14:40:00] [INFO] [WS] 5秒后重连...
[2026-01-05 14:40:05] [ERROR] [ALERT FAILED] ETHUSDT: +35.20% - 5分钟暴涨30%
```

### 异常日志（带堆栈）
```
[2026-01-05 14:45:00] [ERROR] 检查告警时发生异常: division by zero
Traceback (most recent call last):
  File "realtime_monitor_v2.py", line 247, in _sample_loop
    alerts = self._check_alerts()
  File "realtime_monitor_v2.py", line 185, in _check_alerts
    result = 1 / 0
ZeroDivisionError: division by zero
```

## 🚀 使用方法

### 运行监控（自动记录日志）
```bash
python realtime_monitor_v2.py
```

### 查看历史日志
```bash
python view_logs.py
```

### 直接查看日志文件
```bash
# 查看当前日志
type logs\monitor.log

# 或用编辑器打开
notepad logs\monitor.log
```

## ⚙️ 配置选项

### 修改日志保留时间
在 `realtime_monitor_v2.py` 中修改：
```python
self.logger = Logger(name="monitor", keep_hours=48)  # 保留48小时
```

### 修改控制台日志级别
在 `logger.py` 中修改：
```python
console_handler.setLevel(logging.DEBUG)  # 显示所有日志
```

## 🔧 健壮性改进

1. **异常捕获** - 所有关键操作都有 try-except
2. **异常日志** - 使用 `logger.exception()` 记录完整堆栈
3. **错误恢复** - WebSocket 断开自动重连
4. **日志轮转** - 防止单个文件过大
5. **自动清理** - 防止磁盘空间耗尽

## 📝 注意事项

1. **Windows 控制台中文乱码** - 这是正常的，日志文件中是正确的
2. **日志文件编码** - 使用 UTF-8，确保编辑器支持
3. **磁盘空间** - 24小时日志通常占用几MB到几十MB
4. **权限问题** - 确保程序有权限创建 `logs/` 目录

## ✨ 优势

- ✅ **持久化** - 程序崩溃后仍可查看日志
- ✅ **可追溯** - 保留24小时历史，便于问题排查
- ✅ **自动化** - 无需手动管理，自动轮转和清理
- ✅ **结构化** - 时间戳、级别、消息清晰分离
- ✅ **双重输出** - 实时查看 + 文件保存

## 🎉 测试结果

已测试功能：
- ✅ 日志文件创建
- ✅ 中文正确记录
- ✅ 异常堆栈完整记录
- ✅ 日志倒序查看
- ✅ 彩色控制台输出

现在你可以放心地长时间运行监控程序，所有运行信息、错误、告警都会被完整记录到 `logs/` 目录中！
