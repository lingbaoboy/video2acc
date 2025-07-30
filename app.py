import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QMessageBox,
                               QWidget, QVBoxLayout, QListWidget, QLabel, QComboBox,
                               QLineEdit, QPushButton, QHBoxLayout, QRadioButton,
                               QGroupBox, QTextEdit)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIntValidator, QIcon

# 导入 UI 文件（假设您已经通过 pyside6-uic 生成或直接使用我提供的 ui_main_window.py）
from ui_main_window import Ui_MainWindow

# 导入自定义工具模块
from ffmpeg_utils import FFmpegProcessor
from logger_utils import AppLogger
import logging
import logging

# 工具函数：兼容PyInstaller打包和源码运行的资源路径

def resource_path(relative_path):
    import sys, os
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

# --- 工作线程定义 ---
class ProcessingThread(QThread):
    """
    独立线程，用于执行耗时的文件处理操作，避免GUI卡顿。
    通过信号与主线程通信。
    """
    # 定义信号，用于向主线程发送处理状态和日志
    processing_started = Signal(str) # 发送当前处理的文件名
    processing_finished = Signal(str, bool) # 发送文件名和处理结果 (成功/失败)
    new_log_message = Signal(str, int) # 发送新的日志消息和级别，由MainWindow的logger接收

    def __init__(self, files_to_process, processing_config, log_callback, parent=None):
        super().__init__(parent)
        self.files_to_process = files_to_process
        self.config = processing_config
        self.ffmpeg_processor = FFmpegProcessor(log_callback=None)

    def _thread_log(self, message, level=logging.INFO):
        self.new_log_message.emit(message, level)

    def run(self):
        self._thread_log("处理线程启动。", level=logging.INFO)
        for file_path in self.files_to_process:
            self.processing_started.emit(f"开始处理: {os.path.basename(file_path)}")
            self._thread_log(f"[INFO] 开始处理文件: {file_path}")
            success = self.process_single_file(file_path)
            self.processing_finished.emit(os.path.basename(file_path), success)
            if not success:
                self._thread_log(f"[ERROR] 文件处理失败: {file_path}")
            else:
                self._thread_log(f"[INFO] 文件处理完成: {file_path}")
        self._thread_log("[INFO] 所有文件处理完毕。")
        self._thread_log("[INFO] 处理线程结束。")

    def process_single_file(self, file_path):
        try:
            tracks_info = self.ffmpeg_processor.probe_audio_tracks(file_path)
            if not tracks_info:
                self._thread_log(f"[WARNING] 未检测到 {os.path.basename(file_path)} 中的任何音频轨道。跳过。", logging.WARNING)
                self.new_log_message.emit(f"❌ 失败: 文件 '{os.path.basename(file_path)}' (音轨 N/A) - 错误: '未检测到音频轨道' - 输出尝试: 'N/A'", logging.ERROR)
                return False
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = os.path.join(os.path.dirname(file_path), "output")
            os.makedirs(output_dir, exist_ok=True)
            file_processed_successfully = True
            audio_tracks = [t for t in tracks_info if t.get('codec_type') == 'audio']
            for i, track_info in enumerate(audio_tracks):
                track_index = track_info['index']
                audio_track_index = i
                codec_name = track_info['codec_name']
                track_language = track_info.get('tags', {}).get('language', '未知')
                self._thread_log(f"[INFO] 正在处理 {os.path.basename(file_path)} 的音轨 {track_index} (音频流 #{audio_track_index}, 编码: {codec_name}, 语言: {track_language})...")
                current_output_name_prefix = os.path.join(output_dir, f"{base_name}-Track{track_index}")
                if self.config['mode'] == 'direct_extract':
                    if codec_name.lower() == 'aac':
                        output_file = f"{current_output_name_prefix}.m4a"
                        self._thread_log(f"[DEBUG] 尝试直接提取 AAC 音轨: {file_path} -> {output_file}")
                        cmd_success = self.ffmpeg_processor.extract_aac_track(
                            input_path=file_path,
                            output_path=output_file,
                            track_index=audio_track_index
                        )
                        if cmd_success:
                            self.new_log_message.emit(f"✅ 成功: 文件 '{os.path.basename(file_path)}' (音轨 {track_index}) - 操作: '直接提取 AAC' - 输出: '{output_file}'", logging.INFO)
                        else:
                            self.new_log_message.emit(f"❌ 失败: 文件 '{os.path.basename(file_path)}' (音轨 {track_index}) - 错误: '直接提取 AAC 失败' - 输出尝试: '{output_file}'", logging.ERROR)
                            file_processed_successfully = False
                    else:
                        raw_ext = self.ffmpeg_processor.get_common_audio_extension(codec_name)
                        raw_output_file = f"{current_output_name_prefix}.{raw_ext}"
                        self._thread_log(f"[INFO] 音轨 {track_index} ({codec_name}) 非 AAC，先无损提取到 {raw_output_file}")
                        cmd_success_raw = self.ffmpeg_processor.extract_raw_audio(
                            input_path=file_path,
                            output_path=raw_output_file,
                            track_index=audio_track_index,
                            codec_name=codec_name
                        )
                        if not cmd_success_raw:
                            self._thread_log(f"[ERROR] 无损提取原始音频 {raw_output_file} 失败。", logging.ERROR)
                            self.new_log_message.emit(f"❌ 失败: 文件 '{os.path.basename(file_path)}' (音轨 {track_index}) - 错误: '无损提取原始音频失败' - 输出尝试: '{raw_output_file}'", logging.ERROR)
                            file_processed_successfully = False
                            continue
                        self.new_log_message.emit(f"✅ 成功: 文件 '{os.path.basename(file_path)}' (音轨 {track_index}) - 操作: '无损提取 {codec_name}' - 输出: '{raw_output_file}'", logging.INFO)
                        output_file_encoded = f"{current_output_name_prefix}.{self.config['output_format']}"
                        self._thread_log(f"[INFO] 对 {raw_output_file} 重新编码为 {self.config['output_codec']}...")
                        cmd_success_encode = self.ffmpeg_processor.recode_audio(
                            input_path=raw_output_file,
                            output_path=output_file_encoded,
                            codec=self.config['output_codec'],
                            bitrate=self.config.get('bitrate'),
                            samplerate=self.config.get('samplerate'),
                            channels=self.config.get('channels'),
                            quality=self.config.get('quality')
                        )
                        if cmd_success_encode:
                            self.new_log_message.emit(f"✅ 成功: 文件 '{os.path.basename(file_path)}' (音轨 {track_index}) - 操作: '重新编码为 {self.config['output_codec']}' - 输出: '{output_file_encoded}'", logging.INFO)
                        else:
                            self.new_log_message.emit(f"❌ 失败: 文件 '{os.path.basename(file_path)}' (音轨 {track_index}) - 错误: '重新编码为 {self.config['output_codec']} 失败' - 输出尝试: '{output_file_encoded}'", logging.ERROR)
                            file_processed_successfully = False
                elif self.config['mode'] == 'recode':
                    output_file = f"{current_output_name_prefix}.{self.config['output_format']}"
                    self._thread_log(f"[INFO] 重新编码音轨 {track_index} 为 {self.config['output_codec']}...")
                    cmd_success = self.ffmpeg_processor.recode_audio(
                        input_path=file_path,
                        output_path=output_file,
                        track_index=audio_track_index,
                        codec=self.config['output_codec'],
                        bitrate=self.config.get('bitrate'),
                        samplerate=self.config.get('samplerate'),
                        channels=self.config.get('channels'),
                        quality=self.config.get('quality')
                    )
                    if cmd_success:
                        self.new_log_message.emit(f"✅ 成功: 文件 '{os.path.basename(file_path)}' (音轨 {track_index}) - 操作: '重新编码为 {self.config['output_codec']}' - 输出: '{output_file}'", logging.INFO)
                    else:
                        self.new_log_message.emit(f"❌ 失败: 文件 '{os.path.basename(file_path)}' (音轨 {track_index}) - 错误: '重新编码为 {self.config['output_codec']} 失败' - 输出尝试: '{output_file}'", logging.ERROR)
                        file_processed_successfully = False
            return file_processed_successfully
        except Exception as e:
            self._thread_log(f"[CRITICAL ERROR] 处理 {os.path.basename(file_path)} 时发生异常: {e}", logging.ERROR)
            self.new_log_message.emit(f"❌ 失败: 文件 '{os.path.basename(file_path)}' (音轨 N/A) - 错误: '程序异常: {e}' - 输出尝试: 'N/A'", logging.ERROR)
            return False

