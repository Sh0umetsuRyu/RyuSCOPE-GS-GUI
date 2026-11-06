#!/usr/bin/env python3
"""RyuSCOPE GS v0.5-dev: Steam profiles with reversible Gamescope launch integration.

Read-only AMD GPU telemetry; optional logged MangoHud FPS; LACT queried only on demand.
"""
from __future__ import annotations

import json
import shlex
import shutil
import sys
from dataclasses import replace
from pathlib import Path

from telemetry import DEFAULT_LOG_DIR, format_reading, read_gpu_sample, read_live_fps
from ryujinx_integration import (RyujinxError, load_settings as load_ryujinx_settings,
    save_settings as save_ryujinx_settings, scan_games as scan_ryujinx_games,
    read_ryujinx_game_dirs, build_ryujinx_command, launch_ryujinx, SOURCES)

from steam_profile import (SteamProfileError, apply_profile, restore_profile,
    preview_profile, profile_status, discover_localconfigs, request_steam_quit,
    steam_is_running)

from steam_library import (SteamLibraryError, SteamGame, library_root,
    load_manual_libraries, save_manual_libraries, find_libraries, scan_libraries,
    launch_steam_game)

from plugins import ryufg
from integrations import (GamescopeOptions, IntegrationError, build_gamescope_args,
    detect_command, gamescope_help, detect_flags, steam_launch_options, direct_command,
    launch_direct, mangohud_configuration, mangohud_config_file, lact_devices,
    lact_request, LACT_SOCKET)

from PySide6.QtCore import Qt, QTimer, Signal, QRectF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QScrollArea, QSlider, QSpinBox, QStackedWidget,
    QVBoxLayout, QWidget, QSizePolicy, QPlainTextEdit, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QGraphicsOpacityEffect
)

ROOT = Path(__file__).resolve().parent
LOGO = next((p for p in (ROOT / 'assets' / 'ryuscope-logo.png',
                         ROOT / 'assets' / 'ryuscope-emblem.png') if p.exists()),
            ROOT / 'assets' / 'ryuscope-emblem.png')
C = {
    'bg': '#090B0F', 'panel': '#14181F', 'panel2': '#1C212A',
    'border': '#323943', 'text': '#E5E9EF', 'muted': '#9AA5B3',
    'yellow': '#FFD32A', 'yellowsoft': '#D7AF20', 'purple': '#9A48DD',
    'green': '#56D7AA', 'red': '#FF6974'
}

STYLESHEET = '''
QWidget { background: #090B0F; color: #E5E9EF; font-family: "Noto Sans", "DejaVu Sans", sans-serif; font-size: 12px; }
QLabel { background: transparent; border: none; }
QFrame#panel { background: #14181F; border: 1px solid #323943; border-radius: 15px; }
QFrame#panel2 { background: #1C212A; border: 1px solid #323943; border-radius: 12px; }
QFrame#sidebar { background: #11151B; border-right: 1px solid #323943; }
QLabel#heading { color: #F0F2F6; font-size: 26px; font-weight: 700; }
QLabel#section { color: #E5E9EF; font-size: 15px; font-weight: 700; }
QLabel#muted { color: #9AA5B3; }
QLabel#eyebrow { color: #FFD32A; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
QLabel#stat { color: #FFD32A; font-size: 27px; font-weight: 750; }
QLabel#unit { color: #9AA5B3; font-size: 11px; }
QPushButton { background: #252B34; border: 1px solid #3B434F; border-radius: 9px; padding: 9px 15px; color: #E5E9EF; text-align: center; }
QPushButton:hover { border-color: #FFD32A; background: #333A44; }
QPushButton:pressed { background: #4B4731; }
QPushButton#primary { background: #FFD32A; color: #111318; font-weight: 700; border-color: #FFD32A; }
QPushButton#primary:hover { background: #FFE166; }
QPushButton#nav { border: none; background: transparent; color: #A6B0BC; text-align: left; padding: 12px 14px; font-weight: 600; }
QPushButton#nav:hover { color: #F2F4F8; background: #252B34; }
QPushButton#nav[active="true"] { background: #332E19; border-left: 3px solid #FFD32A; border-radius: 0px; color: #FFD32A; }
QComboBox, QSpinBox, QLineEdit { background: #202630; border: 1px solid #434C59; border-radius: 8px; padding: 8px; min-height: 22px; selection-background-color: #65551F; }
QComboBox:hover, QSpinBox:hover, QLineEdit:hover { border-color: #FFD32A; }
QComboBox QAbstractItemView { background: #202630; color: #E5E9EF; selection-background-color: #4B4526; }
QSlider::groove:horizontal { background: #525B67; height: 5px; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #D7AF20; height: 5px; border-radius: 2px; }
QSlider::handle:horizontal { background: #FFD32A; border: 2px solid #FBE99A; width: 17px; margin: -7px 0; border-radius: 9px; }
QSlider::handle:horizontal:hover { background: #FFEB76; }
QCheckBox { spacing: 10px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #69717C; border-radius: 5px; background: #252B34; }
QCheckBox::indicator:checked { background: #FFD32A; border-color: #FFD32A; image: none; }
QProgressBar { border: none; background: #313945; border-radius: 5px; height: 7px; text-align: right; }
QProgressBar::chunk { background: #FFD32A; border-radius: 5px; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #11151B; width: 9px; }
QScrollBar::handle:vertical { background: #424A55; min-height: 25px; border-radius: 4px; }
QPlainTextEdit { background: #202630; border: 1px solid #434C59; color: #E5E9EF; border-radius: 9px; padding: 10px; font-family: "DejaVu Sans Mono", monospace; }
QListWidget { background: #202630; border: 1px solid #434C59; border-radius: 8px; padding: 5px; }
QListWidget::item { padding: 9px; border-radius: 5px; }
QListWidget::item:selected { background: #514821; color: #FFEC9B; }
'''


def vbox(parent=None, spacing=12, margins=(0, 0, 0, 0)):
    layout = QVBoxLayout(parent)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def hbox(parent=None, spacing=12, margins=(0, 0, 0, 0)):
    layout = QHBoxLayout(parent)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def label(text, obj=None):
    x = QLabel(text)
    if obj:
        x.setObjectName(obj)
    x.setWordWrap(True)
    return x


def panel(spacing=12, margins=(18, 17, 18, 17)):
    f = QFrame()
    f.setObjectName('panel')
    lo = vbox(f, spacing, margins)
    return f, lo


def section_heading(title, sub=None):
    box = QWidget()
    lo = vbox(box, 3)
    lo.addWidget(label(title, 'heading'))
    if sub:
        lo.addWidget(label(sub, 'muted'))
    return box


def row_label_value(title, value):
    w = QWidget()
    r = hbox(w)
    r.addWidget(label(title, 'muted'))
    r.addStretch(1)
    r.addWidget(label(value, 'section'))
    return w


class Sparkline(QWidget):
    """Lightweight Qt-painted graph, no external chart dependency."""
    def __init__(self, values=None, color='#FFD32A', parent=None):
        super().__init__(parent)
        self.values = list(values) if values is not None else []
        self.color = QColor(color)
        self.setMinimumHeight(140)

    def append(self, value):
        self.values = (self.values + [value])[-46:]
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(10, 12, -10, -13)
        if rect.width() < 5 or rect.height() < 5:
            return
        p.setPen(QPen(QColor('#303842'), 1))
        for fraction in (0.25, 0.5, 0.75):
            y = rect.top() + rect.height() * fraction
            p.drawLine(rect.left(), int(y), rect.right(), int(y))
        values = self.values
        if not values:
            p.setPen(QPen(QColor('#9AA5B3')))
            p.drawText(rect, Qt.AlignCenter, 'Awaiting live telemetry')
            p.end()
            return
        low = min(values) - 8
        high = max(values) + 8
        height = max(high - low, 1)
        coords = [
            (rect.left() + i * rect.width() / max(1, len(values) - 1),
             rect.bottom() - (v - low) / height * rect.height())
            for i, v in enumerate(values)
        ]
        line = QPainterPath()
        line.moveTo(*coords[0])
        for x, y in coords[1:]:
            line.lineTo(x, y)
        fill = QPainterPath(line)
        fill.lineTo(coords[-1][0], rect.bottom())
        fill.lineTo(coords[0][0], rect.bottom())
        fill.closeSubpath()
        c = QColor(self.color)
        c.setAlpha(28)
        p.fillPath(fill, c)
        p.setPen(QPen(self.color, 2.2))
        p.drawPath(line)
        p.setBrush(self.color)
        p.drawEllipse(QRectF(coords[-1][0] - 3, coords[-1][1] - 3, 6, 6))
        p.end()


class ValueSlider(QWidget):
    changed = Signal(int)

    def __init__(self, title, low, high, initial, suffix='', step=1,
                 endpoints=None, zero_label=None):
        super().__init__()
        self.zero_label = zero_label
        self.suffix = suffix
        self.title = title
        lo = vbox(self, 6)
        r = hbox()
        r.addWidget(label(title))
        r.addStretch()
        self.output = label('', 'eyebrow')
        r.addWidget(self.output)
        lo.addLayout(r)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(low, high)
        self.slider.setSingleStep(step)
        self.slider.setPageStep(step)
        self.slider.setValue(initial)
        self.slider.valueChanged.connect(self._on_value)
        lo.addWidget(self.slider)
        if endpoints:
            endpoints_row = hbox(spacing=8)
            endpoints_row.addWidget(label(str(endpoints[0]), 'muted'))
            endpoints_row.addStretch()
            endpoints_row.addWidget(label(str(endpoints[1]), 'muted'))
            lo.addLayout(endpoints_row)
        self._on_value(initial)

    def _on_value(self, value):
        self.output.setText(self.zero_label if value == 0 and self.zero_label else f'{value}{self.suffix}')
        self.changed.emit(value)


class MetricCard(QFrame):
    def __init__(self, title, value, unit, hint='LIVE'):
        super().__init__()
        self.setObjectName('panel')
        lo = vbox(self, 7, (17, 14, 17, 14))
        top = hbox()
        top.addWidget(label(title.upper(), 'muted'))
        top.addStretch()
        top.addWidget(label(hint, 'eyebrow'))
        lo.addLayout(top)
        self.value = label(value, 'stat')
        self.source = top.itemAt(top.count()-1).widget()
        lo.addWidget(self.value)
        lo.addWidget(label(unit, 'unit'))
        self.setMinimumWidth(145)


