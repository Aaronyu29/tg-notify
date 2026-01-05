# 涨跌幅榜显示优化

## 修改内容

### 修改前
- 只显示涨跌幅绝对值最大的 Top 5
- 涨幅和跌幅混在一起显示
- 只显示币种名称和涨跌幅百分比

### 修改后
- **分开显示涨幅榜和跌幅榜**
- **涨幅榜 Top 5** - 显示涨幅最高的5个币种
- **跌幅榜 Top 5** - 显示跌幅最大的5个币种
- **详细价格信息** - 显示当前价格和N分钟前的价格

## 日志输出示例

### 修改前
```
[23:32:22] [INFO]   🔥 5分钟涨跌幅 Top 5:
[23:32:22] [INFO]       📉 PTBUSDT: -2.15%
[23:32:22] [INFO]       🚀 USELESSUSDT: +1.60%
[23:32:22] [INFO]       🚀 STABLEUSDT: +1.53%
[23:32:22] [INFO]       🚀 PIPPINUSDT: +1.42%
[23:32:22] [INFO]       🚀 SPXUSDT: +1.33%
```

### 修改后
```
[23:32:22] [INFO]   🚀 5分钟涨幅榜 Top 5:
[23:32:22] [INFO]       🚀 USELESSUSDT: +1.60% | 当前: $0.000123 | 5分钟前: $0.000121
[23:32:22] [INFO]       🚀 STABLEUSDT: +1.53% | 当前: $1.015300 | 5分钟前: $1.000000
[23:32:22] [INFO]       🚀 PIPPINUSDT: +1.42% | 当前: $0.342030 | 5分钟前: $0.337200
[23:32:22] [INFO]       🚀 SPXUSDT: +1.33% | 当前: $0.850000 | 5分钟前: $0.838800
[23:32:22] [INFO]       🚀 BTCUSDT: +1.20% | 当前: $45600.50 | 5分钟前: $45055.00

[23:32:22] [INFO]   📉 5分钟跌幅榜 Top 5:
[23:32:22] [INFO]       📉 PTBUSDT: -2.15% | 当前: $0.098500 | 5分钟前: $0.100650
[23:32:22] [INFO]       📉 ETHUSDT: -1.80% | 当前: $2450.00 | 5分钟前: $2495.00
[23:32:22] [INFO]       📉 BNBUSDT: -1.50% | 当前: $310.50 | 5分钟前: $315.25
[23:32:22] [INFO]       📉 ADAUSDT: -1.20% | 当前: $0.495000 | 5分钟前: $0.501000
[23:32:22] [INFO]       📉 SOLUSDT: -0.95% | 当前: $99.50 | 5分钟前: $100.45
```

## 功能特点

### 1. 涨幅榜 🚀
- 显示涨幅最高的 Top 5 币种
- 按涨幅从高到低排序
- 如果涨幅超过告警阈值，显示 ⚠️ 标记

### 2. 跌幅榜 📉
- 显示跌幅最大的 Top 5 币种
- 按跌幅从大到小排序（负值最大的在前）
- 如果跌幅超过告警阈值，显示 ⚠️ 标记

### 3. 价格信息
- **当前价格** - 实时最新价格
- **N分钟前价格** - 根据配置的时间窗口显示历史价格
- **价格格式** - 保留6位小数，适配各种价格范围

### 4. 告警标记
- 涨幅超过阈值（如30%）显示 ⚠️
- 跌幅超过阈值（如30%）显示 ⚠️
- 便于快速识别异常波动

## 代码修改

### 1. `_get_top_movers()` 方法
```python
# 修改前：返回单个列表
def _get_top_movers(self, window_minutes: int, top_n: int = 5) -> list:
    # 按绝对值排序
    movers.sort(key=lambda x: abs(x[1]), reverse=True)
    return movers[:top_n]

# 修改后：返回涨幅榜和跌幅榜
def _get_top_movers(self, window_minutes: int, top_n: int = 5) -> tuple[list, list]:
    # 按涨跌幅排序
    movers.sort(key=lambda x: x[1], reverse=True)

    # 涨幅榜：前 top_n 个
    top_gainers = movers[:top_n]

    # 跌幅榜：后 top_n 个
    top_losers = movers[-top_n:][::-1]

    return top_gainers, top_losers
```

### 2. 显示逻辑
```python
# 获取涨幅榜和跌幅榜
top_gainers, top_losers = self._get_top_movers(min_window, TOP_N_DISPLAY)

# 分别显示涨幅榜
for symbol, change, current_price, old_price in top_gainers:
    self.logger.info(f"🚀 {symbol}: {change:+.2f}% | 当前: ${current_price:.6f} | ...")

# 分别显示跌幅榜
for symbol, change, current_price, old_price in top_losers:
    self.logger.info(f"📉 {symbol}: {change:+.2f}% | 当前: ${current_price:.6f} | ...")
```

## 优势

✅ **信息更清晰** - 涨跌分开，一目了然
✅ **数据更完整** - 显示当前价格和历史价格，便于判断
✅ **便于分析** - 可以快速看到市场热点和风险点
✅ **告警标记** - 异常波动一眼就能看到

## 配置

可以在 `monitor_config.py` 中调整显示数量：

```python
# Top N 显示数量
TOP_N_DISPLAY = 5  # 改为 10 可以显示 Top 10
```

## 使用场景

1. **市场监控** - 快速了解市场整体走势
2. **机会发现** - 涨幅榜可能有投资机会
3. **风险预警** - 跌幅榜提示潜在风险
4. **价格追踪** - 对比当前价格和历史价格，判断趋势

现在你可以更清楚地看到市场的涨跌情况了！
