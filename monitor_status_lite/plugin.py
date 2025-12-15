# -*- coding: utf-8 -*-
"""
Monitor Status Plugin (Lite Edition)
轻量级状态监控插件，无独立进程，无重启功能
"""

import base64
import platform
import sys
import time
import os
import asyncio
from collections import deque
from typing import ClassVar, Type

import psutil

# 全局内存历史记录 (保留最近60个点，每分钟一个)
MEMORY_HISTORY = deque(maxlen=60)

from src.config.config import global_config
from src.plugin_system.apis import plugin_manage_api
from src.plugin_system import register_plugin
from src.plugin_system.base.base_plugin import BasePlugin
from src.plugin_system.base.command_args import CommandArgs
from src.plugin_system.base.component_types import ChatType, PlusCommandInfo, PermissionNodeField
from src.plugin_system.base.plus_command import PlusCommand
from src.plugin_system.utils.permission_decorators import require_permission

# 尝试导入图片生成器
try:
    from .image_generator import MonitorImageGenerator
    IMAGE_GENERATOR_AVAILABLE = True
except ImportError:
    IMAGE_GENERATOR_AVAILABLE = False
    print("[MonitorStatusLite] 图片生成器加载失败，将只提供文字模式")


# ==================== 工具函数 ====================
def format_duration(seconds: int) -> str:
    """格式化时间间隔"""
    if seconds < 0:
        return "N/A"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分")
    if secs > 0 or not parts:
        parts.append(f"{secs}秒")
    
    return "".join(parts[:3])


def get_full_os_version() -> str:
    """获取完整的操作系统版本"""
    try:
        if platform.system() == "Windows":
            version = platform.version()
            release = platform.release()
            return f"{release} (Build {version})"
        else:
            return platform.platform()
    except Exception:
        return platform.release()


def get_disk_info() -> list:
    """获取所有磁盘信息"""
    disks = []
    try:
        for part in psutil.disk_partitions():
            try:
                if 'cdrom' in part.opts.lower() or part.fstype == '':
                    continue
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "mountpoint": part.mountpoint,
                    "percent": usage.percent,
                    "total_gb": usage.total / (1024**3),
                    "used_gb": usage.used / (1024**3),
                    "free_gb": usage.free / (1024**3)
                })
            except:
                pass
    except:
        pass
    return disks


def get_bot_process_info() -> dict:
    """获取Bot进程信息"""
    try:
        process = psutil.Process(os.getpid())
        return {
            "pid": process.pid,
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "threads": process.num_threads(),
            "create_time": process.create_time(),
            "uptime": time.time() - process.create_time()
        }
    except:
        return {}


# ==================== 命令实现 ====================

