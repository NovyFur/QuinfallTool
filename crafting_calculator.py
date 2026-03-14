"""
Crafting XP Calculator for Quinfall Tool
XP level curve data sourced from: https://qfcodex.com/crafting-planner-desktop.html

v4 — XP formula rewrite based on user spreadsheet:
  XP = Base XP × Buff Bracket × Package Bracket × PVP Bracket × Altar Layer

  Buff Bracket   = 1.0 + Statue(0.40) + Clan(0.60) + Potion(0.10/0.15/0.20) + Clan Altar(1.10)
  Package Bracket = Valuable Package(1.15) × Ordenus Secret(1.10) × Anostias Blessing(1.25)
  PVP Bracket    = 1.25x if in PVP channel, else 1.0x
  Altar Layer    = 3.10x if Personal Altar active, else 1.0x
"""

import math
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QScrollArea, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QListWidget, QListWidgetItem,
    QAbstractItemView, QSplitter, QGridLayout, QLineEdit,
    QDoubleSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# ─────────────────────────────────────────────────────────────────────────────
# XP Level Curve  (Lifeskill / Professions)
# Source: https://qfcodex.com/crafting-planner-desktop.html  →  "Level Curve"
# Index = from-level (0-based), value = XP needed to reach next level
# ─────────────────────────────────────────────────────────────────────────────
PROFESSION_XP_CURVE = [
    20,        # 0 → 1
    40,        # 1 → 2
    60,        # 2 → 3
    120,       # 3 → 4
    160,       # 4 → 5
    200,       # 5 → 6
    260,       # 6 → 7
    320,       # 7 → 8
    380,       # 8 → 9
    460,       # 9 → 10
    540,       # 10 → 11
    930,       # 11 → 12
    1050,      # 12 → 13
    1200,      # 13 → 14
    1350,      # 14 → 15
    1500,      # 15 → 16
    1650,      # 16 → 17
    1800,      # 17 → 18
    1950,      # 18 → 19
    2100,      # 19 → 20
    2340,      # 20 → 21
    2580,      # 21 → 22
    2820,      # 22 → 23
    3060,      # 23 → 24
    3360,      # 24 → 25
    3960,      # 25 → 26
    4620,      # 26 → 27
    5280,      # 27 → 28
    6060,      # 28 → 29
    6900,      # 29 → 30
    8100,      # 30 → 31
    12480,     # 31 → 32
    14160,     # 32 → 33
    15840,     # 33 → 34
    17520,     # 34 → 35
    19200,     # 35 → 36
    20880,     # 36 → 37
    22560,     # 37 → 38
    24240,     # 38 → 39
    25920,     # 39 → 40
    27600,     # 40 → 41
    29280,     # 41 → 42
    30960,     # 42 → 43
    32640,     # 43 → 44
    34320,     # 44 → 45
    36000,     # 45 → 46
    37680,     # 46 → 47
    39360,     # 47 → 48
    41040,     # 48 → 49
    42720,     # 49 → 50
    44400,     # 50 → 51
    156000,    # 51 → 52
    162000,    # 52 → 53
    166000,    # 53 → 54
    174000,    # 54 → 55
    180000,    # 55 → 56
    186000,    # 56 → 57
    192000,    # 57 → 58
    198000,    # 58 → 59
    204000,    # 59 → 60
    210000,    # 60 → 61
    434000,    # 61 → 62
    448000,    # 62 → 63
    462000,    # 63 → 64
    476000,    # 64 → 65
    490000,    # 65 → 66
    504000,    # 66 → 67
    518000,    # 67 → 68
    532000,    # 68 → 69
    546000,    # 69 → 70
    560000,    # 70 → 71
    576000,    # 71 → 72
    592000,    # 72 → 73
    608000,    # 73 → 74
    614000,    # 74 → 75
    630000,    # 75 → 76
    646000,    # 76 → 77
    662000,    # 77 → 78
    678000,    # 78 → 79
    694000,    # 79 → 80
    710000,    # 80 → 81
    730000,    # 81 → 82
    750000,    # 82 → 83
    770000,    # 83 → 84
    790000,    # 84 → 85
    810000,    # 85 → 86
    830000,    # 86 → 87
    850000,    # 87 → 88
    870000,    # 88 → 89
    890000,    # 89 → 90
    910000,    # 90 → 91
    935000,    # 91 → 92
    960000,    # 92 → 93
    985000,    # 93 → 94
    1010000,   # 94 → 95
    1035000,   # 95 → 96
    1060000,   # 96 → 97
    1085000,   # 97 → 98
    1110000,   # 98 → 99
    1135000,   # 99 → 100
]

MAX_LEVEL = 100

# Potion tiers: name → additive bonus to Buff Bracket
POTION_TIERS = {
    "None":              0.00,
    "Common (+10%)":     0.10,
    "Uncommon (+15%)":   0.15,
    "Rare (+20%)":       0.20,
}

# Package bracket components
PACKAGE_VALUABLE   = 1.15   # Valuable Package
PACKAGE_ORDENUS    = 1.10   # Ordenus Secret
PACKAGE_ANOSTIAS   = 1.25   # Anostias Blessing

# Fixed multipliers
PVP_MULT   = 1.25
ALTAR_MULT = 3.10


# ─────────────────────────────────────────────────────────────────────────────
# XP formula helpers
# ─────────────────────────────────────────────────────────────────────────────
def compute_xp_multiplier(statue: bool, clan: bool, potion_bonus: float,
                           clan_altar: bool,
                           pkg_valuable: bool, pkg_ordenus: bool, pkg_anostias: bool,
                           pvp: bool, altar: bool) -> dict:
    """
    Compute the full XP multiplier breakdown.

    Returns a dict with each bracket value and the final combined multiplier.
    """
    # Buff Bracket: additive sum, then used as multiplier
    buff = 1.0
    if statue:     buff += 0.40
    if clan:       buff += 0.60
    buff          += potion_bonus          # 0.0 / 0.10 / 0.15 / 0.20
    if clan_altar: buff += 1.10

    # Package Bracket: multiplicative
    pkg = 1.0
    if pkg_valuable: pkg *= PACKAGE_VALUABLE
    if pkg_ordenus:  pkg *= PACKAGE_ORDENUS
    if pkg_anostias: pkg *= PACKAGE_ANOSTIAS

    pvp_mult   = PVP_MULT   if pvp   else 1.0
    altar_mult = ALTAR_MULT if altar else 1.0

    total = buff * pkg * pvp_mult * altar_mult

    return {
        'buff_bracket':    buff,
        'pkg_bracket':     pkg,
        'pvp_bracket':     pvp_mult,
        'altar_layer':     altar_mult,
        'total_xp_mult':   total,
    }


