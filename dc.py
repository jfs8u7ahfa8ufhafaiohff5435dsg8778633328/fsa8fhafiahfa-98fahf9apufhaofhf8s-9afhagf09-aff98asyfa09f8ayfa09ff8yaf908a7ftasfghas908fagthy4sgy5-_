import sys
import os
import shutil
import zipfile
import threading
import time
import webbrowser
import subprocess
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QTextEdit, QProgressBar, QMessageBox, QFileDialog,
    QSplitter, QFrame, QMenu, QAbstractItemView, QDialog, QDialogButtonBox,
    QSlider, QCheckBox, QSpinBox, QGroupBox, QScrollArea,
    QSizePolicy, QInputDialog, QStyle, QStyleOptionSlider
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize, QSettings, QPoint
from PySide6.QtGui import QFont, QAction, QColor

# ==================== LICENSING SYSTEM ====================
USER_HOME = Path.home()
LICENSE_FILE = USER_HOME / "AppData" / "Local" / "DRCM" / "license.json"

def get_hardware_id():
    """Generate a unique hardware ID"""
    try:
        # Get system drive serial number
        result = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.strip() and 'serialnumber' not in line.lower():
                drive_serial = line.strip()
                break
        else:
            drive_serial = "UNKNOWN"
        
        # Get motherboard serial
        result = subprocess.run(['wmic', 'baseboard', 'get', 'serialnumber'], 
                                capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.strip() and 'serialnumber' not in line.lower():
                mb_serial = line.strip()
                break
        else:
            mb_serial = "UNKNOWN"
        
        # Get CPU ID
        result = subprocess.run(['wmic', 'cpu', 'get', 'processorid'], 
                                capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.strip() and 'processorid' not in line.lower():
                cpu_id = line.strip()
                break
        else:
            cpu_id = "UNKNOWN"
        
        # Combine and hash
        hwid_string = f"{drive_serial}_{mb_serial}_{cpu_id}"
        return hashlib.sha256(hwid_string.encode()).hexdigest()
    except:
        # Fallback to a more basic approach
        import uuid
        return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()

class KeyValidationThread(QThread):
    """Thread for validating license keys"""
    finished = Signal(bool, str)
    
    def __init__(self, key):
        super().__init__()
        self.key = key.strip()
        self.keys_url = "https://raw.githubusercontent.com/jfs8u7ahfa8ufhafaiohff5435dsg8778633328/fsa8fhafiahfa-98fahf9apufhaofhf8s-9afhagf09-aff98asyfa09f8ayfa09ff8yaf908a7ftasfghas908fagthy4sgy5-_/refs/heads/main/keys.txt"
    
    def run(self):
        try:
            # Fetch valid keys from GitHub
            response = requests.get(self.keys_url, timeout=10)
            if response.status_code != 200:
                self.finished.emit(False, "Could not fetch license keys")
                return
            
            valid_keys = set(response.text.strip().split('\n'))
            valid_keys = {k.strip() for k in valid_keys if k.strip()}
            
            if self.key not in valid_keys:
                self.finished.emit(False, "Invalid license key")
                return
            
            # Check if key already used
            if LICENSE_FILE.exists():
                with open(LICENSE_FILE, 'r') as f:
                    license_data = json.load(f)
                    if license_data.get('used_keys', []):
                        if self.key in license_data['used_keys']:
                            self.finished.emit(False, "License key already used")
                            return
            
            # Get hardware ID
            hwid = get_hardware_id()
            
            # Save license (key and HWID)
            LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
            license_data = {
                'key': self.key,
                'hwid': hwid,
                'activated_at': datetime.now().isoformat(),
                'used_keys': [self.key]
            }
            
            # Also track used keys
            if LICENSE_FILE.exists():
                with open(LICENSE_FILE, 'r') as f:
                    existing = json.load(f)
                    if 'used_keys' in existing:
                        existing['used_keys'].append(self.key)
                        license_data['used_keys'] = existing['used_keys']
            
            with open(LICENSE_FILE, 'w') as f:
                json.dump(license_data, f, indent=2)
            
            self.finished.emit(True, "License activated successfully")
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

class LicenseDialog(QDialog):
    """License activation dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DRCM - License Activation")
        self.setFixedSize(500, 300)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setup_ui()
        self.validation_thread = None
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #5a5a5a;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        title_label = QLabel("DRCM - License Activation")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        close_btn = QPushButton("X")
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
        
        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        icon_label = QLabel("🔑")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        content_layout.addWidget(icon_label)
        
        title = QLabel("Enter License Key")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4a6fa5;")
        content_layout.addWidget(title)
        
        desc = QLabel("This application requires a valid license key to run.\nPlease enter your key below.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #aaaaaa;")
        content_layout.addWidget(desc)
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.key_input.setStyleSheet("padding: 10px; font-size: 14px;")
        content_layout.addWidget(self.key_input)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.status_label)
        
        button_layout = QHBoxLayout()
        self.activate_btn = QPushButton("Activate")
        self.activate_btn.clicked.connect(self.activate)
        self.activate_btn.setStyleSheet("padding: 8px 20px; font-size: 14px;")
        button_layout.addWidget(self.activate_btn)
        button_layout.addStretch()
        
        content_layout.addLayout(button_layout)
        layout.addWidget(content)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            
    def activate(self):
        key = self.key_input.text().strip()
        if not key:
            self.status_label.setText("Please enter a license key")
            self.status_label.setStyleSheet("color: #ff8888;")
            return
        
        self.activate_btn.setEnabled(False)
        self.activate_btn.setText("Validating...")
        self.status_label.setText("Checking license...")
        self.status_label.setStyleSheet("color: #88ff88;")
        
        self.validation_thread = KeyValidationThread(key)
        self.validation_thread.finished.connect(self.on_validation_complete)
        self.validation_thread.start()
        
    def on_validation_complete(self, success, message):
        self.activate_btn.setEnabled(True)
        self.activate_btn.setText("Activate")
        
        if success:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #88ff88;")
            QTimer.singleShot(1000, self.accept)
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #ff8888;")

def check_license():
    """Check if license is valid and not expired"""
    if not LICENSE_FILE.exists():
        return False
    
    try:
        with open(LICENSE_FILE, 'r') as f:
            data = json.load(f)
        
        # Check HWID match
        current_hwid = get_hardware_id()
        if data.get('hwid') != current_hwid:
            return False
        
        return True
    except:
        return False

# ==================== SOUND MANAGER ====================
class SoundManager:
    def __init__(self):
        self.click_sound = None
        self.download_sound = None
        self.complete_sound = None
        self.error_sound = None
        self.volume = 0.5
        self.enabled = True
        
    def init_sounds(self):
        try:
            from PySide6.QtMultimedia import QSoundEffect
            self.click_sound = QSoundEffect()
            self.download_sound = QSoundEffect()
            self.complete_sound = QSoundEffect()
            self.error_sound = QSoundEffect()
            self.set_volume(self.volume)
        except:
            self.enabled = False
        
    def set_volume(self, volume):
        self.volume = volume / 100.0
        if self.click_sound:
            self.click_sound.setVolume(self.volume)
        if self.download_sound:
            self.download_sound.setVolume(self.volume)
        if self.complete_sound:
            self.complete_sound.setVolume(self.volume)
        if self.error_sound:
            self.error_sound.setVolume(self.volume)
        
    def play_click(self):
        if self.enabled and self.click_sound:
            self.click_sound.play()
        
    def play_download(self):
        if self.enabled and self.download_sound:
            self.download_sound.play()
        
    def play_complete(self):
        if self.enabled and self.complete_sound:
            self.complete_sound.play()
        
    def play_error(self):
        if self.enabled and self.error_sound:
            self.error_sound.play()

# ==================== UTILITY CLASSES ====================
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
                if slider_pos < 0:
                    slider_pos = 0
                elif slider_pos > slider_length:
                    slider_pos = slider_length
                if slider_length > 0:
                    value = self.minimum() + (slider_pos / slider_length) * (self.maximum() - self.minimum())
                else:
                    value = self.minimum()
            else:
                slider_length = groove_rect.height() - handle_rect.height()
                slider_pos = widget_pos.y() - groove_rect.y() - handle_rect.height() / 2
                if slider_pos < 0:
                    slider_pos = 0
                elif slider_pos > slider_length:
                    slider_pos = slider_length
                if slider_length > 0:
                    value = self.minimum() + (slider_pos / slider_length) * (self.maximum() - self.minimum())
                else:
                    value = self.minimum()
            
            self.setValue(int(value))
        super().mousePressEvent(event)

class DraggableDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.drag_pos = None
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        self.drag_pos = None

class IntegratedColorPicker(DraggableDialog):
    def __init__(self, parent=None, initial_color="#4a6fa5"):
        super().__init__(parent)
        self.setWindowTitle("Choose Color")
        self.setFixedSize(450, 400)
        self.selected_color = QColor(initial_color)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #5a5a5a;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        title_label = QLabel("Choose Color")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        close_btn = QPushButton("X")
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
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.preview = QLabel()
        self.preview.setFixedSize(100, 100)
        self.preview.setStyleSheet(f"background-color: {self.selected_color.name()}; border: 2px solid gray; border-radius: 5px;")
        self.preview.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.preview, alignment=Qt.AlignCenter)
        
        rgb_layout = QVBoxLayout()
        
        red_layout = QHBoxLayout()
        red_layout.addWidget(QLabel("R:"))
        self.red_slider = ClickableSlider(Qt.Horizontal)
        self.red_slider.setRange(0, 255)
        self.red_slider.setValue(self.selected_color.red())
        self.red_slider.valueChanged.connect(self.update_from_sliders)
        red_layout.addWidget(self.red_slider)
        self.red_spin = QSpinBox()
        self.red_spin.setRange(0, 255)
        self.red_spin.setValue(self.selected_color.red())
        self.red_spin.valueChanged.connect(self.red_slider.setValue)
        red_layout.addWidget(self.red_spin)
        rgb_layout.addLayout(red_layout)
        
        green_layout = QHBoxLayout()
        green_layout.addWidget(QLabel("G:"))
        self.green_slider = ClickableSlider(Qt.Horizontal)
        self.green_slider.setRange(0, 255)
        self.green_slider.setValue(self.selected_color.green())
        self.green_slider.valueChanged.connect(self.update_from_sliders)
        green_layout.addWidget(self.green_slider)
        self.green_spin = QSpinBox()
        self.green_spin.setRange(0, 255)
        self.green_spin.setValue(self.selected_color.green())
        self.green_spin.valueChanged.connect(self.green_slider.setValue)
        green_layout.addWidget(self.green_spin)
        rgb_layout.addLayout(green_layout)
        
        blue_layout = QHBoxLayout()
        blue_layout.addWidget(QLabel("B:"))
        self.blue_slider = ClickableSlider(Qt.Horizontal)
        self.blue_slider.setRange(0, 255)
        self.blue_slider.setValue(self.selected_color.blue())
        self.blue_slider.valueChanged.connect(self.update_from_sliders)
        blue_layout.addWidget(self.blue_slider)
        self.blue_spin = QSpinBox()
        self.blue_spin.setRange(0, 255)
        self.blue_spin.setValue(self.selected_color.blue())
        self.blue_spin.valueChanged.connect(self.blue_slider.setValue)
        blue_layout.addWidget(self.blue_spin)
        rgb_layout.addLayout(blue_layout)
        
        content_layout.addLayout(rgb_layout)
        
        hex_layout = QHBoxLayout()
        hex_layout.addWidget(QLabel("Hex:"))
        self.hex_input = QLineEdit()
        self.hex_input.setText(self.selected_color.name())
        self.hex_input.textChanged.connect(self.update_from_hex)
        hex_layout.addWidget(self.hex_input)
        content_layout.addLayout(hex_layout)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        content_layout.addLayout(button_layout)
        
        layout.addWidget(content)
        
    def update_from_sliders(self):
        r = self.red_slider.value()
        g = self.green_slider.value()
        b = self.blue_slider.value()
        self.selected_color = QColor(r, g, b)
        self.preview.setStyleSheet(f"background-color: {self.selected_color.name()}; border: 2px solid gray; border-radius: 5px;")
        self.hex_input.setText(self.selected_color.name())
        self.red_spin.setValue(r)
        self.green_spin.setValue(g)
        self.blue_spin.setValue(b)
        
    def update_from_hex(self):
        hex_text = self.hex_input.text()
        if hex_text.startswith("#") and len(hex_text) == 7:
            color = QColor(hex_text)
            if color.isValid():
                self.selected_color = color
                self.red_slider.blockSignals(True)
                self.green_slider.blockSignals(True)
                self.blue_slider.blockSignals(True)
                self.red_slider.setValue(color.red())
                self.green_slider.setValue(color.green())
                self.blue_slider.setValue(color.blue())
                self.red_spin.setValue(color.red())
                self.green_spin.setValue(color.green())
                self.blue_spin.setValue(color.blue())
                self.red_slider.blockSignals(False)
                self.green_slider.blockSignals(False)
                self.blue_slider.blockSignals(False)
                self.preview.setStyleSheet(f"background-color: {self.selected_color.name()}; border: 2px solid gray; border-radius: 5px;")
                
    def get_color(self):
        return self.selected_color.name()

# ==================== THREADS ====================
class DownloadThread(QThread):
    progress = Signal(str)
    status = Signal(str, str)
    download_complete = Signal(str, str)
    browser_closed = Signal()
    
    def __init__(self, download_url, channel, version_id):
        super().__init__()
        self.download_url = download_url
        self.channel = channel
        self.version_id = version_id
        self.browser_process = None
        self.downloads_path = Path.home() / "Downloads"
        self.stop_monitoring = False
        
    def run(self):
        chrome_paths = [
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe")
        ]
        
        for chrome_path in chrome_paths:
            if Path(chrome_path).exists():
                try:
                    self.browser_process = subprocess.Popen([chrome_path, self.download_url])
                    self.progress.emit("Opened in Chrome browser")
                    break
                except:
                    pass
        
        if not self.browser_process:
            webbrowser.open(self.download_url)
            self.progress.emit("Opened in default browser")
        
        self.monitor_downloads()
        
    def monitor_downloads(self):
        initial_files = set()
        if self.downloads_path.exists():
            for item in self.downloads_path.iterdir():
                if item.is_file():
                    initial_files.add(item.name)
        
        timeout = 300
        start_time = time.time()
        downloaded_file = None
        file_stable = False
        
        while time.time() - start_time < timeout:
            if self.stop_monitoring:
                return
            
            if self.browser_process and self.browser_process.poll() is not None:
                self.progress.emit("Browser closed before download completed")
                self.status.emit("Download cancelled", "orange")
                return
            
            if self.downloads_path.exists():
                current_files = set()
                for item in self.downloads_path.iterdir():
                    if item.is_file():
                        current_files.add(item.name)
                
                new_files = current_files - initial_files
                
                for new_file in new_files:
                    self.progress.emit(f"Detected new file: {new_file}")
                    source_path = self.downloads_path / new_file
                    last_size = -1
                    stable_count = 0
                    
                    while stable_count < 3:
                        if source_path.exists():
                            current_size = source_path.stat().st_size
                            if current_size == last_size:
                                stable_count += 1
                            else:
                                stable_count = 0
                                last_size = current_size
                            time.sleep(1)
                        else:
                            break
                        
                        if self.browser_process and self.browser_process.poll() is not None:
                            self.progress.emit("Browser closed during download")
                            return
                    
                    if stable_count >= 3:
                        file_stable = True
                        downloaded_file = new_file
                        break
                
                if file_stable and downloaded_file:
                    break
            
            time.sleep(1)
        
        if file_stable and downloaded_file:
            self.progress.emit("Download complete!")
            
            if self.browser_process:
                try:
                    self.browser_process.terminate()
                    self.progress.emit("Closed Chrome browser")
                    self.browser_closed.emit()
                except:
                    pass
            
            source_path = self.downloads_path / downloaded_file
            self.download_complete.emit(str(source_path), f"{self.channel}-{self.version_id}")
        else:
            self.progress.emit("Download timed out")
            self.status.emit("Download timed out", "red")

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

# ==================== MAIN WINDOW ====================
class RobloxVersionManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DRCM - Roblox Version Manager")
        self.setMinimumSize(1300, 850)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Dynamic paths
        self.base_dir = Path.home() / "Downloads" / "Drcm"
        self.versions_path = self.base_dir / "RbxV"
        self.bloxstrap_path = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / "Bloxstrap" / "Versions"
        self.dt_textures_path = self.base_dir / "dt" / "dt"
        self.nt_textures_path = self.base_dir / "nt" / "nt"
        self.custom_textures_path = self.base_dir / "ct"
        
        # Create folders
        for path in [self.versions_path, self.dt_textures_path, 
                     self.nt_textures_path, self.custom_textures_path,
                     self.base_dir / "Settings", self.base_dir / "Sounds"]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.bg_color = "#1a1a2e"
        self.accent_color = "#4a6fa5"
        self.text_color = "#e0e0e0"
        self.window_transparency = 1.0
        
        self.sound_manager = SoundManager()
        self.sound_manager.init_sounds()
        
        self.download_thread = None
        self.texture_thread = None
        self.tree_state = {}
        self.last_expand_time = 0
        self.last_refresh_time = 0
        self.refresh_in_progress = False
        
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.auto_refresh_versions)
        
        self.setup_ui()
        self.load_settings()
        self.apply_theme()
        self.refresh_versions()
        self.refresh_current_version()
        
        if QSettings("DRCM", "Settings").value("auto_refresh", True, type=bool):
            self.auto_refresh_timer.start(5000)
        
        self.setAcceptDrops(True)
        self.versions_tree.viewport().setAcceptDrops(True)
        self.versions_tree.setDragDropMode(QAbstractItemView.DragDrop)
        
    def auto_refresh_versions(self):
        current_time = time.time()
        if current_time - self.last_refresh_time > 4.9 and not self.refresh_in_progress:
            self.refresh_in_progress = True
            try:
                self.refresh_versions_silent()
            finally:
                self.refresh_in_progress = False
        
    def refresh_versions_silent(self):
        self.versions_tree.clear()
        self.load_tree_state()
        
        def add_items(path, parent=None):
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                for item in items:
                    if item.is_dir():
                        display_name = f"[{item.name}]"
                        tree_item = QTreeWidgetItem(parent or self.versions_tree, [display_name, "Folder", "", ""])
                        add_items(item, tree_item)
                        if self.tree_state.get(item.name, False):
                            tree_item.setExpanded(True)
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
        self.versions_tree.resizeColumnToContents(1)
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_bar = self.CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        menu_bar = QHBoxLayout()
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.open_settings)
        menu_bar.addWidget(settings_btn)
        
        version_label = QLabel("Version 1.0.1")
        version_label.setStyleSheet("color: #888888;")
        menu_bar.addWidget(version_label)
        
        menu_bar.addStretch()
        content_layout.addLayout(menu_bar)
        
        main_splitter = QSplitter(Qt.Horizontal)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
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
        self.channel_combo.setEditable(True)
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
        self.refresh_btn.clicked.connect(self.refresh_versions_manual)
        versions_header.addWidget(self.refresh_btn)
        
        versions_layout.addLayout(versions_header)
        
        self.versions_tree = QTreeWidget()
        self.versions_tree.setHeaderLabels(["Name", "Type", "Size", "Modified"])
        self.versions_tree.setIndentation(20)
        self.versions_tree.setAlternatingRowColors(True)
        self.versions_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.versions_tree.customContextMenuRequested.connect(self.show_version_context_menu)
        self.versions_tree.itemExpanded.connect(self.on_item_expanded)
        self.versions_tree.itemCollapsed.connect(self.save_tree_state)
        versions_layout.addWidget(self.versions_tree)
        
        action_layout = QHBoxLayout()
        self.change_btn = QPushButton("Activate Version")
        self.change_btn.clicked.connect(self.change_version)
        action_layout.addWidget(self.change_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected)
        action_layout.addWidget(self.delete_btn)
        
        self.import_btn = QPushButton("Import Version")
        self.import_btn.clicked.connect(self.import_version)
        action_layout.addWidget(self.import_btn)
        
        action_layout.addStretch()
        versions_layout.addLayout(action_layout)
        
        left_layout.addWidget(versions_frame)
        main_splitter.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
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
        
        custom_btn = QPushButton("Apply Custom Textures")
        custom_btn.clicked.connect(self.apply_custom_textures)
        texture_layout.addWidget(custom_btn)
        
        import_custom_btn = QPushButton("Import Custom Textures")
        import_custom_btn.clicked.connect(self.import_custom_textures)
        texture_layout.addWidget(import_custom_btn)
        
        right_layout.addWidget(texture_frame)
        
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
        self.file_browser.setDragEnabled(True)
        self.file_browser.setAcceptDrops(True)
        browser_layout.addWidget(self.file_browser)
        
        right_layout.addWidget(browser_frame)
        
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([700, 600])
        content_layout.addWidget(main_splitter)
        
        self.log_output = QTextEdit()
        self.log_output.setObjectName("log_output")
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        content_layout.addWidget(self.log_output)
        
        main_layout.addWidget(content)
        
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    class CustomTitleBar(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.setFixedHeight(32)
            self.setup_ui()
            
        def setup_ui(self):
            layout = QHBoxLayout(self)
            layout.setContentsMargins(10, 0, 10, 0)
            layout.setSpacing(8)
            
            self.title_label = QLabel("DRCM - Roblox Version Manager")
            self.title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #e0e0e0;")
            layout.addWidget(self.title_label)
            
            layout.addStretch()
            
            self.min_btn = QPushButton("-")
            self.min_btn.setFixedSize(32, 28)
            self.min_btn.setStyleSheet("""
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
            self.min_btn.clicked.connect(self.parent.showMinimized)
            layout.addWidget(self.min_btn)
            
            self.max_btn = QPushButton("□")
            self.max_btn.setFixedSize(32, 28)
            self.max_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    border: 1px solid #5a5a5a;
                    font-size: 14px;
                    font-weight: bold;
                    color: #ffffff;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #ffaa44;
                }
            """)
            self.max_btn.clicked.connect(self.toggle_maximize)
            layout.addWidget(self.max_btn)
            
            self.close_btn = QPushButton("X")
            self.close_btn.setFixedSize(32, 28)
            self.close_btn.setStyleSheet("""
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
            self.close_btn.clicked.connect(self.parent.close)
            layout.addWidget(self.close_btn)
            
        def toggle_maximize(self):
            if self.parent.isMaximized():
                self.parent.showNormal()
                self.max_btn.setText("□")
            else:
                self.parent.showMaximized()
                self.max_btn.setText("❐")
                
        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.parent.drag_pos = event.globalPosition().toPoint()
                
        def mouseMoveEvent(self, event):
            if event.buttons() == Qt.LeftButton and hasattr(self.parent, 'drag_pos'):
                self.parent.move(self.parent.pos() + event.globalPosition().toPoint() - self.parent.drag_pos)
                self.parent.drag_pos = event.globalPosition().toPoint()
    
    def refresh_versions_manual(self):
        self.last_refresh_time = time.time()
        self.refresh_versions()
        if self.sound_manager.enabled:
            self.sound_manager.play_click()
        
    def on_item_expanded(self, item):
        current_time = time.time()
        if current_time - self.last_expand_time > 0.1:
            self.last_expand_time = current_time
            self.save_tree_state(item)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                dest = self.versions_path / Path(file_path).name
                if Path(file_path).is_dir():
                    shutil.copytree(file_path, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(file_path, dest)
                self.log(f"Copied: {Path(file_path).name}")
        self.refresh_versions()
        if self.sound_manager.enabled:
            self.sound_manager.play_click()
        
    def save_tree_state(self, item):
        if item:
            item_name = item.text(0)
            if item_name.startswith("[") and item_name.endswith("]"):
                item_name = item_name[1:-1]
            self.tree_state[item_name] = item.isExpanded()
            settings = QSettings("DRCM", "TreeState")
            settings.setValue("tree_state", json.dumps(self.tree_state))
            
    def load_tree_state(self):
        settings = QSettings("DRCM", "TreeState")
        state = settings.value("tree_state", "{}")
        try:
            self.tree_state = json.loads(state)
        except:
            self.tree_state = {}
            
    def browse_file(self, item, column):
        file_path = item.data(0, Qt.UserRole)
        if file_path and Path(file_path).exists():
            if Path(file_path).is_dir():
                self.load_file_browser(Path(file_path))
            else:
                os.startfile(file_path)
                
    def load_file_browser(self, path=None):
        self.file_browser.clear()
        if path is None:
            path = self.bloxstrap_path if self.bloxstrap_path.exists() else Path.home()
            
        current_path = QTreeWidgetItem(self.file_browser, ["..", "", ""])
        current_path.setData(0, Qt.UserRole, str(path.parent))
        
        for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.is_dir():
                tree_item = QTreeWidgetItem(self.file_browser, [f"[{item.name}]", "", ""])
            else:
                size_mb = item.stat().st_size / (1024 * 1024)
                modified = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                tree_item = QTreeWidgetItem(self.file_browser, 
                                           [item.name, f"{size_mb:.2f} MB", modified])
            tree_item.setData(0, Qt.UserRole, str(item))
            
        self.file_browser.resizeColumnToContents(0)
        
    def show_version_context_menu(self, position):
        item = self.versions_tree.itemAt(position)
        if item:
            menu = QMenu()
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_selected)
            menu.addAction(delete_action)
            
            open_action = QAction("Open in Explorer", self)
            open_action.triggered.connect(self.open_selected_folder)
            menu.addAction(open_action)
            
            copy_action = QAction("Copy Path", self)
            copy_action.triggered.connect(self.copy_path)
            menu.addAction(copy_action)
            
            menu.exec(self.versions_tree.viewport().mapToGlobal(position))
            
    def copy_path(self):
        items = self.versions_tree.selectedItems()
        if items:
            item_name = items[0].text(0)
            if item_name.startswith("[") and item_name.endswith("]"):
                item_name = item_name[1:-1]
            item_path = self.versions_path / item_name
            QApplication.clipboard().setText(str(item_path))
            self.log(f"Copied path: {item_path}")
            
    def import_version(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Roblox Version", 
                                                   str(Path.home() / "Downloads"), 
                                                   "Roblox Files (*.zip *.roblox *.rbx)")
        if file_path:
            dest = self.versions_path / Path(file_path).name
            shutil.copy2(file_path, dest)
            self.log(f"Imported: {Path(file_path).name}")
            self.refresh_versions()
            if self.sound_manager.enabled:
                self.sound_manager.play_click()
            
    def import_custom_textures(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Import Custom Textures",
                                                str(Path.home() / "Downloads"),
                                                "Image Files (*.png *.jpg *.jpeg *.dds)")
        if files:
            for file in files:
                dest = self.custom_textures_path / Path(file).name
                shutil.copy2(file, dest)
                self.log(f"Imported texture: {Path(file).name}")
            self.log(f"Imported {len(files)} textures")
            if self.sound_manager.enabled:
                self.sound_manager.play_click()
            
    def apply_custom_textures(self):
        current_version = self.get_current_version_path()
        if not current_version:
            self.log("No version active")
            return
            
        textures_path = current_version / "PlatformContent" / "pc" / "textures"
        
        if not self.custom_textures_path.exists():
            self.log("No custom textures found")
            return
            
        self.log("Applying custom textures...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.texture_thread = TextureApplyThread(self.custom_textures_path, textures_path, clear_first=True)
        self.texture_thread.progress.connect(self.log)
        self.texture_thread.finished.connect(self.texture_finished)
        self.texture_thread.start()
        
    def delete_selected(self):
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
            if self.sound_manager.enabled:
                self.sound_manager.play_click()
            
    def open_selected_folder(self):
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
                
    def refresh_current_version(self):
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
        if self.bloxstrap_path.exists():
            for item in self.bloxstrap_path.iterdir():
                if item.is_dir():
                    return item
        return None
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
        self.status_label.setText(message)
        
    def refresh_versions(self):
        self.last_refresh_time = time.time()
        self.versions_tree.clear()
        self.load_tree_state()
        
        def add_items(path, parent=None):
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                for item in items:
                    if item.is_dir():
                        display_name = f"[{item.name}]"
                        tree_item = QTreeWidgetItem(parent or self.versions_tree, [display_name, "Folder", "", ""])
                        add_items(item, tree_item)
                        if self.tree_state.get(item.name, False):
                            tree_item.setExpanded(True)
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
            except Exception as e:
                self.log(f"Error reading directory: {e}")
        
        add_items(self.versions_path)
        self.versions_tree.resizeColumnToContents(0)
        self.versions_tree.resizeColumnToContents(1)
        self.log(f"Found {self.versions_tree.topLevelItemCount()} items")
        
    def download_version(self):
        version_id = self.version_input.text().strip()
        channel = self.channel_combo.currentText()
        
        if not version_id:
            self.log("Enter a version ID")
            return
            
        download_url = f"https://rdd.latte.to/?channel={channel}&binaryType=WindowsPlayer&version={version_id}"
        self.log(f"Downloading: {version_id}")
        
        if self.sound_manager.enabled:
            self.sound_manager.play_download()
        
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.monitor_label.setText("Waiting for download...")
        
        self.download_thread = DownloadThread(download_url, channel, version_id)
        self.download_thread.progress.connect(self.log)
        self.download_thread.status.connect(self.monitor_label.setText)
        self.download_thread.download_complete.connect(self.process_downloaded_file)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()
        
    def download_finished(self):
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.monitor_label.setText("")
        
    def process_downloaded_file(self, source_path_str, folder_name):
        source_path = Path(source_path_str)
        dest_folder = self.versions_path / folder_name
        
        self.log(f"Processing: {source_path.name}")
        self.monitor_label.setText("Extracting...")
        
        try:
            if dest_folder.exists():
                shutil.rmtree(dest_folder)
            dest_folder.mkdir(exist_ok=True)
            
            if source_path.suffix.lower() in ['.zip', '.roblox']:
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    zip_ref.extractall(dest_folder)
                source_path.unlink()
                self.log(f"Extracted to: {folder_name}")
            else:
                shutil.move(str(source_path), str(dest_folder / source_path.name))
                self.log(f"Moved to: {folder_name}")
            
            self.log("Download complete!")
            self.monitor_label.setText("Complete!")
            self.refresh_versions()
            
            if self.sound_manager.enabled:
                self.sound_manager.play_complete()
            
        except Exception as e:
            self.log(f"Error: {e}")
            self.monitor_label.setText("Error")
            if self.sound_manager.enabled:
                self.sound_manager.play_error()
            
        QTimer.singleShot(3000, lambda: self.monitor_label.setText(""))
        
    def change_version(self):
        items = self.versions_tree.selectedItems()
        if not items:
            self.log("Select a version to activate")
            return
            
        item = items[0]
        while item.parent():
            item = item.parent()
            
        item_name = item.text(0)
        if item_name.startswith("[") and item_name.endswith("]"):
            item_name = item_name[1:-1]
            
        item_path = self.versions_path / item_name
        
        if not item_path.exists():
            self.log(f"Not found: {item_name}")
            return
            
        try:
            self.log(f"Activating: {item_name}")
            
            if self.bloxstrap_path.exists():
                for existing in self.bloxstrap_path.iterdir():
                    try:
                        if existing.is_dir():
                            shutil.rmtree(existing)
                        else:
                            existing.unlink()
                    except:
                        pass
            else:
                self.bloxstrap_path.mkdir(parents=True, exist_ok=True)
            
            if item_path.is_dir():
                dest_path = self.bloxstrap_path / item_name
                shutil.copytree(item_path, dest_path)
                self.log(f"Copied folder: {item_name}")
            else:
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
            
            if self.sound_manager.enabled:
                self.sound_manager.play_complete()
            
        except Exception as e:
            self.log(f"Error: {e}")
            if self.sound_manager.enabled:
                self.sound_manager.play_error()
            
    def apply_dark_textures(self):
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
        self.texture_thread.finished.connect(self.texture_finished)
        self.texture_thread.start()
        
    def apply_normal_textures(self):
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
        self.texture_thread.finished.connect(self.texture_finished)
        self.texture_thread.start()
        
    def texture_finished(self, count):
        self.progress_bar.setVisible(False)
        self.log(f"Complete! Processed {count} items")
        if self.sound_manager.enabled:
            self.sound_manager.play_complete()
        
    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.refresh_versions()
            self.refresh_current_version()
        
    def load_settings(self):
        settings = QSettings("DRCM", "Settings")
        self.bg_color = settings.value("bg_color", "#1a1a2e")
        self.accent_color = settings.value("accent_color", "#4a6fa5")
        self.text_color = settings.value("text_color", "#e0e0e0")
        transparency = max(15, int(settings.value("transparency", 100)))
        self.window_transparency = transparency / 100.0
        volume = int(settings.value("volume", 50))
        enable_sounds = settings.value("enable_sounds", True, type=bool)
        
        self.sound_manager.set_volume(volume)
        self.sound_manager.enabled = enable_sounds
        
        self.setWindowOpacity(self.window_transparency)
        
    def apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.bg_color};
            }}
            
            QLabel, QTreeWidget, QTextEdit, QLineEdit, QComboBox {{
                color: {self.text_color};
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
                color: {self.text_color};
                padding: 4px;
                border: none;
            }}
            
            QComboBox {{
                background-color: {self.lighten_color(self.bg_color, 1.1)};
                border: 1px solid {self.accent_color};
                border-radius: 4px;
                padding: 4px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.lighten_color(self.bg_color, 1.1)};
                selection-background-color: {self.accent_color};
            }}
            
            QLineEdit {{
                background-color: {self.lighten_color(self.bg_color, 1.1)};
                border: 1px solid {self.accent_color};
                border-radius: 4px;
                padding: 6px;
            }}
            
            QLineEdit:focus {{
                border: 2px solid {self.accent_color};
            }}
            
            QProgressBar {{
                background-color: {self.lighten_color(self.bg_color, 1.2)};
                border-radius: 2px;
            }}
            
            QProgressBar::chunk {{
                background-color: {self.accent_color};
                border-radius: 2px;
            }}
            
            QMenuBar {{
                background-color: {self.darken_color(self.bg_color, 0.9)};
                color: {self.text_color};
            }}
            
            QMenu {{
                background-color: {self.darken_color(self.bg_color, 0.9)};
                color: {self.text_color};
            }}
            
            QMenu::item:selected {{
                background-color: {self.accent_color};
            }}
            
            QScrollBar:vertical {{
                background-color: {self.darken_color(self.bg_color, 0.9)};
                width: 10px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.accent_color};
                border-radius: 5px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.lighten_color(self.accent_color, 1.2)};
            }}
        """)
        
    def lighten_color(self, color, factor):
        qcolor = QColor(color)
        return qcolor.lighter(int(100 * factor)).name()
        
    def darken_color(self, color, factor):
        qcolor = QColor(color)
        return qcolor.darker(int(100 / factor)).name()

class SettingsDialog(DraggableDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("DRCM Settings")
        self.setMinimumSize(600, 650)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #5a5a5a;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        title_label = QLabel("Settings")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        close_btn = QPushButton("X")
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
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
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
        
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text:"))
        self.text_color_btn = QPushButton("Choose Color")
        self.text_color_btn.clicked.connect(lambda: self.choose_color("text"))
        text_layout.addWidget(self.text_color_btn)
        self.text_preview = QLabel()
        self.text_preview.setFixedSize(50, 25)
        text_layout.addWidget(self.text_preview)
        text_layout.addStretch()
        color_layout.addLayout(text_layout)
        
        color_group.setLayout(color_layout)
        scroll_layout.addWidget(color_group)
        
        credits_group = QGroupBox("About")
        credits_layout = QVBoxLayout()
        
        credits_label = QLabel("DRCM - Roblox Version Manager")
        credits_label.setAlignment(Qt.AlignCenter)
        credits_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a6fa5;")
        credits_layout.addWidget(credits_label)
        
        version_label = QLabel("Version 1.0.1")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #888888;")
        credits_layout.addWidget(version_label)
        
        credits_layout.addSpacing(10)
        
        dev_label = QLabel("Created by: Dev_Z / ipad_halobuck")
        dev_label.setAlignment(Qt.AlignCenter)
        dev_label.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        credits_layout.addWidget(dev_label)
        
        credits_layout.addSpacing(5)
        
        thanks_label = QLabel("Special thanks to the Roblox community")
        thanks_label.setAlignment(Qt.AlignCenter)
        thanks_label.setStyleSheet("color: #888888; font-size: 11px;")
        credits_layout.addWidget(thanks_label)
        
        credits_group.setLayout(credits_layout)
        scroll_layout.addWidget(credits_group)
        
        sound_group = QGroupBox("Sound Settings")
        sound_layout = QVBoxLayout()
        
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = ClickableSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.update_volume_preview)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setSuffix("%")
        self.volume_spin.valueChanged.connect(self.volume_slider.setValue)
        self.volume_slider.valueChanged.connect(self.volume_spin.setValue)
        volume_layout.addWidget(self.volume_spin)
        sound_layout.addLayout(volume_layout)
        
        self.enable_sounds = QCheckBox("Enable UI Sounds")
        self.enable_sounds.setChecked(True)
        sound_layout.addWidget(self.enable_sounds)
        
        sound_group.setLayout(sound_layout)
        scroll_layout.addWidget(sound_group)
        
        window_group = QGroupBox("Window Settings")
        window_layout = QVBoxLayout()
        
        transparent_layout = QHBoxLayout()
        transparent_layout.addWidget(QLabel("Window Transparency:"))
        self.transparency_slider = ClickableSlider(Qt.Horizontal)
        self.transparency_slider.setRange(15, 100)
        self.transparency_slider.setValue(100)
        self.transparency_slider.valueChanged.connect(self.update_transparency_preview)
        transparent_layout.addWidget(self.transparency_slider)
        
        self.transparency_spin = QSpinBox()
        self.transparency_spin.setRange(15, 100)
        self.transparency_spin.setSuffix("%")
        self.transparency_spin.valueChanged.connect(self.transparency_slider.setValue)
        self.transparency_slider.valueChanged.connect(self.transparency_spin.setValue)
        transparent_layout.addWidget(self.transparency_spin)
        
        window_layout.addLayout(transparent_layout)
        window_group.setLayout(window_layout)
        scroll_layout.addWidget(window_group)
        
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        self.auto_refresh = QCheckBox("Auto-refresh versions list (5 seconds)")
        self.auto_refresh.setChecked(True)
        behavior_layout.addWidget(self.auto_refresh)
        
        self.save_state = QCheckBox("Save tree expansion state")
        self.save_state.setChecked(True)
        behavior_layout.addWidget(self.save_state)
        
        behavior_group.setLayout(behavior_layout)
        scroll_layout.addWidget(behavior_group)
        
        path_group = QGroupBox("File Paths")
        path_layout = QVBoxLayout()
        
        rbxv_layout = QHBoxLayout()
        rbxv_layout.addWidget(QLabel("Roblox Versions:"))
        self.rbxv_path = QLineEdit()
        self.rbxv_path.setText(str(self.parent.versions_path))
        rbxv_layout.addWidget(self.rbxv_path)
        rbxv_browse = QPushButton("Browse")
        rbxv_browse.clicked.connect(lambda: self.browse_path("rbxv"))
        rbxv_layout.addWidget(rbxv_browse)
        path_layout.addLayout(rbxv_layout)
        
        bloxstrap_layout = QHBoxLayout()
        bloxstrap_layout.addWidget(QLabel("Bloxstrap Path:"))
        self.bloxstrap_path = QLineEdit()
        self.bloxstrap_path.setText(str(self.parent.bloxstrap_path))
        bloxstrap_layout.addWidget(self.bloxstrap_path)
        bloxstrap_browse = QPushButton("Browse")
        bloxstrap_browse.clicked.connect(lambda: self.browse_path("bloxstrap"))
        bloxstrap_layout.addWidget(bloxstrap_browse)
        path_layout.addLayout(bloxstrap_layout)
        
        ct_layout = QHBoxLayout()
        ct_layout.addWidget(QLabel("Custom Textures:"))
        self.ct_path = QLineEdit()
        self.ct_path.setText(str(self.parent.custom_textures_path))
        ct_layout.addWidget(self.ct_path)
        ct_browse = QPushButton("Browse")
        ct_browse.clicked.connect(lambda: self.browse_path("ct"))
        ct_layout.addWidget(ct_browse)
        path_layout.addLayout(ct_layout)
        
        path_group.setLayout(path_layout)
        scroll_layout.addWidget(path_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        content_layout.addWidget(scroll)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        content_layout.addWidget(buttons)
        
        layout.addWidget(content)
        
    def choose_color(self, color_type):
        initial_color = ""
        if color_type == "bg":
            initial_color = self.parent.bg_color
        elif color_type == "accent":
            initial_color = self.parent.accent_color
        else:
            initial_color = self.parent.text_color
            
        picker = IntegratedColorPicker(self, initial_color)
        if picker.exec():
            color = picker.get_color()
            if color_type == "bg":
                self.parent.bg_color = color
                self.bg_preview.setStyleSheet(f"background-color: {color}; border: 1px solid gray;")
            elif color_type == "accent":
                self.parent.accent_color = color
                self.accent_preview.setStyleSheet(f"background-color: {color}; border: 1px solid gray;")
            elif color_type == "text":
                self.parent.text_color = color
                self.text_preview.setStyleSheet(f"background-color: {color}; border: 1px solid gray;")
            self.parent.apply_theme()
            
    def update_volume_preview(self, value):
        self.parent.sound_manager.set_volume(value)
        if self.enable_sounds.isChecked():
            self.parent.sound_manager.play_click()
                
    def update_transparency_preview(self, value):
        self.parent.window_transparency = value / 100.0
        self.parent.setWindowOpacity(self.parent.window_transparency)
        
    def browse_path(self, path_type):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            if path_type == "rbxv":
                self.rbxv_path.setText(folder)
            elif path_type == "bloxstrap":
                self.bloxstrap_path.setText(folder)
            elif path_type == "ct":
                self.ct_path.setText(folder)
                
    def load_settings(self):
        settings = QSettings("DRCM", "Settings")
        self.bg_preview.setStyleSheet(f"background-color: {settings.value('bg_color', '#1a1a2e')}; border: 1px solid gray;")
        self.accent_preview.setStyleSheet(f"background-color: {settings.value('accent_color', '#4a6fa5')}; border: 1px solid gray;")
        self.text_preview.setStyleSheet(f"background-color: {settings.value('text_color', '#e0e0e0')}; border: 1px solid gray;")
        self.transparency_slider.setValue(max(15, int(settings.value('transparency', 100))))
        self.volume_slider.setValue(int(settings.value('volume', 50)))
        self.enable_sounds.setChecked(settings.value('enable_sounds', True, type=bool))
        self.auto_refresh.setChecked(settings.value('auto_refresh', True, type=bool))
        self.save_state.setChecked(settings.value('save_state', True, type=bool))
        
    def save_settings(self):
        settings = QSettings("DRCM", "Settings")
        settings.setValue("bg_color", self.parent.bg_color)
        settings.setValue("accent_color", self.parent.accent_color)
        settings.setValue("text_color", self.parent.text_color)
        settings.setValue("transparency", max(15, self.transparency_slider.value()))
        settings.setValue("volume", self.volume_slider.value())
        settings.setValue("enable_sounds", self.enable_sounds.isChecked())
        settings.setValue("auto_refresh", self.auto_refresh.isChecked())
        settings.setValue("save_state", self.save_state.isChecked())
        settings.setValue("rbxv_path", self.rbxv_path.text())
        settings.setValue("bloxstrap_path", self.bloxstrap_path.text())
        settings.setValue("ct_path", self.ct_path.text())
        
        self.parent.versions_path = Path(self.rbxv_path.text())
        self.parent.bloxstrap_path = Path(self.bloxstrap_path.text())
        self.parent.custom_textures_path = Path(self.ct_path.text())
        self.parent.sound_manager.set_volume(self.volume_slider.value())
        self.parent.sound_manager.enabled = self.enable_sounds.isChecked()
        
        if self.auto_refresh.isChecked():
            self.parent.auto_refresh_timer.start(5000)
        else:
            self.parent.auto_refresh_timer.stop()
            
        self.parent.apply_theme()
        self.accept()

def main():
    # Check if license is already validated
    if not check_license():
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setApplicationName("DRCM")
        
        # Show license dialog
        license_dialog = LicenseDialog()
        if license_dialog.exec() != QDialog.Accepted:
            sys.exit(0)
    
    # Launch main application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("DRCM")
    
    window = RobloxVersionManager()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
