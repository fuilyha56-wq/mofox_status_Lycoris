# -*- coding: utf-8 -*-
from src.plugin_system.base.plugin_metadata import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="MonitorStatus Lite",
    description="轻量级状态监控插件，无独立进程，提供状态图片和系统信息查询。",
    usage="/status, /sysinfo, /mhelp",
    version="1.0.0",
    author="MoFox-Studio",
    license="GPL-v3.0-or-later",
    keywords=["monitor", "status", "lite"],
    python_dependencies=["psutil", "Pillow"]
)