def xp_needed_between(from_level: int, to_level: int) -> int:
    if from_level >= to_level:
        return 0
    total = 0
    for lvl in range(from_level, min(to_level, MAX_LEVEL)):
        if lvl < len(PROFESSION_XP_CURVE):
            total += PROFESSION_XP_CURVE[lvl]
    return total


def parse_xp(xp_str: str) -> int:
    try:
        return int(re.sub(r'[^\d]', '', str(xp_str)))
    except (ValueError, TypeError):
        return 0


def parse_craft_time_seconds(time_str: str) -> float:
    try:
        return float(re.sub(r'[^\d.]', '', str(time_str)))
    except (ValueError, TypeError):
        return 0.0


def format_time_hms(total_seconds: float) -> str:
    total_seconds = int(total_seconds)
    if total_seconds <= 0:
        return "0s"
    days    = total_seconds // 86400
    hours   = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    secs    = total_seconds % 60
    parts = []
    if days:    parts.append(f"{days}d")
    if hours:   parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if secs:    parts.append(f"{secs}s")
    return " ".join(parts) if parts else "0s"


def effective_time_reduction(wb_time_pct: float, pet_pct: float,
                              level_pct: float, potion_pct: float) -> float:
    """Return time multiplier (0 < mult ≤ 1). All reductions are multiplicative."""
    wb  = wb_time_pct / 100.0
    pet = pet_pct     / 100.0
    lvl = level_pct   / 100.0
    pot = potion_pct  / 100.0
    return max(0.01, (1.0 - wb) * (1.0 - pet) * (1.0 - lvl) * (1.0 - pot))


def effective_double_chance(wb_double_pct: float, pet_pct: float,
                             level_pct: float, potion_pct: float) -> float:
    """Return total 2x craft probability (0–1). Multiplicative stacking."""
    wb  = wb_double_pct / 100.0
    pet = pet_pct       / 100.0
    lvl = level_pct     / 100.0
    pot = potion_pct    / 100.0
    return min(1.0, max(0.0, 1.0 - (1.0 - wb) * (1.0 - pet) * (1.0 - lvl) * (1.0 - pot)))


def crafts_needed_for_xp(xp_target: float, xp_per_craft_effective: float,
                          double_chance: float) -> dict:
    """
    Returns min / expected / max craft counts.

    E[XP per craft] = xp_eff * (1 + p)
    Min = all 2x procs, Max = no 2x procs
    """
    if xp_per_craft_effective <= 0:
        return {'min': 0, 'expected': 0, 'max': 0}

    xp_2x = xp_per_craft_effective * 2.0
    p     = double_chance

    min_c = math.ceil(xp_target / xp_2x) if p > 0 else math.ceil(xp_target / xp_per_craft_effective)
    exp_c = math.ceil(xp_target / (xp_per_craft_effective * (1.0 + p)))
    max_c = math.ceil(xp_target / xp_per_craft_effective)

    return {
        'min':      max(1, min_c),
        'expected': max(1, exp_c),
        'max':      max(1, max_c),
    }


