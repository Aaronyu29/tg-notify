"""
快速测试程序 - 直接发送测试告警
不需要等待历史数据，直接发送模拟数据
"""

import sys
from pathlib import Path
from datetime import datetime

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


def send_test_alert(alert_type: str, symbol: str, change_percent: float,
                    current_price: float, old_price: float):
    """发送测试告警"""

    now_str = datetime.now().strftime("%H:%M:%S")
    window_minutes = 5

    # 转换为中文
    change_percent_chinese = number_to_chinese(change_percent, is_percent=True)
    price_chinese = price_to_chinese(current_price)
    old_price_chinese = price_to_chinese(old_price)
    time_chinese = time_to_chinese(now_str)
    window_chinese = window_to_chinese(window_minutes)

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
    print(f"{'='*60}\n")

    # 创建 AlertGenerator 并发送
    generator = AlertGenerator()
    success = generator.send_alert(message)

    if success:
        print(f"✓ 告警发送成功: {symbol} ({change_percent:+.2f}%)")
        print(f"✓ 已发送到 FWAlert")
    else:
        print(f"✗ 告警发送失败: {symbol}")
        print(f"✗ 请检查 .env 中的 FWALERT_URL 配置")

    return success


def main():
    print("=" * 60)
    print("快速测试程序 - 发送模拟告警到 FWAlert")
    print("=" * 60)
    print()

    # 测试数据 1: 涨幅最高的币
    print("测试 1: 发送涨幅最高的币种告警")
    success1 = send_test_alert(
        alert_type="top_gainer",
        symbol="BTCUSDT",
        change_percent=8.52,
        current_price=45230.5,
        old_price=41680.2
    )

    print("\n" + "-" * 60 + "\n")

    # 测试数据 2: 跌幅最大的币
    print("测试 2: 发送跌幅最大的币种告警")
    success2 = send_test_alert(
        alert_type="top_loser",
        symbol="ETHUSDT",
        change_percent=-6.35,
        current_price=2850.3,
        old_price=3043.8
    )

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    if success1 and success2:
        print("\n✓ 所有告警发送成功！")
        print("✓ 请检查 FWAlert 是否收到消息")
    else:
        print("\n✗ 部分告警发送失败")
        print("✗ 请检查 .env 中的 FWALERT_URL 配置")


if __name__ == "__main__":
    main()
