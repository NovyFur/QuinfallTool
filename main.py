import sys
import json
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, 
    QSlider, QComboBox, QColorDialog, QDialog, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QListWidget, QListWidgetItem, QSpinBox, QSplitter, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QSortFilterProxyModel
from PyQt6.QtGui import QColor, QIcon, QAction, QStandardItemModel, QStandardItem

# Import styles
from styles import MAIN_STYLE, TIMER_STYLE, PROFIT_STYLE

# Import crafting calculator
from crafting_calculator import CraftingCalculatorTab

class PopoutWindow(QMainWindow):
    """Base class for separate windows with their own transparency."""
    closed = pyqtSignal(object)
    unpopout_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(MAIN_STYLE)
        
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
        self.resize(1100, 950)

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
        
        min_btn = QPushButton("-")
        min_btn.setObjectName("MainMinButton")
        min_btn.setFixedSize(36, 36)
        min_btn.clicked.connect(self.showMinimized)
        
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
        
        # ── Timers Tab ────────────────────────────────────────────────────
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
        
        # ── Profit Tab ────────────────────────────────────────────────────
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
        
        # ── Recipes Tab ───────────────────────────────────────────────────
        recipe_tab = QWidget()
        rl = QVBoxLayout(recipe_tab)
        rl.setContentsMargins(6, 6, 6, 6)
        rl.setSpacing(6)

        # Search / filter bar
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search recipes...")
        self.search_input.setStyleSheet(
            "QLineEdit { background:#121212; color:#fff; border:1px solid #555; border-radius:4px; padding:5px; }")
        self.search_input.textChanged.connect(self.filter_recipes)
        self.prof_box = QComboBox()
        self.prof_box.setMinimumWidth(160)
        self.prof_box.addItems(["All Professions", "Cooking", "Alchemy", "BlackSmith", "Tailor",
                                 "Carpenter", "Engineering", "Jewel Crafting", "Woodcrafter",
                                 "Smelting", "Leatherworker", "Essence Refining", "Gem Cutting",
                                 "Thread Viewer", "Construction"])
        self.prof_box.currentTextChanged.connect(self.filter_recipes)
        filter_row.addWidget(self.search_input, 1)
        filter_row.addWidget(self.prof_box)
        rl.addLayout(filter_row)

        # Left/Right splitter
        recipe_splitter = QSplitter(Qt.Orientation.Horizontal)
        recipe_splitter.setStyleSheet("QSplitter::handle { background:#444; width:4px; }")

        # ── LEFT: sortable recipe table ──────────────────────────────────
        left_frame = QFrame()
        left_frame.setStyleSheet(
            "QFrame { background:rgba(18,18,18,220); border:1px solid #333; border-radius:8px; }")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(4)

        sort_hint = QLabel(
            "<span style='color:#666; font-size:10px;'>Click column headers to sort</span>")
        left_layout.addWidget(sort_hint)

        # Table with sortable columns
        self.recipe_table = QTableWidget()
        self.recipe_table.setColumnCount(5)
        self.recipe_table.setHorizontalHeaderLabels(
            ["Name", "Req. Level", "XP Reward", "Craft Time", "Sale Price"])
        self.recipe_table.setStyleSheet("""
            QTableWidget {
                background:#0d0d0d; color:#fff; border:none;
                gridline-color:#2a2a2a; font-size:12px;
            }
            QHeaderView::section {
                background:#1a1a1a; color:#00d4ff;
                border:1px solid #333; padding:5px;
                font-weight:bold; font-size:11px;
            }
            QHeaderView::section:hover { background:#252525; cursor:pointer; }
            QHeaderView::section::down-arrow { image: none; }
            QTableWidget::item { padding:4px 6px; }
            QTableWidget::item:selected { background:#1a3a5c; color:#00d4ff; }
            QTableWidget::item:hover { background:#1e1e2e; }
            QTableWidget { alternate-background-color:#111; }
        """)
        self.recipe_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.recipe_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.recipe_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recipe_table.setAlternatingRowColors(True)
        self.recipe_table.verticalHeader().setVisible(False)
        self.recipe_table.setSortingEnabled(True)
        hdr = self.recipe_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 5):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.recipe_table.itemSelectionChanged.connect(self._on_recipe_table_select)
        left_layout.addWidget(self.recipe_table, 1)
        recipe_splitter.addWidget(left_frame)

        # ── RIGHT: recipe detail panel ───────────────────────────────────
        right_frame = QFrame()
        right_frame.setStyleSheet(
            "QFrame { background:rgba(18,18,18,220); border:1px solid #333; border-radius:8px; }")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(6)

        detail_title = QLabel("<b style='color:#00d4ff;'>Recipe Detail</b>")
        detail_title.setStyleSheet("font-size:13px;")
        right_layout.addWidget(detail_title)

        self.recipe_scroll = QScrollArea()
        self.recipe_scroll.setWidgetResizable(True)
        self.recipe_scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        self.recipe_detail = QLabel("<span style='color:#555; font-style:italic;'>Select a recipe to view details</span>")
        self.recipe_detail.setWordWrap(True)
        self.recipe_detail.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.recipe_detail.setStyleSheet(
            "background:transparent; padding:6px; color:white; font-size:12px;")
        self.recipe_scroll.setWidget(self.recipe_detail)
        right_layout.addWidget(self.recipe_scroll, 1)
        recipe_splitter.addWidget(right_frame)

        recipe_splitter.setSizes([680, 360])
        rl.addWidget(recipe_splitter, 1)

        # ── Crafting Calculator Tab ───────────────────────────────────────
        self.calc_tab = CraftingCalculatorTab(self.recipes)

        # ── Register all tabs ─────────────────────────────────────────────
        self.tabs.addTab(timer_tab, "Timers")
        self.tabs.addTab(profit_tab, "Profit")
        self.tabs.addTab(recipe_tab, "Recipes")
        self.tabs.addTab(self.calc_tab, "Crafting Calculator")
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
        import re as _re
        txt  = self.search_input.text().lower()
        prof = self.prof_box.currentText()

        # Disable sorting while filling to avoid mid-insert re-sorts
        self.recipe_table.setSortingEnabled(False)
        self.recipe_table.setRowCount(0)

        def _parse_num(val):
            """Strip non-numeric chars and return int, or 0 on failure."""
            try:
                return int(_re.sub(r'[^\d]', '', str(val)))
            except (ValueError, TypeError):
                return 0

        for r in self.recipes:
            name = r.get('Name', 'Unknown')
            p    = r.get('Profession', '')
            if (txt and txt not in name.lower()):
                continue
            if prof != "All Professions" and prof != p:
                continue

            row = self.recipe_table.rowCount()
            self.recipe_table.insertRow(row)

            # Col 0 — Name (store full recipe dict in UserRole)
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, r)
            name_item.setForeground(QColor("#ffffff"))
            self.recipe_table.setItem(row, 0, name_item)

            # Col 1 — Required Level (numeric sort)
            req_lvl = _parse_num(r.get('Required Level', 0))
            lvl_item = QTableWidgetItem()
            lvl_item.setData(Qt.ItemDataRole.DisplayRole, req_lvl)
            lvl_item.setForeground(QColor("#81c784"))
            lvl_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.recipe_table.setItem(row, 1, lvl_item)

            # Col 2 — XP Reward (numeric sort)
            xp_val = _parse_num(r.get('XP Reward', 0))
            xp_item = QTableWidgetItem()
            xp_item.setData(Qt.ItemDataRole.DisplayRole, xp_val)
            xp_item.setForeground(QColor("#00d4ff"))
            xp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.recipe_table.setItem(row, 2, xp_item)

            # Col 3 — Craft Time (numeric sort, stored as seconds)
            ct_raw  = r.get('Craft Time', '0 seconds')
            ct_secs = _parse_num(ct_raw)
            ct_item = QTableWidgetItem()
            ct_item.setData(Qt.ItemDataRole.DisplayRole, ct_secs)
            ct_item.setData(Qt.ItemDataRole.UserRole + 1, ct_raw)  # keep display string
            ct_item.setForeground(QColor("#aaaaaa"))
            ct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.recipe_table.setItem(row, 3, ct_item)

            # Col 4 — Sale Price (numeric sort)
            price_val = _parse_num(r.get('Sale Price', 0))
            price_item = QTableWidgetItem()
            price_item.setData(Qt.ItemDataRole.DisplayRole, price_val)
            price_item.setForeground(QColor("#ffd700"))
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.recipe_table.setItem(row, 4, price_item)

        self.recipe_table.setSortingEnabled(True)
        # Default sort: Required Level ascending
        self.recipe_table.sortItems(1, Qt.SortOrder.AscendingOrder)

    def _on_recipe_table_select(self):
        rows = self.recipe_table.selectedItems()
        if not rows:
            return
        # The recipe dict is stored in col 0's UserRole
        row_idx = self.recipe_table.currentRow()
        name_item = self.recipe_table.item(row_idx, 0)
        if name_item is None:
            return
        r = name_item.data(Qt.ItemDataRole.UserRole)
        if r:
            self._render_recipe_detail(r)

    def _render_recipe_detail(self, r: dict):
        name      = r.get('Name', 'Unknown')
        prof      = r.get('Profession', 'N/A')
        tier      = r.get('Tier', 'N/A')
        req_lvl   = r.get('Required Level', 'N/A')
        xp        = r.get('XP Reward', 'N/A')
        craft_time= r.get('Craft Time', 'N/A')
        item_lvl  = r.get('Item Level', 'N/A')
        price     = r.get('Sale Price', 'N/A')
        item_type = r.get('Type', 'N/A')
        weight    = r.get('Weight', 'N/A')

        txt  = f"<b style='color:#00d4ff; font-size:16px;'>{name}</b><br><br>"
        txt += "<table width='100%' style='color:white; border-collapse:collapse;'>"

        def row_html(label, value, color="#ffffff"):
            return (f"<tr>"
                    f"<td style='padding:3px 8px 3px 0; color:#aaa; font-size:12px;'><b>{label}</b></td>"
                    f"<td style='padding:3px 0; color:{color}; font-size:12px;'>{value}</td>"
                    f"</tr>")

        txt += row_html("Profession:",   prof,       "#00d4ff")
        txt += row_html("Type:",         item_type,  "#ce93d8")
        txt += row_html("Tier:",         tier,       "#81c784")
        txt += row_html("Required Lvl:", req_lvl,    "#81c784")
        txt += row_html("Item Level:",   item_lvl,   "#aaa")
        txt += row_html("XP Reward:",    xp,         "#00d4ff")
        txt += row_html("Craft Time:",   craft_time, "#aaa")
        txt += row_html("Weight:",       weight,     "#aaa")
        txt += row_html("Sale Price:",   f"{price} Gold", "#ffd700")
        txt += "</table>"

        mats = r.get('materials', [])
        if mats:
            txt += "<br><b style='color:#00d4ff; font-size:12px;'>Materials Required:</b><br>"
            txt += "<table width='100%' style='border-collapse:collapse;'>"
            for m in mats:
                txt += (f"<tr>"
                        f"<td style='color:#fff; font-size:12px; padding:2px 0;'>• {m.get('item','?')}</td>"
                        f"<td style='color:#ffd700; font-size:12px; text-align:right; padding:2px 0;'>{m.get('quantity','?')}</td>"
                        f"</tr>")
            txt += "</table>"

        self.recipe_detail.setText(txt)

    # Keep old show_recipe for any legacy callers
    def show_recipe(self, item):
        r = item.data(Qt.ItemDataRole.UserRole)
        if r:
            self._render_recipe_detail(r)

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
