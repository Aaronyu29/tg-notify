# 获取 Volume、FDV 和市值数据的方案

## 📊 需求分析

你想要获取以下数据（以 USDT 计价）：
1. **Volume（交易量）** - 时间窗口内的交易量
2. **FDV（Fully Diluted Valuation）** - 完全稀释估值
3. **流通市值（Market Cap）** - 流通总市值

## 🔍 数据源分析

### 当前使用：Binance WebSocket miniTicker
**URL**: `wss://fstream.binance.com/ws/!miniTicker@arr`

**提供的字段**：
```json
{
  "e": "24hrMiniTicker",
  "E": 1672515782136,
  "s": "BTCUSDT",        // 交易对
  "c": "16328.00",       // 最新价格 (close price)
  "o": "16328.00",       // 开盘价 (open price)
  "h": "16328.00",       // 最高价 (high price)
  "l": "16328.00",       // 最低价 (low price)
  "v": "1000",           // ✅ 交易量 (base asset volume)
  "q": "16328000.00"     // ✅ 交易额 (quote asset volume, USDT)
}
```

**可以获取**：
- ✅ **Volume（交易量）** - 字段 `q` (quote asset volume)，已经是 USDT 计价
- ✅ **价格** - 字段 `c` (当前价格)

**无法获取**：
- ❌ **FDV（完全稀释估值）**
- ❌ **流通市值**

### 为什么 miniTicker 没有 FDV 和市值？

**原因**：
1. FDV 和市值需要**代币供应量**数据
2. 供应量数据不在价格流中，需要单独获取
3. Binance WebSocket 只提供价格和交易量数据

#解决方案

### 方案1: 使用 Binance REST API（推荐）

#### 获取交易量
**已有** - miniTicker 的 `q` 字段就是 USDT 计价的交易量

#### 获取 FDV 和市值
需要调用 Binance REST API 获取代币信息：

**API 端点**：
```
GET https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT
```

**返回数据**：
```json
{
  "symbol": "BTCUSDT",
  "priceChange": "-94.99999800",
  "priceChangePercent": "-95.960",
  "weightedAvgPric0.29628482",
  "prevClosePrice": "0.10002000",
  "lastPrice": "4.00000200",
  "lastQty": "200.00000000",
  "bidPrice": "4.00000000",
  "askPrice": "4.00000200",
  "openPrice": "99.00000000",
  "highPrice": "100.00000000",
  "lowPrice": "0.10000000",
  "volume": "8913.30000000",        // 交易量
  "quoteVolume": "15.30000000",     // USDT 交易额
  "openTime": 1499783499040,
  "closeTime": 1499869899040,
  "count": 76                        // 交易笔数
}
```

**问题**：Binance API **不直接提供** FDV 和市值数据！

---

### 方案2: 使用 CoinGecko API（推荐）⭐

CoinGecko 提供完整的市值数据。

**API 端点**：
```
GET https://api.coingecko.com/api/v3/coins/markets
```

**参数**：
```
vs_currency=usd
ids=bitcoin,ethereum
```

**返回数据**：
```json
[
  {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": 45600,
    "market_cap": 890000000000,           // ✅ 流通市值
    "fully_diluted_valuation": 957000000000,  // ✅ FDV
    "total_volume": 28000000000,          // ✅ 24小时交易量
    "circulating_supply": 19500000,
    "total_supply": 21000000,
    "max_supply": 21000000
  }
]
```

**优点**：
- ✅ 直接提供 FDV 和市值
- ✅ 数据完整
- ✅ 免费 API（有速率限制）

**缺点**：
- ⚠️ 需要维护 symbol 映射（BTCUSDT → bitcoin）
- ⚠️ API 速率限制（50次/分钟）
- ⚠️ 数据更新频率较低（1-2分钟）

---

### 方案3: 使用 CoinMarketCap API

**API 端点**：
```
GET https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest
```

**优点**：
- ✅ 数据权威
- ✅ 提供 FDV 和市值

**缺点**：
- ❌ 需要付费 API Key
- ❌ 免费版有严格限制

---

## 🎯 推荐实现方案

### 混合方案：Binance WebSocket + CoinGecko API

#### 1. 实时数据（Binance WebSocket）
- ✅ 价格（实时）
- ✅ 交易量（实时）

#### 2. 市值数据（CoinGecko API）
- ✅ FDV（定期更新，如每5分钟）
- ✅ 流通市值（定期更新）

### 实现步骤

