# -*- coding: utf-8 -*-
"""
Monitor Status Image Generator
生成Bot状态图片
"""
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


class MonitorImageGenerator:
    """生成状态图片"""

    def __init__(self):
        self.width = 1100
        self.height = 920
        self.bg_color = (22, 22, 28)  # 深色背景
        self.card_bg = (32, 32, 40)  # 卡片背景
        self.title_color = (255, 255, 255)
        self.text_color = (170, 170, 180)
        self.value_color = (235, 235, 245)
        self.bar_bg_color = (50, 50, 58)
        self.brand_color = (99, 132, 255)  # 主题蓝
        self.success_color = (72, 199, 142)  # 绿色
        self.warning_color = (255, 193, 69)  # 黄色
        self.danger_color = (255, 99, 99)  # 红色
        self.cyan_color = (69, 199, 227)  # 青色
        self.purple_color = (167, 139, 250)  # 紫色

        try:
            self.font_bold = ImageFont.truetype("msyh.ttc", 30)
            self.font_title = ImageFont.truetype("msyh.ttc", 18)
            self.font_main = ImageFont.truetype("msyh.ttc", 15)
            self.font_small = ImageFont.truetype("msyh.ttc", 12)
            self.font_value = ImageFont.truetype("msyhbd.ttc", 15)
        except OSError:
            self.font_bold = ImageFont.load_default()
            self.font_title = ImageFont.load_default()
            self.font_main = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_value = ImageFont.load_default()

    def generate(self, data: dict) -> bytes:
        """生成图片并返回字节"""
        # 动态计算高度
        disk_count = len(data.get('disks', []))
        disk_card_height = max(35 * min(disk_count, 5) + 55, 90)
        self.height = 920 + max(0, (disk_count - 3) * 35)
        
        image = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)

        # 绘制标题区域
        self._draw_header(draw, data)
        
        y_pos = 80
        card_margin = 25
        card_width = (self.width - card_margin * 3) // 2

        # ===== 左侧卡片 =====
        left_x = card_margin
        
        # 系统信息卡片
        y_pos_left = self._draw_card(draw, "📊 系统信息", left_x, y_pos, card_width, 180, 
                                      lambda d, x, y, w: self._draw_system_info(d, x, y, w, data))
        y_pos_left += 12
        
        # 资源使用卡片
        y_pos_left = self._draw_card(draw, "💻 资源使用", left_x, y_pos_left, card_width, 165, 
                                      lambda d, x, y, w: self._draw_resource_usage(d, x, y, w, data))
        y_pos_left += 12
        
        # 监控统计卡片
        y_pos_left = self._draw_card(draw, "📈 监控统计", left_x, y_pos_left, card_width, 195, 
                                      lambda d, x, y, w: self._draw_monitor_stats(d, x, y, w, data))
        y_pos_left += 12
        
        # 消息统计卡片
        self._draw_card(draw, "💬 消息统计 (24h)", left_x, y_pos_left, card_width, 105, 
                        lambda d, x, y, w: self._draw_message_stats(d, x, y, w, data))

        # ===== 右侧卡片 =====
        right_x = card_margin * 2 + card_width
        y_pos_right = y_pos
        
        # Bot 状态卡片
        y_pos_right = self._draw_card(draw, "🤖 Bot 状态", right_x, y_pos_right, card_width, 195, 
                                       lambda d, x, y, w: self._draw_bot_status(d, x, y, w, data))
        y_pos_right += 12
        
        # 磁盘空间卡片
        y_pos_right = self._draw_card(draw, "💾 磁盘空间", right_x, y_pos_right, card_width, disk_card_height, 
                                       lambda d, x, y, w: self._draw_disk_info(d, x, y, w, data))
        y_pos_right += 12
        
        # 插件信息卡片
        self._draw_card(draw, "🔌 插件信息", right_x, y_pos_right, card_width, 105, 
                        lambda d, x, y, w: self._draw_plugin_info(d, x, y, w, data))

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _draw_header(self, draw, data):
        """绘制头部"""
        # 标题
        self._draw_text(draw, "🦊 MoFox-Bot 状态面板", (30, 22), self.font_bold, self.title_color)
        
        # 时间戳
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._draw_text(draw, current_time, (self.width - 165, 32), self.font_small, self.text_color)

    def _draw_card(self, draw, title, x, y, width, height, content_func):
        """绘制卡片"""
        # 卡片背景
        draw.rounded_rectangle(
            [x, y, x + width, y + height],
            radius=10,
            fill=self.card_bg
        )
        
        # 卡片标题
        self._draw_text(draw, title, (x + 18, y + 12), self.font_title, self.title_color)
        
        # 绘制内容
        content_func(draw, x + 18, y + 42, width - 36)
        
        return y + height

    def _draw_system_info(self, draw, x, y, width, data):
        """绘制系统信息"""
        items = [
            ("操作系统", f"{data.get('os_type', 'N/A')} {data.get('os_version', '')}"),
            ("完整版本", data.get('os_full_version', 'N/A')),
            ("Python", data.get('python_version', 'N/A')),
            ("系统运行", data.get('boot_time', 'N/A')),
        ]
        
        for i, (label, value) in enumerate(items):
            self._draw_info_row(draw, label, str(value), x, y + i * 30, width)

    def _draw_resource_usage(self, draw, x, y, width, data):
        """绘制资源使用"""
        # CPU
        cpu = data.get('cpu_percent', 0)
        self._draw_progress_bar(draw, "CPU", cpu, x, y, width - 15, self._get_usage_color(cpu))
        
        # 内存
        ram = data.get('ram_percent', 0)
        ram_text = f"{data.get('ram_used_gb', 0):.1f}G / {data.get('ram_total_gb', 0):.1f}G"
        self._draw_progress_bar(draw, "内存", ram, x, y + 45, width - 15, self._get_usage_color(ram), ram_text)
        
        # Bot 内存
        bot_mem = data.get('bot_memory_mb', 0)
        self._draw_info_row(draw, "Bot占用", f"{bot_mem:.1f} MB", x, y + 95, width)

    def _draw_bot_status(self, draw, x, y, width, data):
        """绘制Bot状态"""
        bot_status = data.get('bot_status', '未知')
        status_color = self.success_color if bot_status == '运行中' else self.danger_color
        
        items = [
            ("运行状态", bot_status, status_color),
            ("进程 PID", str(data.get('bot_pid', 'N/A')), self.value_color),
            ("运行时间", data.get('bot_uptime', 'N/A'), self.value_color),
            ("线程数量", str(data.get('bot_threads', 0)), self.value_color),
            ("Bot QQ", str(data.get('bot_qq', 'N/A')), self.cyan_color),
        ]
        
        for i, item in enumerate(items):
            label, value, color = item
            self._draw_info_row_colored(draw, label, value, x, y + i * 28, width, color)

    def _draw_disk_info(self, draw, x, y, width, data):
        """绘制磁盘信息"""
        disks = data.get('disks', [])
        
        if not disks:
            self._draw_text(draw, "无可用磁盘信息", (x, y), self.font_main, self.text_color)
            return
        
        for i, disk in enumerate(disks[:5]):  # 最多显示5个
            mountpoint = disk.get('mountpoint', '').replace('\\', '')
            percent = disk.get('percent', 0)
            used = disk.get('used_gb', 0)
            total = disk.get('total_gb', 0)
            
            label = f"{mountpoint}"
            detail = f"{used:.0f}G / {total:.0f}G"
            
            self._draw_mini_progress(draw, label, percent, x, y + i * 32, width - 15, detail)

    def _draw_monitor_stats(self, draw, x, y, width, data):
        """绘制监控统计（数据来自外部监控程序）"""
        # 监控程序状态
        monitor_running = data.get('monitor_running', False)
        monitor_status = "运行中" if monitor_running else "未运行"
        status_color = self.success_color if monitor_running else self.danger_color
        
        self._draw_text(draw, "监控程序", (x, y), self.font_main, self.text_color)
        self._draw_text(draw, monitor_status, (x + 85, y), self.font_value, status_color)
        
        items = [
            ("监控时长", data.get('monitor_duration', 'N/A')),
            ("重启次数", str(data.get('total_restarts', 0))),
            ("内存重启", str(data.get('memory_leak_restarts', 0))),
            ("崩溃计数", str(data.get('crash_count', 0))),
        ]
        
        auto_restart = data.get('auto_restart_interval', 0)
        if auto_restart > 0:
            items.append(("定时重启", f"每 {auto_restart // 60} 分钟"))
        else:
            items.append(("定时重启", "已关闭"))
        
        for i, (label, value) in enumerate(items):
            self._draw_info_row(draw, label, value, x, y + 28 + i * 28, width)

    def _draw_message_stats(self, draw, x, y, width, data):
        """绘制消息统计"""
        items = [
            ("接收消息", str(data.get('total_messages_24h', 0)), self.cyan_color),
            ("发送消息", str(data.get('bot_messages_24h', 0)), self.purple_color),
        ]
        
        for i, (label, value, color) in enumerate(items):
            self._draw_info_row_colored(draw, label, value, x, y + i * 28, width, color)

    def _draw_plugin_info(self, draw, x, y, width, data):
        """绘制插件信息"""
        plugin_count = data.get('plugin_count', 0)
        enabled_count = data.get('enabled_plugin_count', plugin_count)
        
        items = [
            ("已加载", f"{plugin_count} 个插件", self.success_color),
            ("已启用", f"{enabled_count} 个", self.cyan_color),
        ]
        
        for i, (label, value, color) in enumerate(items):
            self._draw_info_row_colored(draw, label, value, x, y + i * 28, width, color)

    def _get_usage_color(self, percent: float) -> tuple:
        """根据使用率返回颜色"""
        if percent < 60:
            return self.success_color
        elif percent < 85:
            return self.warning_color
        else:
            return self.danger_color

    def _draw_text(self, draw, text, position, font, color):
        draw.text(position, str(text), font=font, fill=color)

    def _draw_info_row(self, draw, label, value, x, y, width):
        """绘制信息行"""
        self._draw_text(draw, label, (x, y), self.font_main, self.text_color)
        self._draw_text(draw, value, (x + 85, y), self.font_value, self.value_color)

    def _draw_info_row_colored(self, draw, label, value, x, y, width, value_color):
        """绘制带颜色的信息行"""
        self._draw_text(draw, label, (x, y), self.font_main, self.text_color)
        self._draw_text(draw, value, (x + 85, y), self.font_value, value_color)

    def _draw_progress_bar(self, draw, label, percentage, x, y, width, color, extra_text=""):
        """绘制进度条"""
        bar_height = 18
        bar_width = width - 80
        
        # 标签
        self._draw_text(draw, label, (x, y), self.font_main, self.text_color)
        
        # 背景条
        bar_x = x + 50
        draw.rounded_rectangle(
            [bar_x, y, bar_x + bar_width, y + bar_height],
            radius=4,
            fill=self.bar_bg_color
        )
        
        # 前景条
        fill_width = max(int(bar_width * (percentage / 100)), 6)
        draw.rounded_rectangle(
            [bar_x, y, bar_x + fill_width, y + bar_height],
            radius=4,
            fill=color
        )
        
        # 百分比
        self._draw_text(draw, f"{percentage:.0f}%", (bar_x + bar_width + 8, y), self.font_small, self.value_color)
        
        # 额外文字
        if extra_text:
            self._draw_text(draw, extra_text, (x, y + 22), self.font_small, self.text_color)

    def _draw_mini_progress(self, draw, label, percentage, x, y, width, detail=""):
        """绘制迷你进度条"""
        bar_height = 14
        label_width = 30
        bar_width = width - label_width - 110
        
        # 标签
        self._draw_text(draw, label, (x, y), self.font_main, self.value_color)
        
        # 背景条
        bar_x = x + label_width
        draw.rounded_rectangle(
            [bar_x, y + 2, bar_x + bar_width, y + bar_height],
            radius=3,
            fill=self.bar_bg_color
        )
        
        # 前景条
        color = self._get_usage_color(percentage)
        fill_width = max(int(bar_width * (percentage / 100)), 4)
        draw.rounded_rectangle(
            [bar_x, y + 2, bar_x + fill_width, y + bar_height],
            radius=3,
            fill=color
        )
        
        # 详情
        self._draw_text(draw, f"{percentage:.0f}% {detail}", (bar_x + bar_width + 6, y), self.font_small, self.text_color)
