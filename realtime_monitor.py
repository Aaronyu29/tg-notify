"""
实时价格监控器 - 结合 WebSocket 和 Alert Generator
监控 Binance 永续合约价格，根据自定义规则自动发送告警
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
sys.path.insert(0, str(Path(__file__).parent.parent))

from alert_generator import AlertGenerator, AlertRule

# ========== 配置文件 ==========
# 你可以在这里配置告警规则

# 时间窗口（分钟）
WINDOW_MINUTES = 5

# 暴涨阈值（百分比）
SURGE_THRESHOLD = 30.0

# 暴跌阈值（百分比，正数）
DROP_THRESHOLD = 30.0

# 采样间隔（秒）
SAMPLE_INTERVAL = 60

# 告警冷却时间（秒），防止同一币种频繁告警
ALERT_COOLDOWN = 900  # 15分钟

# Binance WebSocket URL
WS_URL = "wss://fstream.binance.com/ws/!miniTicker@arr"

# ========== 数据结构 ==========
@dataclass
class PricePoint:
    timestamp: float
    price: float


class RealtimePriceMonitor:
    """实时价格监控器"""

    def __init__(self):
        # 价格历史: {symbol: deque of PricePoint}
        self.price_history: dict[str, deque] = {}
        # 最新价格: {symbol: price}
        self.latest_prices: dict[str, float] = {}
        # 上次采样时间
        self.last_sample_time = 0
        # 运行状态
        self.running = False
        # 告警冷却: {symbol: last_alert_time}
        self.alert_cooldowns: dict[str, float] = {}

        # 创建告警生成器
        self.alert_generator = AlertGenerator()

        # 添加规则
        self._setup_rules()

    def _setup_rules(self):
        """设置告警规则"""

        # 规则 1: 暴涨规则
        surge_rule = AlertRule(
            name=f"price_surge_{WINDOW_MINUTES}min",
            condition=lambda data: data.get("change_percent", 0) > SURGE_THRESHOLD,
            message_template=(
                f"{{symbol}} 在过去 {WINDOW_MINUTES} 分钟暴涨 {{change_percent:.2f}}%\n"
                f"当前价格: ${{price}}\n"
                f"{WINDOW_MINUTES}分钟前: ${{old_price}}\n"
                f"检测时间: {{time}}"
            ),
            priority="high"
        )
        self.alert_generator.add_rule(surge_rule)

        # 规则 2: 暴跌规则
        drop_rule = AlertRule(
            name=f"price_drop_{WINDOW_MINUTES}min",
            condition=lambda data: data.get("change_percent", 0) < -DROP_THRESHOLD,
            message_template=(
                f"{{symbol}} 在过去 {WINDOW_MINUTES} 分钟暴跌 {{change_percent:.2f}}%\n"
                f"当前价格: ${{price}}\n"
                f"{WINDOW_MINUTES}分钟前: ${{old_price}}\n"
                f"检测时间: {{time}}"
            ),
            priority="high"
        )
        self.alert_generator.add_rule(drop_rule)

        print(f"✓ 已添加规则: {WINDOW_MINUTES}分钟暴涨 >{SURGE_THRESHOLD}%")
        print(f"✓ 已添加规则: {WINDOW_MINUTES}分钟暴跌 >{DROP_THRESHOLD}%")

    def _get_or_create_history(self, symbol: str) -> deque:
        """获取或创建币种的价格历史队列"""
        if symbol not in self.price_history:
            # 最多保存 WINDOW_MINUTES + 1 个数据点
            self.price_history[symbol] = deque(maxlen=WINDOW_MINUTES + 1)
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

    def _calculate_change(self, symbol: str) -> Optional[tuple[float, float, float]]:
        """
        计算指定时间窗口内的涨跌幅

        Returns:
            (change_percent, current_price, old_price) 或 None
        """
        if symbol not in self.price_history:
            return None

        history = self.price_history[symbol]
        if len(history) < WINDOW_MINUTES + 1:
            return None

        current_price = self.latest_prices.get(symbol)
        if not current_price:
            return None

        # 获取 WINDOW_MINUTES 分钟前的价格
        old_point = history[0]  # 最早的数据点
        old_price = old_point.price

        if old_price <= 0:
            return None

        change_percent = (current_price - old_price) / old_price * 100
        return change_percent, current_price, old_price

    def _can_alert(self, symbol: str) -> bool:
        """检查是否可以发送告警（防止刷屏）"""
        now = time.time()
        last_time = self.alert_cooldowns.get(symbol, 0)

        if now - last_time >= ALERT_COOLDOWN:
            self.alert_cooldowns[symbol] = now
            return True
        return False

    def _check_alerts(self):
        """检查所有币种，触发告警"""
        alerts_sent = 0
        now_str = datetime.now().strftime("%H:%M:%S")

        for symbol in list(self.latest_prices.keys()):
            result = self._calculate_change(symbol)
            if result is None:
                continue

            change_percent, current_price, old_price = result

            # 检查冷却
            if not self._can_alert(symbol):
                continue

            # 准备数据
            data = {
                "symbol": symbol,
                "change_percent": change_percent,
                "price": current_price,
                "old_price": old_price,
                "time": now_str
            }

            # 使用 alert_generator 检查规则
            results = self.alert_generator.check_and_alert(data)

            if results["triggered_rules"]:
                alerts_sent += len(results["triggered_rules"])
                for rule in results["triggered_rules"]:
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

    def _get_top_movers(self, top_n: int = 5) -> list[tuple[str, float]]:
        """获取涨跌幅最大的币种"""
        movers = []
        for symbol in self.latest_prices.keys():
            result = self._calculate_change(symbol)
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
            print(f"  📊 采样: {sampled} 个币种 | 历史: {history_len}/{WINDOW_MINUTES + 1} 分钟")

            # 显示涨跌幅 Top 5
            if history_len >= WINDOW_MINUTES + 1:
                top_movers = self._get_top_movers(5)
                if top_movers:
                    print(f"  🔥 {WINDOW_MINUTES}分钟涨跌幅 Top 5:")
                    for symbol, change in top_movers:
                        emoji = "🚀" if change > 0 else "📉"
                        status = "⚠️" if abs(change) >= min(SURGE_THRESHOLD, DROP_THRESHOLD) else ""
                        print(f"      {emoji} {symbol}: {change:+.2f}% {status}")

                # 告警状态
                if alerts > 0:
                    print(f"  🚨 已发送 {alerts} 条告警")
                else:
                    print(f"  ✅ 暂无币种触发告警阈值")
            else:
                remaining = WINDOW_MINUTES + 1 - history_len
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
        print(f"   时间窗口: {WINDOW_MINUTES} 分钟")
        print(f"   采样间隔: {SAMPLE_INTERVAL} 秒")
        print(f"   暴涨阈值: >{SURGE_THRESHOLD}%")
        print(f"   暴跌阈值: >{DROP_THRESHOLD}%")
        print(f"   告警冷却: {ALERT_COOLDOWN} 秒")
        print("=" * 60)
        print()

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
    monitor = RealtimePriceMonitor()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\n[INFO] 收到退出信号")


if __name__ == "__main__":
    main()
