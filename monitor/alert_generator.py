"""
告警生成器 - 根据规则生成 curl 请求并发送通知
支持自定义规则匹配和告警发送
"""

import os
import sys
import requests
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from dotenv import load_dotenv
from logger import Logger

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 加载 .env 文件
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# ========== 配置 ==========
FWALERT_URL = os.getenv("FWALERT_URL", "")  # 从环境变量读取 URL


class AlertRule:
    """告警规则类"""

    def __init__(self, name: str, condition: Callable[[Dict[str, Any]], bool],
                 message_template: str, priority: str = "normal"):
        """
        初始化告警规则

        Args:
            name: 规则名称
            condition: 判断函数，接收数据字典，返回 True/False
            message_template: 消息模板，可使用 {key} 格式引用数据
            priority: 优先级 (normal/high/critical)
        """
        self.name = name
        self.condition = condition
        self.message_template = message_template
        self.priority = priority

    def check(self, data: Dict[str, Any]) -> bool:
        """检查数据是否满足规则"""
        try:
            return self.condition(data)
        except Exception as e:
            print(f"[规则 {self.name}] 检查失败: {e}")
            return False

    def format_message(self, data: Dict[str, Any]) -> str:
        """格式化消息"""
        try:
            return self.message_template.format(**data)
        except Exception as e:
            print(f"[规则 {self.name}] 格式化消息失败: {e}")
            return self.message_template


