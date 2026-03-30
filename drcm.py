#!/usr/bin/env python3
"""
DRCM - Roblox Version Manager
Created by: Dev_Z / ipad_halobuck
"""

import sys
import os
import shutil
import zipfile
import threading
import time
import webbrowser
import subprocess
import json
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QTextEdit, QProgressBar, QMessageBox, QFileDialog,
    QSplitter, QFrame, QMenu, QAbstractItemView, QDialog, QDialogButtonBox,
    QSlider, QCheckBox, QSpinBox, QGroupBox, QScrollArea,
    QStyle, QStyleOptionSlider, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QAction, QColor, QPalette

# ============== PATH DETECTION ==============
USER_HOME = Path.home()
DOWNLOADS_DIR = USER_HOME / "Downloads"
LOCALAPPDATA = Path(os.environ.get('LOCALAPPDATA', USER_HOME / 'AppData' / 'Local'))
APPDATA = Path(os.environ.get('APPDATA', USER_HOME / 'AppData' / 'Roaming'))

# Supported Roblox clients
SUPPORTED_CLIENTS = {
    "Bloxstrap": LOCALAPPDATA / "Bloxstrap" / "Versions",
    "Fishstrap": LOCALAPPDATA / "Fishstrap" / "Versions",
    "RBXStrapp": LOCALAPPDATA / "RBXStrapp" / "Versions",
    "Official Roblox": LOCALAPPDATA / "Roblox" / "Versions",
}

class AnimatedDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.drag_pos = None
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
    def showEvent(self, event):
        self.opacity_effect.setOpacity(0)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(200)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        super().showEvent(event)
        
    def closeEvent(self, event):
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(150)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.animation.finished.connect(self.close)
        self.animation.start()
        event.ignore()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        self.drag_pos = None

class AnimatedMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
    def showEvent(self, event):
        self.opacity_effect.setOpacity(0)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        super().showEvent(event)

class ClientSelectionDialog(AnimatedDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Roblox Client")
        self.setFixedSize(400, 350)
        self.selected_client = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Select Your Roblox Client")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a6fa5;")
        layout.addWidget(title)
        
        subtitle = QLabel("DRCM can work with different Roblox clients")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #888888; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Client buttons
        for client_name in SUPPORTED_CLIENTS.keys():
            btn = QPushButton(client_name)
            btn.clicked.connect(lambda checked, c=client_name: self.select_client(c))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    border: 1px solid #5a5a5a;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 14px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                    border-color: #4a6fa5;
                }
            """)
            layout.addWidget(btn)
        
        # Custom path option
        custom_btn = QPushButton("Custom Path (Manual)")
        custom_btn.clicked.connect(self.custom_path)
        custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #5a5a5a;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #ffaa44;
            }
        """)
        layout.addWidget(custom_btn)
        
        layout.addStretch()
        
    def select_client(self, client):
        self.selected_client = client
        self.accept()
        
    def custom_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Roblox Versions Folder")
        if folder:
            self.selected_client = "Custom"
            SUPPORTED_CLIENTS["Custom"] = Path(folder)
            self.accept()