class MainWindow(QMainWindow):
    PAGES = [
        ('▦', 'Overview'), ('▣', 'Display & Scaling'), ('◷', 'Performance'),
        ('◈', 'Overlay Designer'), ('▤', 'Game Profiles'),
        ('⌘', 'Steam & Launch'), ('⬡', 'Radeon / LACT'), ('⚙', 'Preferences'),
        ('◉', 'Ryujinx')
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle('RyuSCOPE GS | v1.1 RyuFG')
        self.resize(1270, 830)
        self.setMinimumSize(940, 650)
        if LOGO.exists():
            self.setWindowIcon(QIcon(str(LOGO)))
        self.monitoring_on = True
        self.gamescope_flags = None
        self.integrations = {}
        self.lact_ids = []
        self.steam_games = {}
        self.ryu_games = {}
        self.ryu_settings = load_ryujinx_settings()
        self.nav_buttons = []
        self.pages = QStackedWidget()
        self.sidebar = None
        self.profile_names = ['Default Gaming', 'Competitive 120 FPS', 'Cinematic HDR (sample profile)']
        self.mango_test_process = None
        self._toast_generation = 0
        self.build_shell()
        self.build_pages()
        self.switch_page(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.telemetry_tick)
        self.timer.start(1000)
        QTimer.singleShot(200, self.refresh_integrations)
        QTimer.singleShot(350, self.refresh_steam_games)
        QTimer.singleShot(600, self.telemetry_tick)
        QTimer.singleShot(750, self.refresh_ryujinx_games)

    def build_shell(self):
        shell = QWidget()
        self.setCentralWidget(shell)
        main = hbox(shell, 0)
        nav = QFrame()
        nav.setObjectName('sidebar')
        nav.setFixedWidth(240)
        self.sidebar = nav
        nv = vbox(nav, 8, (13, 23, 13, 15))
        heading = hbox(spacing=10)
        if LOGO.exists():
            from PySide6.QtGui import QPixmap
            img = QLabel()
            img.setObjectName('brandLogo')
            img.setFixedSize(64, 64)
            img.setAlignment(Qt.AlignCenter)
            img.setPixmap(QPixmap(str(LOGO)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            heading.addWidget(img)
        name = vbox(spacing=2)
        name.addWidget(label('RyuSCOPE  GS', 'section'))
        name.addWidget(label('RYUJINWARE', 'eyebrow'))
        heading.addLayout(name)
        nv.addLayout(heading)
        nv.addSpacing(16)
        nv.addWidget(label('CONTROL CENTER', 'eyebrow'))
        for index, (symbol, title) in enumerate(self.PAGES):
            btn = QPushButton(f'{symbol}    {title}')
            btn.setObjectName('nav')
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('active', 'false')
            btn.clicked.connect(lambda _=False, i=index: self.switch_page(i))
            nv.addWidget(btn)
            self.nav_buttons.append(btn)
        nv.addStretch(1)
        disclaimer, dl = panel(6, (12, 13, 12, 13))
        dl.addWidget(label('●  v1.1 RYUFG', 'eyebrow'))
        dl.addWidget(label('Real GPU data · LACT read-only\nSteam profiles require explicit Apply', 'muted'))
        nv.addWidget(disclaimer)
        nv.addWidget(label('Steam + Ryujinx  ·  v1.1', 'muted'))
        main.addWidget(nav)
        main.addWidget(self.pages, 1)
        self.statusBar().showMessage('Gamescope + Steam command mapping · MangoHud preview · LACT read-only · No GPU tuning')
        # Nonblocking launch notification, with a short opacity fade.
        self.launch_toast = QLabel('')
        self.launch_toast.setStyleSheet(
            'background: #252B34; color: #FFD32A; border: 1px solid #FFD32A; '
            'border-radius: 5px; padding: 5px 10px; font-weight: 700;')
        self.launch_toast_effect = QGraphicsOpacityEffect(self.launch_toast)
        self.launch_toast.setGraphicsEffect(self.launch_toast_effect)
        self.launch_toast_animation = QPropertyAnimation(
            self.launch_toast_effect, b'opacity', self)
        self.launch_toast_animation.setDuration(750)
        self.launch_toast_animation.setStartValue(1.0)
        self.launch_toast_animation.setEndValue(0.0)
        self.launch_toast_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.launch_toast_animation.finished.connect(self.launch_toast.hide)
        self.statusBar().addPermanentWidget(self.launch_toast)
        self.launch_toast.hide()

    def new_page(self):
        outer = QScrollArea()
        outer.setWidgetResizable(True)
        outer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName('page')
        layout = vbox(content, 18, (28, 26, 28, 28))
        outer.setWidget(content)
        self.pages.addWidget(outer)
        return layout

    def build_pages(self):
        self.build_overview()
        self.build_display()
        self.build_performance()
        self.build_overlay()
        self.build_profiles()
        self.build_launch()
        self.build_radeon()
        self.build_preferences()
        self.build_ryujinx()

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setProperty('active', 'true' if i == index else 'false')
            button.style().unpolish(button)
            button.style().polish(button)

    def build_overview(self):
        lo = self.new_page()
        top = hbox()
        top.addWidget(section_heading('Gaming Overview', 'Live AMDGPU sensors · optional MangoHud FPS log · no synthetic readings'))
        top.addStretch()
        self.sim_indicator = label('●  LIVE SENSORS', 'eyebrow')
        top.addWidget(self.sim_indicator)
        lo.addLayout(top)
        stats = QGridLayout()
        stats.setSpacing(13)
        self.fps_card = MetricCard('Frame rate', 'N/A', 'FPS · MangoHud CSV', 'MANGOHUD')
        self.temp_card = MetricCard('GPU temperature', 'N/A', '°C · AMDGPU', 'LIVE')
        self.usage_card = MetricCard('GPU utilization', 'N/A', '% · AMDGPU', 'LIVE')
        self.clock_card = MetricCard('GPU clock', 'N/A', 'MHz · AMDGPU', 'LIVE')
        for i, card in enumerate((self.fps_card, self.temp_card, self.usage_card, self.clock_card)):
            stats.addWidget(card, 0, i)
        lo.addLayout(stats)
        cols = hbox(spacing=15)
        chart, cl = panel()
        cl.addWidget(label('GPU UTILIZATION HISTORY', 'eyebrow'))
        cl.addWidget(label('Read-only AMDGPU GPU-load samples', 'section'))
        self.overview_graph = Sparkline([])
        cl.addWidget(self.overview_graph)
        chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        cols.addWidget(chart, 2)
        info, il = panel()
        il.addWidget(label('SESSION STATUS', 'eyebrow'))
        il.addWidget(label('Installed dependency detection', 'section'))
        self.integration_labels = {}
        for name in ('Gamescope', 'MangoHud / mangoapp', 'GameMode', 'Steam', 'LACT'):
            line = row_label_value(name, 'Checking…')
            self.integration_labels[name] = line.layout().itemAt(2).widget()
            il.addWidget(line)
        refresh = QPushButton('Refresh installed tools')
        refresh.clicked.connect(self.refresh_integrations)
        il.addWidget(refresh)
        il.addStretch()
        cols.addWidget(info, 1)
        lo.addLayout(cols)
        graphs = hbox(spacing=15)
        for heading, attr, color in (
            ('GPU TEMPERATURE · °C', 'temperature_graph', '#FFD32A'),
            ('GPU CLOCK · MHz', 'clock_graph', '#56D7AA'),
        ):
            container, graph_layout = panel()
            graph_layout.addWidget(label(heading, 'eyebrow'))
            chart_widget = Sparkline([], color)
            setattr(self, attr, chart_widget)
            graph_layout.addWidget(chart_widget)
            graphs.addWidget(container, 1)
        lo.addLayout(graphs)
        quick, ql = panel()
        ql.addWidget(label('QUICK ACCESS', 'eyebrow'))
        row = hbox()
        for title, idx in [('Configure Display  →', 1), ('Overlay Designer  →', 3), ('View GPU Panel  →', 6)]:
            b = QPushButton(title)
            b.clicked.connect(lambda _=False, i=idx: self.switch_page(i))
            row.addWidget(b)
        ql.addLayout(row)
        lo.addWidget(quick)
        lo.addStretch()

    def build_display(self):
        lo = self.new_page()
        lo.addWidget(section_heading('Display & Scaling', 'Gamescope CLI mapping · settings forwarded to Steam & Launch'))
        cards = hbox(spacing=15)
        left, ll = panel()
        ll.addWidget(label('WINDOW & OUTPUT', 'eyebrow'))
        ll.addWidget(label('Window mode', 'section'))
        self.window_mode = QComboBox()
        self.window_mode.addItems(['Fullscreen', 'Borderless', 'Windowed'])
        ll.addWidget(self.window_mode)
        ll.addWidget(label('Output resolution', 'section'))
        self.output_resolution = QComboBox()
        self.output_resolution.addItems(['1920 × 1080', '2560 × 1440', '3840 × 2160', '1280 × 720'])
        ll.addWidget(self.output_resolution)
        ll.addWidget(label('Internal game resolution', 'section'))
        self.game_resolution = QComboBox()
        self.game_resolution.addItems(['1920 × 1080', '1600 × 900', '1280 × 720', '2560 × 1440'])
        ll.addWidget(self.game_resolution)
        self.refresh = ValueSlider('Game refresh target (-r)', 30, 240, 120, ' Hz', 5)
        ll.addWidget(self.refresh)
        cards.addWidget(left, 1)
        right, rl = panel()
        rl.addWidget(label('IMAGE & FILTER', 'eyebrow'))
        rl.addWidget(label('Scaling behavior (-S)', 'section'))
        self.scaler_mode = QComboBox()
        self.scaler_mode.addItems(['Auto', 'Integer', 'Fit', 'Fill', 'Stretch'])
        rl.addWidget(self.scaler_mode)
        rl.addWidget(label('Upscaling filter (-F)', 'section'))
        self.scaling = QComboBox()
        self.scaling.addItems(['Auto / Default', 'FSR (Gamescope built-in)', 'NIS',
                               'SGSR (Gamescope built-in)', 'Linear', 'Nearest', 'Pixel',
                               'Integer / Nearest'])
        rl.addWidget(self.scaling)
        self.sharpness = ValueSlider('Upscaler sharpness (--sharpness)', 0, 20, 10,
                                     endpoints=('0 · Sharpest', '20 · Softest'))
        rl.addWidget(self.sharpness)
        self.filter_hint = label('Sharpness applies to FSR, NIS and SGSR; 0 is sharpest.', 'muted')
        rl.addWidget(self.filter_hint)
        self.hdr = QCheckBox('Request HDR (support not yet detected)')
        rl.addWidget(self.hdr)
        self.vrr = QCheckBox('Prefer VRR when supported')
        rl.addWidget(self.vrr)
        rl.addStretch()
        cards.addWidget(right, 1)
        lo.addLayout(cards)
        preview, pl = panel()
        pl.addWidget(label('GAMESCOPE SETTINGS · COMMAND IN STEAM & LAUNCH', 'eyebrow'))
        self.display_preview = label('', 'section')
        pl.addWidget(self.display_preview)
        lo.addWidget(preview)
        self.window_mode.currentTextChanged.connect(self.update_display_preview)
        self.output_resolution.currentTextChanged.connect(self.update_display_preview)
        self.game_resolution.currentTextChanged.connect(self.update_display_preview)
        self.scaling.currentTextChanged.connect(self.update_filter_controls)
        self.scaler_mode.currentTextChanged.connect(self.update_display_preview)
        self.refresh.changed.connect(lambda _: self.update_display_preview())
        self.hdr.toggled.connect(self.update_display_preview)
        self.vrr.toggled.connect(self.update_display_preview)
        self.sharpness.changed.connect(self.update_display_preview)
        self.update_filter_controls()
        self.update_display_preview()
        lo.addStretch()

    def update_filter_controls(self, *_):
        supported = self.scaling.currentText() in (
            'FSR (Gamescope built-in)', 'NIS', 'SGSR (Gamescope built-in)')
        self.sharpness.setEnabled(supported)
        self.filter_hint.setText(
            'Sharpness: 0 = sharpest, 20 = softest.' if supported
            else 'Sharpness is not used by the selected filter.')
        self.update_display_preview()

    def update_display_preview(self, *_):
        if not hasattr(self, 'display_preview'):
            return
        cap = self.fps_cap.slider.value() if hasattr(self, 'fps_cap') else 0
        self.display_preview.setText(
            f'{self.window_mode.currentText()}    •    '
            f'{self.game_resolution.currentText()} → {self.output_resolution.currentText()}\n'
            f'Refresh: {self.refresh.slider.value()} Hz    •    '
            f'FPS limit: {cap if cap else "Disabled"}\n'
            f'Scaler: {self.scaler_mode.currentText()}    •    '
            f'Filter: {self.scaling.currentText()}    •    '
            f'Sharpness: {self.sharpness.slider.value() if self.sharpness.isEnabled() else "N/A"}\n'
            f'HDR: {"On" if self.hdr.isChecked() else "Off"}    •    '
            f'VRR: {"On" if self.vrr.isChecked() else "Off"}'
        )

    def build_performance(self):
        lo = self.new_page()
        lo.addWidget(section_heading('Performance', 'Independent refresh/FPS controls · Gamescope 3.17 compatibility'))
        main, ml = panel()
        ml.addWidget(label('FRAME MANAGEMENT', 'eyebrow'))
        self.fps_cap = ValueSlider('FPS limiter (--framerate-limit)', 0, 240, 0, ' FPS', 1,
                                   endpoints=('0 · Disabled', '240 · Maximum'), zero_label='Off')
        ml.addWidget(self.fps_cap)
        ml.addWidget(label('Gamescope limits FPS in divisors of the refresh rate; a requested cap may round to another value.', 'muted'))
        self.low_latency = QCheckBox('Low-latency preference (not mapped; informational only)')
        ml.addWidget(self.low_latency)
        self.gamemode = QCheckBox('Launch with gamemoderun (requires GameMode)')
        ml.addWidget(self.gamemode)
        lo.addWidget(main)
        framegen, fgl = panel()
        fgl.addWidget(label('FRAME GENERATION', 'eyebrow'))
        self.framegen = QCheckBox('Enable RyuFG (AFMF-Linux) for this launch profile')
        fgl.addWidget(self.framegen)
        fgl.addWidget(label('Experimental · 64-bit Vulkan or Proton with DXVK/VKD3D. Disable other frame generation in the game before enabling RyuFG.', 'muted'))
        self.ryufg_status = label(ryufg.status(), 'muted')
        self.ryufg_status.setWordWrap(True)
        fgl.addWidget(self.ryufg_status)
        lo.addWidget(framegen)
        metrics, mm = panel()
        mm.addWidget(label('MEASURED FPS HISTORY · MANGOHUD CSV', 'eyebrow'))
        self.performance_graph = Sparkline([], '#9A48DD')
        mm.addWidget(self.performance_graph)
        lo.addWidget(metrics)
        lo.addWidget(label('FPS only appears when MangoHud has written a recent CSV sample. Without logging, the graph shows Awaiting live telemetry.', 'muted'))
        lo.addStretch()

    def build_overlay(self):
        lo = self.new_page()
        lo.addWidget(section_heading('Overlay Designer', 'MangoHud metrics · per-launch configuration; global files untouched'))
        cols = hbox(spacing=15)
        settings, sl = panel()
        sl.addWidget(label('VISIBLE METRICS', 'eyebrow'))
        self.overlay_checks = {}
        for text, start in [('FPS', True), ('Frametime', True), ('GPU temperature', True),
                            ('GPU utilization', True), ('GPU clock', False), ('VRAM', False),
                            ('CPU utilization', False), ('RAM', False)]:
            check = QCheckBox(text)
            check.setChecked(start)
            check.toggled.connect(self.refresh_overlay_preview)
            self.overlay_checks[text] = check
            sl.addWidget(check)
        sl.addWidget(label('Overlay position', 'section'))
        self.overlay_pos = QComboBox()
        self.overlay_pos.addItems(['Top left', 'Top right', 'Bottom left', 'Bottom right'])
        self.overlay_pos.currentTextChanged.connect(self.refresh_overlay_preview)
        sl.addWidget(self.overlay_pos)
        self.overlay_opacity = ValueSlider('Overlay opacity', 20, 100, 85, '%')
        self.overlay_opacity.changed.connect(self.refresh_overlay_preview)
        sl.addWidget(self.overlay_opacity)
        cols.addWidget(settings, 1)
        preview, pl = panel()
        pl.addWidget(label('OVERLAY MOCKUP', 'eyebrow'))
        self.overlay_box = QFrame()
        self.overlay_box.setObjectName('panel2')
        ol = vbox(self.overlay_box, 8, (14, 14, 14, 14))
        self.overlay_demo = label('', 'section')
        self.overlay_demo.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        ol.addWidget(self.overlay_demo)
        ol.addStretch()
        pl.addWidget(self.overlay_box, 1)
        pl.addWidget(label('Rendered inside the app, not injected into a game.', 'muted'))
        cols.addWidget(preview, 1)
        lo.addLayout(cols)
        self.refresh_overlay_preview()
        self.mango_enabled = QCheckBox('Enable Gamescope MangoHud (--mangoapp) + FPS logging')
        self.mango_enabled.setChecked(False)
        self.mango_enabled.toggled.connect(self.update_launch_preview)
        sl.insertWidget(2, label('When applied, RyuSCOPE replaces a simple existing MangoHud prefix and keeps it in the restore backup. Logging is opt-in and read-only to RyuSCOPE.', 'muted'))
        sl.insertWidget(1, self.mango_enabled)
        export = QPushButton('Export MangoHud.conf…')
        export.clicked.connect(self.export_mango_config)
        sl.addWidget(export)
        pl.addWidget(label('MANGOHUD_CONFIG is scoped to the launched game. Your global MangoHud.conf is never overwritten.', 'muted'))
        lo.addStretch()

    def refresh_overlay_preview(self, *_):
        if not hasattr(self, 'overlay_demo'):
            return
        sample = {
            'FPS': self.fps_card.value.text() if hasattr(self, 'fps_card') else 'N/A',
            'Frametime': 'N/A',
            'GPU temperature': (self.temp_card.value.text() + ' °C') if hasattr(self, 'temp_card') else 'N/A',
            'GPU utilization': (self.usage_card.value.text() + '%') if hasattr(self, 'usage_card') else 'N/A',
            'GPU clock': (self.clock_card.value.text() + ' MHz') if hasattr(self, 'clock_card') else 'N/A',
            'VRAM': (format_reading(getattr(self, 'last_gpu_sample', None).vram_used_gib, digits=1) + ' GiB'
                     if getattr(self, 'last_gpu_sample', None) and self.last_gpu_sample.vram_used_gib is not None else 'N/A'),
            'CPU utilization': 'N/A', 'RAM': 'N/A',
        }
        lines = [f'{k}:  {sample[k]}' for k, widget in self.overlay_checks.items() if widget.isChecked()]
        self.overlay_demo.setText('LAYOUT PREVIEW · AVAILABLE VALUES ONLY\n\n' + ('\n'.join(lines) if lines else '(no metrics selected)'))
        align = Qt.AlignLeft if 'left' in self.overlay_pos.currentText().lower() else Qt.AlignRight
        align |= Qt.AlignTop if 'top' in self.overlay_pos.currentText().lower() else Qt.AlignBottom
        self.overlay_demo.setAlignment(align)
        val = self.overlay_opacity.slider.value() if hasattr(self, 'overlay_opacity') else 85
        self.overlay_demo.setStyleSheet(f'color: rgba(229, 233, 239, {val / 100:.2f}); background: transparent;')

    def build_profiles(self):
        lo = self.new_page()
        lo.addWidget(section_heading('Game Profiles', 'Store RyuSCOPE profiles as JSON; Steam launch options are copied, not installed'))
        cols = hbox(spacing=15)
        left, ll = panel()
        ll.addWidget(label('EXAMPLE PROFILES', 'eyebrow'))
        self.profiles_list = QListWidget()
        self.profiles_list.addItems(self.profile_names)
        self.profiles_list.setCurrentRow(0)
        ll.addWidget(self.profiles_list)
        nrow = hbox()
        self.profile_input = QLineEdit()
        self.profile_input.setPlaceholderText('New profile name')
        nrow.addWidget(self.profile_input, 1)
        add = QPushButton('Add')
        add.clicked.connect(self.add_profile)
        nrow.addWidget(add)
        ll.addLayout(nrow)
        remove = QPushButton('Remove selected demo profile')
        remove.clicked.connect(self.remove_profile)
        ll.addWidget(remove)
        cols.addWidget(left, 1)
        right, rl = panel()
        rl.addWidget(label('PROFILE DETAILS', 'eyebrow'))
        self.profile_selected = label('Default Gaming', 'section')
        rl.addWidget(self.profile_selected)
        self.profiles_list.currentTextChanged.connect(self.profile_selected.setText)
        rl.addWidget(label('Save/load RyuSCOPE JSON profiles. Steam edits only occur through confirmed Apply Profile.', 'muted'))
        rl.addStretch()
        save = QPushButton('Save selected profile to JSON')
        save.clicked.connect(self.save_profile)
        rl.addWidget(save)
        load = QPushButton('Load profile JSON…')
        load.clicked.connect(self.load_profile)
        rl.addWidget(load)
        cols.addWidget(right, 1)
        lo.addLayout(cols)
        lo.addStretch()

    def add_profile(self):
        name = self.profile_input.text().strip()
        if not name:
            return
        if len(name) > 70:
            QMessageBox.warning(self, 'Name too long', 'Use a profile name of 70 characters or fewer.')
            return
        names = [self.profiles_list.item(i).text() for i in range(self.profiles_list.count())]
        if name in names:
            QMessageBox.information(self, 'Already exists', 'That demo profile already exists.')
            return
        self.profiles_list.addItem(name)
        self.profiles_list.setCurrentRow(self.profiles_list.count() - 1)
        self.profile_input.clear()

    def remove_profile(self):
        row = self.profiles_list.currentRow()
        if row >= 0:
            self.profiles_list.takeItem(row)

    def build_radeon(self):
        lo = self.new_page()
        lo.addWidget(section_heading('Radeon / LACT', 'Read-only LACT daemon connection · current config and telemetry on demand'))
        intro, il = panel()
        il.addWidget(label('LACT CONFIGURATION · READ ON DEMAND', 'eyebrow'))
        il.addWidget(label('Crimson Sapphire · Radeon RX 7800 XT', 'section'))
        il.addWidget(label('No remembered clock or voltage numbers are displayed as live settings. Click Refresh LACT below for current device data.', 'muted'))
        lo.addWidget(intro)
        b, bl = panel()
        bl.addWidget(label('TUNING CONTROLS', 'eyebrow'))
        bl.addWidget(label('GPU tuning is intentionally disabled. RyuSCOPE can read LACT data but will never send set/confirm commands in this version.', 'muted'))
        future = QPushButton('GPU tuning controls · not available in Phase 1')
        future.setEnabled(False)
        bl.addWidget(future)
        lo.addWidget(b)
        current, current_lo = panel()
        current_lo.addWidget(label('LACT • LIVE READ-ONLY SNAPSHOT', 'eyebrow'))
        self.lact_status = label('Not read yet. Click Refresh.', 'muted')
        current_lo.addWidget(self.lact_status)
        self.lact_summary = label('Current temperature, load and clock will appear here if supported by LACT.', 'section')
        current_lo.addWidget(self.lact_summary)
        refresh = QPushButton('Refresh LACT devices (read-only)')
        refresh.clicked.connect(self.refresh_lact)
        current_lo.addWidget(refresh)
        self.lact_devices_combo = QComboBox()
        self.lact_devices_combo.currentIndexChanged.connect(self.read_lact_gpu)
        current_lo.addWidget(self.lact_devices_combo)
        self.lact_snapshot = QPlainTextEdit()
        self.lact_snapshot.setReadOnly(True)
        self.lact_snapshot.setMinimumHeight(220)
        self.lact_snapshot.setPlainText('Waiting for LACT device enumeration. No settings will be modified.')
        current_lo.addWidget(self.lact_snapshot)
        lo.addWidget(current)
        lo.addWidget(label('CPU telemetry may be displayed later, but CPU overclocking is explicitly out of scope.', 'muted'))
        lo.addStretch()

    def build_preferences(self):
        lo = self.new_page()
        lo.addWidget(section_heading('Preferences', 'Brand colors locked; placement can be refined later'))
        p, pl = panel()
        pl.addWidget(label('DESIGN IDENTITY', 'eyebrow'))
        for title, val in [('Core background', 'Obsidian black'), ('Primary accent', 'Signal yellow'),
                           ('Typography', 'Metallic silver'), ('Heritage accent', 'Purple in artwork')]:
            pl.addWidget(row_label_value(title, val))
        pl.addWidget(label('Color placement is provisional and will be tested for readability.', 'muted'))
        lo.addWidget(p)
        d, dl = panel()
        dl.addWidget(label('LIVE TELEMETRY', 'eyebrow'))
        self.demo_toggle = QCheckBox('Enable live GPU and FPS monitoring')
        self.demo_toggle.setChecked(True)
        self.demo_toggle.toggled.connect(self.toggle_monitoring)
        dl.addWidget(self.demo_toggle)
        dl.addWidget(label('RyuSCOPE reads AMDGPU sysfs without changing tuning. FPS requires a recent MangoHud CSV log.', 'muted'))
        lo.addWidget(d)
        lo.addStretch()

    def current_options(self) -> GamescopeOptions:
        def dims(text):
            a, b = text.split(' × ')
            return int(a), int(b)
        w, h = dims(self.game_resolution.currentText())
        W, H = dims(self.output_resolution.currentText())
        return GamescopeOptions(game_width=w, game_height=h,
                                output_width=W, output_height=H,
                                refresh=self.refresh.slider.value(),
                                frame_limit=self.fps_cap.slider.value(),
                                scaler=self.scaler_mode.currentText(),
                                mode=self.window_mode.currentText(),
                                scaling=self.scaling.currentText(),
                                sharpness=self.sharpness.slider.value(),
                                hdr=self.hdr.isChecked(),
                                adaptive_sync=self.vrr.isChecked(),
                                mangoapp=self.mango_enabled.isChecked(),
                                gamemode=self.gamemode.isChecked(),
                                ryufg=self.framegen.isChecked())

    def current_mango_config(self):
        enabled = [key for key, cb in self.overlay_checks.items() if cb.isChecked()]
        config = mangohud_configuration(enabled, self.overlay_pos.currentText(),
                                        self.overlay_opacity.slider.value())
        if self.mango_enabled.isChecked():
            # MangoHud writes actual FPS CSV data; our GUI only reads the output.
            config += (f',output_folder={DEFAULT_LOG_DIR},autostart_log=1,log_interval=500')
        return config

    def build_launch(self):
        lo = self.new_page()
        lo.addWidget(section_heading('Steam & Launch',
            'Select a game, configure sliders, safely apply a Gamescope profile, then launch through Steam.'))
        info, il = panel()
        il.addWidget(label('INTEGRATION STATUS', 'eyebrow'))
        self.launch_status = label('Checking Gamescope support…', 'muted')
        il.addWidget(self.launch_status)
        lo.addWidget(info)
        # Safe test harness for MangoApp. The separate toggle never applies or
        # changes a Steam profile; this button launches only Vulkan's vkcube.
        test_panel, test_lo = panel()
        test_lo.addWidget(label('GAMESCOPE + MANGOAPP · LIVE TEST', 'eyebrow'))
        test_lo.addWidget(label('Run a 960×540 → 1280×720 windowed Vulkan test. '
                                'Your game profiles and Display settings are untouched.', 'muted'))
        self.mango_test_checkbox = QCheckBox('Enable MangoApp overlay (--mangoapp)')
        self.mango_test_checkbox.setChecked(True)
        test_lo.addWidget(self.mango_test_checkbox)
        buttons = hbox()
        self.mango_test_start = QPushButton('▶  Launch MangoApp Test')
        self.mango_test_start.setObjectName('primary')
        self.mango_test_start.clicked.connect(self.launch_mangoapp_test)
        buttons.addWidget(self.mango_test_start)
        self.mango_test_stop = QPushButton('■  Stop Test')
        self.mango_test_stop.setEnabled(False)
        self.mango_test_stop.clicked.connect(self.stop_mangoapp_test)
        buttons.addWidget(self.mango_test_stop)
        test_lo.addLayout(buttons)
        self.mango_test_command = QPlainTextEdit()
        self.mango_test_command.setReadOnly(True)
        self.mango_test_command.setMaximumHeight(68)
        test_lo.addWidget(self.mango_test_command)
        self.mango_test_status = label('Ready for Gamescope/MangoApp dependency check.', 'muted')
        test_lo.addWidget(self.mango_test_status)
        self.mango_test_checkbox.toggled.connect(self.update_mangoapp_test_preview)
        lo.addWidget(test_panel)
        # Steam library discovery is read-only. User-linked paths are saved only
        # under ~/.config/RyuSCOPE-GS; never in Steam's own configuration.
        library_panel, lp = panel()
        lp.addWidget(label('STEAM LIBRARY MANAGER', 'eyebrow'))
        lp.addWidget(label('Detected Steam libraries + folders you link manually. Select a SteamLibrary or its steamapps folder.', 'muted'))
        library_buttons = hbox()
        add_library = QPushButton('Add Steam Library…')
        add_library.setObjectName('primary')
        add_library.clicked.connect(self.add_steam_library)
        library_buttons.addWidget(add_library)
        rescan = QPushButton('Rescan libraries')
        rescan.clicked.connect(self.refresh_steam_games)
        library_buttons.addWidget(rescan)
        unlink = QPushButton('Unlink selected folder')
        unlink.clicked.connect(self.remove_steam_library)
        library_buttons.addWidget(unlink)
        library_buttons.addStretch()
        lp.addLayout(library_buttons)
        self.steam_library_list = QListWidget()
        self.steam_library_list.setMaximumHeight(120)
        lp.addWidget(self.steam_library_list)
        self.steam_scan_status = label('Scanning installed games…', 'muted')
        lp.addWidget(self.steam_scan_status)
        self.steam_games_tree = QTreeWidget()
        self.steam_games_tree.setHeaderLabels(['Game', 'App ID', 'Install state', 'Library'])
        self.steam_games_tree.setMinimumHeight(240)
        self.steam_games_tree.setSortingEnabled(True)
        self.steam_games_tree.itemSelectionChanged.connect(self.steam_game_selected)
        searchrow = hbox()
        self.steam_game_search = QLineEdit()
        self.steam_game_search.setPlaceholderText('Search installed games or App IDs…')
        self.steam_game_search.textChanged.connect(self.filter_steam_games)
        searchrow.addWidget(self.steam_game_search, 1)
        self.steam_show_tools = QCheckBox('Show Steam tools / Proton')
        self.steam_show_tools.toggled.connect(self.filter_steam_games)
        searchrow.addWidget(self.steam_show_tools)
        lp.addLayout(searchrow)
        lp.addWidget(self.steam_games_tree)
        self.steam_selection = label('Select an installed Steam game above.', 'muted')
        lp.addWidget(self.steam_selection)
        play_steam = QPushButton('Launch selected game through Steam')
        play_steam.setObjectName('primary')
        play_steam.clicked.connect(self.launch_selected_steam_game)
        lp.addWidget(play_steam)
        lp.addWidget(label('Steam will launch this App ID using its saved settings. Apply a Gamescope profile below first to enable the wrapper.', 'muted'))
        lo.addWidget(library_panel)
        bridge, bl = panel()
        bl.addWidget(label('STEAM + GAMESCOPE PROFILE BRIDGE', 'eyebrow'))
        bl.addWidget(label('Choose a game above. Apply writes only that game’s Steam launch options, with a private backup and one-click restore. Steam must be closed before Apply or Restore.', 'muted'))
        account_row = hbox()
        account_row.addWidget(label('Steam account:', 'section'))
        self.steam_profile_account = QComboBox()
        account_row.addWidget(self.steam_profile_account, 1)
        refresh_accounts = QPushButton('Refresh accounts')
        refresh_accounts.clicked.connect(self.refresh_profile_accounts)
        account_row.addWidget(refresh_accounts)
        bl.addLayout(account_row)
        self.steam_profile_account.currentIndexChanged.connect(self.update_steam_profile_preview)
        self.steam_profile_status = label('Select a Steam game to inspect its profile.', 'section')
        bl.addWidget(self.steam_profile_status)
        self.steam_profile_preview = QPlainTextEdit()
        self.steam_profile_preview.setReadOnly(True)
        self.steam_profile_preview.setMinimumHeight(105)
        bl.addWidget(self.steam_profile_preview)
        actions = hbox()
        apply_button = QPushButton('Apply Gamescope Profile')
        apply_button.setObjectName('primary')
        apply_button.clicked.connect(self.apply_selected_steam_profile)
        actions.addWidget(apply_button)
        quit_button = QPushButton('Request Steam Quit')
        quit_button.clicked.connect(self.request_steam_quit_gui)
        actions.addWidget(quit_button)
        restore_button = QPushButton('Restore Original')
        restore_button.clicked.connect(self.restore_selected_steam_profile)
        actions.addWidget(restore_button)
        bl.addLayout(actions)
        bl.addWidget(label('After applying: launch the selected game above, or use Play in Steam. Steam/Proton handles the executable; Gamescope wraps %command%. Reapply if you change slider settings.', 'muted'))
        lo.addWidget(bridge)
        steam, sl = panel()
        sl.addWidget(label('ADVANCED · GENERATED COMMAND PREVIEW', 'eyebrow'))
        sl.addWidget(label('The Apply button above handles configuration. This is a reference command and optional manual fallback.', 'muted'))
        self.steam_command = QPlainTextEdit()
        self.steam_command.setReadOnly(True)
        self.steam_command.setMaximumHeight(120)
        sl.addWidget(self.steam_command)
        sr = hbox()
        copy = QPushButton('Copy Steam launch options')
        copy.setObjectName('primary')
        copy.clicked.connect(self.copy_steam)
        sr.addWidget(copy)
        refresh = QPushButton('Regenerate preview')
        refresh.clicked.connect(self.update_launch_preview)
        sr.addWidget(refresh)
        sl.addLayout(sr)
        sl.addWidget(label('Steam replaces %command% with its own launch command, including Proton. Your game-specific profile preview is above.', 'muted'))
        lo.addWidget(steam)
        direct, dl = panel()
        dl.addWidget(label('DIRECT LAUNCH (OPTIONAL)', 'eyebrow'))
        file_row = hbox()
        self.game_path = QLineEdit()
        self.game_path.setPlaceholderText('Executable path, e.g. /usr/bin/vkcube')
        self.game_path.textChanged.connect(self.update_launch_preview)
        file_row.addWidget(self.game_path, 1)
        browse = QPushButton('Browse…')
        browse.clicked.connect(self.browse_game)
        file_row.addWidget(browse)
        dl.addLayout(file_row)
        self.game_args = QLineEdit()
        self.game_args.setPlaceholderText('Optional game arguments (shell-style quoting, no shell execution)')
        self.game_args.textChanged.connect(self.update_launch_preview)
        dl.addWidget(self.game_args)
        self.direct_preview = QPlainTextEdit()
        self.direct_preview.setReadOnly(True)
        self.direct_preview.setMaximumHeight(95)
        dl.addWidget(self.direct_preview)
        go = QPushButton('Launch selected executable through Gamescope')
        go.setObjectName('primary')
        go.clicked.connect(self.run_game)
        dl.addWidget(go)
        dl.addWidget(label('Launch uses subprocess.Popen with shell=False. RyuSCOPE does not request root access.', 'muted'))
        lo.addWidget(direct)
        lo.addStretch()
        # Two independent controls: -r is refresh, --framerate-limit is FPS cap.
        self.fps_cap.changed.connect(self.update_launch_preview)
        self.fps_cap.changed.connect(self.update_display_preview)
        self.refresh.changed.connect(self.update_launch_preview)
        for control in (self.window_mode, self.output_resolution, self.game_resolution,
                        self.scaling, self.scaler_mode):
            control.currentIndexChanged.connect(self.update_launch_preview)
        for widget in (self.sharpness,):
            widget.changed.connect(self.update_launch_preview)
        for widget in (self.hdr, self.vrr, self.gamemode, self.framegen):
            widget.toggled.connect(self.update_launch_preview)
        for widget in self.overlay_checks.values():
            widget.toggled.connect(self.update_launch_preview)
        self.overlay_pos.currentIndexChanged.connect(self.update_launch_preview)
        self.overlay_opacity.changed.connect(self.update_launch_preview)
        self.refresh_profile_accounts()
        self.update_launch_preview()
        self.update_mangoapp_test_preview()

    def show_launch_toast(self, message):
        """Show a small confirmation for two seconds, then fade away."""
        self._toast_generation += 1
        generation = self._toast_generation
        self.launch_toast_animation.stop()
        self.launch_toast_effect.setOpacity(1.0)
        self.launch_toast.setText('✓  ' + message)
        self.launch_toast.show()
        QTimer.singleShot(2200, lambda: self._fade_launch_toast(generation))

    def _fade_launch_toast(self, generation):
        if generation == self._toast_generation and self.launch_toast.isVisible():
            self.launch_toast_animation.start()

    def mangoapp_test_options(self):
        """Use a known windowed test preset, leaving actual GUI settings intact."""
        return replace(self.current_options(),
                       game_width=960, game_height=540,
                       output_width=1280, output_height=720,
                       mode='Windowed', refresh=60, frame_limit=0,
                       scaler='Auto', scaling='Auto / Default',
                       hdr=False, adaptive_sync=False,
                       mangoapp=self.mango_test_checkbox.isChecked(),
                       gamemode=False)

    def update_mangoapp_test_preview(self, *_):
        if not hasattr(self, 'mango_test_command'):
            return
        vkcube = shutil.which('vkcube')
        if not vkcube:
            self.mango_test_command.setPlainText('vkcube not found. Install vulkan-tools.')
            self.mango_test_start.setEnabled(False)
            return
        try:
            argv = direct_command(self.mangoapp_test_options(), vkcube, '',
                                  self.gamescope_flags)
            self.mango_test_command.setPlainText(shlex.join(argv))
        except IntegrationError as exc:
            self.mango_test_command.setPlainText('Preview unavailable: ' + str(exc))
        self.mango_test_start.setEnabled(self.mango_test_process is None or
                                        self.mango_test_process.poll() is not None)

    def launch_mangoapp_test(self):
        """Launch an isolated vkcube session through the real integration layer."""
        if self.mango_test_process is not None and self.mango_test_process.poll() is None:
            self.mango_test_status.setText('Test already running. Stop it first.')
            return
        if self.gamescope_flags is None:
            QMessageBox.warning(self, 'Gamescope unavailable',
                'Refresh installed tools and verify Gamescope before launching.')
            return
        vkcube = shutil.which('vkcube')
        if not vkcube:
            QMessageBox.warning(self, 'vkcube missing',
                'Install vulkan-tools to run the Vulkan test.')
            return
        enabled = self.mango_test_checkbox.isChecked()
        if enabled and not detect_command('mangoapp'):
            QMessageBox.warning(self, 'MangoApp missing',
                'MangoApp is not installed. Disable the test checkbox or install mangohud.')
            return
        if enabled:
            try:
                if '--mangoapp' not in gamescope_help():
                    raise IntegrationError('This Gamescope version does not advertise --mangoapp.')
            except IntegrationError as exc:
                QMessageBox.warning(self, 'MangoApp not supported', str(exc))
                return
        try:
            options = self.mangoapp_test_options()
            # This is only an overlay visibility test, not a telemetry CSV test.
            config = (mangohud_configuration(['FPS', 'Frametime', 'GPU temperature'],
                                             'Top left', 85) if enabled else '')
            self.mango_test_process = launch_direct(
                options, vkcube, '', self.gamescope_flags, config)
        except (IntegrationError, OSError, ValueError) as exc:
            self.mango_test_status.setText('Launch failed: ' + str(exc))
            QMessageBox.warning(self, 'Test failed', str(exc))
            return
        pid = self.mango_test_process.pid
        self.mango_test_start.setEnabled(False)
        self.mango_test_stop.setEnabled(True)
        self.mango_test_status.setText(
            f'Launch requested (PID {pid}). Checking that Gamescope stays running…')
        self.show_launch_toast('Gamescope test requested · MangoApp ' +
                               ('on' if enabled else 'off'))
        QTimer.singleShot(1400, self.check_mangoapp_test)

    def check_mangoapp_test(self):
        process = self.mango_test_process
        if process is None:
            return
        code = process.poll()
        if code is None:
            self.mango_test_status.setText(
                'Gamescope test process is running. Verify the overlay visually in vkcube.')
            QTimer.singleShot(1200, self.check_mangoapp_test)
        else:
            self.mango_test_status.setText(
                f'Test process exited (code {code}). If no window appeared, '
                'run from Konsole for Gamescope diagnostics.')
            self.mango_test_process = None
            self.mango_test_stop.setEnabled(False)
            self.mango_test_start.setEnabled(True)

    def stop_mangoapp_test(self):
        process = self.mango_test_process
        if process is not None and process.poll() is None:
            process.terminate()  # Only terminate the test process we launched.
            self.mango_test_status.setText('Stop requested for Gamescope test process.')
        self.mango_test_stop.setEnabled(False)

    def build_ryujinx(self):
        """Ryujinx launcher is independent of Steam's launch options."""
        lo = self.new_page()
        lo.addWidget(section_heading('Ryujinx',
            'Launch Switch games via Ryujinx, optionally wrapped by Gamescope. '
            'Ryujinx settings, firmware, saves and keys remain untouched.'))

        emulator, el = panel()
        el.addWidget(label('EMULATOR INSTALLATION', 'eyebrow'))
        el.addWidget(label('Choose native executable, AppImage or an already-installed Flatpak.', 'muted'))
        self.ryu_source = QComboBox()
        self.ryu_source.addItems(SOURCES)
        self.ryu_source.setCurrentText(self.ryu_settings['source'])
        el.addWidget(self.ryu_source)
        exe_row = hbox()
        self.ryu_executable = QLineEdit()
        self.ryu_executable.setPlaceholderText('Executable path, e.g. /path/to/Ryujinx.AppImage')
        self.ryu_executable.setText(self.ryu_settings['executable'])
        exe_row.addWidget(self.ryu_executable, 1)
        select_exe = QPushButton('Browse executable…')
        select_exe.clicked.connect(self.browse_ryujinx_executable)
        exe_row.addWidget(select_exe)
        el.addLayout(exe_row)
        self.ryu_source.currentIndexChanged.connect(self.ryujinx_settings_changed)
        self.ryu_executable.editingFinished.connect(self.ryujinx_settings_changed)
        lo.addWidget(emulator)

        library, ll = panel()
        ll.addWidget(label('RYUJINX GAME DIRECTORIES', 'eyebrow'))
        ll.addWidget(label('Linked folders are scanned for .XCI, .NSP, .NRO and .NCA. '
                           'No game files are opened, modified or installed.', 'muted'))
        buttons = hbox()
        add = QPushButton('Add game folder…')
        add.setObjectName('primary')
        add.clicked.connect(self.add_ryujinx_folder)
        buttons.addWidget(add)
        import_existing = QPushButton('Import Ryujinx folders')
        import_existing.clicked.connect(self.import_ryujinx_folders)
        buttons.addWidget(import_existing)
        remove = QPushButton('Unlink selected')
        remove.clicked.connect(self.unlink_ryujinx_folder)
        buttons.addWidget(remove)
        rescan = QPushButton('Rescan')
        rescan.clicked.connect(self.refresh_ryujinx_games)
        buttons.addWidget(rescan)
        ll.addLayout(buttons)
        self.ryu_folder_list = QListWidget()
        self.ryu_folder_list.setMaximumHeight(120)
        ll.addWidget(self.ryu_folder_list)
        self.ryu_scan_status = label('Choose or import a game folder to begin.', 'muted')
        ll.addWidget(self.ryu_scan_status)
        self.ryu_search = QLineEdit()
        self.ryu_search.setPlaceholderText('Search Ryujinx game files…')
        self.ryu_search.textChanged.connect(self.filter_ryujinx_games)
        ll.addWidget(self.ryu_search)
        self.ryu_tree = QTreeWidget()
        self.ryu_tree.setHeaderLabels(['Game file', 'Format', 'Directory'])
        self.ryu_tree.setMinimumHeight(245)
        self.ryu_tree.setSortingEnabled(True)
        self.ryu_tree.itemSelectionChanged.connect(self.update_ryujinx_preview)
        ll.addWidget(self.ryu_tree)
        lo.addWidget(library)

        launch_panel, pl = panel()
        pl.addWidget(label('RYUJINX + GAMESCOPE LAUNCH', 'eyebrow'))
        self.ryu_with_gamescope = QCheckBox('Launch through Gamescope (uses Display & Scaling / Performance settings)')
        self.ryu_with_gamescope.setChecked(self.ryu_settings['gamescope'])
        pl.addWidget(self.ryu_with_gamescope)
        self.ryu_fullscreen = QCheckBox('Request Ryujinx fullscreen for selected game')
        self.ryu_fullscreen.setChecked(self.ryu_settings['fullscreen'])
        pl.addWidget(self.ryu_fullscreen)
        pl.addWidget(label('Gamescope output scaling is separate from Ryujinx internal resolution scaling. '
                           'It does not change Switch emulation render resolution.', 'muted'))
        self.ryu_preview = QPlainTextEdit()
        self.ryu_preview.setReadOnly(True)
        self.ryu_preview.setMaximumHeight(105)
        pl.addWidget(self.ryu_preview)
        self.ryu_status = label('Select a title above, or open the emulator.', 'muted')
        pl.addWidget(self.ryu_status)
        play_buttons = hbox()
        open_emu = QPushButton('Open Ryujinx')
        open_emu.clicked.connect(lambda: self.run_ryujinx(None))
        play_buttons.addWidget(open_emu)
        self.ryu_play_selected = QPushButton('Launch selected game')
        self.ryu_play_selected.setObjectName('primary')
        self.ryu_play_selected.clicked.connect(self.launch_selected_ryujinx_game)
        play_buttons.addWidget(self.ryu_play_selected)
        pl.addLayout(play_buttons)
        pl.addWidget(label('Uses subprocess.Popen (shell=False). No changes to Steam, '
                           'Ryujinx save data, keys or emulator configuration. '
                           'AppImage must be executable; Flatpak must have access to your games folder.', 'muted'))
        lo.addWidget(launch_panel)
        lo.addStretch()
        for control in (self.ryu_with_gamescope, self.ryu_fullscreen):
            control.toggled.connect(self.ryujinx_settings_changed)
        for slider in (self.refresh, self.sharpness, self.fps_cap):
            slider.changed.connect(self.update_ryujinx_preview)
        for control in (self.game_resolution, self.output_resolution,
                        self.window_mode, self.scaler_mode, self.scaling):
            control.currentIndexChanged.connect(self.update_ryujinx_preview)
        for box in (self.hdr, self.vrr, self.gamemode, self.mango_enabled, self.framegen):
            box.toggled.connect(self.update_ryujinx_preview)
        self.refresh_ryujinx_games()

    def ryujinx_settings_changed(self, *_):
        self.ryu_settings.update({
            'source': self.ryu_source.currentText(),
            'executable': self.ryu_executable.text().strip(),
            'gamescope': self.ryu_with_gamescope.isChecked(),
            'fullscreen': self.ryu_fullscreen.isChecked(),
        })
        try:
            save_ryujinx_settings(self.ryu_settings)
        except OSError as exc:
            self.ryu_status.setText(f'Cannot save RyuSCOPE Ryujinx settings: {exc}')
        self.update_ryujinx_preview()

    def browse_ryujinx_executable(self):
        selected, _ = QFileDialog.getOpenFileName(
            self, 'Select Ryujinx binary or AppImage', str(Path.home()),
            'Executables / AppImages (*)')
        if selected:
            self.ryu_source.setCurrentText('Custom executable / AppImage')
            self.ryu_executable.setText(selected)
            self.ryujinx_settings_changed()

    def add_ryujinx_folder(self):
        start = str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, 'Link Ryujinx game folder', start)
        if not selected:
            return
        linked = str(Path(selected).expanduser().resolve())
        if linked not in self.ryu_settings['game_dirs']:
            self.ryu_settings['game_dirs'].append(linked)
            try:
                save_ryujinx_settings(self.ryu_settings)
            except OSError as exc:
                QMessageBox.warning(self, 'Cannot save folder', str(exc))
                return
        self.refresh_ryujinx_games()

    def unlink_ryujinx_folder(self):
        item = self.ryu_folder_list.currentItem()
        if item is None:
            return
        folder = item.data(Qt.UserRole)
        self.ryu_settings['game_dirs'] = [p for p in self.ryu_settings['game_dirs'] if p != folder]
        try:
            save_ryujinx_settings(self.ryu_settings)
        except OSError as exc:
            QMessageBox.warning(self, 'Cannot unlink folder', str(exc))
            return
        self.refresh_ryujinx_games()

    def import_ryujinx_folders(self):
        candidates = read_ryujinx_game_dirs()
        if not candidates:
            QMessageBox.information(self, 'No folders found',
                'Ryujinx Config.json did not provide any game directories. '
                'Choose Add game folder instead.')
            return
        existing = {str(Path(x).expanduser().resolve()) for x in self.ryu_settings['game_dirs']}
        for folder in candidates:
            canonical = str(Path(folder).expanduser().resolve())
            if canonical not in existing:
                self.ryu_settings['game_dirs'].append(canonical)
                existing.add(canonical)
        try:
            save_ryujinx_settings(self.ryu_settings)
        except OSError as exc:
            QMessageBox.warning(self, 'Cannot import folders', str(exc))
            return
        self.refresh_ryujinx_games()

    def refresh_ryujinx_games(self, *_):
        if not hasattr(self, 'ryu_tree'):
            return
        self.ryu_folder_list.clear()
        for folder in self.ryu_settings['game_dirs']:
            item = QListWidgetItem(folder)
            item.setData(Qt.UserRole, folder)
            self.ryu_folder_list.addItem(item)
        games, warnings = scan_ryujinx_games(self.ryu_settings['game_dirs'])
        self.ryu_games = {str(game.path): game for game in games}
        self.ryu_tree.clear()
        for game in games:
            item = QTreeWidgetItem([game.name, game.kind, str(game.library)])
            item.setData(0, Qt.UserRole, str(game.path))
            self.ryu_tree.addTopLevelItem(item)
        self.ryu_tree.resizeColumnToContents(0)
        self.ryu_tree.resizeColumnToContents(1)
        msg = f'{len(games)} Ryujinx game file(s) found across {len(self.ryu_settings["game_dirs"])} linked folders.'
        if warnings:
            msg += '  ' + ' | '.join(warnings[:2])
        self.ryu_scan_status.setText(msg)
        self.filter_ryujinx_games()

    def filter_ryujinx_games(self, *_):
        if not hasattr(self, 'ryu_tree'):
            return
        query = self.ryu_search.text().casefold().strip()
        for index in range(self.ryu_tree.topLevelItemCount()):
            item = self.ryu_tree.topLevelItem(index)
            game = self.ryu_games.get(item.data(0, Qt.UserRole))
            item.setHidden(not game or (query not in game.name.casefold()))
        self.update_ryujinx_preview()

    def selected_ryujinx_game(self):
        item = self.ryu_tree.currentItem()
        if item is None or item.isHidden():
            return None
        return self.ryu_games.get(item.data(0, Qt.UserRole))

    def update_ryujinx_preview(self, *_):
        if not hasattr(self, 'ryu_preview'):
            return
        game = self.selected_ryujinx_game()
        self.ryu_play_selected.setEnabled(game is not None)
        if game:
            self.ryu_status.setText(f'{game.name} ({game.kind})\n{game.path}')
        else:
            self.ryu_status.setText('Select a Ryujinx game, or use Open Ryujinx.')
        try:
            argv = build_ryujinx_command(
                self.ryu_source.currentText(), self.ryu_executable.text(),
                str(game.path) if game else None, self.ryu_fullscreen.isChecked(),
                self.ryu_with_gamescope.isChecked(), self.current_options(),
                self.gamescope_flags)
            self.ryu_preview.setPlainText(shlex.join(argv))
        except (RyujinxError, IntegrationError) as exc:
            self.ryu_preview.setPlainText('Launch unavailable: ' + str(exc))

    def launch_selected_ryujinx_game(self):
        game = self.selected_ryujinx_game()
        if game is None:
            QMessageBox.information(self, 'Select a game', 'Choose a Ryujinx game file first.')
            return
        self.run_ryujinx(game.path)

    def run_ryujinx(self, game_path):
        if self.ryu_with_gamescope.isChecked() and self.gamescope_flags is None:
            QMessageBox.warning(self, 'Gamescope not verified',
                'Gamescope flags have not been validated. Refresh installed tools first, '
                'or uncheck Gamescope for an emulator-only launch.')
            return
        try:
            process = launch_ryujinx(
                self.ryu_source.currentText(), self.ryu_executable.text(),
                game_path, self.ryu_fullscreen.isChecked(),
                self.ryu_with_gamescope.isChecked(), self.current_options(),
                self.gamescope_flags, self.current_mango_config())
        except (RyujinxError, IntegrationError) as exc:
            QMessageBox.warning(self, 'Ryujinx launch failed', str(exc))
            return
        self.statusBar().showMessage(
            f'Ryujinx launch requested (PID {process.pid}). Confirm the emulator/game opened.', 15000)
        self.show_launch_toast('Ryujinx launch requested · Gamescope ' +
                               ('on' if self.ryu_with_gamescope.isChecked() else 'off'))

    def refresh_steam_games(self, *_):
        """Scan manifests only; never open game EXEs or alter Steam files."""
        try:
            manual = load_manual_libraries()
            libraries, warnings = find_libraries(manual)
            games, scan_warnings = scan_libraries(libraries)
            warnings.extend(scan_warnings)
        except (OSError, ValueError, SteamLibraryError) as exc:
            self.steam_scan_status.setText(f'Steam discovery failed: {exc}')
            return
        self.steam_games = {game.app_id: game for game in games}
        self.steam_library_list.clear()
        for root in libraries:
            tag = ' [linked]' if str(root) in {str(Path(p).expanduser().resolve()) for p in manual} else ' [detected]'
            item = QListWidgetItem(str(root) + tag)
            item.setData(Qt.UserRole, str(root))
            self.steam_library_list.addItem(item)
        self.steam_games_tree.clear()
        for game in games:
            row = QTreeWidgetItem([game.name, str(game.app_id), game.status, str(game.library)])
            row.setData(0, Qt.UserRole, game.app_id)
            self.steam_games_tree.addTopLevelItem(row)
        for idx in (0, 1, 2):
            self.steam_games_tree.resizeColumnToContents(idx)
        self.filter_steam_games()
        tool_count = sum(game.is_steam_tool for game in games)
        message = (f'{len(games)-tool_count} potential games + {tool_count} known tools '
                   f'across {len(libraries)} libraries.')
        if warnings:
            message += f' {len(warnings)} issue(s): ' + ' | '.join(warnings[:2])
        self.steam_scan_status.setText(message)
        self.steam_game_selected()

    def filter_steam_games(self, *_):
        if not hasattr(self, 'steam_games_tree'):
            return
        query = self.steam_game_search.text().strip().casefold()
        show_tools = self.steam_show_tools.isChecked()
        for index in range(self.steam_games_tree.topLevelItemCount()):
            item = self.steam_games_tree.topLevelItem(index)
            game = self.steam_games.get(item.data(0, Qt.UserRole))
            if not game:
                continue
            matching = query in game.name.casefold() or query in str(game.app_id)
            item.setHidden(not matching or (game.is_steam_tool and not show_tools))
        self.steam_game_selected()

    def add_steam_library(self):
        start = str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, 'Choose SteamLibrary folder', start)
        if not selected:
            return
        try:
            chosen = str(library_root(selected))
            manual = load_manual_libraries()
            current = {str(Path(p).expanduser().resolve()) for p in manual}
            if chosen not in current:
                manual.append(chosen)
                save_manual_libraries(manual)
        except (SteamLibraryError, OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Cannot link Steam library', str(exc))
            return
        self.refresh_steam_games()

    def remove_steam_library(self):
        item = self.steam_library_list.currentItem()
        if item is None:
            QMessageBox.information(self, 'No folder selected', 'Select a linked library first.')
            return
        root = item.data(Qt.UserRole)
        try:
            manual = load_manual_libraries()
            remaining = [p for p in manual if str(Path(p).expanduser().resolve()) != root]
            if len(remaining) == len(manual):
                QMessageBox.information(self, 'Steam-managed library',
                    'This folder is detected from Steam itself. You can only unlink manually added folders here.')
                return
            save_manual_libraries(remaining)
        except (SteamLibraryError, OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Cannot unlink folder', str(exc))
            return
        self.refresh_steam_games()

    def steam_game_selected(self):
        item = self.steam_games_tree.currentItem()
        if item is None:
            self.steam_selection.setText('Select a Steam game from the list.')
            self.update_steam_profile_preview()
            return
        game = self.steam_games.get(item.data(0, Qt.UserRole))
        if game:
            self.steam_selection.setText(
                f'{game.name} · App ID {game.app_id} · {game.status}\n{game.directory}')
        self.update_steam_profile_preview()

    def selected_steam_profile(self):
        game_item = self.steam_games_tree.currentItem()
        game = self.steam_games.get(game_item.data(0, Qt.UserRole)) if game_item else None
        config = self.steam_profile_account.currentData() if hasattr(self, 'steam_profile_account') else None
        if game is None:
            raise SteamProfileError('Select a Steam game first.')
        if not config:
            raise SteamProfileError('No Steam account configuration found. Refresh accounts.')
        return game, Path(config)

    def refresh_profile_accounts(self, *_):
        if not hasattr(self, 'steam_profile_account'):
            return
        current = self.steam_profile_account.currentData()
        self.steam_profile_account.blockSignals(True)
        self.steam_profile_account.clear()
        for path in discover_localconfigs():
            self.steam_profile_account.addItem(f'Account {path.parent.parent.name} · {path}', str(path))
        if current:
            for i in range(self.steam_profile_account.count()):
                if self.steam_profile_account.itemData(i) == current:
                    self.steam_profile_account.setCurrentIndex(i)
                    break
        self.steam_profile_account.blockSignals(False)
        self.update_steam_profile_preview()

    def update_steam_profile_preview(self, *_):
        if not hasattr(self, 'steam_profile_preview'):
            return
        try:
            game, config = self.selected_steam_profile()
            if self.gamescope_flags is None:
                self.steam_profile_status.setText('Gamescope capability detection pending or unavailable.')
                self.steam_profile_preview.setPlainText('No profile can be applied until Gamescope flags are validated.')
                return
            existing, target, state = preview_profile(
                config, game.app_id, self.current_options(), self.gamescope_flags,
                game_dir=game.directory, mango_config=self.current_mango_config() if self.mango_enabled.isChecked() else '')
            self.steam_profile_status.setText(
                f'{game.name} · {state} · Steam ' + ('running' if steam_is_running() else 'closed'))
            self.steam_profile_preview.setPlainText(
                'CURRENT:\n' + (existing if existing is not None else '(no launch options)') +
                '\n\nPROPOSED (Apply):\n' + target)
        except (SteamProfileError, IntegrationError, OSError) as exc:
            self.steam_profile_status.setText('Profile not ready')
            self.steam_profile_preview.setPlainText(str(exc))

    def request_steam_quit_gui(self):
        answer = QMessageBox.question(self, 'Request Steam quit?',
            'Steam and any running games must close before modifying launch options. '
            'Request Steam to quit now? Save your game first.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            request_steam_quit()
        except SteamProfileError as exc:
            QMessageBox.warning(self, 'Steam shutdown error', str(exc))
            return
        self.statusBar().showMessage('Requested Steam shutdown. Wait until Steam fully exits, then click Apply/Restore.', 12000)
        self.update_steam_profile_preview()

    def apply_selected_steam_profile(self):
        try:
            game, config = self.selected_steam_profile()
            if not game.files_present:
                raise SteamProfileError('Selected game installation is unavailable or drive is unplugged.')
            if self.gamescope_flags is None:
                raise SteamProfileError('Refresh installed tools; Gamescope capabilities are not verified.')
            if self.mango_enabled.isChecked() and not detect_command('mangoapp'):
                raise SteamProfileError('mangoapp was not found on PATH. The new Gamescope overlay is unavailable; original Steam MangoHud settings were not changed.')
            old, new, state = preview_profile(
                config, game.app_id, self.current_options(), self.gamescope_flags,
                game_dir=game.directory, mango_config=self.current_mango_config() if self.mango_enabled.isChecked() else '')
            if old == new and state == 'Applied':
                if self.framegen.isChecked():
                    ryufg.prepare_steam()
                QMessageBox.information(self, 'Already applied', 'This exact Gamescope profile is already applied.')
                return
            if steam_is_running():
                QMessageBox.warning(self, 'Quit Steam first',
                    'Steam is still running. Save/close any games, then click Request Steam Quit. '
                    'Once Steam has fully exited, click Apply again. No files have been changed.')
                return
            question = (f'Apply Gamescope profile to {game.name} (App ID {game.app_id})?\n\n'
                        f'Current: {(old if old is not None else "(none)")[:380]}\n\n'
                        f'New: {new[:550]}\n\n'
                        'RyuSCOPE will privately back up localconfig.vdf and change only this app’s LaunchOptions.')
            confirm = QMessageBox.question(self, 'Confirm Steam profile write', question,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm != QMessageBox.Yes:
                return
            if self.mango_enabled.isChecked():
                DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
            applied, backup = apply_profile(
                config, game.app_id, self.current_options(), self.gamescope_flags,
                game_dir=game.directory, mango_config=self.current_mango_config() if self.mango_enabled.isChecked() else '')
        except (SteamProfileError, IntegrationError, ryufg.RyuFGError, OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Gamescope profile not applied', str(exc))
            self.update_steam_profile_preview()
            return
        self.update_steam_profile_preview()
        self.statusBar().showMessage(f'Gamescope profile applied to {game.name}. Backup: {backup}', 15000)
        QMessageBox.information(self, 'Profile applied',
            f'{game.name} is configured. Start the game using Launch through Steam above.\n\nBackup: {backup}')

    def restore_selected_steam_profile(self):
        try:
            game, config = self.selected_steam_profile()
            state, _ = profile_status(config, game.app_id)
            if state != 'Applied':
                raise SteamProfileError('No active RyuSCOPE profile to restore, or Steam settings changed externally.')
            if steam_is_running():
                raise SteamProfileError('Quit Steam completely before restoring original launch options.')
            answer = QMessageBox.question(self, 'Restore Steam launch options?',
                f'Restore the original launch options for {game.name}? Other Steam settings remain untouched.',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return
            backup = restore_profile(config, game.app_id)
        except (SteamProfileError, OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Cannot restore Steam profile', str(exc))
            self.update_steam_profile_preview()
            return
        self.update_steam_profile_preview()
        self.statusBar().showMessage(f'Original Steam launch options restored. Safety backup: {backup}', 15000)

    def launch_selected_steam_game(self):
        item = self.steam_games_tree.currentItem()
        game = self.steam_games.get(item.data(0, Qt.UserRole)) if item else None
        if game is None:
            QMessageBox.information(self, 'Choose a Steam game', 'Select a Steam game first.')
            return
        if not game.files_present:
            QMessageBox.warning(self, 'Game files missing',
                'Steam manifest exists but the install folder is unavailable. Check whether its drive is mounted.')
            return
        try:
            process = launch_steam_game(game.app_id)
        except SteamLibraryError as exc:
            QMessageBox.warning(self, 'Steam launch error', str(exc))
            return
        try:
            config = self.steam_profile_account.currentData()
            state, _ = profile_status(Path(config), game.app_id) if config else ('Not applied', None)
        except (SteamProfileError, OSError):
            state = 'Unknown'
        self.statusBar().showMessage(
            f'Steam launch requested: {game.name} ({game.app_id}), PID {process.pid}. '
            + ('Gamescope profile applied; verify process after startup.' if state == 'Applied'
               else 'No verified RyuSCOPE Gamescope profile applied.'), 15000)
        self.show_launch_toast('Steam launch requested · ' +
                               ('Gamescope profile applied' if state == 'Applied'
                                else 'profile not verified'))

    def update_launch_preview(self, *_):
        if not hasattr(self, 'steam_command'):
            return
        try:
            o = self.current_options()
            config = self.current_mango_config()
            flags = self.gamescope_flags
            preview = steam_launch_options(o, flags, config)
            self.steam_command.setPlainText(preview)
            try:
                direct = direct_command(o, self.game_path.text(), self.game_args.text(), flags)
                from shlex import join
                direct_text = join(direct)
            except IntegrationError as exc:
                direct_text = str(exc)
            self.direct_preview.setPlainText(direct_text)
            detected = bool(self.integrations.get('Gamescope')) and self.gamescope_flags is not None
            self.launch_status.setText('● Gamescope flags validated on this PC' if detected else
                '● Reference preview only until Gamescope --help is verified on this PC')
        except IntegrationError as exc:
            self.steam_command.setPlainText('Cannot generate command: ' + str(exc))
            self.direct_preview.setPlainText('Cannot generate command.')
            self.launch_status.setText('● Configuration validation issue: ' + str(exc))
        self.update_steam_profile_preview()

    def browse_game(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select game or emulator executable',
                                             str(Path.home()))
        if path:
            self.game_path.setText(path)

    def copy_steam(self):
        if self.mango_enabled.isChecked() and not detect_command('mangoapp'):
            QMessageBox.warning(self, 'MangoHud overlay unavailable',
                'mangoapp is required for Gamescope overlays. Install mangoapp or disable the overlay.')
            return
        if self.gamemode.isChecked() and not detect_command('gamemoderun'):
            QMessageBox.warning(self, 'GameMode unavailable',
                'gamemoderun is missing. Install gamemode or turn off the GameMode option.')
            return
        if self.gamescope_flags is None:
            QMessageBox.warning(self, 'Gamescope not validated',
                'Install Gamescope (or resolve --help errors), then refresh detection before copying launch options.')
            return
        text = self.steam_command.toPlainText()
        if not text.startswith(('DISABLE_AFMF=1 ', 'MANGOHUD_CONFIG=')):
            QMessageBox.warning(self, 'Command invalid', 'Review selected settings and regenerate.')
            return
        if self.framegen.isChecked():
            try:
                ryufg.prepare_steam()
            except ryufg.RyuFGError as exc:
                QMessageBox.warning(self, 'RyuFG unavailable', str(exc))
                return
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage('Steam launch options copied. Paste manually into the selected game in Steam.', 12000)

    def run_game(self):
        if self.gamescope_flags is None:
            QMessageBox.warning(self, 'Gamescope not validated',
                                'Use Refresh installed tools to validate Gamescope before launching.')
            return
        if not self.game_path.text().strip():
            QMessageBox.information(self, 'No executable', 'Select the game/emulator executable first.')
            return
        try:
            process = launch_direct(self.current_options(), self.game_path.text(),
                self.game_args.text(), self.gamescope_flags,
                self.current_mango_config())
        except IntegrationError as exc:
            QMessageBox.warning(self, 'Launch blocked', str(exc))
            return
        self.statusBar().showMessage(f'Gamescope launch requested (PID {process.pid}).', 15000)
        self.show_launch_toast('Gamescope launch requested · MangoApp ' +
                               ('on' if self.mango_enabled.isChecked() else 'off'))

    def refresh_integrations(self):
        self.ryufg_status.setText(ryufg.status())
        statuses = {
            'Gamescope': detect_command('gamescope'),
            'MangoHud / mangoapp': detect_command('mangoapp'),
            'GameMode': detect_command('gamemoderun'),
            'Steam': detect_command('steam'),
            'LACT': Path(LACT_SOCKET).exists(),
        }
        self.integrations = statuses
        self.gamescope_flags = None
        error = ''
        if statuses['Gamescope']:
            try:
                self.gamescope_flags = detect_flags(gamescope_help())
            except IntegrationError as exc:
                error = str(exc)
        for name, widget in self.integration_labels.items():
            state = statuses[name]
            if name == 'Gamescope' and state and self.gamescope_flags is None:
                widget.setText('Found · help unverified')
            else:
                widget.setText('Detected' if state else 'Missing')
        if error:
            self.statusBar().showMessage('Gamescope inspection: ' + error, 13000)
        self.update_launch_preview()
        self.update_steam_profile_preview()
        self.update_ryujinx_preview()
        self.update_mangoapp_test_preview()

    def export_mango_config(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Export RyuSCOPE MangoHud configuration',
                            str(Path.home() / 'RyuSCOPE-MangoHud.conf'), 'Config files (*.conf)')
        if not path:
            return
        target = Path(path)
        if target.exists() and QMessageBox.question(self, 'Overwrite file?',
                f'{target} already exists. Replace it?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            target.write_text(mangohud_config_file(self.current_mango_config()), encoding='utf-8')
        except OSError as exc:
            QMessageBox.warning(self, 'Could not export', str(exc))
            return
        self.statusBar().showMessage('Exported MangoHud configuration. Existing global MangoHud configuration untouched.', 12000)

    def profile_data(self):
        o = self.current_options()
        return {'schema': 1, 'name': self.profiles_list.currentItem().text() if self.profiles_list.currentItem() else 'Profile',
                'gamescope': o.__dict__,
                'overlay_metrics': [key for key, cb in self.overlay_checks.items() if cb.isChecked()],
                'overlay_position': self.overlay_pos.currentText(),
                'overlay_opacity': self.overlay_opacity.slider.value()}

    def save_profile(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save RyuSCOPE profile',
                    str(Path.home() / 'RyuSCOPE-profile.json'), 'JSON files (*.json)')
        if not path:
            return
        target = Path(path)
        if target.exists() and QMessageBox.question(self, 'Overwrite profile?',
                    f'{target} already exists. Replace it?',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            target.write_text(json.dumps(self.profile_data(), indent=2) + '\n', encoding='utf-8')
        except OSError as exc:
            QMessageBox.warning(self, 'Save failed', str(exc))
            return
        self.statusBar().showMessage(f'Saved RyuSCOPE profile: {target}', 12000)

    def load_profile(self):
        from dataclasses import fields
        path, _ = QFileDialog.getOpenFileName(self, 'Load RyuSCOPE profile', str(Path.home()),
                                               'JSON files (*.json)')
        if not path:
            return
        try:
            obj = json.loads(Path(path).read_text(encoding='utf-8'))
            if obj.get('schema') != 1:
                raise ValueError('Unsupported profile schema')
            allowed = {f.name for f in fields(GamescopeOptions)}
            settings = {k:v for k,v in obj['gamescope'].items() if k in allowed}
            from integrations import validate_options
            o = GamescopeOptions(**settings)
            validate_options(o)
            if not isinstance(obj.get('overlay_metrics', []), list):
                raise ValueError('Invalid overlay metrics list')
            position = obj.get('overlay_position', 'Top left')
            opacity = int(obj.get('overlay_opacity', 85))
            mangohud_configuration(obj.get('overlay_metrics', []), position, opacity)
        except (OSError, ValueError, TypeError, KeyError, IntegrationError) as exc:
            QMessageBox.warning(self, 'Invalid profile', str(exc))
            return
        def choose(combo, text):
            i = combo.findText(text)
            if i >= 0: combo.setCurrentIndex(i)
        choose(self.game_resolution, f'{o.game_width} × {o.game_height}')
        choose(self.output_resolution, f'{o.output_width} × {o.output_height}')
        choose(self.window_mode, o.mode)
        choose(self.scaling, o.scaling)
        choose(self.scaler_mode, o.scaler)
        for widget, value in ((self.refresh, o.refresh), (self.fps_cap, o.frame_limit),
                              (self.sharpness, o.sharpness), (self.overlay_opacity, opacity)):
            widget.slider.setValue(value)
        self.hdr.setChecked(o.hdr)
        self.vrr.setChecked(o.adaptive_sync)
        self.mango_enabled.setChecked(o.mangoapp)
        self.gamemode.setChecked(o.gamemode)
        self.framegen.setChecked(o.ryufg)
        choose(self.overlay_pos, position)
        for key, cb in self.overlay_checks.items():
            cb.setChecked(key in obj.get('overlay_metrics', []))
        name = str(obj.get('name', Path(path).stem))[:70]
        names = [self.profiles_list.item(i).text() for i in range(self.profiles_list.count())]
        if name not in names:
            self.profiles_list.addItem(name)
        self.profiles_list.setCurrentRow(names.index(name) if name in names else self.profiles_list.count()-1)
        self.update_filter_controls()
        self.update_display_preview()
        self.update_launch_preview()
        self.statusBar().showMessage(f'Loaded RyuSCOPE profile: {Path(path).name}', 12000)

    def refresh_lact(self):
        self.lact_devices_combo.blockSignals(True)
        self.lact_devices_combo.clear()
        self.lact_ids = []
        try:
            devices = lact_devices()
        except IntegrationError as exc:
            self.lact_status.setText('LACT daemon unavailable or permission denied: ' + str(exc))
            self.lact_snapshot.setPlainText('No data. Your GPU tuning was not changed.')
            self.lact_summary.setText('LACT readings unavailable')
            self.lact_devices_combo.blockSignals(False)
            return
        for d in devices:
            self.lact_ids.append(d['id'])
            self.lact_devices_combo.addItem(str(d.get('name', d['id'])))
        self.lact_devices_combo.blockSignals(False)
        self.lact_status.setText(f'Found {len(devices)} LACT GPU(s); requests are read-only')
        if devices:
            self.read_lact_gpu(0)
        else:
            self.lact_snapshot.setPlainText('LACT returned no supported GPUs.')
            self.lact_summary.setText('No supported GPUs reported')

    def read_lact_gpu(self, index):
        if index < 0 or index >= len(self.lact_ids):
            return
        id_ = self.lact_ids[index]
        result = {'gpu_id': id_}
        for command in ('device_info', 'device_stats', 'get_gpu_config'):
            try:
                result[command] = lact_request(command, {'id': id_})
            except IntegrationError as exc:
                result[command] = 'Unavailable: ' + str(exc)
        stats = result.get('device_stats')
        if isinstance(stats, dict):
            temp = stats.get('temps', {}).get('edge') if isinstance(stats.get('temps'), dict) else None
            if isinstance(temp, dict):
                v = temp.get('value')
                temp = v.get('current') if isinstance(v, dict) else None
            clock_stats = stats.get('clockspeed')
            clock = clock_stats.get('gpu_clockspeed') if isinstance(clock_stats, dict) else None
            load = stats.get('busy_percent')
            pieces = []
            if isinstance(temp, (int, float)) and not isinstance(temp, bool):
                pieces.append(f'GPU edge: {temp:.0f} °C')
            if isinstance(load, (int, float)) and not isinstance(load, bool):
                pieces.append(f'GPU load: {load:.0f}%')
            if isinstance(clock, (int, float)) and not isinstance(clock, bool):
                pieces.append(f'GPU clock: {clock:.0f} MHz')
            self.lact_summary.setText('  ·  '.join(pieces) + ' (snapshot)' if pieces else
                                       'Stats received; fields differ from expected schema. See JSON below.')
        else:
            self.lact_summary.setText('Statistics unavailable; see details below')
        self.lact_snapshot.setPlainText(json.dumps(result, indent=2, ensure_ascii=False))

    def toggle_monitoring(self, enabled):
        self.monitoring_on = enabled
        self.sim_indicator.setText('● LIVE SENSORS' if enabled else '● MONITORING PAUSED')
        if enabled:
            self.telemetry_tick()

    def telemetry_tick(self):
        """Only real sensor samples. Never fabricate GPU or FPS measurements."""
        if not self.monitoring_on:
            return
        gpu = read_gpu_sample()
        fps = read_live_fps()
        self.last_gpu_sample = gpu
        self.fps_card.value.setText(format_reading(fps, digits=1))
        self.temp_card.value.setText(format_reading(gpu.temperature_c))
        self.usage_card.value.setText(format_reading(gpu.usage))
        self.clock_card.value.setText(format_reading(gpu.clock_mhz))
        for card, present, source in (
            (self.fps_card, fps is not None, 'MANGOHUD'),
            (self.temp_card, gpu.temperature_c is not None, 'AMDGPU'),
            (self.usage_card, gpu.usage is not None, 'AMDGPU'),
            (self.clock_card, gpu.clock_mhz is not None, 'AMDGPU'),
        ):
            card.source.setText(source if present else 'N/A')
        if gpu.usage is not None:
            self.overview_graph.append(gpu.usage)
        elif self.overview_graph.values:
            self.overview_graph.values.clear()
            self.overview_graph.update()
        if gpu.temperature_c is not None:
            self.temperature_graph.append(gpu.temperature_c)
        elif self.temperature_graph.values:
            self.temperature_graph.values.clear()
            self.temperature_graph.update()
        if gpu.clock_mhz is not None:
            self.clock_graph.append(gpu.clock_mhz)
        elif self.clock_graph.values:
            self.clock_graph.values.clear()
            self.clock_graph.update()
        if fps is not None:
            self.performance_graph.append(fps)
        elif self.performance_graph.values:
            self.performance_graph.values.clear()
            self.performance_graph.update()
        self.sim_indicator.setText('● LIVE AMDGPU' if gpu.card else '● GPU SENSOR UNAVAILABLE')
        if hasattr(self, 'overlay_checks'):
            self.refresh_overlay_preview()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('RyuSCOPE GS')
    app.setOrganizationName('RyujinWARE')
    app.setStyle('Fusion')
    app.setStyleSheet(STYLESHEET)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
