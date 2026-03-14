MAIN_STYLE = """
QMainWindow, QDialog {
    background-color: #1a1a1a;
    border-radius: 12px;
    border: 1px solid #444;
}

QWidget#OverlayContainer {
    background-color: transparent;
}

QLabel {
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}

QPushButton {
    background-color: #333;
    color: #ffffff;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #444;
    border: 1px solid #777;
}

/* Main Control Buttons - Circular backgrounds */
QPushButton#MainCloseButton {
    background-color: #c62828;
    color: white;
    border: 2px solid #444;
    border-radius: 18px;
    font-size: 16px;
    font-weight: bold;
}

QPushButton#MainCloseButton:hover {
    background-color: #ff5252;
}

QPushButton#MainMinButton {
    background-color: #111;
    color: #00d4ff;
    border: 1px solid #444;
    border-radius: 18px;
    font-size: 18px;
    font-weight: bold;
}

QPushButton#MainMinButton:hover {
    background-color: #222;
    border: 1px solid #00d4ff;
}

QPushButton#AddButton {
    background-color: #1b5e20;
    border: none;
    font-weight: bold;
    color: white;
}

QPushButton#AddButton:hover {
    background-color: #2e7d32;
}

QPushButton#StopButton {
    background-color: #b71c1c;
    border: none;
    font-weight: bold;
}

QPushButton#StopButton:hover {
    background-color: #d32f2f;
}

QPushButton#StartButton {
    background-color: #0d47a1;
    border: none;
    font-weight: bold;
}

QPushButton#StartButton:hover {
    background-color: #1565c0;
}

QLineEdit, QSpinBox {
    background-color: #121212;
    color: #ffffff;
    border: 1px solid #444;
    border-radius: 5px;
    padding: 6px;
}

QComboBox {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #555;
    border-radius: 5px;
    padding: 6px;
    font-weight: bold;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #000000;
    selection-background-color: #00d4ff;
    selection-color: #000000;
    border: 1px solid #555;
}

QComboBox::drop-down {
    border: none;
    background: #dddddd;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    width: 20px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QWidget#ListContainer {
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #121212;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #444;
    min-height: 30px;
    border-radius: 4px;
}

QTabWidget::pane { 
    border: 1px solid #444; 
    background: rgba(20,20,20,200); 
    border-radius: 6px;
}

QTabBar::tab { 
    background: #181818; 
    color: #999; 
    padding: 12px 20px; 
    min-width: 100px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected { 
    background: #252525; 
    color: #00d4ff; 
    border-bottom: 3px solid #00d4ff; 
    font-weight: bold;
}

QListWidget {
    background-color: #121212;
    color: #ffffff;
    border: 1px solid #333;
    border-radius: 5px;
}
"""

TIMER_STYLE = """
QFrame#TimerFrame {
    background-color: rgba(35, 35, 35, 230);
    border-radius: 10px;
    border: 1px solid #444;
    margin: 4px;
}

QLabel#TimerName {
    font-weight: bold;
    font-size: 14px;
    color: #ffffff;
}

QLabel#TimerCountdown {
    font-size: 18px;
    color: #00d4ff;
    font-family: 'Consolas', monospace;
    font-weight: bold;
}

QPushButton#IconButton {
    background-color: #444;
    border: 1px solid #666;
    border-radius: 4px;
    color: #ffffff;
    font-size: 10px;
    font-weight: bold;
    min-width: 36px;
}

QPushButton#IconButton:hover {
    background-color: #00d4ff;
    color: black;
}

QPushButton#CloseIconButton {
    background-color: #c62828;
    border: 1px solid #444;
    border-radius: 4px;
    color: white;
    font-size: 12px;
    font-weight: bold;
    min-width: 32px;
}

QPushButton#CloseIconButton:hover {
    background-color: #ff5252;
}
"""

PROFIT_STYLE = """
QFrame#ProfitFrame {
    background-color: rgba(35, 35, 35, 230);
    border-radius: 10px;
    border: 1px solid #ffd700;
    margin: 4px;
}

QLabel#ProfitName {
    font-weight: bold;
    font-size: 14px;
    color: #ffffff;
}

QLabel#GPHValue {
    font-size: 18px;
    color: #ffd700;
    font-family: 'Consolas', monospace;
    font-weight: bold;
}

QPushButton#ProfitIconButton {
    background-color: #444;
    border: 1px solid #666;
    border-radius: 4px;
    color: #ffffff;
    font-size: 10px;
    font-weight: bold;
    min-width: 36px;
}

QPushButton#ProfitIconButton:hover {
    background-color: #ffd700;
    color: black;
}

QPushButton#ProfitCloseButton {
    background-color: #c62828;
    border: 1px solid #444;
    border-radius: 4px;
    color: white;
    font-size: 12px;
    font-weight: bold;
    min-width: 32px;
}

QPushButton#ProfitCloseButton:hover {
    background-color: #ff5252;
}
"""
