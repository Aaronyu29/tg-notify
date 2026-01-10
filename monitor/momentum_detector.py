"""
实时动能检测器
负责判断价格是否持续上涨、高位震荡或开始回落
"""

from enum import Enum
from collections import deque
from typing import Optional
import statistics


class MomentumState(Enum):
    """动能状态枚举"""
    ACCELERATING = "accelerating"      # 加速上涨
    STEADY_RISE = "steady_rise"        # 稳定上涨
    CONSOLIDATING = "consolidating"    # 高位震荡
    DECELERATING = "decelerating"      # 减速/回落


class MomentumDetector:
    """实时动能检测器"""

    def __init__(self, sample_interval: int = 30):
        """
        初始化动能检测器

        Args:
            sample_interval: 采样间隔（秒）
        """
        self.sample_interval = sample_interval

    def analyze(self, price_history: deque) -> Optional[dict]:
        """
        分析价格动能

        Args:
            price_history: 价格历史队列（至少3个点）

        Returns:
            {
                "state": MomentumState,      # 动能状态
                "acceleration": float,        # 价格加速度
                "velocity": float,            # 价格速度
                "volatility": float,          # 短期波动率
                "drawdown": float,            # 峰值回撤
                "score": int                  # 动能评分 0-100
            }
        """
        if not price_history or len(price_history) < 3:
            return None

        # 获取最近3个价格点
        recent = list(price_history)[-3:]
        prices = [p.price for p in recent]

        # 1. 计算价格速度（一阶导数）
        velocity_1 = (prices[1] - prices[0]) / self.sample_interval
        velocity_2 = (prices[2] - prices[1]) / self.sample_interval

        # 2. 计算价格加速度（二阶导数）
        acceleration = (velocity_2 - velocity_1) / self.sample_interval

        # 3. 计算短期波动率
        mean_price = statistics.mean(prices)
        std_price = statistics.stdev(prices) if len(prices) > 1 else 0
        volatility = std_price / mean_price if mean_price > 0 else 0

        # 4. 计算峰值回撤
        peak_price = max(prices)
        current_price = prices[-1]
        drawdown = (peak_price - current_price) / peak_price if peak_price > 0 else 0

        # 5. 判断动能状态
        state = self._determine_state(acceleration, velocity_2, volatility, drawdown)

        # 6. 计算动能评分
        score = self._calculate_score(state, acceleration, volatility, drawdown)

        return {
            "state": state,
            "acceleration": acceleration,
            "velocity": velocity_2,
            "volatility": volatility,
            "drawdown": drawdown,
            "score": score
        }

    def _determine_state(self, acceleration: float, velocity: float,
                        volatility: float, drawdown: float) -> MomentumState:
        """
        判断动能状态

        Args:
            acceleration: 价格加速度
            velocity: 价格速度
            volatility: 波动率
            drawdown: 回撤

        Returns:
            MomentumState: 动能状态
        """
        # 加速上涨：加速度>0，速度>0，波动率低，无明显回撤
        if acceleration > 0 and velocity > 0 and volatility < 0.02 and drawdown < 0.01:
            return MomentumState.ACCELERATING

        # 稳定上涨：速度>0，无明显回撤
        elif velocity > 0 and drawdown < 0.02:
            return MomentumState.STEADY_RISE

        # 高位震荡：波动率高
        elif volatility > 0.03:
            return MomentumState.CONSOLIDATING

        # 减速/回落
        else:
            return MomentumState.DECELERATING

    def _calculate_score(self, state: MomentumState, acceleration: float,
                        volatility: float, drawdown: float) -> int:
        """
        计算动能评分

        Args:
            state: 动能状态
            acceleration: 加速度
            volatility: 波动率
            drawdown: 回撤

        Returns:
            int: 评分 0-100
        """
        if state == MomentumState.ACCELERATING:
            return 100
        elif state == MomentumState.STEADY_RISE:
            return 70
        elif state == MomentumState.CONSOLIDATING:
            return 30
        else:
            return 0
