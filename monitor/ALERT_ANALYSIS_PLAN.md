# 告警效果分析方案
## 波段交易 + 稳健风险导向

---

## 🎯 分析目标

**核心问题：告警信号能否作为可靠的交易信号？**

### 关键指标
1. **准确率** - 告警后价格是否按预期方向运行
2. **收益率** - 跟随告警交易的平均收益
3. **最佳时机** - 何时入场、何时出场
4. **风险控制** - 止损位设置、最大回撤

---

## 📊 分析框架

### 阶段1：告警数据提取（1天）

**提取内容：**
```
告警记录：
- 时间戳
- 币种
- 告警类型（30秒涨2%/30秒跌2%/5分钟涨15%/5分钟跌15%）
- 告警时价格
- 涨跌幅

价格追踪：
- 告警后5分钟价格
- 告警后15分钟价格
- 告警后30分钟价格
- 告警后1小时价格
- 告警后4小时价格
- 告警后24小时价格
```

**数据结构：**
```csv
timestamp, symbol, alert_type, alert_price, change_pct, price_5m, price_15m, price_30m, price_1h, price_4h, price_24h
2026-01-06 13:38:36, BROCCOLIF3BUSDT, 30秒暴跌2%, 0.006073, -2.87%, 0.005950, 0.005920, 0.005880, 0.005850, 0.005800, 0.005750
```

---

### 阶段2：告警效果评估（2天）

#### 2.1 方向准确率分析

**定义成功：**
- **涨告警**：告警后价格继续上涨
- **跌告警**：告警后价格继续下跌

**计算公式：**
```python
# 30秒暴涨告警
if price_15m > alert_price:
    success_count += 1
accuracy = success_count / total_alerts

# 不同时间窗口的准确率
accuracy_5m = ...
accuracy_15m = ...
accuracy_30m = ...
accuracy_1h = ...
```

**预期产出：**
```
30秒暴涨2%告警：
- 5分钟准确率：75%
- 15分钟准确率：68%
- 30分钟准确率：62%
- 1小时准确率：55%

结论：短期准确率高，适合快速交易
```

---

#### 2.2 收益率分析

**交易模拟：**
```python
# 策略1：告警后立即入场，15分钟后出场
for alert in alerts:
    entry_price = alert_price
    exit_price = price_15m
    profit = (exit_price - entry_price) / entry_price * 100

# 策略2：告警后等待回调入场
for alert in alerts:
    entry_price = min(price_1m, price_2m, price_3m)  # 3分钟内最低价
    exit_price = price_15m
    profit = (exit_price - entry_price) / entry_price * 100
```

**统计指标：**
- 平均收益率
- 中位数收益率
- 胜率（盈利次数/总次数）
- 盈亏比（平均盈利/平均亏损）
- 最大单次收益
- 最大单次亏损

**预期产出：**
```
30秒暴涨2%告警 + 立即入场 + 15分钟出场：
- 平均收益：+1.8%
- 胜率：68%
- 盈亏比：2.1
- 最大收益：+8.5%
- 最大亏损：-3.2%

结论：正期望值策略，可以执行
```

---

#### 2.3 最佳时机分析

**入场时机：**
```python
# 测试不同入场策略
strategies = [
    '立即入场',
    '等待1分钟回调',
    '等待3分钟回调',
    '等待5分钟回调',
    '等待突破新高'
]

for strategy in strategies:
    avg_profit = calculate_profit(strategy)

# 找出最优入场时机
```

**出场时机：**
```python
# 测试不同出场策略
exit_times = [5, 10, 15, 30, 60]  # 分钟

for time in exit_times:
    avg_profit = calculate_profit(exit_time=time)

# 找出最优出场时机
```

**预期产出：**
```
最佳入场：告警后等待2-3分钟回调
- 平均入场价格比告警价低0.5%
- 收益率提升至2.3%

最佳出场：告警后15-20分钟
- 此时收益率最高
- 超过20分钟收益开始回落
```

---

#### 2.4 风险控制分析

**止损位设置：**
```python
# 测试不同止损位
stop_loss_levels = [-1%, -2%, -3%, -5%]

for sl in stop_loss_levels:
    trades = simulate_with_stop_loss(sl)
    max_drawdown = calculate_max_drawdown(trades)
    final_profit = calculate_total_profit(trades)

# 找出最优止损位
```

**仓位管理：**
```python
# 基于胜率和盈亏比的凯利公式
kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

# 稳健型：使用半凯利或1/4凯利
position_size = kelly * 0.5
```

**预期产出：**
```
推荐止损：-2%
- 触发概率：15%
- 保护大部分利润
- 最大回撤控制在5%以内

推荐仓位：单次10-15%
- 基于半凯利公式
- 即使连续3次亏损，总资金损失<5%
```

---

### 阶段3：不同告警类型对比（1天）

