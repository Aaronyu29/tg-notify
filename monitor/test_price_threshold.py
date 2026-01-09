"""
测试价格阈值报警功能
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from alert_generator import AlertGenerator
from chinese_converter import price_to_chinese
import json


def test_price_threshold_alert():
    """测试价格阈值报警"""
    print("=" * 60)
    print("  测试价格阈值报警功能")
    print("=" * 60)

    # 创建告警生成器
    generator = AlertGenerator()

    # 测试场景 1: BNB 跌破 800
    print("\n测试场景 1: BNB 跌破 800")
    print("-" * 60)

    message = {
        "type": "price_threshold",
        "symbol": "BNB",
        "direction": "跌破",
        "threshold": price_to_chinese(800.0),
        "currentPrice": price_to_chinese(795.5)
    }

    message_json = json.dumps(message, ensure_ascii=False)
    print(f"消息内容: {message_json}")

    success = generator.send_alert(message_json)
    if success:
        print("✓ 告警发送成功")
    else:
        print("✗ 告警发送失败")

    # 测试场景 2: BTC 突破 100000
    print("\n测试场景 2: BTC 突破 100000")
    print("-" * 60)

    message = {
        "type": "price_threshold",
        "symbol": "BTC",
        "direction": "突破",
        "threshold": price_to_chinese(100000.0),
        "currentPrice": price_to_chinese(100500.0)
    }

    message_json = json.dumps(message, ensure_ascii=False)
    print(f"消息内容: {message_json}")

    success = generator.send_alert(message_json)
    if success:
        print("✓ 告警发送成功")
    else:
        print("✗ 告警发送失败")

    # 测试场景 3: ETH 跌破 3000
    print("\n测试场景 3: ETH 跌破 3000")
    print("-" * 60)

    message = {
        "type": "price_threshold",
        "symbol": "ETH",
        "direction": "跌破",
        "threshold": price_to_chinese(3000.0),
        "currentPrice": price_to_chinese(2985.25)
    }

    message_json = json.dumps(message, ensure_ascii=False)
    print(f"消息内容: {message_json}")

    success = generator.send_alert(message_json)
    if success:
        print("✓ 告警发送成功")
    else:
        print("✗ 告警发送失败")

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_price_threshold_alert()
