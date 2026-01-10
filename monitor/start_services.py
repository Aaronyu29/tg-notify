"""
一键启动脚本 - 同时启动通知服务器和实时监控器
支持优雅关闭、实时日志显示、错误处理
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import socket


class ServiceManager:
    """服务管理器 - 管理多个子进程"""

    def __init__(self):
        self.processes = {}
        self.running = True
        self.log_threads = []

        # 颜色代码（Windows 兼容）
        self.colors = {
            'server': '\033[94m',      # 蓝色
            'monitor': '\033[92m',     # 绿色
            'error': '\033[91m',       # 红色
            'warning': '\033[93m',     # 黄色
            'info': '\033[96m',        # 青色
            'reset': '\033[0m'
        }

        # 检测是否支持颜色（Windows CMD 可能不支持）
        if sys.platform == "win32":
            try:
                import colorama
                colorama.init()
            except ImportError:
                # 如果没有 colorama，禁用颜色
                self.colors = {k: '' for k in self.colors}

    def print_colored(self, service: str, message: str, level: str = 'info'):
        """打印带颜色的日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = self.colors.get(service, self.colors['reset'])
        reset = self.colors['reset']

        # 服务名称固定宽度对齐
        service_name = f"[{service.upper():8s}]"
        print(f"{color}{timestamp} {service_name}{reset} {message}", flush=True)

    def check_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return True
        except OSError:
            return False

    def stream_output(self, process, service_name: str):
        """实时读取并显示进程输出"""
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                line = line.strip()
                if line:
                    self.print_colored(service_name, line)
        except Exception as e:
            if self.running:
                self.print_colored(service_name, f"读取输出异常: {e}", 'error')

    def start_service(self, name: str, script_path: str, cwd: str = None):
        """启动一个服务"""
        try:
            self.print_colored('info', f"正在启动 {name}...")

            # 构建命令
            if sys.platform == "win32":
                # Windows: 使用当前 Python 解释器
                cmd = [sys.executable, script_path]
            else:
                # Linux/Mac
                cmd = [sys.executable, script_path]

            # 启动进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=cwd,
                bufsize=1,  # 行缓冲
                universal_newlines=True
            )

            self.processes[name] = process

            # 启动输出读取线程
            thread = threading.Thread(
                target=self.stream_output,
                args=(process, name),
                daemon=True
            )
            thread.start()
            self.log_threads.append(thread)

            # 等待一小段时间检查是否启动成功
            time.sleep(1)
            if process.poll() is not None:
                self.print_colored('error', f"{name} 启动失败 (退出码: {process.returncode})")
                return False

            self.print_colored('info', f"✓ {name} 启动成功 (PID: {process.pid})")
            return True

        except Exception as e:
            self.print_colored('error', f"启动 {name} 时发生异常: {e}")
            return False

    def stop_service(self, name: str):
        """停止一个服务"""
        process = self.processes.get(name)
        if not process:
            return

        try:
            self.print_colored('info', f"正在停止 {name}...")

            # 尝试优雅关闭
            if sys.platform == "win32":
                # Windows: 发送 Ctrl+C
                process.send_signal(signal.CTRL_C_EVENT)
            else:
                # Linux/Mac: 发送 SIGINT
                process.send_signal(signal.SIGINT)

            # 等待最多 5 秒
            try:
                process.wait(timeout=5)
                self.print_colored('info', f"✓ {name} 已停止")
            except subprocess.TimeoutExpired:
                # 强制终止
                self.print_colored('warning', f"{name} 未响应，强制终止...")
                process.kill()
                process.wait()
                self.print_colored('info', f"✓ {name} 已强制终止")

        except Exception as e:
            self.print_colored('error', f"停止 {name} 时发生异常: {e}")

    def stop_all(self):
        """停止所有服务"""
        self.running = False
        self.print_colored('info', "正在关闭所有服务...")

        for name in list(self.processes.keys()):
            self.stop_service(name)

        self.print_colored('info', "所有服务已关闭")

    def monitor_processes(self):
        """监控进程状态，如果崩溃则报告"""
        while self.running:
            time.sleep(2)

            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    # 进程已退出
                    exit_code = process.returncode
                    if exit_code != 0:
                        self.print_colored('error',
                            f"⚠️  {name} 异常退出 (退出码: {exit_code})")
                    else:
                        self.print_colored('info', f"{name} 已正常退出")

                    # 从列表中移除
                    del self.processes[name]

                    # 如果所有进程都退出了，停止监控
                    if not self.processes:
                        self.running = False
                        break


def main():
    """主函数"""
    # 设置 UTF-8 编码（Windows 兼容）
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

    # 获取路径
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent
    server_script = parent_dir / "server.py"
    monitor_script = current_dir / "realtime_monitor_v2.py"

    # 检查文件是否存在
    if not server_script.exists():
        print(f"错误: 找不到 server.py: {server_script}")
        return 1

    if not monitor_script.exists():
        print(f"错误: 找不到 realtime_monitor_v2.py: {monitor_script}")
        return 1

    # 创建服务管理器
    manager = ServiceManager()

    # 打印启动信息
    print("=" * 70)
    print("  TG Notify - 一键启动脚本")
    print("=" * 70)
    print(f"  Server:  {server_script}")
    print(f"  Monitor: {monitor_script}")
    print("-" * 70)

    # 检查端口 8000 是否可用
    if not manager.check_port_available(8000):
        manager.print_colored('warning', "端口 8000 已被占用，server.py 可能无法启动")
        manager.print_colored('warning', "如果 server.py 已在运行，请先关闭它")
        response = input("\n是否继续启动? (y/N): ").strip().lower()
        if response != 'y':
            print("已取消启动")
            return 0

    print()
    manager.print_colored('info', "开始启动服务...")
    print()

    # 启动服务
    success_count = 0

    # 1. 启动 server.py
    if manager.start_service('server', str(server_script), cwd=str(parent_dir)):
        success_count += 1
        time.sleep(2)  # 等待 server 完全启动

    # 2. 启动 monitor
    if manager.start_service('monitor', str(monitor_script), cwd=str(current_dir)):
        success_count += 1

    if success_count == 0:
        manager.print_colored('error', "所有服务启动失败")
        return 1

    print()
    print("=" * 70)
    manager.print_colored('info', f"✓ 成功启动 {success_count}/2 个服务")
    print("-" * 70)
    manager.print_colored('info', "按 Ctrl+C 停止所有服务")
    print("=" * 70)
    print()

    # 设置信号处理
    def signal_handler(signum, frame):
        print("\n")
        manager.print_colored('info', "收到退出信号 (Ctrl+C)")
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)

    # 启动进程监控线程
    monitor_thread = threading.Thread(target=manager.monitor_processes, daemon=True)
    monitor_thread.start()

    # 主线程等待
    try:
        while manager.running and manager.processes:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if manager.processes:
            manager.stop_all()

    print()
    manager.print_colored('info', "程序已退出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