class AlertGenerator:
    """告警生成器"""

    def __init__(self, fwalert_url: str = None):
        """
        初始化告警生成器

        Args:
            fwalert_url: FWAlert webhook URL，如果不提供则从环境变量读取
        """
        self.fwalert_url = fwalert_url or FWALERT_URL
        self.rules = []
        self.logger = Logger(name="alert_generator", keep_hours=24)

        if not self.fwalert_url:
            self.logger.warning("⚠️  警告: FWALERT_URL 未配置，请在 .env 中设置或初始化时传入")

    def add_rule(self, rule: AlertRule):
        """添加规则"""
        self.rules.append(rule)
        self.logger.info(f"✓ 已添加规则: {rule.name}")

    def check_and_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查数据并发送告警

        Args:
            data: 要检查的数据字典

        Returns:
            结果字典，包含触发的规则和发送状态
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "triggered_rules": [],
            "alerts_sent": []
        }

        for rule in self.rules:
            if rule.check(data):
                message = rule.format_message(data)
                results["triggered_rules"].append({
                    "rule": rule.name,
                    "message": message,
                    "priority": rule.priority
                })

                # 发送告警
                success = self.send_alert(message)
                results["alerts_sent"].append({
                    "rule": rule.name,
                    "success": success
                })

                if success:
                    self.logger.info(f"✓ [{rule.name}] 告警已发送")
                else:
                    self.logger.error(f"✗ [{rule.name}] 告警发送失败")

        return results

    def send_alert(self, message) -> bool:
        """
        发送告警到 FWAlert 和 Telegram

        Args:
            message: 告警消息 (str 或 dict)

        Returns:
            是否至少有一个渠道发送成功
        """
        fwalert_success = False
        telegram_success = False

        # 1. 发送到 FWAlert
        if self.fwalert_url:
            try:
                # 如果 message 是字符串，尝试解析为 JSON
                if isinstance(message, str):
                    try:
                        import json
                        payload = json.loads(message)
                    except json.JSONDecodeError:
                        # 如果不是 JSON，则包装为 {"message": ...}
                        payload = {"message": message}
                else:
                    # 如果已经是 dict，直接使用
                    payload = message

                response = requests.post(
                    self.fwalert_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                fwalert_success = response.status_code == 200
                if fwalert_success:
                    self.logger.info("✓ FWAlert 发送成功")
                else:
                    self.logger.error(f"✗ FWAlert 发送失败: HTTP {response.status_code}")
            except Exception as e:
                self.logger.error(f"✗ FWAlert 发送失败: {e}")
        else:
            self.logger.warning("⚠️  FWAlert URL 未配置，跳过")

        # 2. 发送到 Telegram (通过本地 notify server)
        try:
            # 导入 notify_client（在父目录）
            parent_dir = Path(__file__).parent.parent
            if str(parent_dir) not in sys.path:
                sys.path.insert(0, str(parent_dir))

            from notify_client import notify

            # 解析消息内容
            if isinstance(message, str):
                try:
                    import json
                    data = json.loads(message)
                except json.JSONDecodeError:
                    data = {"message": message}
            else:
                data = message

            # 构建 Telegram 消息
            if data.get("type") == "price_threshold":
                # 价格阈值报警
                symbol = data.get('symbol', '未知')
                direction = data.get('direction', '')
                threshold = data.get('thresholdValue', data.get('threshold', ''))
                current_price = data.get('currentPriceValue', data.get('price', ''))

                title = f"🚨 价格阈值报警"
                msg = f"{symbol} {direction} ${threshold}\n当前价格: ${current_price}"
            else:
                # 涨跌幅报警
                symbol = data.get("symbol", "未知")
                change_percent = data.get("changePercent", "")
                current_price = data.get("currentPriceValue", "")
                before_price = data.get("beforePriceValue", "")

                title = f"📊 {symbol} 价格变动"
                msg = f"涨跌幅: {change_percent}%\n当前价格: ${current_price}\n之前价格: ${before_price}"

            # 发送到 Telegram
            telegram_success = notify(
                title=title,
                message=msg,
                channel="alert",  # 修改为 alert，避免与 price 字段冲突
                priority="high"
            )

            if telegram_success:
                self.logger.info("✓ Telegram 发送成功")
            else:
                self.logger.error("✗ Telegram 发送失败")

        except Exception as e:
            self.logger.error(f"✗ Telegram 发送失败: {e}")

        # 只要有一个成功就返回 True
        return fwalert_success or telegram_success

    def generate_curl_command(self, message: str) -> str:
        """
        生成 curl 命令（用于调试或手动执行）

        Args:
            message: 告警消息

        Returns:
            curl 命令字符串
        """
        if not self.fwalert_url:
            return "# FWALERT_URL 未配置"

        curl_cmd = f"""curl --location '{self.fwalert_url}' \\
--header 'Content-Type: application/json' \\
--data '{{
    "message": "{message}"
}}'"""
        return curl_cmd


# ========== 预定义规则示例 ==========

def create_price_surge_rule(symbol: str, threshold_percent: float) -> AlertRule:
    """创建价格暴涨规则"""
    return AlertRule(
        name=f"{symbol}_price_surge",
        condition=lambda data: (
            data.get("symbol") == symbol and
            data.get("change_percent", 0) > threshold_percent
        ),
        message_template=f"{symbol} 价格在过去五分钟涨了 {{change_percent:.1f}}%，请及时关注",
        priority="high"
    )


def create_price_drop_rule(symbol: str, threshold_percent: float) -> AlertRule:
    """创建价格暴跌规则"""
    return AlertRule(
        name=f"{symbol}_price_drop",
        condition=lambda data: (
            data.get("symbol") == symbol and
            data.get("change_percent", 0) < -threshold_percent
        ),
        message_template=f"{symbol} 价格在过去五分钟跌了 {{change_percent:.1f}}%，请注意风险",
        priority="high"
    )


def create_volume_spike_rule(symbol: str, threshold_multiplier: float) -> AlertRule:
    """创建交易量激增规则"""
    return AlertRule(
        name=f"{symbol}_volume_spike",
        condition=lambda data: (
            data.get("symbol") == symbol and
            data.get("volume_ratio", 0) > threshold_multiplier
        ),
        message_template=f"{symbol} 交易量激增 {{volume_ratio:.1f}} 倍，当前价格 ${{price}}",
        priority="normal"
    )


def create_price_threshold_rule(symbol: str, price_threshold: float,
                                direction: str = "above") -> AlertRule:
    """创建价格阈值规则"""
    if direction == "above":
        condition = lambda data: (
            data.get("symbol") == symbol and
            data.get("price", 0) > price_threshold
        )
        message = f"{symbol} 价格突破 ${price_threshold}，当前价格 ${{price}}"
    else:
        condition = lambda data: (
            data.get("symbol") == symbol and
            data.get("price", 0) < price_threshold
        )
        message = f"{symbol} 价格跌破 ${price_threshold}，当前价格 ${{price}}"

    return AlertRule(
        name=f"{symbol}_price_{direction}_{price_threshold}",
        condition=condition,
        message_template=message,
        priority="high"
    )


# ========== 使用示例 ==========

if __name__ == "__main__":
    print("=" * 60)
    print("  告警生成器测试")
    print("=" * 60)

    # 创建告警生成器
    generator = AlertGenerator()

    # 添加规则：BNB 涨幅超过 30%
    bnb_surge_rule = create_price_surge_rule("BNB", 30.0)
    generator.add_rule(bnb_surge_rule)

    # 添加规则：BTC 跌幅超过 10%
    btc_drop_rule = create_price_drop_rule("BTC", 10.0)
    generator.add_rule(btc_drop_rule)

    # 添加规则：ETH 价格突破 4000
    eth_threshold_rule = create_price_threshold_rule("ETH", 4000, "above")
    generator.add_rule(eth_threshold_rule)

    print("\n" + "=" * 60)
    print("  测试数据 1: BNB 暴涨")
    print("=" * 60)

    # 测试数据 1: BNB 暴涨
    test_data_1 = {
        "symbol": "BNB",
        "price": 650.5,
        "change_percent": 35.2,
        "volume_ratio": 3.5
    }

    print(f"数据: {test_data_1}")
    results_1 = generator.check_and_alert(test_data_1)
    print(f"触发规则数: {len(results_1['triggered_rules'])}")

    # 生成 curl 命令示例
    if results_1['triggered_rules']:
        print("\n生成的 curl 命令:")
        print(generator.generate_curl_command(results_1['triggered_rules'][0]['message']))

    print("\n" + "=" * 60)
    print("  测试数据 2: BTC 暴跌")
    print("=" * 60)

    # 测试数据 2: BTC 暴跌
    test_data_2 = {
        "symbol": "BTC",
        "price": 42000,
        "change_percent": -12.5,
        "volume_ratio": 2.1
    }

    print(f"数据: {test_data_2}")
    results_2 = generator.check_and_alert(test_data_2)
    print(f"触发规则数: {len(results_2['triggered_rules'])}")

    print("\n" + "=" * 60)
    print("  测试数据 3: ETH 价格正常")
    print("=" * 60)

    # 测试数据 3: 不触发任何规则
    test_data_3 = {
        "symbol": "ETH",
        "price": 3500,
        "change_percent": 2.5,
        "volume_ratio": 1.2
    }

    print(f"数据: {test_data_3}")
    results_3 = generator.check_and_alert(test_data_3)
    print(f"触发规则数: {len(results_3['triggered_rules'])}")

    print("\n" + "=" * 60)