# --- 主窗口类 ---
class MainWindow(QMainWindow):
    """
    应用程序的主窗口，负责GUI的显示、用户交互和任务调度。
    """

    def __init__(self):
        super().__init__()
        # 优先使用ico.ico，其次ico.png，全部用resource_path
        icon_path_ico = resource_path("ico.ico")
        icon_path_png = resource_path("ico.png")
        if os.path.exists(icon_path_ico):
            self.setWindowIcon(QIcon(icon_path_ico))
        elif os.path.exists(icon_path_png):
            self.setWindowIcon(QIcon(icon_path_png))
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 添加页脚作者信息
        from PySide6.QtWidgets import QLabel
        author_label = QLabel("作者：lingbaoboy")
        author_label.setStyleSheet("color: gray; font-size: 10pt; padding: 2px 8px;")
        author_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.statusBar().addPermanentWidget(author_label)

        self.logger = AppLogger("AppLogger", log_to_file=True, gui_log_display=self.ui.log_display_text_edit)
        # 修正ffmpeg路径传递
        ffmpeg_dir = resource_path("ffmpeg")
        self.ffmpeg_processor = FFmpegProcessor(log_callback=self.logger.log_gui_message)
        self.ffmpeg_processor.ffmpeg_dir = ffmpeg_dir
        self.selected_files = []
        self.processing_thread = None
        self.track_info_cache = {} # 用于缓存文件音轨信息

        self.setup_ui_connections()
        self.setup_encoding_parameters()
        self.update_ui_state()

        # 启用拖拽文件到主窗口
        self.setAcceptDrops(True)

        self.logger.log_gui_message("[INFO] 应用程序启动。请选择媒体文件或直接拖入。")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if os.path.isfile(local_path):
                files.append(local_path)
        if files:
            # 合并去重
            all_files = list(dict.fromkeys(self.selected_files + files))
            self.selected_files = all_files
            self.track_info_cache.clear()
            self.ui.file_list_widget.clear()
            for f in self.selected_files:
                self.ui.file_list_widget.addItem(os.path.basename(f))
            self.logger.log_gui_message(f"[INFO] 拖入 {len(files)} 个文件，当前共 {len(self.selected_files)} 个文件。")
            self.update_ui_state(force_probe=True)

    def setup_ui_connections(self):
        """连接UI控件的信号到对应的槽函数。"""
        self.ui.select_files_button.clicked.connect(self.select_files)
        self.ui.start_processing_button.clicked.connect(self.start_processing)
        
        # 模式选择单选按钮连接到更新UI状态的槽
        self.ui.direct_extract_radio.toggled.connect(self.update_ui_state)
        self.ui.recode_radio.toggled.connect(self.update_ui_state)

        # 编码格式选择下拉框连接到更新编码参数提示的槽
        self.ui.codec_combo_box.currentIndexChanged.connect(self.update_codec_parameters)

        # 限制输入框只能输入数字
        self.ui.bitrate_line_edit.setValidator(QIntValidator(1, 999999)) # 比特率可以更高
        # 采样率允许小数点，单位为kHz
        from PySide6.QtGui import QDoubleValidator
        self.ui.samplerate_line_edit.setValidator(QDoubleValidator(1.0, 192.0, 2))
        self.ui.channels_line_edit.setValidator(QIntValidator(1, 8)) # 例如，最多8声道
        # 质量参数通常也是数字，但范围因编码器而异，这里也用IntValidator
        self.ui.quality_line_edit.setValidator(QIntValidator(0, 100)) # 质量范围，根据实际编码器调整

    def setup_encoding_parameters(self):
        """填充编码格式选项，并设置默认值。"""
        self.ui.codec_combo_box.clear()
        self.ui.codec_combo_box.addItems(["aac", "mp3", "opus", "flac"])
        self.ui.codec_combo_box.setCurrentText("aac") # 默认选中AAC
        # --- Opus采样率下拉框替换 ---
        # 采样率区采用水平布局，采样率输入框和下拉框同行
        from PySide6.QtWidgets import QComboBox, QHBoxLayout
        # 若已存在采样率下拉框，先移除
        if hasattr(self, 'samplerate_combo_box'):
            self.samplerate_combo_box.setParent(None)
            self.samplerate_combo_box.deleteLater()
            del self.samplerate_combo_box
        # 获取采样率行的水平布局
        samplerate_layout = None
        for i in range(self.ui.formLayout_encoding_params.count()):
            item = self.ui.formLayout_encoding_params.itemAt(i)
            if isinstance(item, QHBoxLayout):
                # 检查该行是否包含采样率输入框
                for j in range(item.count()):
                    w = item.itemAt(j).widget()
                    if w is self.ui.samplerate_line_edit:
                        samplerate_layout = item
                        break
            if samplerate_layout:
                break
        # 创建采样率下拉框
        self.samplerate_combo_box = QComboBox(self.ui.encoding_params_group_box)
        self.samplerate_combo_box.addItems(["48", "24", "16", "12", "8"])
        self.samplerate_combo_box.setCurrentText("48")
        self.samplerate_combo_box.setVisible(False)
        self.samplerate_combo_box.setFixedWidth(70)
        # 插入到采样率输入框右侧
        if samplerate_layout:
            # 查找采样率输入框在该行的索引
            idx = -1
            for j in range(samplerate_layout.count()):
                w = samplerate_layout.itemAt(j).widget()
                if w is self.ui.samplerate_line_edit:
                    idx = j
                    break
            if idx != -1:
                samplerate_layout.insertWidget(idx + 1, self.samplerate_combo_box)
            else:
                samplerate_layout.addWidget(self.samplerate_combo_box)
        else:
            # 如果没找到，直接加到主布局
            self.ui.formLayout_encoding_params.addWidget(self.samplerate_combo_box)
        # 默认采样率 44.1kHz，声道2
        self.ui.samplerate_line_edit.setText("44.1")
        self.ui.channels_line_edit.setText("2")
        self.update_codec_parameters() # 初始化参数显示

    def update_codec_parameters(self):
        """根据选择的编码格式更新编码参数区域的提示文本和常见参数。"""
        selected_codec = self.ui.codec_combo_box.currentText()
        # Opus采样率下拉框逻辑
        if selected_codec == "opus":
            self.ui.bitrate_line_edit.setPlaceholderText("默认: 256k(ABR)")
            if hasattr(self, 'samplerate_combo_box'):
                self.samplerate_combo_box.setVisible(True)
                self.samplerate_combo_box.setToolTip("Opus编码仅支持采样率: 48, 24, 16, 12, 8 kHz")
                self.samplerate_combo_box.setCurrentText("48")
            self.ui.samplerate_line_edit.setVisible(False)
        else:
            self.ui.bitrate_line_edit.setPlaceholderText("默认:aac 256k  mp3 320k (ABR)" if selected_codec in ["aac", "mp3"] else "")
            if hasattr(self, 'samplerate_combo_box'):
                self.samplerate_combo_box.setVisible(False)
            self.ui.samplerate_line_edit.setVisible(True)
            self.ui.samplerate_line_edit.setPlaceholderText("采样率 (kHz)，如44.1")
            self.ui.samplerate_line_edit.setToolTip("")
        if selected_codec in ["aac", "mp3", "opus"]:
            self.ui.quality_label.setVisible(False)
            self.ui.quality_line_edit.setVisible(False)
        elif selected_codec == "flac":
            self.ui.bitrate_line_edit.setPlaceholderText("无损编码, 可留空")
            self.ui.quality_label.setText("压缩级别:")
            self.ui.quality_label.setVisible(True)
            self.ui.quality_line_edit.setVisible(True)
            self.ui.quality_line_edit.setPlaceholderText("0-8 (8最高压缩)")
            self.ui.quality_line_edit.setText("5")
            self.ui.samplerate_line_edit.setPlaceholderText("采样率 (kHz)，如44.1")
            self.ui.samplerate_line_edit.setToolTip("")
        else:
            self.ui.quality_label.setVisible(True)
            self.ui.quality_label.setText("质量:")
            self.ui.quality_line_edit.setVisible(True)
            self.ui.quality_line_edit.setPlaceholderText("")
            self.ui.samplerate_line_edit.setPlaceholderText("采样率 (kHz)，如44.1")
            self.ui.samplerate_line_edit.setToolTip("")
        self.ui.channels_line_edit.setPlaceholderText("声道数，常用2")
        # 清空输入框，避免混淆
        self.ui.quality_line_edit.clear()
        self.ui.bitrate_line_edit.clear()

    def update_ui_state(self, force_probe=False):
        """
        根据当前选择的处理模式和文件分析结果，更新编码参数区域的可见性。
        Args:
            force_probe (bool): 是否强制重新探测文件信息，忽略缓存。
        """
        is_recode_mode = self.ui.recode_radio.isChecked()
        
        if is_recode_mode:
            self.ui.encoding_params_group_box.setVisible(True)
            self.logger.log_gui_message("[INFO] 已选择 '重新编码音频' 模式，请设置编码参数。")
        else: # 直接提取模式
            self.ui.encoding_params_group_box.setVisible(False)
            if self.selected_files:
                needs_encoding = False
                for file_path in self.selected_files:
                    if force_probe or file_path not in self.track_info_cache:
                        self.logger.log_gui_message(f"[INFO] 正在探测 {os.path.basename(file_path)}...")
                        tracks_info = self.ffmpeg_processor.probe_audio_tracks(file_path)
                        self.track_info_cache[file_path] = tracks_info
                    else:
                        tracks_info = self.track_info_cache[file_path]

                    if tracks_info:
                        if any(t['codec_name'].lower() != 'aac' for t in tracks_info):
                            needs_encoding = True
                            break
                
                if needs_encoding:
                    self.ui.encoding_params_group_box.setVisible(True)
                    self.logger.log_gui_message("[INFO] 在 '直接提取' 模式下，检测到非AAC音频，请设置编码参数。")
                else:
                    self.logger.log_gui_message("[INFO] 在 '直接提取' 模式下，所有音轨均为AAC，无需设置编码参数。")
            else:
                self.logger.log_gui_message("[INFO] 请选择文件以开始。")


    def select_files(self):
        """打开文件对话框，允许用户选择多个视频/音频文件。"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles) # 允许选择多个已存在的文件
        # 设置文件过滤器，包含常见的视频和音频格式
        file_dialog.setNameFilter("媒体文件 (*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.webm *.ts *.mpg *.mp3 *.wav *.flac *.aac *.ogg *.opus *.m4a *.wma *.ac3 *.dts *.truehd)")
        
        if file_dialog.exec():
            self.selected_files = file_dialog.selectedFiles()
            self.track_info_cache.clear() # 清空缓存
            self.ui.file_list_widget.clear() # 清空文件列表显示
            for f in self.selected_files:
                self.ui.file_list_widget.addItem(os.path.basename(f)) # 只显示文件名
            
            self.logger.log_gui_message(f"[INFO] 选中 {len(self.selected_files)} 个文件。")
            self.update_ui_state(force_probe=True) # 强制重新探测

    def start_processing(self):
        """开始处理按钮的槽函数，收集参数并启动处理线程。"""
        if not self.selected_files:
            QMessageBox.warning(self, "警告", "请先选择要处理的文件。")
            return
        # 防止重复点击，如果线程已在运行
        if self.processing_thread and self.processing_thread.isRunning():
            QMessageBox.warning(self, "警告", "已有任务正在运行，请等待其完成。")
            return
        # 检查 FFmpeg 是否可用
        if not self.ffmpeg_processor.check_ffmpeg_available():
            QMessageBox.critical(self, "错误", "FFmpeg/ffprobe 可执行文件未找到或无法运行。请确保 'ffmpeg' 文件夹存在并包含正确的二进制文件。")
            self.logger.log_gui_message("[ERROR] FFmpeg/ffprobe 未找到或无法运行。")
            return
        # 收集用户设置的编码参数
        # 采集并修正采样率（kHz转Hz），声道默认2
        selected_codec = self.ui.codec_combo_box.currentText()
        # --- 采样率 ---
        if selected_codec == "opus":
            samplerate = str(int(self.samplerate_combo_box.currentText()) * 1000)
        else:
            raw_samplerate = self.ui.samplerate_line_edit.text().strip()
            if raw_samplerate:
                try:
                    if raw_samplerate.lower().endswith('k'):
                        samplerate = str(int(float(raw_samplerate[:-1]) * 1000))
                    else:
                        samplerate = str(int(float(raw_samplerate) * 1000))
                except Exception:
                    samplerate = None
            else:
                samplerate = "44100"
        raw_channels = self.ui.channels_line_edit.text().strip()
        channels = raw_channels if raw_channels else "2"
        # --- 码率 ---
        bitrate = self.ui.bitrate_line_edit.text().strip()
        if not bitrate:
            if selected_codec in ["aac", "opus"]:
                bitrate = "256"
            elif selected_codec == "mp3":
                bitrate = "320"
        # 只为aac/mp3传递bitrate，不传quality
        quality = None
        if selected_codec not in ["aac", "mp3"]:
            quality = self.ui.quality_line_edit.text().strip() if self.ui.quality_line_edit.text().strip() else None
        processing_config = {
            'mode': 'direct_extract' if self.ui.direct_extract_radio.isChecked() else 'recode',
            'output_codec': selected_codec,
            'bitrate': bitrate,
            'samplerate': samplerate,
            'channels': channels,
            'quality': quality,
        }
        # 根据 output_codec 确定最终输出文件后缀
        processing_config['output_format'] = self.get_output_format_suffix(processing_config['output_codec'])
        self.logger.log_gui_message("[INFO] 开始处理文件...")
        self.ui.start_processing_button.setEnabled(False) # 禁用按钮，避免重复点击
        # 创建并启动处理线程，将 logger 的 log_gui_message 方法作为回调传递
        self.processing_thread = ProcessingThread(
            self.selected_files, 
            processing_config, 
            log_callback=self.logger.log_gui_message
        )
        # 连接线程的信号到主窗口的槽函数
        self.processing_thread.processing_started.connect(self.on_processing_started)
        self.processing_thread.processing_finished.connect(self.on_processing_finished)
        self.processing_thread.new_log_message.connect(self.on_thread_log_message)
        self.processing_thread.finished.connect(self.on_thread_finished)
        self.processing_thread.start()

    def on_thread_log_message(self, msg, lvl):
        """主线程安全地处理子线程日志信号，写入GUI和文件。"""
        self.logger.log_gui_message(msg, level=lvl)

    def on_processing_started(self, filename):
        """处理线程开始处理单个文件时更新状态标签。"""
        self.ui.status_label.setText(f"正在处理: {filename}")
        # 日志已由线程内部的_thread_log发出

    def on_processing_finished(self, filename, success):
        """处理线程完成单个文件处理时更新状态标签。"""
        status = "成功" if success else "失败"
        self.ui.status_label.setText(f"文件 {filename} 处理 {status}。")
        # 日志已由线程内部的_thread_log发出
        
    def on_thread_finished(self):
        """处理线程完全结束后，重新启用开始按钮，并更新最终状态。"""
        self.ui.start_processing_button.setEnabled(True)
        self.ui.status_label.setText("所有任务处理完成。")
        self.logger.log_gui_message("[INFO] 所有处理任务已完成。")

    def get_output_format_suffix(self, codec: str) -> str:
        """
        根据用户选择的编码器返回常见的输出文件后缀。
        """
        codec_map = {
            "aac": "m4a",
            "mp3": "mp3",
            "opus": "opus",
            "flac": "flac"
        }
        return codec_map.get(codec.lower(), "m4a") # 默认m4a


if __name__ == "__main__":
    # 创建 QApplication 实例
    app = QApplication(sys.argv)
    # 设置全局应用图标，按平台优先级选择，全部用resource_path
    import platform
    from PySide6.QtGui import QIcon
    icon_path_icns = resource_path("ico.icns")
    icon_path_ico = resource_path("ico.ico")
    icon_path_png = resource_path("ico.png")
    system = platform.system().lower()
    if system == "darwin" and os.path.exists(icon_path_icns):
        app.setWindowIcon(QIcon(icon_path_icns))
    elif system == "windows" and os.path.exists(icon_path_ico):
        app.setWindowIcon(QIcon(icon_path_ico))
    elif os.path.exists(icon_path_png):
        app.setWindowIcon(QIcon(icon_path_png))
    elif os.path.exists(icon_path_ico):
        app.setWindowIcon(QIcon(icon_path_ico))
    elif os.path.exists(icon_path_icns):
        app.setWindowIcon(QIcon(icon_path_icns))
    # 创建主窗口实例
    window = MainWindow()
    window.show()
    sys.exit(app.exec())