def combine_workbench_bonuses(t1_qty: int, t2_qty: int, t3_qty: int,
                               pet_time: float, lvl_time: float, pot_time: float,
                               pet_double: float, lvl_double: float, pot_double: float) -> dict:
    total = t1_qty + t2_qty + t3_qty
    if total == 0:
        total = 1

    wb_time_pct   = (t2_qty * 20.0 + t3_qty * 40.0) / total
    wb_double_pct = (t2_qty *  5.0 + t3_qty * 10.0) / total

    time_mult     = effective_time_reduction(wb_time_pct, pet_time, lvl_time, pot_time)
    double_chance = effective_double_chance(wb_double_pct, pet_double, lvl_double, pot_double)

    return {
        'total_stations': total,
        'wb_time_pct':    wb_time_pct,
        'wb_double_pct':  wb_double_pct,
        'time_mult':      time_mult,
        'double_chance':  double_chance,
        't1': t1_qty, 't2': t2_qty, 't3': t3_qty,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Shared widget helpers
# ─────────────────────────────────────────────────────────────────────────────
_SPINBOX_SS = """
    QDoubleSpinBox, QSpinBox {
        background: #121212; color: #fff;
        border: 1px solid #555; border-radius: 4px; padding: 3px;
    }
"""

_CHECK_SS = """
    QCheckBox {
        color: #fff;
        font-size: 12px;
        spacing: 6px;
    }
    QCheckBox::indicator {
        width: 16px; height: 16px;
        border: 1px solid #555;
        border-radius: 3px;
        background: #1a1a1a;
    }
    QCheckBox::indicator:checked {
        background: #00d4ff;
        border: 1px solid #00d4ff;
    }
    QCheckBox::indicator:hover {
        border: 1px solid #00d4ff;
    }
"""

_COMBO_SS = """
    QComboBox {
        background: #ffffff; color: #000000;
        border: 1px solid #555; border-radius: 4px; padding: 4px;
        font-weight: bold;
    }
    QComboBox QAbstractItemView {
        background: #ffffff; color: #000000;
        selection-background-color: #00d4ff;
        selection-color: #000;
    }
"""

_PANEL_SS = lambda border: f"""
    QFrame {{
        background: rgba(22,22,30,230);
        border-radius: 8px;
        border: 1px solid {border};
    }}
"""


def _pct_spin(tip: str = "") -> QDoubleSpinBox:
    sb = QDoubleSpinBox()
    sb.setRange(0.0, 999.0)
    sb.setDecimals(1)
    sb.setSuffix(" %")
    sb.setValue(0.0)
    sb.setFixedWidth(86)
    if tip:
        sb.setToolTip(tip)
    sb.setStyleSheet(_SPINBOX_SS)
    return sb


def _int_spin(lo: int, hi: int, val: int = 0, tip: str = "") -> QSpinBox:
    sb = QSpinBox()
    sb.setRange(lo, hi)
    sb.setValue(val)
    sb.setFixedWidth(70)
    if tip:
        sb.setToolTip(tip)
    sb.setStyleSheet(_SPINBOX_SS)
    return sb


def _hdr(text: str, color: str = "#00d4ff") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{color}; font-weight:bold; font-size:12px;")
    return lbl


def _sub(text: str, color: str = "#aaa") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{color}; font-size:12px;")
    return lbl


def _chk(text: str, tip: str = "") -> QCheckBox:
    cb = QCheckBox(text)
    cb.setStyleSheet(_CHECK_SS)
    if tip:
        cb.setToolTip(tip)
    return cb


# ─────────────────────────────────────────────────────────────────────────────
# Crafting Item Row
# ─────────────────────────────────────────────────────────────────────────────
class CraftingItemRow(QFrame):
    def __init__(self, recipe: dict, parent=None):
        super().__init__(parent)
        self.recipe = recipe
        self.setObjectName("CraftItemRow")
        self.setStyleSheet("""
            QFrame#CraftItemRow {
                background: rgba(30,30,30,220);
                border: 1px solid #444;
                border-radius: 6px;
                margin: 1px;
            }
            QLabel { color: #fff; font-size: 12px; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        name = recipe.get('Name', 'Unknown')
        xp   = parse_xp(recipe.get('XP Reward', '0 XP'))
        secs = parse_craft_time_seconds(recipe.get('Craft Time', '0 seconds'))

        name_lbl = QLabel(f"<b>{name}</b>")
        name_lbl.setMinimumWidth(160)
        name_lbl.setWordWrap(True)

        xp_lbl   = QLabel(f"<span style='color:#00d4ff;'>{xp} XP</span>")
        xp_lbl.setFixedWidth(65)
        time_lbl = QLabel(f"<span style='color:#aaa;'>{format_time_hms(secs)}</span>")
        time_lbl.setFixedWidth(58)

        rm_btn = QPushButton("✕")
        rm_btn.setFixedSize(26, 26)
        rm_btn.setStyleSheet("""
            QPushButton { background:#c62828; border:none; border-radius:4px;
                          color:white; font-weight:bold; font-size:12px; }
            QPushButton:hover { background:#ff5252; }
        """)
        rm_btn.clicked.connect(lambda: self.setParent(None))

        layout.addWidget(name_lbl, 1)
        layout.addWidget(xp_lbl)
        layout.addWidget(time_lbl)
        layout.addWidget(rm_btn)


# ─────────────────────────────────────────────────────────────────────────────
# Main Calculator Tab
# ─────────────────────────────────────────────────────────────────────────────
class CraftingCalculatorTab(QWidget):
    def __init__(self, recipes: list, parent=None):
        super().__init__(parent)
        self.all_recipes = recipes
        self._last_items: list = []
        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(5)

        # ═══════════════════════════════════════════════════════════════════
        # ROW 1 — Profession / Levels
        # ═══════════════════════════════════════════════════════════════════
        row1 = QFrame()
        row1.setStyleSheet(_PANEL_SS("#333"))
        r1l = QHBoxLayout(row1)
        r1l.setContentsMargins(10, 6, 10, 6)
        r1l.setSpacing(10)

        r1l.addWidget(_hdr("Profession:"))
        self.prof_combo = QComboBox()
        self.prof_combo.setStyleSheet(_COMBO_SS)
        self.prof_combo.setMinimumWidth(160)
        self.prof_combo.addItems([
            "Cooking", "Alchemy", "BlackSmith", "Tailor", "Carpenter",
            "Engineering", "Jewel Crafting", "Woodcrafter", "Smelting",
            "Leatherworker", "Essence Refining", "Gem Cutting",
            "Thread Viewer", "Construction"
        ])
        self.prof_combo.currentTextChanged.connect(self._refresh_recipe_list)
        r1l.addWidget(self.prof_combo)

        r1l.addWidget(_hdr("Current Level:"))
        self.current_lvl = _int_spin(0, 99, 1)
        r1l.addWidget(self.current_lvl)

        r1l.addWidget(_hdr("Target Level:"))
        self.target_lvl = _int_spin(1, 100, 10)
        r1l.addWidget(self.target_lvl)

        self.xp_needed_lbl = QLabel("XP Needed: —")
        self.xp_needed_lbl.setStyleSheet("color:#00d4ff; font-weight:bold; font-size:13px;")
        r1l.addWidget(self.xp_needed_lbl)
        r1l.addStretch()

        self.current_lvl.valueChanged.connect(self._update_xp_label)
        self.target_lvl.valueChanged.connect(self._update_xp_label)
        self._update_xp_label()
        root.addWidget(row1)

        # ═══════════════════════════════════════════════════════════════════
        # ROW 2 — Workbench Tiers
        # ═══════════════════════════════════════════════════════════════════
        row2 = QFrame()
        row2.setStyleSheet(_PANEL_SS("#4a3a1a"))
        r2l = QHBoxLayout(row2)
        r2l.setContentsMargins(10, 6, 10, 6)
        r2l.setSpacing(14)

        r2l.addWidget(_hdr("🏭 Workbench Stations:", "#ffd700"))

        for tier, color, border, info in [
            (1, "rgba(40,40,40,180)", "#555",    "No bonus"),
            (2, "rgba(30,50,30,180)", "#2e7d32", "−20% time | +5% 2x"),
            (3, "rgba(30,30,60,180)", "#1565c0", "−40% time | +10% 2x"),
        ]:
            f = QFrame()
            f.setStyleSheet(f"QFrame {{ background:{color}; border-radius:6px; border:1px solid {border}; }}")
            fl = QHBoxLayout(f); fl.setContentsMargins(8,4,8,4); fl.setSpacing(6)
            fl.addWidget(_sub(f"Tier {tier}:"))
            sp = _int_spin(0, 999, 0, f"Number of Tier {tier} workbenches")
            setattr(self, f"wb_t{tier}", sp)
            fl.addWidget(sp)
            fl.addWidget(QLabel(f"<span style='color:#888; font-size:10px;'>{info}</span>"))
            r2l.addWidget(f)

        r2l.addStretch()
        self.stations_lbl = QLabel("Total Stations: 0")
        self.stations_lbl.setStyleSheet("color:#ffd700; font-weight:bold; font-size:12px;")
        r2l.addWidget(self.stations_lbl)

        for sp in (self.wb_t1, self.wb_t2, self.wb_t3):
            sp.valueChanged.connect(self._update_stations_label)
        self._update_stations_label()
        root.addWidget(row2)

        # ═══════════════════════════════════════════════════════════════════
        # ROW 3 — Craft Time / 2x Chance bonuses (compact) + XP Buffs (right)
        # ═══════════════════════════════════════════════════════════════════
        row3 = QHBoxLayout()
        row3.setSpacing(5)

        # — Left column: Time Reduction + 2x Chance stacked vertically, compact —
        left_col = QVBoxLayout()
        left_col.setSpacing(4)

        # Time Reduction — compact horizontal row
        tf = QFrame(); tf.setStyleSheet(_PANEL_SS("#1a3a6c"))
        tfl = QHBoxLayout(tf); tfl.setContentsMargins(8,5,8,5); tfl.setSpacing(8)
        tfl.addWidget(_hdr("⏱ Time Reduction"))
        tfl.addWidget(_sub("Pet:"))
        self.time_pet = _pct_spin("Pet time reduction")
        self.time_pet.setFixedWidth(78)
        tfl.addWidget(self.time_pet)
        tfl.addWidget(_sub("Level:"))
        self.time_level = _pct_spin("Level time reduction")
        self.time_level.setFixedWidth(78)
        tfl.addWidget(self.time_level)
        tfl.addWidget(_sub("Potion:"))
        self.time_potion = _pct_spin("Potion time reduction")
        self.time_potion.setFixedWidth(78)
        tfl.addWidget(self.time_potion)
        left_col.addWidget(tf)

        # 2x Chance — compact horizontal row
        df = QFrame(); df.setStyleSheet(_PANEL_SS("#1a6c1a"))
        dfl = QHBoxLayout(df); dfl.setContentsMargins(8,5,8,5); dfl.setSpacing(8)
        dfl.addWidget(_hdr("🎲 2x Craft Chance", "#81c784"))
        dfl.addWidget(_sub("Pet:"))
        self.double_pet = _pct_spin("Pet 2x chance")
        self.double_pet.setFixedWidth(78)
        dfl.addWidget(self.double_pet)
        dfl.addWidget(_sub("Level:"))
        self.double_level = _pct_spin("Level 2x chance")
        self.double_level.setFixedWidth(78)
        dfl.addWidget(self.double_level)
        dfl.addWidget(_sub("Potion:"))
        self.double_potion = _pct_spin("Potion 2x chance")
        self.double_potion.setFixedWidth(78)
        dfl.addWidget(self.double_potion)
        left_col.addWidget(df)
        left_col.addStretch()

        left_widget = QWidget(); left_widget.setStyleSheet("background:transparent;")
        left_widget.setLayout(left_col)

        # ── XP Buffs — compact two-row horizontal layout ─────────────────
        xf = QFrame(); xf.setStyleSheet(_PANEL_SS("#6c3a1a"))
        xfl = QVBoxLayout(xf); xfl.setContentsMargins(8,5,8,5); xfl.setSpacing(3)

        # Row A: label + all checkboxes
        xrow_a = QHBoxLayout(); xrow_a.setSpacing(10)
        xrow_a.addWidget(_hdr("✨ XP Buffs", "#ffb74d"))
        self.chk_statue     = _chk("Statue (+40%)",          "XP Statue buff")
        self.chk_clan       = _chk("Clan (+60%)",            "Clan XP buff")
        self.chk_clan_altar = _chk("Clan Altar (+110%)",     "Clan Altar XP buff")
        self.chk_valuable   = _chk("Valuable Pkg (+15%)",    "Valuable Package ×1.15")
        self.chk_ordenus    = _chk("Ordenus Secret (+10%)",  "Ordenus Secret ×1.10")
        self.chk_anostias   = _chk("Anostias Blessing (+25%)", "Anostias Blessing ×1.25")
        self.chk_pvp        = _chk("PVP Channel (+25%)",     "In a PVP channel ×1.25")
        self.chk_altar      = _chk("Personal Altar (+210%)", "Personal Altar ×3.10")
        for chk in (self.chk_statue, self.chk_clan, self.chk_clan_altar,
                    self.chk_valuable, self.chk_ordenus, self.chk_anostias,
                    self.chk_pvp, self.chk_altar):
            xrow_a.addWidget(chk)
        xfl.addLayout(xrow_a)

        # Row B: potion dropdown + live multiplier preview
        xrow_b = QHBoxLayout(); xrow_b.setSpacing(8)
        xrow_b.addWidget(_sub("Potion:"))
        self.potion_combo = QComboBox()
        self.potion_combo.setStyleSheet(_COMBO_SS)
        self.potion_combo.setMinimumWidth(160)
        self.potion_combo.addItems(list(POTION_TIERS.keys()))
        xrow_b.addWidget(self.potion_combo)
        self.xp_mult_preview = QLabel("")
        self.xp_mult_preview.setStyleSheet("color:#ffd700; font-weight:bold; font-size:11px;")
        xrow_b.addWidget(self.xp_mult_preview)
        xrow_b.addStretch()
        xfl.addLayout(xrow_b)

        # Connect all controls to preview update
        for chk in (self.chk_statue, self.chk_clan, self.chk_clan_altar,
                    self.chk_valuable, self.chk_ordenus, self.chk_anostias,
                    self.chk_pvp, self.chk_altar):
            chk.stateChanged.connect(self._update_xp_preview)
        self.potion_combo.currentIndexChanged.connect(self._update_xp_preview)
        self._update_xp_preview()

        # Stack all three panels (Time / 2x / XP) vertically on the left
        left_col.addWidget(xf)

        row3.addWidget(left_widget, 1)
        root.addLayout(row3, 0)

        # ═══════════════════════════════════════════════════════════════════
        # ROW 4 — Recipe picker (left) + Selected items (right)
        # ═══════════════════════════════════════════════════════════════════
        mid = QSplitter(Qt.Orientation.Horizontal)
        mid.setStyleSheet("QSplitter::handle { background:#444; width:4px; }")

        # Left — recipe list
        lf = QFrame(); lf.setStyleSheet(_PANEL_SS("#333"))
        ll = QVBoxLayout(lf); ll.setContentsMargins(7,7,7,7); ll.setSpacing(5)
        ll.addWidget(_hdr("Available Recipes"))
        self.recipe_search = QLineEdit()
        self.recipe_search.setPlaceholderText("Filter recipes...")
        self.recipe_search.setStyleSheet(
            "QLineEdit { background:#121212; color:#fff; border:1px solid #555; border-radius:4px; padding:4px; }")
        self.recipe_search.textChanged.connect(self._refresh_recipe_list)
        ll.addWidget(self.recipe_search)
        self.recipe_list = QListWidget()
        self.recipe_list.setStyleSheet("""
            QListWidget { background:#0d0d0d; color:#fff; border:1px solid #333; border-radius:5px; }
            QListWidget::item { padding:4px 6px; }
            QListWidget::item:selected { background:#1a3a5c; color:#00d4ff; }
            QListWidget::item:hover { background:#1e1e1e; }
        """)
        self.recipe_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.recipe_list.itemDoubleClicked.connect(self._add_selected_item)
        ll.addWidget(self.recipe_list, 1)
        add_btn = QPushButton("+ Add Selected Item(s)")
        add_btn.setObjectName("AddButton")
        add_btn.setMinimumHeight(32)
        add_btn.clicked.connect(self._add_selected_item)
        ll.addWidget(add_btn)
        mid.addWidget(lf)

        # Right — selected items
        rf = QFrame(); rf.setStyleSheet(_PANEL_SS("#333"))
        rl = QVBoxLayout(rf); rl.setContentsMargins(7,7,7,7); rl.setSpacing(5)
        sel_hdr = QHBoxLayout()
        sel_hdr.addWidget(_hdr("Selected Items to Craft"))
        sel_hdr.addStretch()
        clr_btn = QPushButton("Clear All")
        clr_btn.setFixedHeight(26)
        clr_btn.setStyleSheet("""
            QPushButton { background:#7b1fa2; border:none; border-radius:4px;
                          color:white; font-size:11px; font-weight:bold; padding:3px 8px; }
            QPushButton:hover { background:#9c27b0; }
        """)
        clr_btn.clicked.connect(self._clear_items)
        sel_hdr.addWidget(clr_btn)
        rl.addLayout(sel_hdr)

        ch = QFrame(); ch.setStyleSheet("QFrame{background:transparent;border:none;}")
        chl = QHBoxLayout(ch); chl.setContentsMargins(8,0,8,0)
        for txt, w in [("Item Name", None), ("Base XP", 65), ("Base Time", 58), ("", 26)]:
            lb = QLabel(txt); lb.setStyleSheet("color:#666; font-size:10px;")
            if w: lb.setFixedWidth(w); chl.addWidget(lb)
            else: chl.addWidget(lb, 1)
        rl.addWidget(ch)

        self.items_scroll = QScrollArea()
        self.items_scroll.setWidgetResizable(True)
        self.items_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.items_cont = QWidget(); self.items_cont.setStyleSheet("background:transparent;")
        self.items_vbox = QVBoxLayout(self.items_cont)
        self.items_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.items_vbox.setSpacing(3)
        self.items_scroll.setWidget(self.items_cont)
        rl.addWidget(self.items_scroll, 1)

        self.no_items_lbl = QLabel("Double-click a recipe or click '+ Add' to add items")
        self.no_items_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_items_lbl.setStyleSheet("color:#555; font-size:12px; font-style:italic;")
        self.items_vbox.addWidget(self.no_items_lbl)
        mid.addWidget(rf)

        mid.setSizes([260, 380])
        root.addWidget(mid, 3)

        # ═══════════════════════════════════════════════════════════════════
        # ROW 5 — Calculate button
        # ═══════════════════════════════════════════════════════════════════
        calc_btn = QPushButton("⚙  Calculate")
        calc_btn.setMinimumHeight(38)
        calc_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                              stop:0 #0d47a1, stop:1 #1565c0);
                          color:white; border:none; border-radius:8px;
                          font-size:14px; font-weight:bold; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                              stop:0 #1565c0, stop:1 #1976d2); }
        """)
        calc_btn.clicked.connect(self._calculate)
        root.addWidget(calc_btn)

        # ═══════════════════════════════════════════════════════════════════
        # ROW 6 — Results (scrollable)
        # ═══════════════════════════════════════════════════════════════════
        res_scroll = QScrollArea()
        res_scroll.setWidgetResizable(True)
        res_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.results_widget = QWidget(); self.results_widget.setStyleSheet("background:transparent;")
        self.results_vbox = QVBoxLayout(self.results_widget)
        self.results_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_vbox.setSpacing(6)
        res_scroll.setWidget(self.results_widget)
        root.addWidget(res_scroll, 5)

        self._refresh_recipe_list()

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _update_xp_label(self):
        cur, tgt = self.current_lvl.value(), self.target_lvl.value()
        if tgt <= cur:
            self.xp_needed_lbl.setText("⚠ Target must be > Current")
            self.xp_needed_lbl.setStyleSheet("color:#ff5252; font-weight:bold; font-size:13px;")
        else:
            self.xp_needed_lbl.setText(f"XP Needed: {xp_needed_between(cur, tgt):,}")
            self.xp_needed_lbl.setStyleSheet("color:#00d4ff; font-weight:bold; font-size:13px;")

    def _update_stations_label(self):
        total = self.wb_t1.value() + self.wb_t2.value() + self.wb_t3.value()
        self.stations_lbl.setText(f"Total Stations: {total}")

    def _update_xp_preview(self):
        """Update the live XP multiplier preview label."""
        xp_info = self._read_xp_buffs()
        m = xp_info['total_xp_mult']
        b = xp_info['buff_bracket']
        p = xp_info['pkg_bracket']
        pvp = xp_info['pvp_bracket']
        alt = xp_info['altar_layer']
        self.xp_mult_preview.setText(
            f"Effective XP: ×{m:.3f}  "
            f"(Buff {b:.2f} × Pkg {p:.3f} × PVP {pvp:.2f} × Altar {alt:.2f})"
        )

    def _refresh_recipe_list(self):
        prof  = self.prof_combo.currentText()
        query = self.recipe_search.text().lower()
        self.recipe_list.clear()
        for r in self.all_recipes:
            if r.get('Profession', '') != prof:
                continue
            name = r.get('Name', '')
            if query and query not in name.lower():
                continue
            xp   = parse_xp(r.get('XP Reward', '0 XP'))
            secs = parse_craft_time_seconds(r.get('Craft Time', '0 seconds'))
            li   = QListWidgetItem(f"{name}  [{xp} XP | {format_time_hms(secs)}]")
            li.setData(Qt.ItemDataRole.UserRole, r)
            self.recipe_list.addItem(li)

    def _add_selected_item(self, _=None):
        selected = self.recipe_list.selectedItems()
        if not selected:
            return
        if self.no_items_lbl.isVisible():
            self.no_items_lbl.hide()
        for li in selected:
            self.items_vbox.addWidget(CraftingItemRow(li.data(Qt.ItemDataRole.UserRole)))

    def _clear_items(self):
        for i in reversed(range(self.items_vbox.count())):
            w = self.items_vbox.itemAt(i).widget()
            if w and isinstance(w, CraftingItemRow):
                w.setParent(None)
        self.no_items_lbl.show()
        self._clear_results()

    def _clear_results(self):
        for i in reversed(range(self.results_vbox.count())):
            w = self.results_vbox.itemAt(i).widget()
            if w:
                w.setParent(None)
        self._last_items = []

    def _get_active_rows(self) -> list:
        return [
            self.items_vbox.itemAt(i).widget()
            for i in range(self.items_vbox.count())
            if isinstance(self.items_vbox.itemAt(i).widget(), CraftingItemRow)
        ]

    def _read_xp_buffs(self) -> dict:
        """Read all XP buff checkboxes/dropdown and return the multiplier breakdown."""
        potion_bonus = POTION_TIERS.get(self.potion_combo.currentText(), 0.0)
        return compute_xp_multiplier(
            statue      = self.chk_statue.isChecked(),
            clan        = self.chk_clan.isChecked(),
            potion_bonus= potion_bonus,
            clan_altar  = self.chk_clan_altar.isChecked(),
            pkg_valuable= self.chk_valuable.isChecked(),
            pkg_ordenus = self.chk_ordenus.isChecked(),
            pkg_anostias= self.chk_anostias.isChecked(),
            pvp         = self.chk_pvp.isChecked(),
            altar       = self.chk_altar.isChecked(),
        )

    def _read_bonuses(self) -> dict:
        t1, t2, t3 = self.wb_t1.value(), self.wb_t2.value(), self.wb_t3.value()
        bonuses = combine_workbench_bonuses(
            t1, t2, t3,
            self.time_pet.value(), self.time_level.value(), self.time_potion.value(),
            self.double_pet.value(), self.double_level.value(), self.double_potion.value()
        )
        xp_info = self._read_xp_buffs()
        bonuses['xp_mult']      = xp_info['total_xp_mult']
        bonuses['xp_breakdown'] = xp_info
        return bonuses

    # ── Calculation ──────────────────────────────────────────────────────────
    def _calculate(self):
        self._clear_results()
        cur, tgt = self.current_lvl.value(), self.target_lvl.value()
        if tgt <= cur:
            self._show_error("Target level must be greater than current level.")
            return
        rows = self._get_active_rows()
        if not rows:
            self._show_error("Please add at least one item to craft.")
            return

        bonuses         = self._read_bonuses()
        total_xp_needed = xp_needed_between(cur, tgt)

        items = []
        for row in rows:
            r        = row.recipe
            xp_base  = parse_xp(r.get('XP Reward', '0 XP'))
            secs_raw = parse_craft_time_seconds(r.get('Craft Time', '0 seconds'))
            stations = bonuses['total_stations']
            secs_eff = (secs_raw * bonuses['time_mult']) / max(1, stations)
            # Apply the full XP formula: Base × all brackets
            xp_eff   = xp_base * bonuses['xp_mult']
            items.append({
                'name':      r.get('Name', 'Unknown'),
                'xp_base':   xp_base,
                'secs_raw':  secs_raw,
                'xp_eff':    xp_eff,
                'secs_eff':  secs_eff,
                'materials': r.get('materials', []),
            })

        # Distribute XP by expected XP/hr weight
        def exp_xph(it):
            if it['secs_eff'] > 0:
                return it['xp_eff'] * (1.0 + bonuses['double_chance']) / it['secs_eff'] * 3600
            return 0.0

        rates      = [exp_xph(it) for it in items]
        total_rate = sum(rates)
        weights    = [r / total_rate for r in rates] if total_rate > 0 else [1.0 / len(items)] * len(items)

        for i, item in enumerate(items):
            xp_share = total_xp_needed * weights[i]
            counts   = crafts_needed_for_xp(xp_share, item['xp_eff'], bonuses['double_chance'])
            item['qty_min']      = counts['min']
            item['qty_expected'] = counts['expected']
            item['qty_max']      = counts['max']
            item['xp_exp']       = counts['expected'] * item['xp_eff'] * (1.0 + bonuses['double_chance'])
            item['time_min']     = counts['min']      * item['secs_eff']
            item['time_exp']     = counts['expected'] * item['secs_eff']
            item['time_max']     = counts['max']      * item['secs_eff']

        self._last_items = items

        grand_qty_min  = sum(it['qty_min']     for it in items)
        grand_qty_exp  = sum(it['qty_expected'] for it in items)
        grand_qty_max  = sum(it['qty_max']      for it in items)
        grand_time_min = sum(it['time_min']     for it in items)
        grand_time_exp = sum(it['time_exp']     for it in items)
        grand_time_max = sum(it['time_max']     for it in items)
        grand_xp_exp   = sum(it['xp_exp']       for it in items)

        self.results_vbox.addWidget(self._make_bonus_card(bonuses))
        self.results_vbox.addWidget(
            self._make_summary_card(cur, tgt, total_xp_needed, bonuses,
                                    grand_qty_min, grand_qty_exp, grand_qty_max,
                                    grand_time_min, grand_time_exp, grand_time_max,
                                    grand_xp_exp)
        )
        self.results_vbox.addWidget(self._make_item_table(items, bonuses))
        self.results_vbox.addWidget(self._make_materials_card(items))

    def _show_error(self, msg: str):
        lbl = QLabel(f"<span style='color:#ff5252;'>⚠ {msg}</span>")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size:13px; padding:8px;")
        self.results_vbox.addWidget(lbl)

    # ── Result card builders ─────────────────────────────────────────────────
    def _make_bonus_card(self, b: dict) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:rgba(30,20,50,200);border:1px solid #555;border-radius:8px;} QLabel{color:#fff;}")
        lay = QVBoxLayout(frame); lay.setContentsMargins(10,7,10,7); lay.setSpacing(3)
        lay.addWidget(QLabel("<b style='color:#c084fc;font-size:12px;'>⚙ Active Bonuses Applied</b>"))
        grid = QGridLayout(); grid.setSpacing(5)

        def row(r, lbl, val, col="#fff"):
            grid.addWidget(QLabel(f"<span style='color:#aaa;font-size:11px;'>{lbl}</span>"), r, 0)
            grid.addWidget(QLabel(f"<b style='color:{col};font-size:11px;'>{val}</b>"), r, 1)

        xb = b['xp_breakdown']
        t_pct = (1.0 - b['time_mult']) * 100.0
        d_pct = b['double_chance'] * 100.0
        wb_str = f"T1×{b['t1']}  T2×{b['t2']}  T3×{b['t3']}  ({b['total_stations']} total)"

        row(0, "Workbenches:",           wb_str,                                      "#ffd700")
        row(1, "Time Reduction:",        f"{t_pct:.1f}%  (×{b['time_mult']:.3f})",   "#4fc3f7")
        row(2, "2x Craft Chance:",       f"{d_pct:.2f}%",                             "#81c784")
        row(3, "Buff Bracket:",          f"×{xb['buff_bracket']:.3f}",               "#ffb74d")
        row(4, "Package Bracket:",       f"×{xb['pkg_bracket']:.3f}",                "#ffb74d")
        row(5, "PVP Bracket:",           f"×{xb['pvp_bracket']:.2f}",                "#ffb74d")
        row(6, "Altar Layer:",           f"×{xb['altar_layer']:.2f}",                "#ffb74d")
        row(7, "Total XP Multiplier:",   f"×{xb['total_xp_mult']:.4f}",              "#ffd700")
        lay.addLayout(grid)
        return frame

    def _make_summary_card(self, cur, tgt, xp_needed, b,
                           qty_min, qty_exp, qty_max,
                           t_min, t_exp, t_max, xp_exp) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:rgba(13,71,161,35);border:1px solid #1565c0;border-radius:8px;} QLabel{color:#fff;}")
        lay = QVBoxLayout(frame); lay.setContentsMargins(10,8,10,8); lay.setSpacing(4)
        lay.addWidget(QLabel(f"<b style='color:#00d4ff;font-size:14px;'>📊 Summary — Level {cur} → {tgt}</b>"))
        grid = QGridLayout(); grid.setSpacing(6)

        def row(r, lbl, val, col="#fff"):
            grid.addWidget(QLabel(f"<b style='color:#aaa;font-size:12px;'>{lbl}</b>"), r, 0)
            grid.addWidget(QLabel(f"<span style='color:{col};font-size:12px;'>{val}</span>"), r, 1)

        row(0, "XP Required:", f"{xp_needed:,} XP", "#00d4ff")
        d_pct = b['double_chance'] * 100.0
        row(1, "Expected XP from Crafts:",
            f"{xp_exp:,.0f} XP" + (f"  (incl. {d_pct:.1f}% 2x)" if d_pct > 0 else ""),
            "#4caf50" if xp_exp >= xp_needed else "#ff9800")

        if qty_min != qty_max:
            row(2, "Crafts (Min / Exp / Max):", f"{qty_min:,}  /  {qty_exp:,}  /  {qty_max:,}", "#fff")
            row(3, "Time   (Min / Exp / Max):",
                f"{format_time_hms(t_min)}  /  {format_time_hms(t_exp)}  /  {format_time_hms(t_max)}", "#ffd700")
        else:
            row(2, "Crafts Needed:", f"{qty_exp:,}", "#fff")
            row(3, "Total Craft Time:", format_time_hms(t_exp), "#ffd700")

        if xp_exp >= xp_needed:
            status = QLabel("<b style='color:#4caf50;'>✔ Sufficient XP to reach target level</b>")
        else:
            status = QLabel(
                f"<b style='color:#ff9800;'>⚠ Expected XP deficit: {xp_needed - xp_exp:,.0f} XP short</b>")
        grid.addWidget(status, 4, 0, 1, 2)
        lay.addLayout(grid)
        return frame

    def _make_item_table(self, items: list, b: dict) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:rgba(20,20,20,200);border:1px solid #333;border-radius:8px;} "
            "QLabel{color:#00d4ff;font-weight:bold;font-size:13px;}")
        lay = QVBoxLayout(frame); lay.setContentsMargins(10,8,10,8); lay.setSpacing(5)
        lay.addWidget(QLabel("🔨 Crafting Breakdown"))

        has_range = b['double_chance'] > 0
        if has_range:
            hdrs = ["Item", "Base XP", "Eff. XP/Craft", "Time/Craft",
                    "Qty Min", "Qty Exp", "Qty Max",
                    "Time Min", "Time Exp", "Time Max"]
        else:
            hdrs = ["Item", "Base XP", "Eff. XP/Craft", "Time/Craft", "Qty", "Total XP", "Total Time"]

        table = QTableWidget(len(items), len(hdrs))
        table.setHorizontalHeaderLabels(hdrs)
        table.setStyleSheet("""
            QTableWidget { background:#0d0d0d; color:#fff; border:none; gridline-color:#333; font-size:12px; }
            QHeaderView::section { background:#1a1a1a; color:#00d4ff; border:1px solid #333;
                                   padding:4px; font-weight:bold; font-size:11px; }
            QTableWidget::item { padding:3px 5px; }
            QTableWidget::item:selected { background:#1a3a5c; }
            QTableWidget { alternate-background-color:#111; }
        """)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, len(hdrs)):
            table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)

        def cell(txt, col="#fff", align=Qt.AlignmentFlag.AlignCenter):
            it = QTableWidgetItem(txt)
            it.setForeground(QColor(col))
            it.setTextAlignment(align)
            return it

        for ri, item in enumerate(items):
            table.setItem(ri, 0, cell(item['name'], "#fff",
                                      Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
            table.setItem(ri, 1, cell(f"{item['xp_base']:,}", "#aaa"))
            table.setItem(ri, 2, cell(f"{item['xp_eff']:,.2f}", "#00d4ff"))
            table.setItem(ri, 3, cell(format_time_hms(item['secs_eff']), "#aaa"))
            if has_range:
                table.setItem(ri, 4, cell(f"{item['qty_min']:,}", "#81c784"))
                table.setItem(ri, 5, cell(f"{item['qty_expected']:,}", "#4caf50"))
                table.setItem(ri, 6, cell(f"{item['qty_max']:,}", "#ff9800"))
                table.setItem(ri, 7, cell(format_time_hms(item['time_min']), "#81c784"))
                table.setItem(ri, 8, cell(format_time_hms(item['time_exp']), "#ffd700"))
                table.setItem(ri, 9, cell(format_time_hms(item['time_max']), "#ff9800"))
            else:
                table.setItem(ri, 4, cell(f"{item['qty_expected']:,}", "#4caf50"))
                table.setItem(ri, 5, cell(f"{item['xp_exp']:,.0f}", "#4caf50"))
                table.setItem(ri, 6, cell(format_time_hms(item['time_exp']), "#ffd700"))

        row_h = 26
        table.setFixedHeight(table.horizontalHeader().height() + len(items) * row_h + 4)
        lay.addWidget(table)

        if has_range:
            lay.addWidget(QLabel(
                "<span style='color:#888;font-size:10px;'>"
                "Min = best case (all 2x) &nbsp;|&nbsp; Exp = expected average &nbsp;|&nbsp; Max = worst case (no 2x)"
                "</span>"
            ))
        return frame

    def _make_materials_card(self, items: list) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:rgba(20,20,20,200);border:1px solid #333;border-radius:8px;}")
        lay = QVBoxLayout(frame); lay.setContentsMargins(10,8,10,8); lay.setSpacing(6)

        hdr_row = QHBoxLayout()
        hdr_row.addWidget(QLabel("<b style='color:#ffd700;font-size:13px;'>📦 Total Materials Required</b>"))
        hdr_row.addStretch()
        hdr_row.addWidget(QLabel("<span style='color:#aaa;font-size:11px;'>Show quantities for:</span>"))
        self.mat_mode_combo = QComboBox()
        self.mat_mode_combo.setStyleSheet(_COMBO_SS)
        self.mat_mode_combo.setFixedWidth(150)
        self.mat_mode_combo.addItems(["Expected (Avg)", "Minimum (Best)", "Maximum (Worst)"])
        self.mat_mode_combo.currentIndexChanged.connect(self._refresh_materials_table)
        hdr_row.addWidget(self.mat_mode_combo)
        lay.addLayout(hdr_row)

        self.mat_table_container = QVBoxLayout()
        self.mat_table_container.setSpacing(0)
        lay.addLayout(self.mat_table_container)

        self._refresh_materials_table()
        return frame

    def _refresh_materials_table(self):
        while self.mat_table_container.count():
            w = self.mat_table_container.takeAt(0).widget()
            if w:
                w.setParent(None)

        items = self._last_items
        if not items:
            lbl = QLabel("<span style='color:#888;'>Run a calculation first.</span>")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.mat_table_container.addWidget(lbl)
            return

        mode_idx = self.mat_mode_combo.currentIndex()
        qty_key  = ['qty_expected', 'qty_min', 'qty_max'][mode_idx]

        agg: dict[str, int] = {}
        for item in items:
            qty = item.get(qty_key, item['qty_expected'])
            for mat in item['materials']:
                mat_name = mat.get('item', 'Unknown')
                try:
                    mat_qty = int(mat.get('quantity', 1))
                except (ValueError, TypeError):
                    mat_qty = 1
                agg[mat_name] = agg.get(mat_name, 0) + mat_qty * qty

        if not agg:
            lbl = QLabel("<span style='color:#888;'>No material data available.</span>")
            self.mat_table_container.addWidget(lbl)
            return

        table = QTableWidget(len(agg), 2)
        table.setHorizontalHeaderLabels(["Material", "Quantity Needed"])
        table.setStyleSheet("""
            QTableWidget { background:#0d0d0d; color:#fff; border:none; gridline-color:#333; font-size:12px; }
            QHeaderView::section { background:#1a1a1a; color:#ffd700; border:1px solid #333;
                                   padding:4px; font-weight:bold; }
            QTableWidget::item { padding:3px 6px; }
            QTableWidget::item:selected { background:#1a3a5c; }
            QTableWidget { alternate-background-color:#111; }
        """)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)

        for ri, (mat_name, qty) in enumerate(sorted(agg.items())):
            ni = QTableWidgetItem(mat_name)
            ni.setForeground(QColor("#fff"))
            qi = QTableWidgetItem(f"{qty:,}")
            qi.setForeground(QColor("#ffd700"))
            qi.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(ri, 0, ni)
            table.setItem(ri, 1, qi)

        row_h  = 25
        max_vis = 16
        vis    = min(len(agg), max_vis)
        table.setFixedHeight(table.horizontalHeader().height() + vis * row_h + 4)
        self.mat_table_container.addWidget(table)
