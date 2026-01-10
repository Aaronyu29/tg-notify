"""
监控配置文件
在这里配置你的告警规则
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# ========== 基础配置 ==========

# 采样间隔（秒）- 改为 30 秒以支持 30 秒告警规则
SAMPLE_INTERVAL = 30

# 告警冷却时间（秒）- 防止同一币种频繁告警
ALERT_COOLDOWN = 60  # 1分钟

# Binance WebSocket URL
WS_URL = "wss://fstream.binance.com/ws/!miniTicker@arr"


# ========== 告警规则配置 ==========

# 规则格式说明：
# {
#     "name": "规则名称",
#     "window_minutes": 时间窗口（分钟），支持小数（如 0.5 = 30秒）,
#     "threshold": 阈值（百分比）,
#     "direction": "up" 或 "down",  # up=暴涨, down=暴跌
#     "priority": "normal" 或 "high" 或 "critical"
# }

ALERT_RULES = [
    # 30秒暴涨 5%
    {
        "name": "30秒暴涨5%",
        "window_minutes": 0.5,  # 0.5分钟 = 30秒
        "threshold": 5.0,
        "direction": "up",
        "priority": "high"
    },

    # 30秒暴跌 5%
    {
        "name": "30秒暴跌5%",
        "window_minutes": 0.5,  # 0.5分钟 = 30秒
        "threshold": 5.0,
        "direction": "down",
        "priority": "high"
    },

    # 5分钟暴涨 15%
    {
        "name": "5分钟暴涨15%",
        "window_minutes": 5,
        "threshold": 15.0,
        "direction": "up",
        "priority": "high"
    },

    # 5分钟暴跌 15%
    {
        "name": "5分钟暴跌15%",
        "window_minutes": 5,
        "threshold": 15.0,
        "direction": "down",
        "priority": "high"
    },

    # 你可以添加更多规则，例如：

    # 15分钟暴涨 50%
    # {
    #     "name": "15分钟暴涨50%",
    #     "window_minutes": 15,
    #     "threshold": 50.0,
    #     "direction": "up",
    #     "priority": "critical"
    # },

    # 10分钟暴跌 20%
    # {
    #     "name": "10分钟暴跌20%",
    #     "window_minutes": 10,
    #     "threshold": 20.0,
    #     "direction": "down",
    #     "priority": "high"
    # },
]


# ========== 高级配置 ==========

# 最大历史深度（分钟）- 自动计算为最大时间窗口 + 1
# 不需要手动设置，会根据 ALERT_RULES 自动计算
MAX_HISTORY_MINUTES = None  # 自动计算

# 是否显示详细日志
VERBOSE = True

# Top N 显示数量
TOP_N_DISPLAY = 5


# ========== 价格阈值报警配置 ==========

# 价格阈值规则格式说明：
# {
#     "symbol": "币种符号（如 BNBUSDT）",
#     "threshold": 阈值价格,
#     "direction": "above" 或 "below",  # above=突破, below=跌破
#     "priority": "normal" 或 "high" 或 "critical"
# }

PRICE_THRESHOLD_RULES = [
    # SOL 跌破 136.28
    {
        "symbol": "SOLUSDT",
        "threshold": 136.19,
        "direction": "below",
        "priority": "high"
    },

    # SOL 突破 136.34
    {
        "symbol": "SOLUSDT",
        "threshold": 136.24,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.35
    {
        "symbol": "SOLUSDT",
        "threshold": 136.26,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.36
    {
        "symbol": "SOLUSDT",
        "threshold": 136.28,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.37
    {
        "symbol": "SOLUSDT",
        "threshold": 136.37,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.38
    {
        "symbol": "SOLUSDT",
        "threshold": 136.38,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.39
    {
        "symbol": "SOLUSDT",
        "threshold": 136.39,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.40
    {
        "symbol": "SOLUSDT",
        "threshold": 136.40,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.41
    {
        "symbol": "SOLUSDT",
        "threshold": 136.41,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.42
    {
        "symbol": "SOLUSDT",
        "threshold": 136.42,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.43
    {
        "symbol": "SOLUSDT",
        "threshold": 136.43,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.44
    {
        "symbol": "SOLUSDT",
        "threshold": 136.44,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.45
    {
        "symbol": "SOLUSDT",
        "threshold": 136.45,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.46
    {
        "symbol": "SOLUSDT",
        "threshold": 136.46,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.47
    {
        "symbol": "SOLUSDT",
        "threshold": 136.47,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.48
    {
        "symbol": "SOLUSDT",
        "threshold": 136.48,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.49
    {
        "symbol": "SOLUSDT",
        "threshold": 136.49,
        "direction": "above",
        "priority": "high"
    },

    # SOL 突破 136.50
    {
        "symbol": "SOLUSDT",
        "threshold": 136.50,
        "direction": "above",
        "priority": "high"
    },

    # BNB 跌破 800
    {
        "symbol": "BNBUSDT",
        "threshold": 800.0,
        "direction": "below",
        "priority": "high"
    },

    # 你可以添加更多阈值规则，例如：

    # BTC 突破 100000
    # {
    #     "symbol": "BTCUSDT",
    #     "threshold": 100000.0,
    #     "direction": "above",
    #     "priority": "high"
    # },

    # ETH 跌破 3000
    # {
    #     "symbol": "ETHUSDT",
    #     "threshold": 3000.0,
    #     "direction": "below",
    #     "priority": "high"
    # },
]

# 价格阈值报警冷却时间（秒）- 防止频繁报警
PRICE_THRESHOLD_COOLDOWN = 3600  # 1小时

# 价格阈值报警专用 Webhook URL（可选，不配置则使用 FWALERT_URL）
PRICE_THRESHOLD_WEBHOOK_URL = os.getenv("PRICE_THRESHOLD_WEBHOOK_URL", "")
