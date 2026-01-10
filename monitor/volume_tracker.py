"""
交易量动能追踪器
负责追踪分钟级交易量变化
"""

from collections import deque, defaultdict
from typing import Dict, Optional
import statistics


class VolumeTracker:
    """交易量动能追踪器"""

    def __init__(self, history_size: int = 20):
        """
        初始化交易量追踪器

        Args:
            history_size: 历史快照数量
        """
        # 存储每个币种的交易量快照历史
        # {symbol: deque([volume_snapshot_1, volume_snapshot_2, ...])}
        self.volume_snapshots: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_size)
        )

        # 存储历史平均交易量（用于异常检测）
        self.historical_avg: Dict[str, float] = {}

    def update_snapshot(self, symbol: str, volume: float):
        """
        更新交易量快照

        Args:
            symbol: 币种符号
            volume: 24h累计交易量
        """
        self.volume_snapshots[symbol].append(volume)

        # 更新历史平均值（使用最近10个快照）
        if len(self.volume_snapshots[symbol]) >= 10:
            recent_snapshots = list(self.volume_snapshots[symbol])[-10:]
            # 计算增量交易量的平均值
            incremental_volumes = [
                recent_snapshots[i] - recent_snapshots[i-1]
                for i in range(1, len(recent_snapshots))
            ]
            if incremental_volumes:
                self.historical_avg[symbol] = statistics.mean(incremental_volumes)

    def analyze(self, symbol: str) -> Optional[dict]:
        """
        分析交易量动能

        Args:
            symbol: 币种符号

        Returns:
            {
                "incremental_volume": float,      # 最近30秒增量
                "volume_change_rate": float,      # 变化率(%)
                "volume_acceleration": float,     # 交易量加速度
                "is_abnormal_surge": bool,        # 是否异常放量
                "score": int                      # 交易量评分 0-100
            }
        """
        snapshots = self.volume_snapshots.get(symbol)
        if not snapshots or len(snapshots) < 3:
            return None

        # 获取最近3个快照
        recent = list(snapshots)[-3:]

        # 1. 计算增量交易量
        incremental_volumes = [
            recent[i] - recent[i-1]
            for i in range(1, len(recent))
        ]

        # 2. 计算交易量变化率
        if incremental_volumes[0] > 0:
            volume_change_rate = (
                (incremental_volumes[-1] - incremental_volumes[0])
                / incremental_volumes[0] * 100
            )
        else:
            volume_change_rate = 0

        # 3. 计算交易量加速度
        volume_acceleration = incremental_volumes[-1] - incremental_volumes[0]

        # 4. 异常放量检测
        historical_avg = self.historical_avg.get(symbol, 0)
        is_abnormal_surge = (
            incremental_volumes[-1] > historical_avg * 3
            if historical_avg > 0 else False
        )

        # 5. 计算评分
        score = self._calculate_score(
            volume_change_rate,
            is_abnormal_surge,
            volume_acceleration
        )

        return {
            "incremental_volume": incremental_volumes[-1],
            "volume_change_rate": volume_change_rate,
            "volume_acceleration": volume_acceleration,
            "is_abnormal_surge": is_abnormal_surge,
            "score": score
        }

    def _calculate_score(self, change_rate: float, is_surge: bool,
                        acceleration: float) -> int:
        """
        计算交易量评分

        Args:
            change_rate: 变化率
            is_surge: 是否异常放量
            acceleration: 加速度

        Returns:
            int: 评分 0-100
        """
        score = 50  # 基础分

        # 交易量放大
        if change_rate > 100:
            score += 30
        elif change_rate > 50:
            score += 20
        elif change_rate > 20:
            score += 10

        # 异常放量
        if is_surge:
            score += 15

        # 加速度
        if acceleration > 0:
            score += 5

        return min(score, 100)
