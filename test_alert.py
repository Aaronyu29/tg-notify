"""
测试程序 - 发送涨幅最高和最低的币种告警
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

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from alert_generator import AlertGenerator
from chinese_converter import (
    number_to_chinese,
    price_to_chinese,
    time_to_chinese,
    window_to_chinese
)

# ========== 配置 ==========
WINDOW_MINUTES = 1  # 1分钟窗口
SAMPLE_INTERVAL = 60  # 60秒采样一次
WS_URL = "wss://fstream.binance.com/ws/!miniTicker@arr"


@dataclass
class PricePoint:
    timestamp: float
    price: float


class TestMonitor:
    """测试监控器"""

    def __init__(self):
        self.price_history: dict[str, deque] = {}
        self.latest_prices: dict[str, float] = {}
        self.last_sample_time = 0
        self.running = False
        self.alert_generator = AlertGenerator()
        self.samples_collected = 0

    def _get_or_create_history(self, symbol: str) -> deque:
        """获取或创建币种的价格历史队列"""
        if symbol not in self.price_history:
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
        self.samples_collected += 1
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

        old_point = history[0]
        old_price = old_point.price

        if old_price <= 0:
            return None

        change_percent = (current_price - old_price) / old_price * 100
        return change_percent, current_price, old_price

    def _get_top_and_bottom(self) -> tuple[Optional[tuple], Optional[tuple]]:
        """
        获取涨幅最高和最低的币种

        Returns:
            (top_gainer, top_loser) 每个是 (symbol, change_percent, current_price, old_price)
        """
        changes = []

        for symbol in self.latest_prices.keys():
            result = self._calculate_change(symbol)
            if result is not None:
                change_percent, current_price, old_price = result
                changes.append((symbol, change_percent, current_price, old_price))

        if not changes:
            return None, None

        # 按涨跌幅排序
        changes.sort(key=lambda x: x[1], reverse=True)

        top_gainer = changes[0] if changes else None
        top_loser = changes[-1] if changes else None

        return top_gainer, top_loser

    def _send_alert(self, symbol: str, change_percent: float, current_price: float,
                    old_price: float, alert_type: str):
        """发送告警"""
        now_str = datetime.now().strftime("%H:%M:%S")

        # 转换为中文
        change_percent_chinese = number_to_chinese(change_percent, is_percent=True)
        price_chinese = price_to_chinese(current_price)
        old_price_chinese = price_to_chinese(old_price)
        time_chinese = time_to_chinese(now_str)
        window_chinese = window_to_chinese(WINDOW_MINUTES)

        # 生成消息
        if alert_type == "top_gainer":
            title = f"{symbol} {window_chinese}内涨幅最高"
        else:
            title = f"{symbol} {window_chinese}内跌幅最大"

        message = (
            f"{title}\n"
            f"涨跌幅: {change_percent_chinese}\n"
            f"当前价格: {price_chinese}\n"
            f"{window_chinese}前: {old_price_chinese}\n"
            f"检测时间: {time_chinese}"
        )

        print(f"\n{'='*60}")
        print(f"发送告警: {alert_type}")
        print(f"{'='*60}")
        print(message)
        print(f"{'='*60}")

        # 发送到 FWAlert
        success = self.alert_generator.send_alert(message)

        if success:
            print(f"✓ 告警发送成功: {symbol} ({change_percent:+.2f}%)")
        else:
            print(f"✗ 告警发送失败: {symbol}")

        return success

    async def _handle_message(self, data: list):
        """处理 WebSocket 消息"""
        for ticker in data:
            symbol = ticker.get("s", "")
            if not symbol.endswith("USDT"):
                continue

            price = float(ticker.get("c", 0))
            if price > 0:
                self.latest_prices[symbol] = price

    async def _sample_loop(self):
        """定时采样循环"""
        print(f"\n开始采样，需要等待 {WINDOW_MINUTES + 1} 分钟积累历史数据...")
        print(f"采样间隔: {SAMPLE_INTERVAL} 秒\n")

        while self.running:
            await asyncio.sleep(SAMPLE_INTERVAL)

            now_str = datetime.now().strftime("%H:%M:%S")
            sampled = self._sample_prices()

            history_len = 0
            if self.price_history:
                history_len = len(next(iter(self.price_history.values())))

            print(f"[{now_str}] 采样 #{self.samples_collected}: {sampled} 个币种 | 历史: {history_len}/{WINDOW_MINUTES + 1} 分钟")

            # 当历史数据足够时，发送告警
            if history_len >= WINDOW_MINUTES + 1:
                print(f"\n历史数据已足够，开始分析...")

                top_gainer, top_loser = self._get_top_and_bottom()

                if top_gainer:
                    symbol, change, price, old_price = top_gainer
                    print(f"\n涨幅最高: {symbol} {change:+.2f}%")
                    self._send_alert(symbol, change, price, old_price, "top_gainer")

                if top_loser:
                    symbol, change, price, old_price = top_loser
                    print(f"\n跌幅最大: {symbol} {change:+.2f}%")
                    self._send_alert(symbol, change, price, old_price, "top_loser")

                # 发送完成后停止
                print(f"\n测试完成，停止监控...")
                self.running = False
                break

    async def _websocket_loop(self):
        """WebSocket 连接循环"""
        while self.running:
            try:
                print(f"[WS] 正在连接 Binance WebSocket...")
                async with websockets.connect(WS_URL, ping_interval=20) as ws:
                    print(f"[WS] 连接成功！开始接收价格数据...\n")

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
        """启动测试"""
        print("=" * 60)
        print("测试程序 - 发送涨跌幅最高/最低币种告警")
        print("=" * 60)
        print(f"时间窗口: {WINDOW_MINUTES} 分钟")
        print(f"采样间隔: {SAMPLE_INTERVAL} 秒")
        print(f"需要等待: {WINDOW_MINUTES + 1} 分钟")
        print("=" * 60)

        self.running = True

        try:
            await asyncio.gather(
                self._websocket_loop(),
                self._sample_loop()
            )
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            print("\n[INFO] 测试结束")


def main():
    monitor = TestMonitor()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\n[INFO] 收到退出信号")


if __name__ == "__main__":
    main()
