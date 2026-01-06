"""
CoinGecko API 客户端
用于获取加密货币的市值、FDV 等数据
"""

import requests
import time
from typing import Dict, Optional, List
from logger import Logger


class CoinGeckoClient:
    """CoinGecko API 客户端"""

    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.timeout = 10  # 10秒超时
        self.cache = {}  # 缓存市值数据
        self.last_update = 0
        self.cache_duration = 300  # 5分钟缓存
        self.logger = Logger(name="coingecko", keep_hours=24)

        # 限速控制
        self.last_request_time = 0
        self.min_request_interval = 2  # 最小请求间隔（秒），免费版约30次/分钟
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 5  # 重试延迟（秒）

        # Symbol 映射：Binance symbol → CoinGecko ID
        # 这个映射需要维护，可以从 CoinGecko API 自动获取
        self.symbol_map = {
            "BTCUSDT": "bitcoin",
            "ETHUSDT": "ethereum",
            "BNBUSDT": "binancecoin",
            "SOLUSDT": "solana",
            "XRPUSDT": "ripple",
            "ADAUSDT": "cardano",
            "DOGEUSDT": "dogecoin",
            "MATICUSDT": "matic-network",
            "DOTUSDT": "polkadot",
            "LINKUSDT": "chainlink",
            "AVAXUSDT": "avalanche-2",
            "UNIUSDT": "uniswap",
            "ATOMUSDT": "cosmos",
            "LTCUSDT": "litecoin",
            "ETCUSDT": "ethereum-classic",
            "NEARUSDT": "near",
            "APTUSDT": "aptos",
            "ARBUSDT": "arbitrum",
            "OPUSDT": "optimism",
            "INJUSDT": "injective-protocol",
            # 可以继续添加更多...
        }

    def _rate_limit_wait(self):
        """
        确保请求间隔满足限速要求
        免费版 API 限制约 30 次/分钟，设置 2 秒间隔确保不超限
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            self.logger.debug(f"限速等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        获取市值数据

        Args:
            symbols: Binance symbol 列表，如 ["BTCUSDT", "ETHUSDT"]

        Returns:
            {
                "BTCUSDT": {
                    "market_cap": 890000000000,
                    "fdv": 957000000000,
                    "volume_24h": 28000000000
                },
                ...
            }
        """
        # 检查缓存
        now = time.time()
        if now - self.last_update < self.cache_duration and self.cache:
            return self.cache

        # 转换为 CoinGecko IDs
        ids = []
        for symbol in symbols:
            cg_id = self.symbol_map.get(symbol)
            if cg_id:
                ids.append(cg_id)

        if not ids:
            self.logger.warning("没有找到可映射的 CoinGecko ID")
            return {}

        # 重试机制
        for attempt in range(self.max_retries):
            try:
                # 限速等待
                self._rate_limit_wait()

                # 调用 CoinGecko API
                self.logger.debug(f"正在获取 {len(ids)} 个币种的市值数据... (尝试 {attempt + 1}/{self.max_retries})")

                response = requests.get(
                    f"{self.base_url}/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "ids": ",".join(ids[:250]),  # 最多250个
                        "per_page": 250,
                        "sparkline": "false"
                    },
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    result = {}

                    for coin in data:
                        # 反向映射：CoinGecko ID → Binance symbol
                        for symbol, cg_id in self.symbol_map.items():
                            if cg_id == coin["id"]:
                                result[symbol] = {
                                    "market_cap": coin.get("market_cap") or 0,
                                    "fdv": coin.get("fully_diluted_valuation") or 0,
                                    "volume_24h": coin.get("total_volume") or 0
                                }

                    self.cache = result
                    self.last_update = now
                    self.logger.info(f"成功获取 {len(result)} 个币种的市值数据")
                    return result

                elif response.status_code == 429:
                    # 触发限速
                    self.logger.warning(f"触发 API 限速 (429)，尝试 {attempt + 1}/{self.max_retries}")
                    if attempt < self.max_retries - 1:
                        self.logger.info(f"等待 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        self.logger.error("达到最大重试次数，返回缓存数据")
                        return self.cache

                else:
                    self.logger.error(f"CoinGecko API 返回错误: {response.status_code}")
                    return self.cache  # 返回缓存数据

            except requests.Timeout:
                self.logger.error(f"CoinGecko API 请求超时（10秒），尝试 {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    self.logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self.logger.error("达到最大重试次数，返回缓存数据")
                    return self.cache

            except Exception as e:
                self.logger.error(f"获取市值数据失败: {e}，尝试 {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    self.logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self.logger.error("达到最大重试次数，返回缓存数据")
                    return self.cache

        # 所有重试都失败，返回缓存
        return self.cache

    def format_market_cap(self, value: float) -> str:
        """
        格式化市值显示

        Args:
            value: 市值（美元）

        Returns:
            格式化字符串，如 "$890B", "$12.5M", "N/A"
        """
        if value == 0:
            return "N/A"

        if value >= 1e9:  # 十亿
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:  # 百万
            return f"${value/1e6:.2f}M"
        elif value >= 1e3:  # 千
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"

    def format_volume(self, value: float) -> str:
        """
        格式化交易量显示

        Args:
            value: 交易量（美元）

        Returns:
            格式化字符串，如 "$125M", "$1.5B"
        """
        return self.format_market_cap(value)


# 测试代码
if __name__ == "__main__":
    client = CoinGeckoClient()

    # 测试获取市值数据
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    data = client.get_market_data(symbols)

    print("=" * 60)
    print("CoinGecko API 测试")
    print("=" * 60)

    for symbol, info in data.items():
        print(f"\n{symbol}:")
        print(f"  市值: {client.format_market_cap(info['market_cap'])}")
        print(f"  FDV: {client.format_market_cap(info['fdv'])}")
        print(f"  24h交易量: {client.format_volume(info['volume_24h'])}")
