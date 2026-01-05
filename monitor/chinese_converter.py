"""
数字转中文工具
"""

import sys

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 数字到中文的映射
DIGIT_MAP = {
    '0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
    '5': '五', '6': '六', '7': '七', '8': '八', '9': '九',
    '.': '点', '+': '正', '-': '负'
}


def number_to_chinese(num: float, is_percent: bool = False) -> str:
    """
    将数字转换为中文

    Args:
        num: 数字
        is_percent: 是否是百分比

    Returns:
        中文字符串
    """
    # 处理百分比
    if is_percent:
        if num >= 0:
            prefix = "正百分之"
        else:
            prefix = "负百分之"
            num = abs(num)

        # 转换数字部分
        num_str = f"{num:.2f}"
        chinese = ""
        for char in num_str:
            chinese += DIGIT_MAP.get(char, char)

        return prefix + chinese

    # 处理普通数字
    num_str = str(num)
    chinese = ""

    for char in num_str:
        chinese += DIGIT_MAP.get(char, char)

    return chinese


def price_to_chinese(price: float) -> str:
    """
    将价格转换为中文

    Args:
        price: 价格

    Returns:
        中文价格字符串
    """
    price_str = f"{price:.6g}"
    chinese = ""

    for char in price_str:
        chinese += DIGIT_MAP.get(char, char)

    return chinese + "美元"


def time_to_chinese(time_str: str) -> str:
    """
    将时间转换为中文

    Args:
        time_str: 时间字符串，格式如 "21:35:00"

    Returns:
        中文时间字符串
    """
    parts = time_str.split(":")
    if len(parts) != 3:
        return time_str

    hour, minute, second = parts

    # 转换小时
    hour_chinese = ""
    for char in hour:
        hour_chinese += DIGIT_MAP.get(char, char)

    # 转换分钟
    minute_chinese = ""
    for char in minute:
        minute_chinese += DIGIT_MAP.get(char, char)

    return f"{hour_chinese}点{minute_chinese}分"


def window_to_chinese(minutes: int) -> str:
    """
    将时间窗口转换为中文

    Args:
        minutes: 分钟数

    Returns:
        中文时间窗口
    """
    minute_map = {
        1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
        6: "六", 7: "七", 8: "八", 9: "九", 10: "十",
        15: "十五", 20: "二十", 30: "三十", 60: "六十"
    }

    return minute_map.get(minutes, str(minutes)) + "分钟"


def threshold_to_chinese(threshold: float) -> str:
    """
    将阈值转换为中文

    Args:
        threshold: 阈值百分比

    Returns:
        中文阈值
    """
    threshold_map = {
        10: "十", 15: "十五", 20: "二十", 25: "二十五",
        30: "三十", 40: "四十", 50: "五十", 60: "六十",
        70: "七十", 80: "八十", 90: "九十", 100: "一百"
    }

    threshold_int = int(threshold)
    if threshold_int in threshold_map:
        return "百分之" + threshold_map[threshold_int]
    else:
        # 处理其他数字
        chinese = ""
        for char in str(threshold_int):
            chinese += DIGIT_MAP.get(char, char)
        return "百分之" + chinese


# 测试
if __name__ == "__main__":
    print("测试数字转中文:")
    print(f"35.20% -> {number_to_chinese(35.20, is_percent=True)}")
    print(f"-12.50% -> {number_to_chinese(-12.50, is_percent=True)}")
    print(f"$650.5 -> {price_to_chinese(650.5)}")
    print(f"$0.003 -> {price_to_chinese(0.003)}")
    print(f"21:35:00 -> {time_to_chinese('21:35:00')}")
    print(f"5分钟 -> {window_to_chinese(5)}")
    print(f"30% -> {threshold_to_chinese(30)}")
