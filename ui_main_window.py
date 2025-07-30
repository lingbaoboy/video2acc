# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt Designer
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QRadioButton, QSizePolicy,
    QSlider, QSpacerItem, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(720, 800)
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"多功能音频处理工具", None)) # 设置窗口标题

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_main = QVBoxLayout(self.centralwidget)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")

        # --- 1. 文件选择区 ---
        self.file_selection_groupbox = QGroupBox(self.centralwidget)
        self.file_selection_groupbox.setObjectName(u"file_selection_groupbox")
        self.file_selection_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"文件选择", None))
        self.verticalLayout_file_selection = QVBoxLayout(self.file_selection_groupbox)
        self.verticalLayout_file_selection.setObjectName(u"verticalLayout_file_selection")

        self.select_files_button = QPushButton(self.file_selection_groupbox)
        self.select_files_button.setObjectName(u"select_files_button")
        self.select_files_button.setText(QCoreApplication.translate("MainWindow", u"选择媒体文件...", None))
        self.verticalLayout_file_selection.addWidget(self.select_files_button)

        self.file_list_widget = QListWidget(self.file_selection_groupbox)
        self.file_list_widget.setObjectName(u"file_list_widget")
        self.file_list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection) # 不允许在列表中选择，只用于显示
        self.verticalLayout_file_selection.addWidget(self.file_list_widget)

        self.verticalLayout_main.addWidget(self.file_selection_groupbox)

        # --- 2. 处理选项区 ---
        self.processing_mode_groupbox = QGroupBox(self.centralwidget)
        self.processing_mode_groupbox.setObjectName(u"processing_mode_groupbox")
        self.processing_mode_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"处理模式", None))
        self.horizontalLayout_mode = QHBoxLayout(self.processing_mode_groupbox)
        self.horizontalLayout_mode.setObjectName(u"horizontalLayout_mode")

        self.direct_extract_radio = QRadioButton(self.processing_mode_groupbox)
        self.direct_extract_radio.setObjectName(u"direct_extract_radio")
        self.direct_extract_radio.setText(QCoreApplication.translate("MainWindow", u"直接提取音频 (不转码)", None))
        self.direct_extract_radio.setChecked(True) # 默认选中
        self.horizontalLayout_mode.addWidget(self.direct_extract_radio)

        self.recode_radio = QRadioButton(self.processing_mode_groupbox)
        self.recode_radio.setObjectName(u"recode_radio")
        self.recode_radio.setText(QCoreApplication.translate("MainWindow", u"重新编码音频 (强制转码)", None))
        self.horizontalLayout_mode.addWidget(self.recode_radio)

        self.horizontalSpacer_mode = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayout_mode.addItem(self.horizontalSpacer_mode)

        self.verticalLayout_main.addWidget(self.processing_mode_groupbox)

        # --- 3. 编码参数设置区 ---
        self.encoding_params_group_box = QGroupBox(self.centralwidget)
        self.encoding_params_group_box.setObjectName(u"encoding_params_group_box")
        self.encoding_params_group_box.setTitle(QCoreApplication.translate("MainWindow", u"编码参数设置", None))
        self.formLayout_encoding_params = QVBoxLayout(self.encoding_params_group_box)
        self.formLayout_encoding_params.setObjectName(u"formLayout_encoding_params")

        # 编码格式
        self.horizontalLayout_codec = QHBoxLayout()
        self.horizontalLayout_codec.setObjectName(u"horizontalLayout_codec")
        self.codec_label = QLabel(self.encoding_params_group_box)
        self.codec_label.setObjectName(u"codec_label")
        self.codec_label.setText(QCoreApplication.translate("MainWindow", u"编码格式:", None))
        self.horizontalLayout_codec.addWidget(self.codec_label)
        self.codec_combo_box = QComboBox(self.encoding_params_group_box)
        self.codec_combo_box.setObjectName(u"codec_combo_box")
        self.horizontalLayout_codec.addWidget(self.codec_combo_box)
        self.horizontalSpacer_codec = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.horizontalLayout_codec.addItem(self.horizontalSpacer_codec)
        self.formLayout_encoding_params.addLayout(self.horizontalLayout_codec)

        # 比特率
        self.horizontalLayout_bitrate = QHBoxLayout()
        self.horizontalLayout_bitrate.setObjectName(u"horizontalLayout_bitrate")
        self.bitrate_label = QLabel(self.encoding_params_group_box)
        self.bitrate_label.setObjectName(u"bitrate_label")
        self.bitrate_label.setText(QCoreApplication.translate("MainWindow", u"比特率 (k):", None))
        self.horizontalLayout_bitrate.addWidget(self.bitrate_label)
        self.bitrate_line_edit = QLineEdit(self.encoding_params_group_box)
        self.bitrate_line_edit.setObjectName(u"bitrate_line_edit")
        self.bitrate_line_edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"例如: 128 (k)", None))
        self.horizontalLayout_bitrate.addWidget(self.bitrate_line_edit)
        self.horizontalSpacer_bitrate = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayout_bitrate.addItem(self.horizontalSpacer_bitrate)
        self.formLayout_encoding_params.addLayout(self.horizontalLayout_bitrate)

        # 质量参数 (CRF/VBR/压缩级别)
        self.horizontalLayout_quality = QHBoxLayout()
        self.horizontalLayout_quality.setObjectName(u"horizontalLayout_quality")
        self.quality_label = QLabel(self.encoding_params_group_box)
        self.quality_label.setObjectName(u"quality_label")
        self.quality_label.setText(QCoreApplication.translate("MainWindow", u"质量:", None))
        self.horizontalLayout_quality.addWidget(self.quality_label)
        self.quality_line_edit = QLineEdit(self.encoding_params_group_box)
        self.quality_line_edit.setObjectName(u"quality_line_edit")
        self.quality_line_edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"例如: 20 (AAC VBR)", None))
        self.horizontalLayout_quality.addWidget(self.quality_line_edit)
        self.horizontalSpacer_quality = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayout_quality.addItem(self.horizontalSpacer_quality)
        self.formLayout_encoding_params.addLayout(self.horizontalLayout_quality)
        
        # 采样率
        self.horizontalLayout_samplerate = QHBoxLayout()
        self.horizontalLayout_samplerate.setObjectName(u"horizontalLayout_samplerate")
        self.samplerate_label = QLabel(self.encoding_params_group_box)
        self.samplerate_label.setObjectName(u"samplerate_label")
        self.samplerate_label.setText(QCoreApplication.translate("MainWindow", u"采样率 (kHz):", None))
        self.horizontalLayout_samplerate.addWidget(self.samplerate_label)
        self.samplerate_line_edit = QLineEdit(self.encoding_params_group_box)
        self.samplerate_line_edit.setObjectName(u"samplerate_line_edit")
        self.samplerate_line_edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"例如: 48000", None))
        self.horizontalLayout_samplerate.addWidget(self.samplerate_line_edit)
        self.horizontalSpacer_samplerate = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayout_samplerate.addItem(self.horizontalSpacer_samplerate)
        self.formLayout_encoding_params.addLayout(self.horizontalLayout_samplerate)

        # 声道数
        self.horizontalLayout_channels = QHBoxLayout()
        self.horizontalLayout_channels.setObjectName(u"horizontalLayout_channels")
        self.channels_label = QLabel(self.encoding_params_group_box)
        self.channels_label.setObjectName(u"channels_label")
        self.channels_label.setText(QCoreApplication.translate("MainWindow", u"声道数:", None))
        self.horizontalLayout_channels.addWidget(self.channels_label)
        self.channels_line_edit = QLineEdit(self.encoding_params_group_box)
        self.channels_line_edit.setObjectName(u"channels_line_edit")
        self.channels_line_edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"例如: 2 (立体声)", None))
        self.horizontalLayout_channels.addWidget(self.channels_line_edit)
        self.horizontalSpacer_channels = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayout_channels.addItem(self.horizontalSpacer_channels)
        self.formLayout_encoding_params.addLayout(self.horizontalLayout_channels)
        
        self.verticalLayout_main.addWidget(self.encoding_params_group_box)

        # --- 4. 操作按钮区 ---
        self.start_processing_button = QPushButton(self.centralwidget)
        self.start_processing_button.setObjectName(u"start_processing_button")
        self.start_processing_button.setText(QCoreApplication.translate("MainWindow", u"开始处理", None))
        self.verticalLayout_main.addWidget(self.start_processing_button)

        # --- 5. 状态/日志显示区 ---
        self.status_label = QLabel(self.centralwidget)
        self.status_label.setObjectName(u"status_label")
        self.status_label.setText(QCoreApplication.translate("MainWindow", u"状态: 等待选择文件...", None))
        self.verticalLayout_main.addWidget(self.status_label)

        self.log_display_text_edit = QTextEdit(self.centralwidget)
        self.log_display_text_edit.setObjectName(u"log_display_text_edit")
        self.log_display_text_edit.setReadOnly(True) # 日志显示框只读
        self.verticalLayout_main.addWidget(self.log_display_text_edit)

        MainWindow.setCentralWidget(self.centralwidget)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi