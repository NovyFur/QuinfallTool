import sys
import json
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, 
    QSlider, QComboBox, QColorDialog, QDialog, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QListWidget, QListWidgetItem, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QIcon, QAction

# Import styles
from styles import MAIN_STYLE, TIMER_STYLE, PROFIT_STYLE

class PopoutWindow(QMainWindow):
    """Base class for separate windows with their own transparency."""
    closed = pyqtSignal(object)
    unpopout_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Keep popouts as tools to avoid cluttering taskbar, but main window will be on taskbar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def closeEvent(self, event):
        self.closed.emit(self)
        super().closeEvent(event)

class PopoutTimer(PopoutWindow):
    def __init__(self, name, duration_secs, category, color="#00d4ff", parent=None):
        super().__init__(parent)
        self.name = name
        self.remaining_seconds = duration_secs
        self.color = color
        self.is_running = True
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def init_ui(self):
        self.container = QFrame()
        self.container.setObjectName("TimerFrame")
        self.container.setStyleSheet(f"""
            QFrame#TimerFrame {{
                background-color: rgba(20, 20, 20, 245);
                border-radius: 12px;
                border: 2px solid {self.color};
            }}
            QLabel {{ color: white; font-family: 'Segoe UI'; }}
        """)
        self.setCentralWidget(self.container)
        
        layout = QVBoxLayout(self.container)
        header = QHBoxLayout()
        name_label = QLabel(f"<b>{self.name}</b>")
        
        self.unpop_btn = QPushButton("BACK")
        self.unpop_btn.setFixedSize(45, 24)
        self.unpop_btn.setStyleSheet("background: #444; border: 1px solid #666; border-radius: 4px; color: white; font-weight: bold; font-size: 9px;")
        self.unpop_btn.clicked.connect(lambda: self.unpopout_requested.emit(self))
        
        close_btn = QPushButton("X")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("background: #c62828; border: 1px solid #444; border-radius: 4px; color: white; font-weight: bold; font-size: 12px;")
        close_btn.clicked.connect(self.close)
        
        header.addWidget(name_label)
        header.addStretch()
        header.addWidget(self.unpop_btn)
        header.addWidget(close_btn)
        
        self.time_label = QLabel(self.format_time(self.remaining_seconds))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(f"font-size: 28px; color: {self.color}; font-family: 'Consolas'; font-weight: bold;")
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(95)
        self.opacity_slider.valueChanged.connect(lambda v: self.setWindowOpacity(v/100.0))
        
        layout.addLayout(header)
        layout.addWidget(self.time_label)
        layout.addWidget(self.opacity_slider)
        self.setFixedSize(220, 120)

    def format_time(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def update_timer(self):
        if self.is_running and self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.time_label.setText(self.format_time(self.remaining_seconds))
            if self.remaining_seconds == 0:
                self.time_label.setStyleSheet("color: #ff4444; font-size: 28px; font-weight: bold;")

class PopoutProfit(PopoutWindow):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.total_gold = 0
        self.start_time = None
        self.elapsed_before_stop = 0
        self.is_running = False
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def init_ui(self):
        self.container = QFrame()
        self.container.setObjectName("ProfitFrame")
        self.container.setStyleSheet("""
            QFrame#ProfitFrame {
                background-color: rgba(20, 20, 20, 245);
                border-radius: 12px;
                border: 2px solid #ffd700;
            }
            QLabel { color: white; font-family: 'Segoe UI'; }
        """)
        self.setCentralWidget(self.container)
        
        layout = QVBoxLayout(self.container)
        header = QHBoxLayout()
        name_label = QLabel(f"<b>{self.name}</b>")
        
        self.unpop_btn = QPushButton("BACK")
        self.unpop_btn.setFixedSize(45, 24)
        self.unpop_btn.setStyleSheet("background: #444; border: 1px solid #666; border-radius: 4px; color: white; font-weight: bold; font-size: 9px;")
        self.unpop_btn.clicked.connect(lambda: self.unpopout_requested.emit(self))
        
        close_btn = QPushButton("X")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("background: #c62828; border: 1px solid #444; border-radius: 4px; color: white; font-weight: bold; font-size: 12px;")
        close_btn.clicked.connect(self.close)
        
        header.addWidget(name_label)
        header.addStretch()
        header.addWidget(self.unpop_btn)
        header.addWidget(close_btn)
        
        self.gph_label = QLabel("GPH: 0")
        self.gph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gph_label.setStyleSheet("font-size: 26px; color: #ffd700; font-family: 'Consolas'; font-weight: bold;")
        
        self.total_label = QLabel("Total: 0 Gold")
        self.time_label = QLabel("Time: 00:00:00")
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(95)
        self.opacity_slider.valueChanged.connect(lambda v: self.setWindowOpacity(v/100.0))
        
        layout.addLayout(header)
        layout.addWidget(self.gph_label)
        layout.addWidget(self.total_label)
        layout.addWidget(self.time_label)
        layout.addWidget(self.opacity_slider)
        self.setFixedSize(220, 160)

    def update_stats(self):
        if not self.is_running or self.start_time is None:
            return
        elapsed = int(time.time() - self.start_time) + self.elapsed_before_stop
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        self.time_label.setText(f"Time: {h:02d}:{m:02d}:{s:02d}")
        elapsed_hours = elapsed / 3600
        gph = int(self.total_gold / elapsed_hours) if elapsed_hours > 0 else 0
        self.gph_label.setText(f"GPH: {gph:,}")
        self.total_label.setText(f"Total: {self.total_gold:,} Gold")

class TimerWidget(QFrame):
    removed = pyqtSignal(object)
    popout_requested = pyqtSignal(object)

    def __init__(self, name, duration_secs, category, color="#00d4ff", parent=None):
        super().__init__(parent)
        self.setObjectName("TimerFrame")
        self.setStyleSheet(TIMER_STYLE)
        self.name = name
        self.category = category
        self.color = color
        self.total_seconds = duration_secs
        self.remaining_seconds = duration_secs
        self.is_running = True
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def init_ui(self):
        layout = QHBoxLayout(self)
        self.name_label = QLabel(self.name)
        self.name_label.setObjectName("TimerName")
        self.name_label.setFixedWidth(130)
        
        self.time_label = QLabel(self.format_time(self.remaining_seconds))
        self.time_label.setObjectName("TimerCountdown")
        self.time_label.setStyleSheet(f"color: {self.color};")
        self.time_label.setFixedWidth(90)

        self.pop_btn = QPushButton("OUT")
        self.pop_btn.setObjectName("IconButton")
        self.pop_btn.setFixedSize(36, 32)
        self.pop_btn.clicked.connect(lambda: self.popout_requested.emit(self))

        self.reset_btn = QPushButton("RES")
        self.reset_btn.setObjectName("IconButton")
        self.reset_btn.setFixedSize(36, 32)
        self.reset_btn.clicked.connect(self.reset_timer)

        self.remove_btn = QPushButton("X")
        self.remove_btn.setObjectName("CloseIconButton")
        self.remove_btn.setFixedSize(32, 32)
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))

        layout.addWidget(self.name_label)
        layout.addWidget(self.time_label)
        layout.addStretch()
        layout.addWidget(self.pop_btn)
        layout.addWidget(self.reset_btn)
        layout.addWidget(self.remove_btn)

    def format_time(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def update_timer(self):
        if self.is_running and self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.time_label.setText(self.format_time(self.remaining_seconds))
            if self.remaining_seconds == 0:
                self.time_label.setStyleSheet("color: #ff4444; font-weight: bold;")

    def reset_timer(self):
        self.remaining_seconds = self.total_seconds
        self.time_label.setText(self.format_time(self.remaining_seconds))
        self.time_label.setStyleSheet(f"color: {self.color};")
        self.is_running = True

class ProfitWidget(QFrame):
    removed = pyqtSignal(object)
    popout_requested = pyqtSignal(object)

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setObjectName("ProfitFrame")
        self.setStyleSheet(PROFIT_STYLE)
        self.name = name
        self.total_gold = 0
        self.start_time = None
        self.elapsed_before_stop = 0
        self.is_running = False
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        self.name_label = QLabel(self.name)
        self.name_label.setObjectName("ProfitName")
        header.addWidget(self.name_label)
        header.addStretch()
        
        self.pop_btn = QPushButton("OUT")
        self.pop_btn.setObjectName("ProfitIconButton")
        self.pop_btn.setFixedSize(36, 32)
        self.pop_btn.clicked.connect(lambda: self.popout_requested.emit(self))
        
        self.remove_btn = QPushButton("X")
        self.remove_btn.setObjectName("ProfitCloseButton")
        self.remove_btn.setFixedSize(32, 32)
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))
        
        header.addWidget(self.pop_btn)
        header.addWidget(self.remove_btn)
        
        stats_layout = QHBoxLayout()
        self.gph_label = QLabel("GPH: 0")
        self.gph_label.setObjectName("GPHValue")
        self.total_label = QLabel("Total: 0 Gold")
        self.time_label = QLabel("Time: 00:00:00")
        stats_layout.addWidget(self.gph_label)
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.time_label)
        
        controls = QHBoxLayout()
        self.gold_input = QLineEdit()
        self.gold_input.setPlaceholderText("Add Gold...")
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_gold)
        
        self.start_stop_btn = QPushButton("Start")
        self.start_stop_btn.setObjectName("StartButton")
        self.start_stop_btn.clicked.connect(self.toggle_running)
        
        controls.addWidget(self.gold_input)
        controls.addWidget(self.add_btn)
        controls.addWidget(self.start_stop_btn)
        
        layout.addLayout(header)
        layout.addLayout(stats_layout)
        layout.addLayout(controls)

    def toggle_running(self):
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True
            self.start_stop_btn.setText("Stop")
            self.start_stop_btn.setObjectName("StopButton")
        else:
            self.elapsed_before_stop += int(time.time() - self.start_time)
            self.is_running = False
            self.start_stop_btn.setText("Start")
            self.start_stop_btn.setObjectName("StartButton")
        self.start_stop_btn.setStyle(self.start_stop_btn.style())

    def add_gold(self):
        try:
            val = int(self.gold_input.text().replace(',', ''))
            self.total_gold += val
            self.gold_input.clear()
        except: pass

    def update_stats(self):
        if not self.is_running or self.start_time is None:
            return
        elapsed = int(time.time() - self.start_time) + self.elapsed_before_stop
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        self.time_label.setText(f"Time: {h:02d}:{m:02d}:{s:02d}")
        elapsed_hours = elapsed / 3600
        gph = int(self.total_gold / elapsed_hours) if elapsed_hours > 0 else 0
        self.gph_label.setText(f"GPH: {gph:,}")
        self.total_label.setText(f"Total: {self.total_gold:,} Gold")

class QuinfallOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quinfall Tool")
        # Change WindowStaysOnTopHint to allow normal minimize behavior while keeping it on top when active
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(MAIN_STYLE)
        
        # Try to load icon if it exists
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, 'icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except: pass

        self.old_pos = None
        self.recipes = self.load_recipes()
        self.popouts = []
        self.init_ui()
        self.resize(520, 720)

    def load_recipes(self):
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(base_path, 'quinfall_recipes_full.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []

    def init_ui(self):
        central = QWidget()
        central.setObjectName("OverlayContainer")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        header = QHBoxLayout()
        title = QLabel("QUINFALL TOOL")
        title.setStyleSheet("font-weight: bold; color: #00d4ff; letter-spacing: 2px; font-size: 18px;")
        
        # MINIMIZE BUTTON
        min_btn = QPushButton("-")
        min_btn.setObjectName("MainMinButton")
        min_btn.setFixedSize(36, 36)
        min_btn.clicked.connect(self.showMinimized)
        
        # CLOSE BUTTON
        close_btn = QPushButton("X")
        close_btn.setObjectName("MainCloseButton")
        close_btn.setFixedSize(36, 36)
        close_btn.clicked.connect(self.close)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(min_btn)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        
        # Timers Tab
        timer_tab = QWidget()
        tl = QVBoxLayout(timer_tab)
        self.timer_scroll = QScrollArea()
        self.timer_scroll.setWidgetResizable(True)
        self.timer_cont = QWidget()
        self.timer_cont.setObjectName("ListContainer")
        self.timer_layout = QVBoxLayout(self.timer_cont)
        self.timer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.timer_scroll.setWidget(self.timer_cont)
        add_timer_btn = QPushButton("+ Add New Timer")
        add_timer_btn.setObjectName("AddButton")
        add_timer_btn.clicked.connect(self.show_add_timer)
        tl.addWidget(self.timer_scroll)
        tl.addWidget(add_timer_btn)
        
        # Profit Tab
        profit_tab = QWidget()
        pl = QVBoxLayout(profit_tab)
        self.profit_scroll = QScrollArea()
        self.profit_scroll.setWidgetResizable(True)
        self.profit_cont = QWidget()
        self.profit_cont.setObjectName("ListContainer")
        self.profit_layout = QVBoxLayout(self.profit_cont)
        self.profit_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.profit_scroll.setWidget(self.profit_cont)
        add_profit_btn = QPushButton("+ New Profit Session")
        add_profit_btn.setObjectName("AddButton")
        add_profit_btn.clicked.connect(self.add_profit_session)
        pl.addWidget(self.profit_scroll)
        pl.addWidget(add_profit_btn)
        
        # Recipes Tab
        recipe_tab = QWidget()
        rl = QVBoxLayout(recipe_tab)
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search recipes...")
        self.search_input.textChanged.connect(self.filter_recipes)
        self.prof_box = QComboBox()
        self.prof_box.addItems(["All Professions", "Cooking", "Alchemy", "BlackSmith", "Tailor", "Carpenter", "Engineering", "Jewel Crafting", "Woodcrafter", "Smelting", "Leatherworker"])
        self.prof_box.currentTextChanged.connect(self.filter_recipes)
        search_box.addWidget(self.search_input)
        search_box.addWidget(self.prof_box)
        
        self.recipe_list = QListWidget()
        self.recipe_list.itemClicked.connect(self.show_recipe)
        
        self.recipe_scroll = QScrollArea()
        self.recipe_scroll.setWidgetResizable(True)
        self.recipe_detail = QLabel("Select a recipe")
        self.recipe_detail.setWordWrap(True)
        self.recipe_detail.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.recipe_detail.setStyleSheet("background: #121212; padding: 15px; border-radius: 8px; border: 1px solid #333; color: white;")
        self.recipe_scroll.setWidget(self.recipe_detail)
        self.recipe_scroll.setFixedHeight(250)
        
        rl.addLayout(search_box)
        rl.addWidget(self.recipe_list)
        rl.addWidget(self.recipe_scroll)
        
        self.tabs.addTab(timer_tab, "Timers")
        self.tabs.addTab(profit_tab, "Profit")
        self.tabs.addTab(recipe_tab, "Recipes")
        layout.addWidget(self.tabs)
        self.filter_recipes()

    def show_add_timer(self):
        d = QDialog(self)
        d.setWindowTitle("Add Timer")
        d.setFixedSize(350, 280)
        d.setStyleSheet(MAIN_STYLE)
        l = QFormLayout(d)
        l.setContentsMargins(20, 20, 20, 20)
        l.setSpacing(10)
        
        name = QLineEdit()
        hrs = QSpinBox(); hrs.setRange(0, 999)
        mins = QSpinBox(); mins.setRange(0, 59); mins.setValue(30)
        color_btn = QPushButton("Pick Color")
        color = ["#00d4ff"]
        def pick():
            c = QColorDialog.getColor(QColor(color[0]), d)
            if c.isValid(): 
                color[0] = c.name()
                color_btn.setStyleSheet(f"background: {c.name()}; color: black; font-weight: bold;")
        color_btn.clicked.connect(pick)
        color_btn.setStyleSheet(f"background: {color[0]}; color: black; font-weight: bold;")
        
        btn = QPushButton("Add Timer")
        btn.setObjectName("AddButton")
        btn.setMinimumHeight(40)
        btn.clicked.connect(d.accept)
        
        l.addRow("Name:", name)
        l.addRow("Hours:", hrs)
        l.addRow("Minutes:", mins)
        l.addRow("Color:", color_btn)
        l.addRow(btn)
        
        if d.exec():
            secs = (hrs.value() * 3600) + (mins.value() * 60)
            w = TimerWidget(name.text() or "Timer", secs, "General", color[0])
            w.removed.connect(lambda x: x.deleteLater())
            w.popout_requested.connect(self.popout_timer)
            self.timer_layout.addWidget(w)

    def popout_timer(self, w):
        p = PopoutTimer(w.name, w.remaining_seconds, "General", w.color)
        p.unpopout_requested.connect(self.unpopout_timer)
        p.show(); self.popouts.append(p)
        w.deleteLater()

    def unpopout_timer(self, p):
        w = TimerWidget(p.name, p.remaining_seconds, "General", p.color)
        w.removed.connect(lambda x: x.deleteLater())
        w.popout_requested.connect(self.popout_timer)
        self.timer_layout.addWidget(w)
        p.close()

    def add_profit_session(self):
        d = QDialog(self)
        d.setWindowTitle("New Session")
        d.setFixedSize(300, 150)
        d.setStyleSheet(MAIN_STYLE)
        l = QVBoxLayout(d)
        l.setContentsMargins(20, 20, 20, 20)
        
        name = QLineEdit(); name.setPlaceholderText("Session Name (e.g. Farming)")
        btn = QPushButton("Create Session")
        btn.setObjectName("AddButton")
        btn.setMinimumHeight(40)
        btn.clicked.connect(d.accept)
        
        l.addWidget(name); l.addWidget(btn)
        if d.exec():
            w = ProfitWidget(name.text() or "Session")
            w.removed.connect(lambda x: x.deleteLater())
            w.popout_requested.connect(self.popout_profit)
            self.profit_layout.addWidget(w)

    def popout_profit(self, w):
        p = PopoutProfit(w.name)
        p.total_gold = w.total_gold
        p.start_time = w.start_time
        p.elapsed_before_stop = w.elapsed_before_stop
        p.is_running = w.is_running
        p.unpopout_requested.connect(self.unpopout_profit)
        p.show(); self.popouts.append(p)
        w.deleteLater()

    def unpopout_profit(self, p):
        w = ProfitWidget(p.name)
        w.total_gold = p.total_gold
        w.start_time = p.start_time
        w.elapsed_before_stop = p.elapsed_before_stop
        w.is_running = p.is_running
        w.removed.connect(lambda x: x.deleteLater())
        w.popout_requested.connect(self.popout_profit)
        self.profit_layout.addWidget(w)
        p.close()

    def filter_recipes(self):
        txt = self.search_input.text().lower()
        prof = self.prof_box.currentText()
        self.recipe_list.clear()
        for r in self.recipes:
            n = r.get('Name', 'Unknown')
            p = r.get('Profession', '')
            if (not txt or txt in n.lower()) and (prof == "All Professions" or prof == p):
                item = QListWidgetItem(n)
                item.setData(Qt.ItemDataRole.UserRole, r)
                self.recipe_list.addItem(item)

    def show_recipe(self, item):
        r = item.data(Qt.ItemDataRole.UserRole)
        name = r.get('Name', 'Unknown')
        prof = r.get('Profession', 'N/A')
        tier = r.get('Tier', 'N/A')
        req_lvl = r.get('Required Level', 'N/A')
        xp = r.get('XP Reward', 'N/A')
        craft_time = r.get('Craft Time', 'N/A')
        item_lvl = r.get('Item Level', 'N/A')
        price = r.get('Sale Price', 'N/A')
        
        txt = f"<b style='color:#00d4ff; font-size:20px;'>{name}</b><br><br>"
        txt += "<table width='100%' style='color: white;'>"
        txt += f"<tr><td><b>Profession:</b></td><td style='color:#00d4ff;'>{prof}</td></tr>"
        txt += f"<tr><td><b>Tier:</b></td><td style='color:#00d4ff;'>{tier}</td></tr>"
        txt += f"<tr><td><b>Required Lvl:</b></td><td style='color:#00d4ff;'>{req_lvl}</td></tr>"
        txt += f"<tr><td><b>XP Reward:</b></td><td style='color:#00d4ff;'>{xp}</td></tr>"
        txt += f"<tr><td><b>Craft Time:</b></td><td style='color:#00d4ff;'>{craft_time}</td></tr>"
        txt += f"<tr><td><b>Item Level:</b></td><td style='color:#00d4ff;'>{item_lvl}</td></tr>"
        txt += f"<tr><td><b>Sale Price:</b></td><td style='color:#ffd700;'>{price} Gold</td></tr>"
        txt += "</table><br>"
        
        txt += "<b style='color:#00d4ff;'>Materials Required:</b><br>"
        for m in r.get('materials', []):
            txt += f"<span style='color: white;'>• {m['item']}: <span style='color: #ffd700;'>{m['quantity']}</span></span><br>"
        self.recipe_detail.setText(txt)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def closeEvent(self, event):
        for p in self.popouts: 
            try: p.close()
            except: pass
        QApplication.quit()
        os._exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = QuinfallOverlay()
    overlay.show()
    sys.exit(app.exec())
