"""
查看日志工具 - 显示最近24小时的日志（倒序）
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from logger import get_recent_logs


def main():
    print("=" * 80)
    print("📋 监控日志查看器 - 最近24小时日志（最新的在前）")
    print("=" * 80)
    print()

    # 获取最近24小时的日志
    logs = get_recent_logs(log_dir="logs", name="monitor", hours=24)

    if not logs:
        print("暂无日志记录")
        return

    print(f"共找到 {len(logs)} 条日志记录\n")
    print("-" * 80)

    # 显示所有日志（已经是倒序）
    for log in logs:
        print(log.rstrip())

    print("-" * 80)
    print(f"\n总计: {len(logs)} 条日志")


if __name__ == "__main__":
    main()
