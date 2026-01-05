"""
监控配置文件
在这里配置你的告警规则
"""

# ========== 基础配置 ==========

# 采样间隔（秒）- 建议 60 秒
SAMPLE_INTERVAL = 60

# 告警冷却时间（秒）- 防止同一币种频繁告警
ALERT_COOLDOWN = 900  # 15分钟

# Binance WebSocket URL
WS_URL = "wss://fstream.binance.com/ws/!miniTicker@arr"


# ========== 告警规则配置 ==========

# 规则格式说明：
# {
#     "name": "规则名称",
#     "window_minutes": 时间窗口（分钟）,
#     "threshold": 阈值（百分比）,
#     "direction": "up" 或 "down",  # up=暴涨, down=暴跌
#     "priority": "normal" 或 "high" 或 "critical"
# }

ALERT_RULES = [
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
