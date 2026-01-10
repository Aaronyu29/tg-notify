"""
交易决策引擎
综合多维度指标生成买入/观望建议
"""

from typing import Dict, Optional
from collections import deque
from momentum_detector import MomentumDetector, MomentumState
from volume_tracker import VolumeTracker


class TradingDecisionEngine:
    """交易决策引擎"""

    def __init__(self, momentum_detector: MomentumDetector,
                 volume_tracker: VolumeTracker):
        """
        初始化决策引擎

        Args:
            momentum_detector: 动能检测器
            volume_tracker: 交易量追踪器
        """
        self.momentum_detector = momentum_detector
        self.volume_tracker = volume_tracker

        # 配置参数
        self.confidence_threshold = 70  # 置信度阈值
        self.risk_threshold = 50        # 风险阈值
        self.entry_premium = 0.005      # 入场价溢价（0.5%）
        self.stop_loss_ratio = 0.92     # 止损比例（-8%）
        self.take_profit_ratio = 1.20   # 止盈比例（+20%）

    def make_decision(self, symbol: str, alert_data: dict,
                     price_history: deque, market_data: dict) -> dict:
        """
        生成交易决策

        Args:
            symbol: 币种符号
            alert_data: 告警数据（涨跌幅、价格等）
            price_history: 价格历史队列
            market_data: 市值数据

        Returns:
            {
                "action": "BUY" | "WATCH",
                "confidence": int,      # 置信度 0-100
                "risk_score": int,      # 风险评分 0-100
                "reason": str,          # 决策理由
                "entry_price": float,   # 建议入场价
                "stop_loss": float,     # 止损价
                "take_profit": float,   # 止盈价
                "details": dict         # 详细分析数据
            }
        """
        # 1. 动能分析
        momentum_result = self.momentum_detector.analyze(price_history)
        if not momentum_result:
            return self._default_watch_decision("数据不足，无法分析动能")

        # 2. 交易量分析
        volume_result = self.volume_tracker.analyze(symbol)
        if not volume_result:
            return self._default_watch_decision("交易量数据不足")

        # 3. 多维度评分
        scores = {
            "momentum": momentum_result["score"],
            "volume": volume_result["score"],
            "market_cap": self._score_market_cap(market_data),
            "price_action": self._score_price_action(alert_data)
        }

        # 4. 计算综合置信度
        confidence = self._calculate_confidence(scores)

        # 5. 计算风险评分
        risk_score = self._calculate_risk(
            market_data.get("market_cap", 0),
            momentum_result["volatility"],
            momentum_result["drawdown"]
        )

        # 6. 决策逻辑（激进策略）
        current_price = alert_data["price"]

        if confidence >= self.confidence_threshold and risk_score <= self.risk_threshold:
            action = "BUY"
            reason = self._generate_buy_reason(
                momentum_result, volume_result, scores
            )
        else:
            action = "WATCH"
            reason = self._generate_watch_reason(
                momentum_result, volume_result, scores, risk_score
            )

        # 7. 计算交易计划
        entry_price = current_price * (1 + self.entry_premium)
        stop_loss = current_price * self.stop_loss_ratio
        take_profit = current_price * self.take_profit_ratio

        return {
            "action": action,
            "confidence": confidence,
            "risk_score": risk_score,
            "reason": reason,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "details": {
                "momentum": momentum_result,
                "volume": volume_result,
                "scores": scores
            }
        }

    def _score_market_cap(self, market_data: dict) -> int:
        """
        市值评分 (0-100)
        如果无法获取市值，使用24h交易量作为替代指标

        Args:
            market_data: 市值数据

        Returns:
            int: 评分
        """
        market_cap = market_data.get("market_cap", 0)
        volume_24h = market_data.get("volume_24h", 0)

        # 优先使用市值
        if market_cap and market_cap > 0:
            if market_cap > 1e9:  # >10亿美元
                return 90  # 大盘币，相对安全
            elif market_cap > 1e8:  # >1亿美元
                return 70  # 中盘币，适中
            elif market_cap > 1e7:  # >1000万美元
                return 40  # 小盘币，风险较高
            else:
                return 10  # 微盘币，极高风险

        # 如果没有市值数据，使用24h交易量作为替代指标
        # 交易量大的币种通常流动性好，相对安全
        elif volume_24h and volume_24h > 0:
            if volume_24h > 1e8:  # >1亿美元日交易量
                return 75  # 高流动性，相对安全
            elif volume_24h > 5e7:  # >5000万美元
                return 60  # 中等流动性
            elif volume_24h > 1e7:  # >1000万美元
                return 40  # 低流动性，风险较高
            else:
                return 20  # 极低流动性，高风险

        # 既没有市值也没有交易量数据，给予中等偏低评分
        else:
            return 35  # 数据不足，谨慎对待

    def _score_price_action(self, price_data: dict) -> int:
        """
        价格行为评分 (0-100)

        Args:
            price_data: 价格数据

        Returns:
            int: 评分
        """
        change_percent = abs(price_data.get("change_percent", 0))

        # 涨幅适中最佳（15-30%）
        if 15 <= change_percent <= 30:
            return 90
        elif 30 < change_percent <= 50:
            return 70  # 涨幅过大，追高风险
        elif 10 <= change_percent < 15:
            return 60  # 涨幅偏小
        else:
            return 30  # 涨幅过大或过小

    def _calculate_confidence(self, scores: dict) -> int:
        """
        计算综合置信度

        Args:
            scores: 各维度评分

        Returns:
            int: 置信度 0-100
        """
        # 加权平均
        weights = {
            "momentum": 0.35,      # 动能最重要
            "volume": 0.30,        # 交易量次之
            "market_cap": 0.20,    # 市值风险控制
            "price_action": 0.15   # 价格行为
        }

        confidence = sum(
            scores[key] * weights[key]
            for key in weights
        )

        return int(confidence)

    def _calculate_risk(self, market_cap: float, volatility: float,
                       drawdown: float) -> int:
        """
        计算风险评分(0-100，越高越危险)

        Args:
            market_cap: 市值
            volatility: 波动率
            drawdown: 回撤

        Returns:
            int: 风险评分
        """
        risk = 0

        # 市值风险
        if market_cap < 1e7:
            risk += 40  # 微盘币高风险
        elif market_cap < 1e8:
            risk += 20  # 小盘币中风险

        # 波动率风险
        if volatility > 0.05:
            risk += 30  # 高波动
        elif volatility > 0.03:
            risk += 15

        # 回撤风险
        if drawdown > 0.05:
            risk += 30  # 已经回撤5%
        elif drawdown > 0.02:
            risk += 15

        return min(risk, 100)

    def _generate_buy_reason(self, momentum: dict, volume: dict,
                            scores: dict) -> str:
        """生成买入理由"""
        reasons = []

        # 动能理由
        if momentum["state"] == MomentumState.ACCELERATING:
            reasons.append("价格加速上涨（动能强劲）")
        elif momentum["state"] == MomentumState.STEADY_RISE:
            reasons.append("价格稳定上涨")

        # 交易量理由
        if volume["is_abnormal_surge"]:
            reasons.append(f"交易量异常放大 {volume['volume_change_rate']:.1f}%")
        elif volume["volume_change_rate"] > 50:
            reasons.append(f"交易量大幅增加 {volume['volume_change_rate']:.1f}%")

        # 市值理由
        if scores["market_cap"] >= 70:
            reasons.append("市值适中，风险可控")

        # 价格行为理由
        if scores["price_action"] >= 80:
            reasons.append("涨幅适中，未过度追高")

        return "；".join(reasons) if reasons else "综合指标良好"

    def _generate_watch_reason(self, momentum: dict, volume: dict,
                              scores: dict, risk_score: int) -> str:
        """生成观望理由"""
        reasons = []

        # 动能问题
        if momentum["state"] == MomentumState.CONSOLIDATING:
            reasons.append("价格高位震荡")
        elif momentum["state"] == MomentumState.DECELERATING:
            reasons.append("价格动能减弱或回落")

        # 交易量问题
        if volume["score"] < 60:
            reasons.append("交易量未明显放大")

        # 风险问题
        if risk_score > 50:
            reasons.append(f"风险评分过高 ({risk_score}/100)")

        # 置信度问题
        if scores["momentum"] < 50:
            reasons.append("动能不足")

        return "；".join(reasons) if reasons else "综合指标未达标"

    def _default_watch_decision(self, reason: str) -> dict:
        """默认观望决策"""
        return {
            "action": "WATCH",
            "confidence": 0,
            "risk_score": 100,
            "reason": reason,
            "entry_price": 0,
            "stop_loss": 0,
            "take_profit": 0,
            "details": {}
        }