#### 步骤1: 添加 CoinGecko API 客户端
```python
import requests
from typing import Dict, Optional

class CoinGeckoClient:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}  # 缓存市值数据
        self.cache_time = {}
        self.cache_duration = 300  # 5分钟缓存

        # Symbol 映射：Binance symbol → CoinGecko ID
        self.symbol_map = {
            "BTCUSDT": "bitcoin",
            "ETHUSDT": "ethereum",
            "BNBUSDT": "binancecoin",
            # ... 需要维护完整映射
        }

    def get_market_data(self, symbols: list) -> Dict:
        """获取市值数据"""
        # 转换为 CoinGecko IDs
        ids = [self.symbol_map.get(s) for s in symbols if s in self.symbol_map]

        if not ids:
            return {}

        try:
            response = requests.get(
                f"{self.base_url}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": ",".join(ids[:250]),  # 最多250个
                    "per_page": 250
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                result = {}
                for coin in data:
                    # 反向映射：CoinGecko ID → Binance symbol
                    for symbol, cg_id in self.symbol_map.items():
                        if cg_id == coin["id"]:
                            result[symbol] = {
                                "market_cap": coin.get("market_cap", 0),
                                "fdv": coin.get("fully_diluted_valuation", 0),
                                "volume_24h": coin.get("total_volume", 0)
                            }
                return result
        except Exception as e:
            print(f"获取市值数据失败: {e}")
            return {}
```

#### 步骤2: 修改数据结构
```python
@dataclass
class PricePoint:
    timestamp: float
    price: float
    volume: float  # 新增：交易量

@dataclass
class CoinMarketData:
    market_cap: float  # 流通市值
    fdv: float         # 完全稀释估值
    volume_24h: float  # 24小时交易量
```

#### 步骤3: 在监控器中集成
```python
class ConfigurableMonitor:
    def __init__(self):
        # ... 现有代码
        self.coingecko = CoinGeckoClient()
        self.market_data = {}  # 存储市值数据
        self.last_market_update = 0

    async def _update_market_data(self):
        """定期更新市值数据"""
        now = time.time()
        if now - self.last_market_update < 300:  # 5分钟更新一次
            return

        # 获取 Top 50 币种的市值数据
        top_symbols = list(self.latest_prices.keys())[:50]
        self.market_data = self.coingecko.get_market_data(top_symbols)
        self.last_market_update = now
```

#### 步骤4: 显示市值数据
```python
# 显示涨幅榜时添加市值信息
for symbol, change, current_price, old_price in top_gainers:
    market_info = self.market_data.get(symbol, {})
    market_cap = market_info.get("market_cap", 0)
    fdv = market_info.get("fdv", 0)

    self.logger.info(
        f"      🚀 {symbol}: {change:+.2f}% | "
        f"价格: ${current_price:.6f} | "
        f"市值: ${market_cap/1e9:.2f}B | "  # 以十亿美元显示
        f"FDV: ${fdv/1e9:.2f}B"
    )
```

---

## ⚠️ 注意事项

### 1. Symbol 映射维护
需要维护 Binance symbol 到 CoinGecko ID 的映射：
```python
symbol_map = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "BNBUSDT": "binancecoin",
    "SOLUSDT": "solana",
    "ADAUSDT": "cardano",
    # ... 需要手动维护或自动获取
}
```

### 2. API 速率限制
- CoinGecko 免费版：**50次/分钟**
- 建议：每5分钟更新一次市值数据
- 只获取 Top 50-100 币种的数据

### 3. 数据延迟
- 价格数据：实时（Binance WebSocket）
- 市值数据：延迟1-2分钟（CoinGecko）
- 这是可接受的，因为市值变化较慢

### 4. 交易量数据
- **实时交易量**：使用 Binance WebSocket 的 `q` 字段
- **24小时交易量**：使用 CoinGecko API

---

## 📊 最终效果示例

```
[10:15:00] 🚀 30秒涨幅榜 Top 5:
    🚀 BTCUSDT: +5.32% | 价格: $45600.50 | 30秒交易量: $125M | 市值: $890B | FDV: $957B
    🚀 ETHUSDT: +4.50% | 价格: $2450.00 | 30秒交易量: $85M | 市值: $295B | FDV: $295B
    🚀 BNBUSDT: +3.20% | 价格: $310.50 | 30秒交易量: $12M | 市值: $47B | FDV: $62B
    ...
```

---

## 🚀 是否实现？

**需要确认**：
1. 是否接受使用 CoinGecko API？（免费但有限制）
2. 是否需要维护 symbol 映射？
3. 是否接受市值数据有1-2分钟延迟？

如果确认，我可以立即开始实现！