**对比维度：**
```
1. 30秒暴涨2% vs 30秒暴跌2%
2. 30秒告警 vs 5分钟告警
3. 不同币种的告警效果
4. 不同时段的告警效果
```

**分析方法：**
```python
# 按告警类型分组
alerts_by_type = group_by_alert_type(alerts)

for alert_type, data in alerts_by_type.items():
    accuracy = calculate_accuracy(data)
    avg_profit = calculate_avg_profit(data)
    win_rate = calculate_win_rate(data)

    print(f"{alert_type}:")
    print(f"  准确率: {accuracy}%")
    print(f"  平均收益: {avg_profit}%")
    print(f"  胜率: {win_rate}%")
```

**预期产出：**
```
告警类型效果排名：

1. 30秒暴涨2%
   - 准确率：68%
   - 平均收益：+1.8%
   - 胜率：65%
   - 评级：⭐⭐⭐⭐⭐

2. 30秒暴跌2%
   - 准确率：62%
   - 平均收益：+1.5%
   - 胜率：60%
   - 评级：⭐⭐⭐⭐

3. 5分钟暴涨15%
   - 准确率：45%
   - 平均收益：+0.8%
   - 胜率：48%
   - 评级：⭐⭐⭐

结论：30秒告警效果最好，适合波段交易
```

---

### 阶段4：策略优化（2天）

#### 4.1 过滤条件优化

**添加过滤器：**
```python
# 过滤器1：交易量
if volume_24h < 1M:
    skip  # 流动性太差

# 过滤器2：市值
if market_cap < 10M or market_cap > 1B:
    skip  # 太小风险高，太大波动小

# 过滤器3：连续告警
if same_coin_alerted_in_last_1h:
    skip  # 避免追高

# 过滤器4：时间窗口确认
if change_30s > 2% and change_5m > 0%:
    confidence = 'high'  # 多时间框架确认
```

**效果对比：**
```
无过滤：
- 告警数：100次
- 胜率：65%
- 平均收益：+1.8%

添加过滤后：
- 告警数：45次
- 胜率：78%
- 平均收益：+2.5%

结论：过滤后质量显著提升
```

---

#### 4.2 组合策略

**策略A：激进型（不推荐）**
```
- 所有告警都交易
- 立即入场
- 5分钟出场
- 无止损

预期：高频交易，收益不稳定
```

**策略B：稳健型（推荐）⭐⭐⭐⭐⭐**
```
- 只交易30秒告警
- 添加交易量和市值过滤
- 等待2-3分钟回调入场
- 15分钟出场或止损-2%
- 单次仓位10%

预期：
- 月交易次数：20-30次
- 月收益率：8-15%
- 最大回撤：<8%
- 夏普比率：>1.5
```

**策略C：保守型**
```
- 只交易多时间框架确认的告警
- 严格过滤（交易量>5M，市值50M-500M）
- 等待5分钟回调入场
- 30分钟出场或止损-1.5%
- 单次仓位5%

预期：
- 月交易次数：5-10次
- 月收益率：3-6%
- 最大回撤：<5%
- 夏普比率：>2.0
```

---

### 阶段5：实盘验证（持续）

#### 5.1 模拟交易

**设置：**
```
初始资金：10,000 USDT
策略：稳健型
周期：2周
```

**记录：**
```
每笔交易记录：
- 入场时间、价格
- 出场时间、价格
- 收益率
- 持仓时间
- 备注（为什么入场/出场）
```

**评估指标：**
```
- 总收益率
- 胜率
- 盈亏比
- 最大回撤
- 夏普比率
- 卡玛比率
```

---

#### 5.2 持续优化

**每周复盘：**
```
1. 哪些交易成功了？为什么？
2. 哪些交易失败了？为什么？
3. 策略需要调整吗？
4. 有新的发现吗？
```

**动态调整：**
```
- 根据市场环境调整仓位
- 根据胜率调整止损位
- 根据波动率调整持仓时间
```

---

## 🛠️ 技术实现

### 工具1：日志解析脚本

```python
# alert_parser.py
import re
from datetime import datetime

def parse_alerts(log_file):
    """提取所有告警记录"""
    alerts = []

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '[ALERT]' in line:
                # 提取：时间、币种、涨跌幅、告警类型
                match = re.search(
                    r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*\[ALERT\] (\w+): ([+-]?\d+\.\d+)% - (.+)',
                    line
                )
                if match:
                    alerts.append({
                        'timestamp': match.group(1),
                        'symbol': match.group(2),
                        'change': float(match.group(3)),
                        'alert_type': match.group(4)
                    })

    return alerts

# 使用
alerts = parse_alerts('monitor.log')
print(f"找到 {len(alerts)} 条告警")
```

---

### 工具2：价格追踪脚本