class ClickableSlider(QSlider):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setTracking(True)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            click_pos = event.globalPosition().toPoint()
            widget_pos = self.mapFromGlobal(click_pos)
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            groove_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
            handle_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
            
            if self.orientation() == Qt.Horizontal:
                slider_length = groove_rect.width() - handle_rect.width()
                slider_pos = widget_pos.x() - groove_rect.x() - handle_rect.width() / 2
                slider_pos = max(0, min(slider_pos, slider_length))
                if slider_length > 0:
                    value = self.minimum() + (slider_pos / slider_length) * (self.maximum() - self.minimum())
                    self.setValue(int(value))
        super().mousePressEvent(event)

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(35)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)
        
        self.title_label = QLabel("DRCM - Roblox Version Manager")
        self.title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        for text, color, slot in [("-", "#4a6fa5", self.parent.showMinimized),
                                   ("□", "#ffaa44", self.toggle_maximize),
                                   ("×", "#ff4444", self.parent.close)]:
            btn = QPushButton(text)
            btn.setFixedSize(32, 28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2d2d2d;
                    border: 1px solid #5a5a5a;
                    font-size: 14px;
                    font-weight: bold;
                    color: #ffffff;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                }}
            """)
            btn.clicked.connect(slot)
            layout.addWidget(btn)
            
    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

class DownloadThread(QThread):
    progress = Signal(str)
    status = Signal(str, str)
    download_complete = Signal(str, str)
    
    def __init__(self, download_url, channel, version_id):
        super().__init__()
        self.download_url = download_url
        self.channel = channel
        self.version_id = version_id
        self.downloads_path = DOWNLOADS_DIR
        
    def run(self):
        try:
            # Silent download - no browser window
            from requests import get
            response = get(self.download_url, stream=True, allow_redirects=True)
            response.raise_for_status()
            
            filename = f"{self.channel}_{self.version_id}.roblox"
            filepath = self.downloads_path / filename
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            self.progress.emit(f"Downloading: {percent:.1f}%")
            
            self.progress.emit("Download complete!")
            self.download_complete.emit(str(filepath), f"{self.channel}-{self.version_id}")
            
        except Exception as e:
            self.progress.emit(f"Error: {e}")
            self.status.emit("Download failed", "red")

class TextureApplyThread(QThread):
    progress = Signal(str)
    finished = Signal(int)
    
    def __init__(self, source_path, dest_path, clear_first=False):
        super().__init__()
        self.source_path = source_path
        self.dest_path = dest_path
        self.clear_first = clear_first
        
    def run(self):
        try:
            if self.clear_first and self.dest_path.exists():
                for item in self.dest_path.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                    except:
                        pass
                self.progress.emit("Cleared textures folder")
            
            self.dest_path.mkdir(parents=True, exist_ok=True)
            
            file_count = 0
            for item in self.source_path.iterdir():
                dest = self.dest_path / item.name
                try:
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                        file_count += sum(1 for _ in item.rglob('*') if _.is_file())
                    else:
                        shutil.copy2(item, dest)
                        file_count += 1
                except Exception as e:
                    self.progress.emit(f"Error: {e}")
            self.finished.emit(file_count)
        except Exception as e:
            self.progress.emit(f"Error: {e}")
            self.finished.emit(0)

class SettingsDialog(AnimatedDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("DRCM Settings")
        self.setMinimumSize(650, 550)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #5a5a5a;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        title_label = QLabel("Settings")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #5a5a5a;
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff4444;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_bar)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Client Selection
        client_group = QGroupBox("Roblox Client")
        client_layout = QVBoxLayout()
        
        self.client_combo = QComboBox()
        for client in SUPPORTED_CLIENTS.keys():
            self.client_combo.addItem(client)
        self.client_combo.currentTextChanged.connect(self.on_client_changed)
        client_layout.addWidget(self.client_combo)
        
        self.client_path_label = QLabel()
        self.client_path_label.setStyleSheet("color: #888888; font-family: monospace; font-size: 11px;")
        self.client_path_label.setWordWrap(True)
        client_layout.addWidget(self.client_path_label)
        
        client_group.setLayout(client_layout)
        scroll_layout.addWidget(client_group)
        
        # Theme Colors
        color_group = QGroupBox("Theme Colors")
        color_layout = QVBoxLayout()
        
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background:"))
        self.bg_color_btn = QPushButton("Choose Color")
        self.bg_color_btn.clicked.connect(lambda: self.choose_color("bg"))
        bg_layout.addWidget(self.bg_color_btn)
        self.bg_preview = QLabel()
        self.bg_preview.setFixedSize(50, 25)
        bg_layout.addWidget(self.bg_preview)
        bg_layout.addStretch()
        color_layout.addLayout(bg_layout)
        
        accent_layout = QHBoxLayout()
        accent_layout.addWidget(QLabel("Accent:"))
        self.accent_color_btn = QPushButton("Choose Color")
        self.accent_color_btn.clicked.connect(lambda: self.choose_color("accent"))
        accent_layout.addWidget(self.accent_color_btn)
        self.accent_preview = QLabel()
        self.accent_preview.setFixedSize(50, 25)
        accent_layout.addWidget(self.accent_preview)
        accent_layout.addStretch()
        color_layout.addLayout(accent_layout)
        
        color_group.setLayout(color_layout)
        scroll_layout.addWidget(color_group)
        
        # Credits
        credits_group = QGroupBox("About")
        credits_layout = QVBoxLayout()
        
        credits_label = QLabel("DRCM - Roblox Version Manager")
        credits_label.setAlignment(Qt.AlignCenter)
        credits_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4a6fa5;")
        credits_layout.addWidget(credits_label)
        
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #888888;")
        credits_layout.addWidget(version_label)
        
        credits_layout.addSpacing(5)
        
        dev_label = QLabel("Created by: Dev_Z / ipad_halobuck")
        dev_label.setAlignment(Qt.AlignCenter)
        dev_label.setStyleSheet("color: #e0e0e0; font-size: 11px;")
        credits_layout.addWidget(dev_label)
        
        credits_group.setLayout(credits_layout)
        scroll_layout.addWidget(credits_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        content_layout.addWidget(scroll)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        content_layout.addWidget(buttons)
        
        layout.addWidget(content)
        
    def on_client_changed(self, client_name):
        if client_name in SUPPORTED_CLIENTS:
            self.client_path_label.setText(f"Path: {SUPPORTED_CLIENTS[client_name]}")
        
    def choose_color(self, color_type):
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            if color_type == "bg":
                self.parent.bg_color = color.name()
                self.bg_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
            elif color_type == "accent":
                self.parent.accent_color = color.name()
                self.accent_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
            self.parent.apply_theme()
                
    def load_settings(self):
        settings = QSettings("DRCM", "Settings")
        self.bg_preview.setStyleSheet(f"background-color: {settings.value('bg_color', '#1a1a2e')}; border: 1px solid gray;")
        self.accent_preview.setStyleSheet(f"background-color: {settings.value('accent_color', '#4a6fa5')}; border: 1px solid gray;")
        
        client = settings.value("client", "Bloxstrap")
        idx = self.client_combo.findText(client)
        if idx >= 0:
            self.client_combo.setCurrentIndex(idx)
        
    def save_settings(self):
        settings = QSettings("DRCM", "Settings")
        settings.setValue("bg_color", self.parent.bg_color)
        settings.setValue("accent_color", self.parent.accent_color)
        settings.setValue("client", self.client_combo.currentText())
        
        self.parent.bloxstrap_path = SUPPORTED_CLIENTS.get(self.client_combo.currentText(), SUPPORTED_CLIENTS["Bloxstrap"])
        self.parent.apply_theme()
        self.accept()

class RobloxVersionManager(AnimatedMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DRCM - Roblox Version Manager")
        self.setMinimumSize(1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Paths
        self.drcm_dir = DOWNLOADS_DIR / "Drcm"
        self.versions_path = self.drcm_dir / "RbxV"
        self.dt_textures_path = self.drcm_dir / "dt" / "dt"
        self.nt_textures_path = self.drcm_dir / "nt" / "nt"
        self.custom_textures_path = self.drcm_dir / "ct"
        
        # Load client from settings
        settings = QSettings("DRCM", "Settings")
        client_name = settings.value("client", "")
        if client_name and client_name in SUPPORTED_CLIENTS:
            self.bloxstrap_path = SUPPORTED_CLIENTS[client_name]
        else:
            # First time - ask user
            dialog = ClientSelectionDialog(self)
            if dialog.exec() == QDialog.Accepted and dialog.selected_client:
                self.bloxstrap_path = SUPPORTED_CLIENTS.get(dialog.selected_client, SUPPORTED_CLIENTS["Bloxstrap"])
                settings.setValue("client", dialog.selected_client)
            else:
                self.bloxstrap_path = SUPPORTED_CLIENTS["Bloxstrap"]
        
        # Create folders
        for path in [self.versions_path, self.dt_textures_path, self.nt_textures_path, self.custom_textures_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Theme colors
        self.bg_color = settings.value("bg_color", "#1a1a2e")
        self.accent_color = settings.value("accent_color", "#4a6fa5")
        
        self.download_thread = None
        self.texture_thread = None
        self.tree_state = {}
        
        self.setup_ui()
        self.apply_theme()
        self.refresh_versions()
        self.refresh_current_version()
        
        self.setAcceptDrops(True)
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Menu bar
        menu_bar = QHBoxLayout()
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.open_settings)
        menu_bar.addWidget(settings_btn)
        menu_bar.addStretch()
        content_layout.addLayout(menu_bar)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # Download section
        download_frame = QFrame()
        download_frame.setObjectName("card")
        download_layout = QVBoxLayout(download_frame)
        
        download_title = QLabel("Download Roblox Version")
        download_title.setObjectName("card_title")
        download_layout.addWidget(download_title)
        
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Channel:"))
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["LIVE", "LIVE-Client", "LIVE-WindowsPlayer", "LIVE-Studio"])
        controls_layout.addWidget(self.channel_combo)
        
        controls_layout.addWidget(QLabel("Version:"))
        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("version-6776addb8fbc4d17")
        self.version_input.setText("version-6776addb8fbc4d17")
        controls_layout.addWidget(self.version_input)
        
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.download_version)
        controls_layout.addWidget(self.download_btn)
        controls_layout.addStretch()
        download_layout.addLayout(controls_layout)
        
        self.monitor_label = QLabel("")
        self.monitor_label.setObjectName("monitor_label")
        download_layout.addWidget(self.monitor_label)
        
        left_layout.addWidget(download_frame)
        
        # Versions tree
        versions_frame = QFrame()
        versions_frame.setObjectName("card")
        versions_layout = QVBoxLayout(versions_frame)
        
        versions_header = QHBoxLayout()
        versions_title = QLabel("Roblox Versions")
        versions_title.setObjectName("card_title")
        versions_header.addWidget(versions_title)
        versions_header.addStretch()
        
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setFixedSize(32, 28)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #5a5a5a;
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a6fa5;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_versions)
        versions_header.addWidget(self.refresh_btn)
        
        versions_layout.addLayout(versions_header)
        
        self.versions_tree = QTreeWidget()
        self.versions_tree.setHeaderLabels(["Name", "Type", "Size", "Modified"])
        self.versions_tree.setIndentation(20)
        self.versions_tree.setAlternatingRowColors(True)
        self.versions_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.versions_tree.customContextMenuRequested.connect(self.show_context_menu)
        versions_layout.addWidget(self.versions_tree)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.change_btn = QPushButton("Activate Version")
        self.change_btn.clicked.connect(self.change_version)
        action_layout.addWidget(self.change_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected)
        action_layout.addWidget(self.delete_btn)
        
        self.import_btn = QPushButton("Import Version (ZIP)")
        self.import_btn.clicked.connect(self.import_version)
        action_layout.addWidget(self.import_btn)
        
        action_layout.addStretch()
        versions_layout.addLayout(action_layout)
        
        left_layout.addWidget(versions_frame)
        main_splitter.addWidget(left_panel)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Active version
        active_frame = QFrame()
        active_frame.setObjectName("card")
        active_layout = QVBoxLayout(active_frame)
        
        active_title = QLabel("Active Version")
        active_title.setObjectName("card_title")
        active_layout.addWidget(active_title)
        
        self.current_version_display = QLabel("No version active")
        self.current_version_display.setObjectName("active_version")
        self.current_version_display.setAlignment(Qt.AlignCenter)
        active_layout.addWidget(self.current_version_display)
        
        right_layout.addWidget(active_frame)
        
        # Texture management
        texture_frame = QFrame()
        texture_frame.setObjectName("card")
        texture_layout = QVBoxLayout(texture_frame)
        
        texture_title = QLabel("Texture Management")
        texture_title.setObjectName("card_title")
        texture_layout.addWidget(texture_title)
        
        dark_btn = QPushButton("Apply Dark Textures")
        dark_btn.clicked.connect(self.apply_dark_textures)
        texture_layout.addWidget(dark_btn)
        
        normal_btn = QPushButton("Restore Normal Textures")
        normal_btn.clicked.connect(self.apply_normal_textures)
        texture_layout.addWidget(normal_btn)
        
        custom_btn = QPushButton("Apply Custom Textures (ZIP)")
        custom_btn.clicked.connect(self.apply_custom_textures)
        texture_layout.addWidget(custom_btn)
        
        import_custom_btn = QPushButton("Import Custom Texture ZIP")
        import_custom_btn.clicked.connect(self.import_custom_textures)
        texture_layout.addWidget(import_custom_btn)
        
        right_layout.addWidget(texture_frame)
        
        # File browser
        browser_frame = QFrame()
        browser_frame.setObjectName("card")
        browser_layout = QVBoxLayout(browser_frame)
        
        browser_title = QLabel("File Browser")
        browser_title.setObjectName("card_title")
        browser_layout.addWidget(browser_title)
        
        self.file_browser = QTreeWidget()
        self.file_browser.setHeaderLabels(["Name", "Size", "Modified"])
        self.file_browser.setIndentation(20)
        self.file_browser.itemDoubleClicked.connect(self.browse_file)
        browser_layout.addWidget(self.file_browser)
        
        right_layout.addWidget(browser_frame)
        
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([650, 550])
        content_layout.addWidget(main_splitter)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setObjectName("log_output")
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(100)
        content_layout.addWidget(self.log_output)
        
        main_layout.addWidget(content)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def extract_zip(self, zip_path, dest_folder):
        """Extract a zip file to destination folder"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(dest_folder)
            return True
        except Exception as e:
            self.log(f"Error extracting zip: {e}")
            return False
    
    def import_version(self):
        """Import a Roblox version from ZIP file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Roblox Version", 
                                                   str(DOWNLOADS_DIR), 
                                                   "Zip Files (*.zip)")
        if file_path:
            folder_name = Path(file_path).stem
            dest_folder = self.versions_path / folder_name
            
            self.log(f"Importing {Path(file_path).name}...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            if self.extract_zip(file_path, dest_folder):
                self.log(f"Successfully imported to: {dest_folder}")
                self.refresh_versions()
            else:
                self.log("Import failed!")
            
            self.progress_bar.setVisible(False)
    
    def import_custom_textures(self):
        """Import custom textures from ZIP file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Custom Textures",
                                                   str(DOWNLOADS_DIR),
                                                   "Zip Files (*.zip)")
        if file_path:
            folder_name = Path(file_path).stem
            dest_folder = self.custom_textures_path
            
            self.log(f"Importing textures from {Path(file_path).name}...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            if self.extract_zip(file_path, dest_folder):
                self.log(f"Successfully imported textures to: {dest_folder}")
            else:
                self.log("Import failed!")
            
            self.progress_bar.setVisible(False)
    
    def apply_custom_textures(self):
        """Apply custom textures from imported ZIP"""
        if not self.custom_textures_path.exists():
            self.log("No custom textures found. Import a ZIP first.")
            return
            
        current_version = self.get_current_version_path()
        if not current_version:
            self.log("No version active")
            return
            
        textures_path = current_version / "PlatformContent" / "pc" / "textures"
        
        self.log("Applying custom textures...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.texture_thread = TextureApplyThread(self.custom_textures_path, textures_path, clear_first=True)
        self.texture_thread.progress.connect(self.log)
        self.texture_thread.finished.connect(self.on_texture_finished)
        self.texture_thread.start()
    
    def download_version(self):
        """Download version silently in background"""
        version_id = self.version_input.text().strip()
        channel = self.channel_combo.currentText()
        
        if not version_id:
            self.log("Enter a version ID")
            return
            
        download_url = f"https://rdd.latte.to/?channel={channel}&binaryType=WindowsPlayer&version={version_id}"
        self.log(f"Downloading: {version_id}")
        
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.monitor_label.setText("Downloading...")
        
        self.download_thread = DownloadThread(download_url, channel, version_id)
        self.download_thread.progress.connect(self.log)
        self.download_thread.status.connect(self.monitor_label.setText)
        self.download_thread.download_complete.connect(self.on_download_complete)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_complete(self, filepath, folder_name):
        """Handle downloaded file"""
        source_path = Path(filepath)
        dest_folder = self.versions_path / folder_name
        
        self.log(f"Processing: {source_path.name}")
        self.monitor_label.setText("Extracting...")
        
        try:
            # Extract the file (it's a zip disguised as .roblox)
            dest_folder.mkdir(exist_ok=True)
            with zipfile.ZipFile(source_path, 'r') as zip_ref:
                zip_ref.extractall(dest_folder)
            source_path.unlink()
            
            self.log(f"Extracted to: {folder_name}")
            self.log("Download complete!")
            self.monitor_label.setText("Complete!")
            self.refresh_versions()
            
        except Exception as e:
            self.log(f"Error: {e}")
            self.monitor_label.setText("Error")
    
    def on_download_finished(self):
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        QTimer.singleShot(3000, lambda: self.monitor_label.setText(""))
    
    def change_version(self):
        """Activate selected version"""
        items = self.versions_tree.selectedItems()
        if not items:
            self.log("Select a version to activate")
            return
            
        item = items[0]
        while item.parent():
            item = item.parent()
            
        item_name = item.text(0)
        if item_name.startswith("["):
            item_name = item_name[1:-1]
            
        item_path = self.versions_path / item_name
        
        if not item_path.exists():
            self.log(f"Not found: {item_name}")
            return
            
        try:
            self.log(f"Activating: {item_name}")
            
            # Wipe current versions folder
            if self.bloxstrap_path.exists():
                for existing in self.bloxstrap_path.iterdir():
                    try:
                        if existing.is_dir():
                            shutil.rmtree(existing)
                        else:
                            existing.unlink()
                    except:
                        pass
            
            # Copy selected version
            if item_path.is_dir():
                dest_path = self.bloxstrap_path / item_name
                shutil.copytree(item_path, dest_path)
                self.log(f"Copied folder: {item_name}")
            else:
                # Extract if it's a file
                folder_name = item_path.stem
                dest_folder = self.bloxstrap_path / folder_name
                dest_folder.mkdir(exist_ok=True)
                
                if item_path.suffix.lower() in ['.zip', '.roblox']:
                    with zipfile.ZipFile(item_path, 'r') as zip_ref:
                        zip_ref.extractall(dest_folder)
                else:
                    shutil.copy2(item_path, dest_folder / item_path.name)
            
            self.log("Activation complete!")
            self.refresh_current_version()
            
        except Exception as e:
            self.log(f"Error: {e}")
    
    def apply_dark_textures(self):
        """Apply dark textures from dt folder"""
        current_version = self.get_current_version_path()
        if not current_version:
            self.log("No version active")
            return
            
        textures_path = current_version / "PlatformContent" / "pc" / "textures"
        
        if not self.dt_textures_path.exists():
            self.log("Dark textures not found")
            return
            
        self.log("Applying dark textures...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.texture_thread = TextureApplyThread(self.dt_textures_path, textures_path, clear_first=True)
        self.texture_thread.progress.connect(self.log)
        self.texture_thread.finished.connect(self.on_texture_finished)
        self.texture_thread.start()
    
    def apply_normal_textures(self):
        """Restore normal textures from nt folder"""
        current_version = self.get_current_version_path()
        if not current_version:
            self.log("No version active")
            return
            
        textures_path = current_version / "PlatformContent" / "pc" / "textures"
        
        if not textures_path.exists():
            self.log("Textures folder not found")
            return
            
        if not self.nt_textures_path.exists():
            self.log("Normal textures not found")
            return
            
        self.log("Restoring normal textures...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.texture_thread = TextureApplyThread(self.nt_textures_path, textures_path, clear_first=True)
        self.texture_thread.progress.connect(self.log)
        self.texture_thread.finished.connect(self.on_texture_finished)
        self.texture_thread.start()
    
    def on_texture_finished(self, count):
        self.progress_bar.setVisible(False)
        self.log(f"Complete! Processed {count} items")
    
    def refresh_versions(self):
        """Refresh the versions tree"""
        self.versions_tree.clear()
        
        def add_items(path, parent=None):
            try:
                for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    if item.is_dir():
                        display_name = f"[{item.name}]"
                        tree_item = QTreeWidgetItem(parent or self.versions_tree, [display_name, "Folder", "", ""])
                        add_items(item, tree_item)
                    else:
                        size_mb = item.stat().st_size / (1024 * 1024)
                        modified = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                        file_type = item.suffix[1:].upper() if item.suffix else "File"
                        tree_item = QTreeWidgetItem(parent or self.versions_tree, 
                                                    [item.name, file_type, f"{size_mb:.2f} MB", modified])
                    if parent:
                        parent.addChild(tree_item)
                    else:
                        self.versions_tree.addTopLevelItem(tree_item)
            except Exception:
                pass
        
        add_items(self.versions_path)
        self.versions_tree.resizeColumnToContents(0)
        self.log(f"Found {self.versions_tree.topLevelItemCount()} items")
    
    def refresh_current_version(self):
        """Update the active version display"""
        try:
            if self.bloxstrap_path.exists():
                for item in self.bloxstrap_path.iterdir():
                    if item.is_dir():
                        self.current_version_display.setText(item.name)
                        self.load_file_browser(self.bloxstrap_path / item.name)
                        return
            self.current_version_display.setText("No version active")
            self.load_file_browser()
        except Exception as e:
            self.log(f"Error: {e}")
    
    def get_current_version_path(self):
        """Get the path of the currently active version"""
        if self.bloxstrap_path.exists():
            for item in self.bloxstrap_path.iterdir():
                if item.is_dir():
                    return item
        return None
    
    def load_file_browser(self, path=None):
        """Load file browser for a given path"""
        self.file_browser.clear()
        if path is None:
            path = self.bloxstrap_path if self.bloxstrap_path.exists() else USER_HOME
        
        try:
            current_path = QTreeWidgetItem(self.file_browser, ["..", "", ""])
            current_path.setData(0, Qt.UserRole, str(path.parent))
            
            for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.is_dir():
                    tree_item = QTreeWidgetItem(self.file_browser, [f"[{item.name}]", "", ""])
                else:
                    size_mb = item.stat().st_size / (1024 * 1024)
                    modified = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    tree_item = QTreeWidgetItem(self.file_browser, [item.name, f"{size_mb:.2f} MB", modified])
                tree_item.setData(0, Qt.UserRole, str(item))
            
            self.file_browser.resizeColumnToContents(0)
        except Exception as e:
            self.log(f"Error loading file browser: {e}")
    
    def browse_file(self, item, column):
        """Open file or folder in explorer"""
        file_path = item.data(0, Qt.UserRole)
        if file_path and Path(file_path).exists():
            try:
                if Path(file_path).is_dir():
                    os.startfile(str(file_path))
                else:
                    os.startfile(str(file_path))
            except Exception as e:
                self.log(f"Error opening: {e}")
    
    def show_context_menu(self, position):
        """Show right-click context menu"""
        item = self.versions_tree.itemAt(position)
        if item:
            menu = QMenu()
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_selected)
            menu.addAction(delete_action)
            
            open_action = QAction("Open in Explorer", self)
            open_action.triggered.connect(self.open_selected_folder)
            menu.addAction(open_action)
            
            menu.exec(self.versions_tree.viewport().mapToGlobal(position))
    
    def delete_selected(self):
        """Delete selected items"""
        items = self.versions_tree.selectedItems()
        if not items:
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Delete {len(items)} item(s)?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for item in items:
                item_name = item.text(0)
                if item_name.startswith("[") and item_name.endswith("]"):
                    item_name = item_name[1:-1]
                item_path = self.versions_path / item_name
                try:
                    if item_path.is_dir():
                        shutil.rmtree(item_path)
                    else:
                        item_path.unlink()
                    self.log(f"Deleted: {item_name}")
                except Exception as e:
                    self.log(f"Error: {e}")
            self.refresh_versions()
    
    def open_selected_folder(self):
        """Open selected folder in Windows Explorer"""
        items = self.versions_tree.selectedItems()
        if items:
            item_name = items[0].text(0)
            if item_name.startswith("[") and item_name.endswith("]"):
                item_name = item_name[1:-1]
            item_path = self.versions_path / item_name
            if item_path.exists():
                try:
                    os.startfile(str(item_path))
                except Exception as e:
                    self.log(f"Error opening folder: {e}")
                    QMessageBox.warning(self, "Error", f"Could not open folder: {e}")
    
    def log(self, message):
        """Add message to log output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
        self.status_label.setText(message)
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.apply_theme()
            self.refresh_current_version()
    
    def apply_theme(self):
        """Apply current theme colors"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.bg_color};
            }}
            
            QLabel, QTreeWidget, QTextEdit, QLineEdit, QComboBox {{
                color: #e0e0e0;
            }}
            
            QPushButton {{
                background-color: {self.accent_color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {self.lighten_color(self.accent_color, 1.2)};
            }}
            
            QPushButton:pressed {{
                background-color: {self.darken_color(self.accent_color, 0.8)};
            }}
            
            #card {{
                background-color: {self.lighten_color(self.bg_color, 1.1)};
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }}
            
            #card_title {{
                font-size: 14px;
                font-weight: bold;
                color: {self.accent_color};
                padding-bottom: 8px;
                border-bottom: 1px solid {self.lighten_color(self.bg_color, 1.2)};
                margin-bottom: 10px;
            }}
            
            #active_version {{
                font-size: 12px;
                font-weight: bold;
                color: {self.accent_color};
                padding: 8px;
                background-color: {self.lighten_color(self.bg_color, 1.2)};
                border-radius: 4px;
                border: 1px solid {self.accent_color};
            }}
            
            #log_output {{
                background-color: {self.darken_color(self.bg_color, 0.8)};
                font-family: monospace;
                font-size: 11px;
            }}
            
            QTreeWidget {{
                background-color: {self.lighten_color(self.bg_color, 1.1)};
                alternate-background-color: {self.lighten_color(self.bg_color, 1.05)};
                border: none;
            }}
            
            QTreeWidget::item:selected {{
                background-color: {self.accent_color};
            }}
            
            QHeaderView::section {{
                background-color: {self.lighten_color(self.bg_color, 1.2)};
                color: #e0e0e0;
                padding: 4px;
                border: none;
            }}
            
            QComboBox, QLineEdit {{
                background-color: {self.lighten_color(self.bg_color, 1.1)};
                border: 1px solid {self.accent_color};
                border-radius: 4px;
                padding: 6px;
            }}
        """)
    
    def lighten_color(self, color, factor):
        """Lighten a color by factor"""
        qcolor = QColor(color)
        return qcolor.lighter(int(100 * factor)).name()
    
    def darken_color(self, color, factor):
        """Darken a color by factor"""
        qcolor = QColor(color)
        return qcolor.darker(int(100 / factor)).name()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("DRCM")
    
    window = RobloxVersionManager()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
