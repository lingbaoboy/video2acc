import logging
import os
import tempfile
from datetime import datetime
from PySide6.QtWidgets import QTextEdit
from typing import Optional

class AppLogger:
    def __init__(self, name="AudioProcessor", log_file_name="processing_log.txt", log_to_file=True, gui_log_display: Optional[QTextEdit] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 日志写入系统临时目录，保证打包后和双击启动都不会因权限或路径问题导致崩溃
        log_dir = os.path.join(tempfile.gettempdir(), "video2acc_logs")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file_path = os.path.join(log_dir, log_file_name)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        if log_to_file:
            file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        self.gui_log_display = gui_log_display
        
        self.logger.propagate = False

    def log_gui_message(self, message, level=logging.INFO):
        """向GUI发送日志消息并同时记录到文件。"""
        if self.gui_log_display:
            self.gui_log_display.append(message)
            self.gui_log_display.verticalScrollBar().setValue(self.gui_log_display.verticalScrollBar().maximum())

        self.logger.log(level, message)

    def log_success(self, original_file, track_index, output_file_path, operation_type):
        log_msg = (
            f"✅ 成功: "
            f"文件 '{os.path.basename(original_file)}' (音轨 {track_index}) - "
            f"操作: '{operation_type}' - "
            f"输出: '{output_file_path}'"
        )
        self.log_gui_message(log_msg, logging.INFO)

    def log_failure(self, original_file, track_index, error_message, output_file_path="N/A"):
        log_msg = (
            f"❌ 失败: "
            f"文件 '{os.path.basename(original_file)}' (音轨 {track_index}) - "
            f"错误: '{error_message}' - "
            f"输出尝试: '{output_file_path}'"
        )
        self.log_gui_message(log_msg, logging.ERROR)

    def log_info(self, message):
        self.log_gui_message(f"[INFO] {message}", logging.INFO)

    def log_warning(self, message):
        self.log_gui_message(f"[WARNING] {message}", logging.WARNING)

    def log_error(self, message):
        self.log_gui_message(f"[ERROR] {message}", logging.ERROR)