"""
Alert Generator 使用示例
演示如何使用告警生成器监控加密货币价格
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from alert_generator import (
    AlertGenerator,
    AlertRule,
    create_price_surge_rule,
    create_price_drop_rule,
    create_price_threshold_rule,
    create_volume_spike_rule
)

def example_1_basic():
    """示例 1: 基本使用"""
    print("\n" + "=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)

    # 创建告警生成器
    generator = AlertGenerator()

    # 添加规则：BNB 涨幅超过 30%
    rule = AlertRule(
        name="BNB_surge",
        condition=lambda data: (
            data.get("symbol") == "BNB" and
            data.get("change_percent", 0) > 30
        ),
        message_template="BNB 价格在过去五分钟涨了 {change_percent:.1f}%，请及时关注",
        priority="high"
    )
    generator.add_rule(rule)

    # 测试数据
    data = {
        "symbol": "BNB",
        "price": 650.5,
        "change_percent": 35.2
    }

    # 检查并发送告警
    results = generator.check_and_alert(data)
    print(f"\n触发规则数: {len(results['triggered_rules'])}")


def example_2_multiple_rules():
    """示例 2: 使用多个预定义规则"""
    print("\n" + "=" * 60)
    print("示例 2: 使用多个预定义规则")
    print("=" * 60)

    generator = AlertGenerator()

    # 添加多个规则
    generator.add_rule(create_price_surge_rule("BNB", 30.0))
    generator.add_rule(create_price_drop_rule("BTC", 10.0))
    generator.add_rule(create_price_threshold_rule("ETH", 4000, "above"))
    generator.add_rule(create_volume_spike_rule("BNB", 5.0))

    # 测试数据：BNB 暴涨且交易量激增
    data = {
        "symbol": "BNB",
        "price": 650.5,
        "change_percent": 35.2,
        "volume_ratio": 6.5
    }

    results = generator.check_and_alert(data)
    print(f"\n触发规则数: {len(results['triggered_rules'])}")
    for rule in results['triggered_rules']:
        print(f"  - {rule['rule']}: {rule['message']}")


def example_3_custom_rule():
    """示例 3: 自定义复杂规则"""
    print("\n" + "=" * 60)
    print("示例 3: 自定义复杂规则")
    print("=" * 60)

    generator = AlertGenerator()

    # 自定义规则：价格上涨且交易量激增
    def price_volume_condition(data):
        price_up = data.get("change_percent", 0) > 10
        volume_high = data.get("volume_ratio", 0) > 3
        symbol_match = data.get("symbol") == "BNB"
        return symbol_match and price_up and volume_high

    custom_rule = AlertRule(
        name="BNB_price_volume_surge",
        condition=price_volume_condition,
        message_template="⚠️ BNB 异常波动：价格上涨 {change_percent:.1f}% 且交易量激增 {volume_ratio:.1f} 倍，当前价格 ${price}",
        priority="high"
    )

    generator.add_rule(custom_rule)

    # 测试数据
    data = {
        "symbol": "BNB",
        "price": 650.5,
        "change_percent": 15.5,
        "volume_ratio": 4.2
    }

    results = generator.check_and_alert(data)
    print(f"\n触发规则数: {len(results['triggered_rules'])}")


def example_4_generate_curl():
    """示例 4: 生成 curl 命令"""
    print("\n" + "=" * 60)
    print("示例 4: 生成 curl 命令")
    print("=" * 60)

    generator = AlertGenerator()

    message = "BNB 价格在过去五分钟涨了 30%，请及时关注"
    curl_cmd = generator.generate_curl_command(message)

    print("\n生成的 curl 命令：")
    print(curl_cmd)


def example_5_monitoring_loop():
    """示例 5: 模拟监控循环"""
    print("\n" + "=" * 60)
    print("示例 5: 模拟监控循环")
    print("=" * 60)

    generator = AlertGenerator()

    # 添加规则
    generator.add_rule(create_price_surge_rule("BNB", 30.0))
    generator.add_rule(create_price_drop_rule("BTC", 10.0))

    # 模拟多次价格检查
    test_data_list = [
        {"symbol": "BNB", "price": 600, "change_percent": 5.0},
        {"symbol": "BNB", "price": 650, "change_percent": 35.0},  # 触发
        {"symbol": "BTC", "price": 45000, "change_percent": -2.0},
        {"symbol": "BTC", "price": 40000, "change_percent": -12.0},  # 触发
    ]

    for i, data in enumerate(test_data_list, 1):
        print(f"\n检查 #{i}: {data['symbol']} 价格 ${data['price']}, 变化 {data['change_percent']}%")
        results = generator.check_and_alert(data)
        if results['triggered_rules']:
            print(f"  ✓ 触发 {len(results['triggered_rules'])} 条规则")
        else:
            print("  - 未触发规则")


def example_6_with_telegram():
    """示例 6: 结合 Telegram 通知"""
    print("\n" + "=" * 60)
    print("示例 6: 结合 Telegram 通知（需要配置 notify_client）")
    print("=" * 60)

    generator = AlertGenerator()
    generator.add_rule(create_price_surge_rule("BNB", 30.0))

    data = {
        "symbol": "BNB",
        "price": 650.5,
        "change_percent": 35.2
    }

    results = generator.check_and_alert(data)

    # 同时发送到 Telegram
    if results["triggered_rules"]:
        print("\n同时发送到 Telegram...")
        try:
            from notify_client import notify
            for rule in results["triggered_rules"]:
                notify(
                    title=f"价格告警: {rule['rule']}",
                    message=rule['message'],
                    channel="alert",
                    priority=rule['priority']
                )
            print("✓ Telegram 通知已发送")
        except ImportError:
            print("⚠️  notify_client 未配置，跳过 Telegram 通知")


if __name__ == "__main__":
    print("=" * 60)
    print("  Alert Generator 使用示例")
    print("=" * 60)

    # 运行所有示例
    example_1_basic()
    example_2_multiple_rules()
    example_3_custom_rule()
    example_4_generate_curl()
    example_5_monitoring_loop()
    example_6_with_telegram()

    print("\n" + "=" * 60)
    print("  所有示例运行完成")
    print("=" * 60)
