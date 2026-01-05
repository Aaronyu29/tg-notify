# 常见问题解答 (FAQ)

## Q1: 为什么每分钟 WS 获取到的币种数量不一致？

### 现象
```
[23:47:32] [INFO]   📊 采样: 471 个币种 | 历史: 2/6 分钟
[23:48:32] [INFO]   📊 采样: 505 个币种 | 历史: 3/6 分钟
[23:49:32] [INFO]   📊 采样: 489 个币种 | 历史: 4/6 分钟
```

### 原因
这是**正常现象**，原因包括：

1. **币种动态变化**
   - Binance 会实时上架/下架交易对
   - 某些币种可能暂时停止交易

2. **价格过滤机制**
   ```python
   price = float(ticker.get("c", 0))
   if price > 0:  # 只记录价格大于0的
       self.latest_prices[symbol] = price
   ```
   - 价格为0的币种会被过滤
   - 某些币种可能暂时没有价格数据

3. **WebSocket 数据推送**
   - 不是所有币种每秒都有价格更新
   - 有些币种交易量小，更新频率低

4. **网络波动**
   - 短暂的网络延迟可能导致部分数据丢失
   - 程序会自动重连，不影响整体监控

### 正常范围
- **通常范围**: 450-550 个币种
- **波动幅度**: ±50 个币种是正常的
- **不影响功能**: 监控和告警功能正常工作

### 何时需要关注？
- ❌ 如果数量突然降到 **< 100** 个 → 可能网络有问题
- ❌ 如果长时间 **= 0** 个 → WebSocket 连接失败
- ✅ 在 400-600 之间波动 → 完全正常

---

## Q2: 为什么 monitor.log 没有实时写入？

### 问题
- 终端在打印日志
- 但 `monitor.log` 文件没有实时更新
- 需要等一段时间或程序退出后才能看到

### 原因
这是 Python 日志系统的**缓冲机制**：
- 为了提高性能，日志会先写入缓冲区
- 缓冲区满了或程序退出时才写入磁盘
- 默认缓冲大小通常是 4KB 或 8KB

### 解决方案
已修复！在 `logger.py` 中添加了实时写入：

```python
# 关闭缓冲，实时写入
file_handler.stream.reconfigure(line_buffering=True)
```

### 修复后的效果
- ✅ 每条日志立即写入文件
- ✅ 可以实时查看 `monitor.log`
- ✅ 程序崩溃也不会丢失日志

### 如何验证？
```bash
# 方法1：实时查看日志（Windows）
powershell Get-Content monitor\logs\monitor.log -Wait

# 方法2：使用文本编辑器
# 打开 monitor\logs\monitor.log，每秒刷新一次即可看到新日志
```

---

## Q3: WebSocket 频繁断开重连正常吗？

### 现象
```
[23:48:01] [ERROR] [WS] 连接断开: no close frame received or sent
[23:48:01] [INFO] [WS] 5秒后重连...
[23:48:06] [INFO] [WS] 正在连接 Binance WebSocket...
[23:48:25] [INFO] [WS] 连接成功！
```

### 原因
1. **Binance 服务器主动断开**
   - 为了负载均衡，服务器会定期断开连接
   - 通常每 24 小时断开一次

2. **网络波动**
   - 家庭网络可能有短暂中断
   - ISP 可能有临时故障

3. **防火墙/代理**
   - 某些网络环境会限制长连接
   - 企业网络可能有连接时长限制

### 正常频率
- ✅ **每小时 < 5 次** → 正常
- ⚠️ **每小时 5-20 次** → 网络不太稳定，但可接受
- ❌ **每分钟多次** → 网络有严重问题

### 程序的处理
- ✅ 自动重连（5秒后）
- ✅ 保留历史数据（不会丢失）
- ✅ 继续监控（不影响功能）

---

## Q4: AttributeError: 'ClientConnection' object has no attribute 'recv_messages'

### 现象
```
Exception in callback Connection.connection_lost()
AttributeError: 'ClientConnection' object has no attribute 'recv_messages'
```

### 原因
这是 `websockets` 库的内部错误，通常是：
- WebSocket 连接异常关闭
- 库的版本兼容性问题

### 影响
- ❌ **不影响程序运行** - 只是一个警告
- ✅ **程序会自动重连** - 5秒后重新连接
- ✅ **数据不会丢失** - 历史数据保留

### 解决方案
1. **忽略这个错误** - 不影响功能
2. **升级 websockets 库**（可选）：
   ```bash
   pip install --upgrade websockets
   ```

---

## Q5: 如何实时查看日志？

### Windows 方法

**方法1：PowerShell（推荐）**
```powershell
# 实时跟踪日志
Get-Content monitor\logs\monitor.log -Wait -Tail 50
```

**方法2：使用文本编辑器**
- 用 Notepad++ 或 VS Code 打开 `monitor\logs\monitor.log`
- 启用自动刷新功能
- VS Code: 安装 "Log File Highlighter" 插件

**方法3：使用第三方工具**
- BareTail（免费）
- Tail for Win32
- mTAIL

### Linux/Mac 方法
```bash
# 实时跟踪日志
tail -f monitor/logs/monitor.log

# 只看最后50行
tail -f -n 50 monitor/logs/monitor.log
```

---

## Q6: 程序运行多久需要重启？

### 建议
- **不需要定期重启** - 程序设计为长期运行
- **自动管理内存** - 不会有内存泄漏
- **自动清理日志** - 只保留24小时

### 何时需要重启？
1. **修改配置后** - 修改 `monitor_config.py` 后需要重启
2. **升级代码后** - 更新程序文件后需要重启
3. **网络长时间异常** - 如果重连失败超过1小时

### 如何优雅重启？
```bash
# 1. 在终端按 Ctrl+C 停止程序
# 2. 等待程序完全退出
# 3. 重新启动
python realtime_monitor_v2.py
```

---

## Q7: 如何调整日志级别？

### 当前设置
- **文件日志**: DEBUG（记录所有）
- **控制台日志**: INFO（只显示重要信息）

### 修改方法
编辑 `logger.py`:

```python
# 文件日志级别
file_handler.setLevel(logging.DEBUG)  # 改为 INFO 可以减少日志量

# 控制台日志级别
console_handler.setLevel(logging.INFO)  # 改为 DEBUG 可以看到更多信息
```

### 日志级别说明
- **DEBUG**: 最详细，包括告警详情 JSON
- **INFO**: 普通信息，采样、连接状态
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

---

## Q8: 日志文件太大怎么办？

### 当前设置
- **轮转周期**: 每小时
- **保留时间**: 24小时
- **预计大小**: 每小时 1-5 MB，24小时约 24-120 MB

### 如果觉得太大
编辑 `realtime_monitor_v2.py`:

```python
# 减少保留时间
self.logger = Logger(name="monitor", keep_hours=12)  # 只保留12小时

# 或修改 logger.py 中的轮转周期
when='H',  # 改为 'D' 表示每天轮转一次
```

---

## 总结

| 问题 | 是否正常 | 需要处理 |
|------|---------|---------|
| 币种数量波动 | ✅ 正常 | ❌ 不需要 |
| 日志不实时写入 | ✅ 已修复 | ✅ 重启程序 |
| WebSocket 断开重连 | ✅ 正常 | ❌ 不需要 |
| AttributeError 异常 | ✅ 可忽略 | ❌ 不需要 |

**现在重启程序，日志就会实时写入了！**
