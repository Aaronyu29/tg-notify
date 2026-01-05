"""
日志记录器 - 同时输出到控制台和文件
支持日志轮转，保留24小时的日志
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


class CustomFormatter(logging.Formatter):
    """自定义格式化器，支持彩色输出到控制台"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }

    def __init__(self, use_color=True):
        super().__init__()
        self.use_color = use_color

    def format(self, record):
        # 格式: [时间] [级别] 消息
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        message = record.getMessage()

        if self.use_color and sys.platform == 'win32':
            color = self.COLORS.get(level, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            return f"[{timestamp}] {color}[{level}]{reset} {message}"
        else:
            return f"[{timestamp}] [{level}] {message}"


class Logger:
    """日志管理器"""

    def __init__(self, name="monitor", log_dir="logs", keep_hours=24):
        """
        初始化日志器

        Args:
            name: 日志器名称
            log_dir: 日志目录
            keep_hours: 保留日志的小时数
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.keep_hours = keep_hours

        # 创建日志目录
        self.log_dir.mkdir(exist_ok=True)

        # 创建 logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 清除已有的 handlers
        self.logger.handlers.clear()

        # 添加文件处理器（每小时轮转）
        self._add_file_handler()

        # 添加控制台处理器
        self._add_console_handler()

        # 清理旧日志
        self._cleanup_old_logs()

    def _add_file_handler(self):
        """添加文件处理器"""
        log_file = self.log_dir / f"{self.name}.log"

        # 使用 TimedRotatingFileHandler，每小时轮转一次
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when='H',  # 每小时
            interval=1,
            backupCount=self.keep_hours,  # 保留24个文件
            encoding='utf-8'
        )

        # 设置文件日志格式（不使用颜色）
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)

        self.logger.addHandler(file_handler)

    def _add_console_handler(self):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)

        # 设置控制台格式（使用彩色）
        console_formatter = CustomFormatter(use_color=True)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上

        self.logger.addHandler(console_handler)

    def _cleanup_old_logs(self):
        """清理超过保留时间的旧日志"""
        cutoff_time = datetime.now() - timedelta(hours=self.keep_hours)

        for log_file in self.log_dir.glob(f"{self.name}.log*"):
            try:
                # 获取文件修改时间
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff_time:
                    log_file.unlink()
                    self.logger.debug(f"已删除旧日志: {log_file.name}")
            except Exception as e:
                self.logger.error(f"删除旧日志失败 {log_file.name}: {e}")

    def debug(self, message):
        """调试日志"""
        self.logger.debug(message)

    def info(self, message):
        """信息日志"""
        self.logger.info(message)

    def warning(self, message):
        """警告日志"""
        self.logger.warning(message)

    def error(self, message):
        """错误日志"""
        self.logger.error(message)

    def critical(self, message):
        """严重错误日志"""
        self.logger.critical(message)
    def exception(self, message):
        """异常日志（包含堆栈信息）"""
        self.logger.exception(message)


def get_recent_logs(log_dir="logs", name="monitor", hours=24):
    """
    获取最近的日志内容（倒序）

    Args:
        log_dir: 日志目录
        name: 日志器名称
        hours: 获取最近多少小时的日志

    Returns:
        日志内容列表（倒序）
    """
    log_dir = Path(log_dir)
    cutoff_time = datetime.now() - timedelta(hours=hours)

    logs = []

    # 收集所有符合条件的日志文件
    log_files = []
    for log_file in log_dir.glob(f"{name}.log*"):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime >= cutoff_time:
                log_files.append((mtime, log_file))
        except Exception:
            continue

    # 按时间排序（最新的在前）
    log_files.sort(reverse=True)

    # 读取日志内容
    for _, log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logs.extend(lines)
        except Exception as e:
            print(f"读取日志文件失败 {log_file.name}: {e}")

    # 倒序返回（最新的在前）
    return list(reversed(logs))


# 使用示例
if __name__ == "__main__":
    # 创建日志器
    logger = Logger(name="test", keep_hours=24)

    # 测试不同级别的日志
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误")

    # 测试异常日志
    try:
        1 / 0
    except Exception:
        logger.exception("发生了异常")

    print("\n" + "="*60)
    print("最近的日志（倒序）:")
    print("="*60)

    # 获取最近的日志
    recent_logs = get_recent_logs(name="test", hours=24)
    for log in recent_logs[-10:]:  # 只显示最后10条
        print(log.rstrip())