class StatusCommand(PlusCommand):
    """显示Bot状态图片"""

    command_name: str = "status"
    command_description: str = "显示Bot状态和系统信息"
    command_aliases: ClassVar[list[str]] = ["状态", "about", "关于", "info", "status_image", "状态图"]
    chat_type_allow: ChatType = ChatType.ALL
    priority: int = 10

    @require_permission("access", deny_message="❌ 你没有权限查看状态")
    async def execute(self, args: CommandArgs) -> tuple[bool, str | None, bool]:
        """执行命令"""
        # 收集数据
        data = {}
        
        # 系统信息
        data['os_type'] = platform.system()
        data['os_version'] = platform.release()
        data['os_full_version'] = get_full_os_version()
        data['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        data['boot_time'] = format_duration(int(time.time() - psutil.boot_time()))
        
        # 资源使用
        data['cpu_percent'] = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        data['ram_percent'] = ram.percent
        data['ram_used_gb'] = ram.used / (1024**3)
        data['ram_total_gb'] = ram.total / (1024**3)
        
        # 磁盘信息
        data['disks'] = get_disk_info()
        
        # Bot 信息
        bot_info = get_bot_process_info()
        data['bot_pid'] = bot_info.get('pid', 'N/A')
        data['bot_memory_mb'] = bot_info.get('memory_mb', 0)
        data['bot_threads'] = bot_info.get('threads', 0)
        data['bot_uptime'] = format_duration(int(bot_info.get('uptime', 0)))
        data['bot_status'] = "运行中"
        data['bot_qq'] = global_config.bot.bot_qq_id
        
        # 插件统计
        plugins = plugin_manage_api.get_all_plugins()
        data['plugin_count'] = len(plugins)
        data['enabled_plugin_count'] = len([p for p in plugins if p.enable_plugin])
        
        if IMAGE_GENERATOR_AVAILABLE:
            try:
                # 生成图片
                generator = MonitorImageGenerator()
                img_bytes = generator.generate(data)
                
                # 发送图片
                b64_img = base64.b64encode(img_bytes).decode()
                await self.send_image(b64_img)
                return True, "状态图片已发送", True
            except Exception as e:
                await self.send_text(f"❌ 图片生成失败: {e}\n正在发送文字版...")
        
        # 如果图片生成失败或不可用，发送文字版
        text = f"""
📊 **Bot 状态报告**
------------------
🤖 Bot QQ: {data['bot_qq']}
⏱️ 运行时间: {data['bot_uptime']}
🧠 内存占用: {data['bot_memory_mb']:.1f} MB
🧵 线程数量: {data['bot_threads']}
------------------
💻 系统: {data['os_full_version']}
🐍 Python: {data['python_version']}
⚙️ CPU: {data['cpu_percent']}%
💾 RAM: {data['ram_percent']}% ({data['ram_used_gb']:.1f}/{data['ram_total_gb']:.1f} GB)
------------------
📦 插件: {data['enabled_plugin_count']}/{data['plugin_count']} 已启用
"""
        await self.send_text(text.strip())
        return True, "状态信息已发送", True


class SysInfoCommand(PlusCommand):
    """显示系统信息（文字版）"""

    command_name: str = "sysinfo"
    command_description: str = "显示系统信息（文字版）"
    command_aliases: ClassVar[list[str]] = ["系统信息", "status_text", "状态文"]
    chat_type_allow: ChatType = ChatType.ALL
    priority: int = 20

    @require_permission("access", deny_message="❌ 你没有权限查看系统信息")
    async def execute(self, args: CommandArgs) -> tuple[bool, str | None, bool]:
        """执行命令"""
        # 收集简要信息
        cpu_p = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        
        info = [
            "🖥️ **系统概览**",
            f"OS: {get_full_os_version()}",
            f"CPU: {cpu_p}%",
            f"RAM: {ram.percent}% ({ram.used / (1024**3):.1f}GB Used)",
            f"Boot: {format_duration(int(time.time() - psutil.boot_time()))} ago"
        ]
        
        # 磁盘
        info.append("\n💾 **磁盘状态**")
        for disk in get_disk_info():
            info.append(f"- {disk['mountpoint']}: {disk['percent']}% ({disk['free_gb']:.1f}GB Free)")
            
        await self.send_text("\n".join(info))
        return True, "系统信息已发送", True


class MemoryAnalysisCommand(PlusCommand):
    """内存分析报告"""

    command_name: str = "mem"
    command_description: str = "查看Bot内存历史趋势分析"
    command_aliases: ClassVar[list[str]] = ["内存分析", "memory"]
    chat_type_allow: ChatType = ChatType.ALL
    priority: int = 20

    @require_permission("access", deny_message="❌ 无权操作")
    async def execute(self, args: CommandArgs) -> tuple[bool, str | None, bool]:
        """执行命令"""
        if not MEMORY_HISTORY:
            # 如果没有历史数据，先采集一次
            try:
                process = psutil.Process(os.getpid())
                mem = process.memory_info().rss / 1024 / 1024
                MEMORY_HISTORY.append(mem)
            except:
                pass
        
        if not MEMORY_HISTORY:
             return True, "❌ 暂无内存数据", False

        current = MEMORY_HISTORY[-1]
        avg = sum(MEMORY_HISTORY) / len(MEMORY_HISTORY)
        max_mem = max(MEMORY_HISTORY)
        min_mem = min(MEMORY_HISTORY)
        
        # 趋势分析
        trend_str = "➡️ 相对平稳"
        if len(MEMORY_HISTORY) >= 5:
            # 比较最近5分钟和最早5分钟的平均值
            history_list = list(MEMORY_HISTORY)
            recent_avg = sum(history_list[-5:]) / len(history_list[-5:])
            old_avg = sum(history_list[:5]) / len(history_list[:5])
            
            diff = recent_avg - old_avg
            if diff > 10:
                trend_str = "↗️ 明显上升 (可能存在泄漏)"
            elif diff > 2:
                trend_str = "↗️ 缓慢上升"
            elif diff < -10:
                trend_str = "↘️ 明显下降"
            elif diff < -2:
                trend_str = "↘️ 缓慢下降"
        else:
            trend_str = "🔄 数据收集中..."

        msg = f"""
🧠 **内存分析报告** (近 {len(MEMORY_HISTORY)} 分钟)
------------------
当前: {current:.1f} MB
平均: {avg:.1f} MB
峰值: {max_mem:.1f} MB
趋势: {trend_str}
------------------
* 数据每分钟自动采集一次
"""
        await self.send_text(msg.strip())
        return True, "内存分析已发送", True


class MonitorHelpCommand(PlusCommand):
    """显示监控命令帮助"""

    command_name: str = "mhelp"
    command_description: str = "显示监控相关命令帮助"
    command_aliases: ClassVar[list[str]] = ["监控帮助"]
    chat_type_allow: ChatType = ChatType.ALL
    priority: int = 20

    async def execute(self, args: CommandArgs) -> tuple[bool, str | None, bool]:
        """执行命令"""
        help_text = """
📋 **监控插件帮助**
------------------
/status  - 查看Bot状态图片
/sysinfo - 查看Bot状态文字
/mem     - 内存趋势分析
"""
        await self.send_text(help_text.strip())
        return True, "帮助已发送", True


# ==================== 插件注册 ====================

@register_plugin
class MonitorStatusLitePlugin(BasePlugin):
    plugin_name: str = "monitor_status_lite"
    enable_plugin: bool = True
    config_file_name: str = "config.toml"

    def get_plugin_components(self) -> list[tuple[PlusCommandInfo, Type[PlusCommand]]]:
        """返回插件的PlusCommand组件"""
        return [
            (StatusCommand.get_plus_command_info(), StatusCommand),
            (SysInfoCommand.get_plus_command_info(), SysInfoCommand),
            (MonitorHelpCommand.get_plus_command_info(), MonitorHelpCommand),
            (MemoryAnalysisCommand.get_plus_command_info(), MemoryAnalysisCommand),
        ]

    async def on_plugin_loaded(self):
        """插件加载时启动内存记录任务"""
        asyncio.create_task(self._memory_recorder())
        
    async def _memory_recorder(self):
        """后台任务：每分钟记录一次内存"""
        while True:
            try:
                process = psutil.Process(os.getpid())
                mem = process.memory_info().rss / 1024 / 1024
                MEMORY_HISTORY.append(mem)
            except Exception:
                pass
            await asyncio.sleep(60)

    permission_nodes: ClassVar[list[PermissionNodeField]] = [
        PermissionNodeField(
            node_name="access",
            description="可以使用/status等查看命令",
        ),
    ]