```python
# price_tracker.py
def get_price_after_alert(log_file, alert_time, symbol, minutes):
    """获取告警后N分钟的价格"""
    target_time = alert_time + timedelta(minutes=minutes)

    # 在日志中查找最接近target_time的价格记录
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if symbol in line and '现价:' in line:
                time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', line)
                price_match = re.search(r'现价: \$(\d+\.\d+)', line)

                if time_match and price_match:
                    line_time = parse_time(time_match.group(1))
                    if abs((line_time - target_time).seconds) < 30:
                        return float(price_match.group(1))

    return None
```

---

### 工具3：回测框架

```python
# backtest.py
class AlertBacktest:
    def __init__(self, alerts, strategy):
        self.alerts = alerts
        self.strategy = strategy
        self.trades = []

    def run(self):
        """运行回测"""
        for alert in self.alerts:
            # 检查过滤条件
            if not self.strategy.should_trade(alert):
                continue

            # 模拟交易
            entry_price = self.get_entry_price(alert)
            exit_price = self.get_exit_price(alert)

            profit = (exit_price - entry_price) / entry_price * 100

            self.trades.append({
                'symbol': alert['symbol'],
                'entry': entry_price,
                'exit': exit_price,
                'profit': profit
            })

        return self.calculate_metrics()

    def calculate_metrics(self):
        """计算性能指标"""
        profits = [t['profit'] for t in self.trades]

        return {
            'total_trades': len(self.trades),
            'win_rate': len([p for p in profits if p > 0]) / len(profits),
            'avg_profit': sum(profits) / len(profits),
            'max_profit': max(profits),
            'max_loss': min(profits),
            'sharpe_ratio': self.calculate_sharpe(profits)
        }
```

---

## 📅 实施时间表

### Week 1: 数据提取与基础分析
- **Day 1-2**: 编写解析脚本，提取告警数据
- **Day 3-4**: 追踪价格变化，建立数据集
- **Day 5-7**: 计算准确率和收益率

### Week 2: 深度分析与策略制定
- **Day 1-2**: 最佳时机分析
- **Day 3-4**: 风险控制分析
- **Day 5-7**: 策略优化和对比

### Week 3-4: 回测与验证
- **Week 3**: 历史数据回测
- **Week 4**: 模拟交易验证

### Week 5+: 实盘跟踪
- 小仓位实盘
- 持续优化
- 扩大规模

---

## 🎯 成功标准

### 最低目标（必须达到）
- ✅ 告警准确率 >60%
- ✅ 平均收益率 >1%
- ✅ 胜率 >55%
- ✅ 最大回撤 <10%

### 理想目标
- 🎯 告警准确率 >70%
- 🎯 平均收益率 >2%
- 🎯 胜率 >65%
- 🎯 最大回撤 <8%
- 🎯 月收益率 >10%

### 优秀目标
- 🌟 告警准确率 >80%
- 🌟 平均收益率 >3%
- 🌟 胜率 >70%
- 🌟 最大回撤 <5%
- 🌟 月收益率 >15%

---

## 💡 关键洞察（预测）

基于经验，我预测您会发现：

1. **30秒告警效果最好**
   - 短期动量强，延续性好
   - 适合快速进出

2. **最佳持仓时间：10-20分钟**
   - 太短抓不住利润
   - 太长容易回吐

3. **过滤很重要**
   - 交易量<1M的币种成功率低
   - 连续告警的币种要谨慎

4. **时段效应**
   - 某些时段告警质量更高
   - 可能是欧美交易时段

5. **币种特性**
   - 某些币种告警特别准
   - 可以建立"白名单"

---

## 📊 预期报告格式

### 最终报告结构

```
1. 执行摘要
   - 核心发现
   - 推荐策略
   - 预期收益

2. 数据概览
   - 告警总数
   - 币种分布
   - 时间分布

3. 效果分析
   - 准确率分析
   - 收益率分析
   - 风险分析

4. 策略建议
   - 推荐策略
   - 入场规则
   - 出场规则
   - 风控规则

5. 回测结果
   - 历史表现
   - 关键指标
   - 风险评估

6. 实施计划
   - 操作流程
   - 监控指标
   - 优化方向
```

---

## 🚀 立即开始

### 第一步：快速验证（今天完成）

```python
# quick_test.py
# 快速统计最近的告警效果

import re

# 1. 提取最近10条告警
alerts = parse_recent_alerts(n=10)

# 2. 手动查看价格变化
for alert in alerts:
    print(f"{alert['symbol']} 告警时间: {alert['time']}")
    print(f"  告警价格: {alert['price']}")
    print(f"  15分钟后价格: [手动查看日志]")
    print(f"  收益: [手动计算]")
    print()

# 3. 初步判断
# 如果10条中有6-7条盈利 → 值得深入分析
# 如果10条中只有3-4条盈利 → 需要优化策略
```

---

*Created: 2026-01-06*
*Target: 波段交易 + 稳健风险*
*Focus: 告警效果分析*
*Version: 1.0*
