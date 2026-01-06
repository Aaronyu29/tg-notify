"""
实时价格监控器 - 使用配置文件
监控 Binance 永续合约价格，根据配置文件中的规则自动发送告警
"""

import asyncio
import json
import sys
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import websockets
from python_socks.async_.asyncio import Proxy

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from alert_generator import AlertGenerator, AlertRule
from monitor_config import (
    ALERT_RULES,
    SAMPLE_INTERVAL,
    ALERT_COOLDOWN,
    WS_URL,
    VERBOSE,
    TOP_N_DISPLAY
)
from chinese_converter import (
    number_to_chinese,
    price_to_chinese
)
from logger import Logger
from coingecko_client import CoinGeckoClient


# ========== 数据结构 ==========
@dataclass
class PricePoint:
    timestamp: float
    price: float
    volume: float = 0.0  # 交易量（USDT）


class ConfigurableMonitor:
    """可配置的实时价格监控器"""

    def __init__(self):
        # 初始化日志器
        self.logger = Logger(name="monitor", keep_hours=24)

        # 计算采样间隔（分钟）
        self.sample_interval_minutes = SAMPLE_INTERVAL / 60  # 例如: 30秒 = 0.5分钟

        # 计算最大历史深度（考虑采样间隔）
        self.max_window = max(rule["window_minutes"] for rule in ALERT_RULES)
        # 例如: 5分钟窗口，30秒采样 = 5 / 0.5 + 1 = 11个点
        self.max_history = int(self.max_window / self.sample_interval_minutes) + 1

        # 价格历史: {symbol: deque of PricePoint}
        self.price_history: dict[str, deque] = {}
        # 最新价格: {symbol: price}
        self.latest_prices: dict[str, float] = {}
        # 最新交易量: {symbol: volume}
        self.latest_volumes: dict[str, float] = {}
        # 上次采样时间
        self.last_sample_time = 0
        # 运行状态
        self.running = False
        # 告警冷却: {(symbol, rule_name): last_alert_time}
        self.alert_cooldowns: dict[tuple, float] = {}

        # 创建告警生成器
        self.alert_generator = AlertGenerator()

        # 创建 CoinGecko 客户端
        self.coingecko = CoinGeckoClient()
        self.market_data = {}  # 存储市值数据
        self.last_market_update = 0

        # 添加规则
        self._setup_rules()

    def _setup_rules(self):
        """根据配置文件设置告警规则"""
        self.logger.info("📋 加载告警规则:")

        for rule_config in ALERT_RULES:
            name = rule_config["name"]
            window = rule_config["window_minutes"]
            threshold = rule_config["threshold"]
            direction = rule_config["direction"]
            priority = rule_config["priority"]

            # 根据方向创建条件
            if direction == "up":
                condition = lambda data, t=threshold: data.get("change_percent", 0) > t
            else:  # down
                condition = lambda data, t=threshold: data.get("change_percent", 0) < -t

            # 创建规则 - 不需要 message_template，我们会直接发送 JSON
            rule = AlertRule(
                name=name,
                condition=condition,
                message_template="",  # 不使用模板
                priority=priority
            )

            self.alert_generator.add_rule(rule)

            # 格式化时间窗口显示
            if window < 1:
                window_text = f"{int(window * 60)}秒"
            else:
                window_text = f"{int(window)}分钟"

            self.logger.info(f"  ✓ {name} ({window_text}, {direction}, {priority})")

    def _get_or_create_history(self, symbol: str) -> deque:
        """获取或创建币种的价格历史队列"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.max_history)
        return self.price_history[symbol]

    def _sample_prices(self):
        """采样当前所有币种的价格到历史记录"""
        now = time.time()
        sampled_count = 0

        for symbol, price in self.latest_prices.items():
            history = self._get_or_create_history(symbol)
            volume = self.latest_volumes.get(symbol, 0.0)
            history.append(PricePoint(timestamp=now, price=price, volume=volume))
            sampled_count += 1

        self.last_sample_time = now
        return sampled_count

    def _calculate_change(self, symbol: str, window_minutes: float) -> Optional[tuple[float, float, float]]:
        """
        计算指定时间窗口内的涨跌幅

        Args:
            window_minutes: 时间窗口（分钟），支持小数（如0.5表示30秒）

        Returns:
            (change_percent, current_price, old_price) 或 None
        """
        if symbol not in self.price_history:
            return None

        history = self.price_history[symbol]

        # 计算需要多少个采样点
        # 例如: 30秒(0.5分钟) / 0.5分钟采样间隔 = 1个点
        # 例如: 5分钟 / 0.5分钟采样间隔 = 10个点
        samples_needed = int(window_minutes / self.sample_interval_minutes)

        # 需要 samples_needed + 1 个点（包括当前点）
        if len(history) < samples_needed + 1:
            return None

        current_price = self.latest_prices.get(symbol)
        if not current_price:
            return None

        # 获取 window_minutes 分钟前的价格
        # history[-1] 是最新的，history[-(samples_needed + 1)] 是 window_minutes 前的
        old_point = history[-(samples_needed + 1)]
        old_price = old_point.price

        if old_price <= 0:
            return None

        change_percent = (current_price - old_price) / old_price * 100
        return change_percent, current_price, old_price

    def _can_alert(self, symbol: str, rule_name: str) -> bool:
        """检查是否可以发送告警（防止刷屏）"""
        key = (symbol, rule_name)
        now = time.time()
        last_time = self.alert_cooldowns.get(key, 0)

        if now - last_time >= ALERT_COOLDOWN:
            self.alert_cooldowns[key] = now
            return True
        return False

    def _check_alerts(self):
        """检查所有币种和规则，触发告警"""
        alerts_sent = 0

        # 按规则检查
        for rule_config in ALERT_RULES:
            window = rule_config["window_minutes"]
            rule_name = rule_config["name"]

            for symbol in list(self.latest_prices.keys()):
                result = self._calculate_change(symbol, window)
                if result is None:
                    continue

                change_percent, current_price, old_price = result

                # 检查冷却
                if not self._can_alert(symbol, rule_name):
                    continue

                # 准备数据用于规则检查
                data = {
                    "symbol": symbol,
                    "change_percent": change_percent,
                    "price": current_price,
                    "old_price": old_price
                }

                # 检查规则是否触发
                for rule in self.alert_generator.rules:
                    if rule.name == rule_name and rule.check(data):
                        # 构建精简的 JSON 消息
                        symbol_short = symbol.replace("USDT", "")
                        message = {
                            "upOrDown": number_to_chinese(change_percent, is_percent=True),
                            "symbol": symbol_short,
                            "currentPrice": price_to_chinese(current_price),
                            "beforePrice": price_to_chinese(old_price)
                        }

                        # 转换为 JSON 字符串并发送
                        message_json = json.dumps(message, ensure_ascii=False)
                        success = self.alert_generator.send_alert(message_json)

                        if success:
                            alerts_sent += 1
                            self.logger.info(f"[ALERT] {symbol}: {change_percent:+.2f}% - {rule_name}")
                            if VERBOSE:
                                self.logger.debug(f"告警详情: {message_json}")
                        else:
                            self.logger.error(f"[ALERT FAILED] {symbol}: {change_percent:+.2f}% - {rule_name}")

        return alerts_sent

    async def _handle_message(self, data: list):
        """处理 WebSocket 消息"""
        for ticker in data:
            symbol = ticker.get("s", "")
            if not symbol.endswith("USDT"):
                continue

            price = float(ticker.get("c", 0))
            volume = float(ticker.get("q", 0))  # quote asset volume (USDT)

            if price > 0:
                self.latest_prices[symbol] = price
                self.latest_volumes[symbol] = volume

    def _get_top_movers(self, window_minutes: int, top_n: int = 5) -> tuple[list, list]:
        """
        获取涨跌幅最大的币种

        Returns:
            (top_gainers, top_losers) - 涨幅榜和跌幅榜
            每个元素是 (symbol, change_percent, current_price, old_price, window_volume)
        """
        movers = []
        for symbol in self.latest_prices.keys():
            result = self._calculate_change(symbol, window_minutes)
            if result is not None:
                change_percent, current_price, old_price = result

                # 计算时间窗口内的交易量
                window_volume = self._calculate_window_volume(symbol, window_minutes)

                movers.append((symbol, change_percent, current_price, old_price, window_volume))

        # 按涨跌幅排序
        movers.sort(key=lambda x: x[1], reverse=True)

        # 涨幅榜：前 top_n 个
        top_gainers = movers[:top_n] if movers else []

        # 跌幅榜：后 top_n 个（倒序）
        top_losers = movers[-top_n:][::-1] if len(movers) >= top_n else movers[::-1]

        return top_gainers, top_losers

    def _calculate_window_volume(self, symbol: str, window_minutes: float) -> float:
        """
        计算时间窗口内的交易量总和

        Args:
            symbol: 币种符号
            window_minutes: 时间窗口（分钟）

        Returns:
            交易量总和（USDT）
        """
        if symbol not in self.price_history:
            return 0.0

        history = self.price_history[symbol]
        samples_needed = int(window_minutes / self.sample_interval_minutes)

        if len(history) < samples_needed + 1:
            return 0.0

        # 计算窗口内所有采样点的交易量总和
        total_volume = 0.0
        for i in range(samples_needed + 1):
            point = history[-(i + 1)]
            total_volume += point.volume

        return total_volume

    def _update_market_data(self):
        """更新市值数据（每5分钟）"""
        now = time.time()
        if now - self.last_market_update < 300:  # 5分钟更新一次
            return

        try:
            # 获取 Top 50 币种的市值数据
            top_symbols = list(self.latest_prices.keys())[:50]
            if top_symbols:
                self.market_data = self.coingecko.get_market_data(top_symbols)
                self.last_market_update = now
        except Exception as e:
            self.logger.error(f"更新市值数据失败: {e}")

    async def _sample_loop(self):
        """定时采样循环"""
        while self.running:
            await asyncio.sleep(SAMPLE_INTERVAL)

            now_str = datetime.now().strftime("%H:%M:%S")
            sampled = self._sample_prices()

            # 更新市值数据（每5分钟）
            self._update_market_data()

            # 检查告警
            try:
                alerts = self._check_alerts()
            except Exception as e:
                self.logger.exception(f"检查告警时发生异常: {e}")
                alerts = 0

            # 状态输出
            history_len = 0
            if self.price_history:
                history_len = len(next(iter(self.price_history.values())))

            self.logger.info(f"\n[{now_str}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.logger.info(f"  📊 采样: {sampled} 个币种 | 历史: {history_len}/{self.max_history} 点")

            # 显示涨跌幅 Top N - 每个时间窗口独立判断
            # 获取所有不同的时间窗口并排序
            windows_to_display = sorted(set(rule["window_minutes"] for rule in ALERT_RULES))

            has_any_display = False  # 标记是否有任何窗口可以显示

            # 遍历每个时间窗口
            for window in windows_to_display:
                # 格式化时间窗口显示
                if window < 1:
                    window_text = f"{int(window * 60)}秒"
                else:
                    window_text = f"{int(window)}分钟"

                # 计算需要的采样点数
                samples_needed = int(window / self.sample_interval_minutes)

                # 检查是否有足够的历史数据（独立判断每个窗口）
                if history_len < samples_needed + 1:
                    # 这个窗口数据不够，跳过
                    continue

                has_any_display = True
                top_gainers, top_losers = self._get_top_movers(window, TOP_N_DISPLAY)

                # 显示涨幅榜
                if top_gainers:
                    self.logger.info(f"  🚀 {window_text}涨幅榜 Top {TOP_N_DISPLAY}:")
                    for symbol, change, current_price, old_price, window_volume in top_gainers:
                        # 检查是否超过任何阈值
                        alert_emoji = ""
                        for rule in ALERT_RULES:
                            if rule["window_minutes"] == window:
                                if rule["direction"] == "up" and change > rule["threshold"]:
                                    alert_emoji = "⚠️"

                        # 获取市值数据
                        market_info = self.market_data.get(symbol, {})
                        market_cap = market_info.get("market_cap", 0)
                        fdv = market_info.get("fdv", 0)

                        # 格式化显示
                        volume_str = self.coingecko.format_volume(window_volume)
                        market_cap_str = self.coingecko.format_market_cap(market_cap)
                        fdv_str = self.coingecko.format_market_cap(fdv)

                        self.logger.info(
                            f"      🚀 {symbol}: {change:+.2f}% | "
                            f"价格: ${current_price:.6f} | "
                            f"{window_text}量: {volume_str} | "
                            f"市值: {market_cap_str} | "
                            f"FDV: {fdv_str} {alert_emoji}"
                        )

                # 显示跌幅榜
                if top_losers:
                    self.logger.info(f"  📉 {window_text}跌幅榜 Top {TOP_N_DISPLAY}:")
                    for symbol, change, current_price, old_price, window_volume in top_losers:
                        # 检查是否超过任何阈值
                        alert_emoji = ""
                        for rule in ALERT_RULES:
                            if rule["window_minutes"] == window:
                                if rule["direction"] == "down" and change < -rule["threshold"]:
                                    alert_emoji = "⚠️"

                        # 获取市值数据
                        market_info = self.market_data.get(symbol, {})
                        market_cap = market_info.get("market_cap", 0)
                        fdv = market_info.get("fdv", 0)

                        # 格式化显示
                        volume_str = self.coingecko.format_volume(window_volume)
                        market_cap_str = self.coingecko.format_market_cap(market_cap)
                        fdv_str = self.coingecko.format_market_cap(fdv)

                        self.logger.info(
                            f"      📉 {symbol}: {change:+.2f}% | "
                            f"价格: ${current_price:.6f} | "
                            f"{window_text}量: {volume_str} | "
                            f"市值: {market_cap_str} | "
                            f"FDV: {fdv_str} {alert_emoji}"
                        )

            # 显示告警状态或等待提示
            if has_any_display:
                # 告警状态
                if alerts > 0:
                    self.logger.info(f"  🚨 已发送 {alerts} 条告警")
                else:
                    self.logger.info(f"  ✅ 暂无币种触发告警阈值")

                # 显示还在等待的窗口
                waiting_windows = []
                for window in windows_to_display:
                    samples_needed = int(window / self.sample_interval_minutes)
                    if history_len < samples_needed + 1:
                        if window < 1:
                            window_text = f"{int(window * 60)}秒"
                        else:
                            window_text = f"{int(window)}分钟"
                        remaining = samples_needed + 1 - history_len
                        waiting_windows.append(f"{window_text}(还需{remaining}点)")

                if waiting_windows:
                    self.logger.info(f"  ⏳ 等待数据: {', '.join(waiting_windows)}")
            else:
                # 所有窗口都没有足够数据
                remaining_samples = self.max_history - history_len
                remaining_time = remaining_samples * SAMPLE_INTERVAL
                self.logger.info(f"  ⏳ 等待历史数据积累中... (还需 {remaining_samples} 个采样点，约 {remaining_time} 秒)")

    async def _websocket_loop(self):
        """WebSocket 连接循环"""
        while self.running:
            try:
                self.logger.info("[WS] 正在连接 Binance WebSocket...")

                # 配置代理
                proxy = Proxy.from_url('http://localhost:7897')
                sock = await proxy.connect(dest_host='fstream.binance.com', dest_port=443)

                async with websockets.connect(
                    WS_URL,
                    ping_interval=20,
                    sock=sock,
                    server_hostname='fstream.binance.com'
                ) as ws:
                    self.logger.info("[WS] 连接成功！")

                    async for message in ws:
                        if not self.running:
                            break

                        try:
                            data = json.loads(message)
                            await self._handle_message(data)
                        except json.JSONDecodeError as e:
                            self.logger.debug(f"[WS] JSON 解析失败: {e}")
                        except Exception as e:
                            self.logger.error(f"[WS] 处理消息时发生异常: {e}")

            except Exception as e:
                self.logger.error(f"[WS] 连接断开: {e}")
                if self.running:
                    self.logger.info("[WS] 5秒后重连...")
                    await asyncio.sleep(5)

    async def run(self):
        """启动监控"""
        self.logger.info("=" * 60)
        self.logger.info("🔍 实时价格监控器启动")
        self.logger.info(f"   采样间隔: {SAMPLE_INTERVAL} 秒")
        self.logger.info(f"   最大时间窗口: {self.max_window} 分钟")
        self.logger.info(f"   告警冷却: {ALERT_COOLDOWN} 秒")
        self.logger.info(f"   规则数量: {len(ALERT_RULES)}")
        self.logger.info("=" * 60)

        self.running = True

        try:
            # 并行运行 WebSocket 和采样循环
            await asyncio.gather(
                self._websocket_loop(),
                self._sample_loop()
            )
        except KeyboardInterrupt:
            self.logger.info("收到退出信号")
        except Exception as e:
            self.logger.exception(f"监控运行时发生异常: {e}")
        finally:
            self.running = False
            self.logger.info("[INFO] 监控已停止")


def main():
    monitor = ConfigurableMonitor()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\n[INFO] 收到退出信号")
    except Exception as e:
        print(f"\n[ERROR] 程序异常退出: {e}")


if __name__ == "__main__":
    main()
