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

        # 配置代理
        self.proxies = {
            'http': 'http://localhost:7897',
            'https': 'http://localhost:7897'
        }

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

        # 自动搜索缓存：{symbol: {"id": coingecko_id or None, "timestamp": unix_timestamp}}
        self.search_cache = {}
        self.search_cache_file = "coingecko_symbol_cache.json"
        self.search_cache_ttl = 86400 * 7  # 7天过期（对于null值）
        self._load_search_cache()

    def _load_search_cache(self):
        """从文件加载搜索缓存"""
        try:
            import json
            from pathlib import Path
            cache_path = Path(__file__).parent / self.search_cache_file
            if cache_path.exists():
                with open(cache_path, 'r', encoding='utf-8') as f:
                    old_cache = json.load(f)

                # 兼容旧格式：{symbol: id} 转换为新格式：{symbol: {id, timestamp}}
                for symbol, value in old_cache.items():
                    if isinstance(value, dict):
                        # 新格式
                        self.search_cache[symbol] = value
                    else:
                        # 旧格式，转换为新格式
                        self.search_cache[symbol] = {
                            "id": value,
                            "timestamp": time.time()
                        }

                self.logger.info(f"加载了 {len(self.search_cache)} 个币种的映射缓存")
        except Exception as e:
            self.logger.debug(f"加载搜索缓存失败: {e}")

    def _save_search_cache(self):
        """保存搜索缓存到文件"""
        try:
            import json
            from pathlib import Path
            cache_path = Path(__file__).parent / self.search_cache_file
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.search_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.debug(f"保存搜索缓存失败: {e}")

    def _search_coin_id(self, symbol: str) -> Optional[str]:
        """
        搜索币种的 CoinGecko ID

        Args:
            symbol: Binance symbol，如 "BREVUSDT"

        Returns:
            CoinGecko ID 或 None
        """
        # 检查缓存
        if symbol in self.search_cache:
            cache_entry = self.search_cache[symbol]
            coin_id = cache_entry.get("id")
            timestamp = cache_entry.get("timestamp", 0)

            # 如果找到了ID（非None），直接返回
            if coin_id is not None:
                return coin_id

            # 如果是None，检查是否过期（7天后重试）
            if time.time() - timestamp < self.search_cache_ttl:
                # 未过期，返回None
                return None
            else:
                # 已过期，删除缓存，重新搜索
                self.logger.debug(f"{symbol} 的null缓存已过期，重新搜索")
                del self.search_cache[symbol]

        # 提取币种名称（去掉 USDT）
        coin_symbol = symbol.replace("USDT", "").lower()

        try:
            # 限速等待
            self._rate_limit_wait()

            # 搜索币种
            self.logger.debug(f"搜索币种: {coin_symbol}")
            response = requests.get(
                f"{self.base_url}/search",
                params={"query": coin_symbol},
                timeout=self.timeout,
                proxies=self.proxies
            )

            if response.status_code == 200:
                data = response.json()
                coins = data.get("coins", [])

                # 尝试精确匹配 symbol
                for coin in coins:
                    if coin.get("symbol", "").lower() == coin_symbol:
                        coin_id = coin.get("id")
                        self.logger.info(f"找到映射: {symbol} -> {coin_id}")
                        self.search_cache[symbol] = {
                            "id": coin_id,
                            "timestamp": time.time()
                        }
                        self._save_search_cache()
                        return coin_id

                # 如果没有精确匹配，返回 None
                self.logger.debug(f"未找到 {symbol} 的精确匹配")
                self.search_cache[symbol] = {
                    "id": None,
                    "timestamp": time.time()
                }
                self._save_search_cache()
                return None
            else:
                self.logger.debug(f"搜索失败: {response.status_code}")
                return None

        except Exception as e:
            self.logger.debug(f"搜索 {symbol} 失败: {e}")
            return None

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
        unknown_symbols = []

        for symbol in symbols:
            # 先查找预定义映射
            cg_id = self.symbol_map.get(symbol)

            # 如果没有预定义映射，尝试自动搜索
            if not cg_id:
                cg_id = self._search_coin_id(symbol)

            if cg_id:
                ids.append(cg_id)
            else:
                unknown_symbols.append(symbol)

        if unknown_symbols and len(unknown_symbols) <= 10:
            self.logger.debug(f"未找到映射的币种: {', '.join(unknown_symbols)}")

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
                    timeout=self.timeout,
                    proxies=self.proxies
                )

                if response.status_code == 200:
                    data = response.json()
                    result = {}

                    # 创建反向映射：CoinGecko ID → Binance symbol
                    id_to_symbol = {}
                    # 添加预定义映射
                    for symbol, cg_id in self.symbol_map.items():
                        if cg_id:
                            id_to_symbol[cg_id] = symbol
                    # 添加搜索缓存中的映射
                    for symbol, cache_entry in self.search_cache.items():
                        cg_id = cache_entry.get("id") if isinstance(cache_entry, dict) else cache_entry
                        if cg_id:
                            id_to_symbol[cg_id] = symbol

                    for coin in data:
                        coin_id = coin["id"]
                        # 使用反向映射查找 symbol
                        if coin_id in id_to_symbol:
                            symbol = id_to_symbol[coin_id]
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
