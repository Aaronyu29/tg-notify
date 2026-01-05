"""
测试中文消息格式
"""

import sys
from pathlib import Path

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, str(Path(__file__).parent))

from chinese_converter import (
    number_to_chinese,
    price_to_chinese,
    time_to_chinese,
    window_to_chinese,
    threshold_to_chinese
)

# 测试数据
symbol = "BNBUSDT"
change_percent = 35.20
current_price = 650.5
old_price = 481.2
time_str = "21:35:00"
window = 5
threshold = 30

# 转换为中文
change_percent_chinese = number_to_chinese(change_percent, is_percent=True)
price_chinese = price_to_chinese(current_price)
old_price_chinese = price_to_chinese(old_price)
time_chinese = time_to_chinese(time_str)
window_chinese = window_to_chinese(window)
threshold_chinese = threshold_to_chinese(threshold)

# 生成消息
message = (
    f"{symbol} {window_chinese}内暴涨{threshold_chinese}\n"
    f"涨跌幅: {change_percent_chinese}\n"
    f"当前价格: {price_chinese}\n"
    f"{window_chinese}前: {old_price_chinese}\n"
    f"检测时间: {time_chinese}"
)

print("=" * 60)
print("测试消息格式（发送到 FWAlert）")
print("=" * 60)
print(message)
print("=" * 60)

# 测试暴跌
print("\n测试暴跌消息:")
change_percent_drop = -30.5
change_percent_drop_chinese = number_to_chinese(change_percent_drop, is_percent=True)

message_drop = (
    f"{symbol} {window_chinese}内暴跌{threshold_chinese}\n"
    f"涨跌幅: {change_percent_drop_chinese}\n"
    f"当前价格: {price_chinese}\n"
    f"{window_chinese}前: {old_price_chinese}\n"
    f"检测时间: {time_chinese}"
)

print("=" * 60)
print(message_drop)
print("=" * 60)
