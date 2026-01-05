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
    price_to_chinese,
    time_to_chinese,
    window_to_chinese,
    threshold_to_chinese
)


# ========== 数据结构 ==========
@dataclass
class PricePoint:
    timestamp: float
    price: float


class ConfigurableMonitor:
    """可配置的实时价格监控器"""

    def __init__(self):
        # 计算最大历史深度
        self.max_window = max(rule["window_minutes"] for rule in ALERT_RULES)
        self.max_history = self.max_window + 1

        # 价格历史: {symbol: deque of PricePoint}
        self.price_history: dict[str, deque] = {}
        # 最新价格: {symbol: price}
        self.latest_prices: dict[str, float] = {}
        # 上次采样时间
        self.last_sample_time = 0
        # 运行状态
        self.running = False
        # 告警冷却: {(symbol, rule_name): last_alert_time}
        self.alert_cooldowns: dict[tuple, float] = {}

        # 创建告警生成器
        self.alert_generator = AlertGenerator()

        # 添加规则
        self._setup_rules()

    def _setup_rules(self):
        """根据配置文件设置告警规则"""
        print("\n📋 加载告警规则:")

        for rule_config in ALERT_RULES:
            name = rule_config["name"]
            window = rule_config["window_minutes"]
            threshold = rule_config["threshold"]
            direction = rule_config["direction"]
            priority = rule_config["priority"]

            # 根据方向创建条件
            if direction == "up":
                condition = lambda data, t=threshold: data.get("change_percent", 0) > t
                direction_text = "暴涨"
            else:  # down
                condition = lambda data, t=threshold: data.get("change_percent", 0) < -t
                direction_text = "暴跌"

            # 转换为中文
            window_chinese = window_to_chinese(window)
            threshold_chinese = threshold_to_chinese(threshold)

            # 创建规则 - 使用中文格式，无表情符号
            rule = AlertRule(
                name=name,
                condition=condition,
                message_template=(
                    f"{{symbol}} {window_chinese}内{direction_text}{threshold_chinese}\n"
                    f"涨跌幅: {{change_percent_chinese}}\n"
                    f"当前价格: {{price_chinese}}\n"
                    f"{window_chinese}前: {{old_price_chinese}}\n"
                    f"检测时间: {{time_chinese}}"
                ),
                priority=priority
            )

            self.alert_generator.add_rule(rule)
            print(f"  ✓ {name} ({window}分钟, {direction}, {priority})")

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
            history.append(PricePoint(timestamp=now, price=price))
            sampled_count += 1

        self.last_sample_time = now
        return sampled_count

    def _calculate_change(self, symbol: str, window_minutes: int) -> Optional[tuple[float, float, float]]:
        """
        计算指定时间窗口内的涨跌幅

        Returns:
            (change_percent, current_price, old_price) 或 None
        """
        if symbol not in self.price_history:
            return None

        history = self.price_history[symbol]
        if len(history) < window_minutes + 1:
            return None

        current_price = self.latest_prices.get(symbol)
        if not current_price:
            return None

        # 获取 window_minutes 分钟前的价格
        # history[0] 是最早的，history[-1] 是最新的
        old_point = history[-(window_minutes + 1)]
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
        now_str = datetime.now().strftime("%H:%M:%S")

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

                # 准备数据 - 添加中文格式
                data = {
                    "symbol": symbol,
                    "change_percent": change_percent,
                    "change_percent_chinese": number_to_chinese(change_percent, is_percent=True),
                    "price": current_price,
                    "price_chinese": price_to_chinese(current_price),
                    "old_price": old_price,
                    "old_price_chinese": price_to_chinese(old_price),
                    "time": now_str,
                    "time_chinese": time_to_chinese(now_str)
                }

                # 使用 alert_generator 检查规则
                results = self.alert_generator.check_and_alert(data)

                if results["triggered_rules"]:
                    alerts_sent += len(results["triggered_rules"])
                    for rule in results["triggered_rules"]:
                        if VERBOSE:
                            print(f"[ALERT] {symbol}: {change_percent:+.2f}% - {rule['rule']}")

        return alerts_sent

    async def _handle_message(self, data: list):
        """处理 WebSocket 消息"""
        for ticker in data:
            symbol = ticker.get("s", "")
            if not symbol.endswith("USDT"):
                continue

            price = float(ticker.get("c", 0))
            if price > 0:
                self.latest_prices[symbol] = price

    def _get_top_movers(self, window_minutes: int, top_n: int = 5) -> list[tuple[str, float]]:
        """获取涨跌幅最大的币种"""
        movers = []
        for symbol in self.latest_prices.keys():
            result = self._calculate_change(symbol, window_minutes)
            if result is not None:
                change_percent, _, _ = result
                movers.append((symbol, change_percent))

        # 按涨跌幅绝对值排序
        movers.sort(key=lambda x: abs(x[1]), reverse=True)
        return movers[:top_n]

    async def _sample_loop(self):
        """定时采样循环"""
        while self.running:
            await asyncio.sleep(SAMPLE_INTERVAL)

            now_str = datetime.now().strftime("%H:%M:%S")
            sampled = self._sample_prices()

            # 检查告警
            alerts = self._check_alerts()

            # 状态输出
            history_len = 0
            if self.price_history:
                history_len = len(next(iter(self.price_history.values())))

            print(f"\n[{now_str}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"  📊 采样: {sampled} 个币种 | 历史: {history_len}/{self.max_history} 分钟")

            # 显示涨跌幅 Top N
            if history_len >= self.max_window + 1:
                # 显示最小时间窗口的 Top N
                min_window = min(rule["window_minutes"] for rule in ALERT_RULES)
                top_movers = self._get_top_movers(min_window, TOP_N_DISPLAY)
                if top_movers:
                    print(f"  🔥 {min_window}分钟涨跌幅 Top {TOP_N_DISPLAY}:")
                    for symbol, change in top_movers:
                        emoji = "🚀" if change > 0 else "📉"
                        # 检查是否超过任何阈值
                        alert_emoji = ""
                        for rule in ALERT_RULES:
                            if rule["window_minutes"] == min_window:
                                if rule["direction"] == "up" and change > rule["threshold"]:
                                    alert_emoji = "⚠️"
                                elif rule["direction"] == "down" and change < -rule["threshold"]:
                                    alert_emoji = "⚠️"
                        print(f"      {emoji} {symbol}: {change:+.2f}% {alert_emoji}")

                # 告警状态
                if alerts > 0:
                    print(f"  🚨 已发送 {alerts} 条告警")
                else:
                    print(f"  ✅ 暂无币种触发告警阈值")
            else:
                remaining = self.max_window + 1 - history_len
                print(f"  ⏳ 等待历史数据积累中... (还需 {remaining} 分钟)")

    async def _websocket_loop(self):
        """WebSocket 连接循环"""
        while self.running:
            try:
                print(f"[WS] 正在连接 Binance WebSocket...")
                async with websockets.connect(WS_URL, ping_interval=20) as ws:
                    print(f"[WS] 连接成功！")

                    async for message in ws:
                        if not self.running:
                            break

                        try:
                            data = json.loads(message)
                            await self._handle_message(data)
                        except json.JSONDecodeError:
                            pass

            except Exception as e:
                print(f"[WS] 连接断开: {e}")
                if self.running:
                    print(f"[WS] 5秒后重连...")
                    await asyncio.sleep(5)

    async def run(self):
        """启动监控"""
        print("=" * 60)
        print("🔍 实时价格监控器启动")
        print(f"   采样间隔: {SAMPLE_INTERVAL} 秒")
        print(f"   最大时间窗口: {self.max_window} 分钟")
        print(f"   告警冷却: {ALERT_COOLDOWN} 秒")
        print(f"   规则数量: {len(ALERT_RULES)}")
        print("=" * 60)

        self.running = True

        try:
            # 并行运行 WebSocket 和采样循环
            await asyncio.gather(
                self._websocket_loop(),
                self._sample_loop()
            )
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            print("\n[INFO] 监控已停止")


def main():
    monitor = ConfigurableMonitor()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\n[INFO] 收到退出信号")


if __name__ == "__main__":
    main()
