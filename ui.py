from __future__ import annotations

import json
import math
import os
import random
import re
import sys
import threading
import time
import traceback
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from core.curriculum_loader import get_children, get_levels, get_node_by_path, get_reb_level_summaries
except Exception:
    get_children = None
    get_levels = None
    get_node_by_path = None
    get_reb_level_summaries = None

try:
    from core.local_auth import authenticate, has_accounts
except Exception:
    def authenticate(u, p):
        return bool(u.strip()), "Signed in.", "student"
    def has_accounts():
        return False

try:
    from core.profile_stats import lessons_count, quiz_average, record_quiz_score, touch_study_day
except Exception:
    def lessons_count(p):
        return len(p.get("completed_lessons", []))
    def quiz_average(p):
        scores = p.get("quiz_scores", [])
        return f"{int(sum(scores)/len(scores))}%" if scores else "—"
    def record_quiz_score(p, s):
        p.setdefault("quiz_scores", []).append(s)
    def touch_study_day(p):
        pass


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = _base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE = CONFIG_DIR / "api_keys.json"
PROFILE_FILE = CONFIG_DIR / "student_profile.json"
ASSET_DIR = BASE_DIR / "assets"
CURRICULUM_DIR = BASE_DIR / "data" / "curriculum"

_DEFAULT_W, _DEFAULT_H = 1360, 860
_MIN_W, _MIN_H = 430, 640
_LEFT_W, _LEFT_W_COMPACT = 278, 86


LIGHT = {
    "bg": "#F6F8FB",
    "bg2": "#EEF3F8",
    "surface": "#FFFFFF",
    "surface2": "#F9FBFE",
    "card": "#FFFFFF",
    "line": "#E3EAF2",
    "line2": "#CDD8E5",
    "text": "#14213D",
    "muted": "#64748B",
    "faint": "#8A98AA",
    "primary": "#19376D",
    "primary2": "#2D5B9A",
    "secondary": "#EF6C4D",
    "gold": "#F6B443",
    "teal": "#21A7A8",
    "green": "#2F9D68",
    "warning": "#D99520",
    "error": "#D94F4F",
    "purple": "#7B5FD6",
    "sky": "#EAF5FF",
    "warm": "#FFF3E6",
    "success_bg": "#E9F7EF",
    "shadow": "#16324F",
}

DARK = {
    "bg": "#0D1424",
    "bg2": "#121C2F",
    "surface": "#182338",
    "surface2": "#202D46",
    "card": "#172235",
    "line": "#2A3953",
    "line2": "#3A4C68",
    "text": "#F3F7FB",
    "muted": "#B9C5D5",
    "faint": "#8796AA",
    "primary": "#7DAAF5",
    "primary2": "#A3C4FA",
    "secondary": "#FF8C69",
    "gold": "#F6C35D",
    "teal": "#4DC9C9",
    "green": "#56C18B",
    "warning": "#F0B94A",
    "error": "#FF7070",
    "purple": "#A694F2",
    "sky": "#172D45",
    "warm": "#342418",
    "success_bg": "#173425",
    "shadow": "#000000",
}


def asset(*parts: str) -> Path:
    return ASSET_DIR.joinpath(*parts)


def app_font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont("Segoe UI", size, weight)
    font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 100)
    return font


def safe_exec(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            print(traceback.format_exc())
    return wrapper


def qcol(hex_color: str, alpha: int = 255) -> QColor:
    color = QColor(hex_color)
    color.setAlpha(alpha)
    return color


def apply_shadow(widget: QWidget, color: str = "#16324F", blur: int = 30, y: int = 14, alpha: int = 30):
    effect = QGraphicsDropShadowEffect(widget)
    c = QColor(color)
    c.setAlpha(alpha)
    effect.setColor(c)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y)
    widget.setGraphicsEffect(effect)


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        child_layout = item.layout()
        widget = item.widget()
        if child_layout is not None:
            clear_layout(child_layout)
        if widget is not None:
            widget.deleteLater()


def _short(text: str, limit: int = 62) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _load_json(path: Path, fallback):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return fallback


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _draw_icon(p: QPainter, name: str, r: QRectF, color: QColor, stroke: float = 2.0):
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color, stroke, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    x, y, w, h = r.x(), r.y(), r.width(), r.height()
    cx, cy = x + w / 2, y + h / 2

    if name == "home":
        path = QPainterPath()
        path.moveTo(x + w * 0.15, y + h * 0.48)
        path.lineTo(cx, y + h * 0.18)
        path.lineTo(x + w * 0.85, y + h * 0.48)
        p.drawPath(path)
        p.drawRoundedRect(QRectF(x + w * 0.27, y + h * 0.46, w * 0.46, h * 0.38), 3, 3)
    elif name in {"learn", "book"}:
        p.drawRoundedRect(QRectF(x + w * 0.12, y + h * 0.22, w * 0.34, h * 0.56), 3, 3)
        p.drawRoundedRect(QRectF(x + w * 0.54, y + h * 0.22, w * 0.34, h * 0.56), 3, 3)
        p.drawLine(QPointF(cx, y + h * 0.25), QPointF(cx, y + h * 0.82))
        p.drawLine(QPointF(x + w * 0.2, y + h * 0.38), QPointF(x + w * 0.39, y + h * 0.38))
        p.drawLine(QPointF(x + w * 0.61, y + h * 0.38), QPointF(x + w * 0.8, y + h * 0.38))
    elif name == "classroom":
        p.drawRoundedRect(QRectF(x + w * 0.16, y + h * 0.2, w * 0.68, h * 0.43), 3, 3)
        p.drawLine(QPointF(cx, y + h * 0.63), QPointF(cx, y + h * 0.82))
        p.drawLine(QPointF(x + w * 0.34, y + h * 0.82), QPointF(x + w * 0.66, y + h * 0.82))
    elif name == "quizzes":
        p.drawEllipse(QRectF(x + w * 0.16, y + h * 0.16, w * 0.68, h * 0.68))
        p.drawLine(QPointF(x + w * 0.34, y + h * 0.52), QPointF(x + w * 0.46, y + h * 0.64))
        p.drawLine(QPointF(x + w * 0.46, y + h * 0.64), QPointF(x + w * 0.68, y + h * 0.38))
    elif name == "missions":
        p.drawEllipse(QRectF(x + w * 0.18, y + h * 0.18, w * 0.64, h * 0.64))
        p.drawEllipse(QRectF(x + w * 0.34, y + h * 0.34, w * 0.32, h * 0.32))
        p.drawLine(QPointF(cx, cy), QPointF(x + w * 0.86, y + h * 0.14))
        p.drawLine(QPointF(x + w * 0.78, y + h * 0.14), QPointF(x + w * 0.86, y + h * 0.14))
        p.drawLine(QPointF(x + w * 0.86, y + h * 0.14), QPointF(x + w * 0.86, y + h * 0.22))
    elif name == "progress":
        p.drawLine(QPointF(x + w * 0.18, y + h * 0.8), QPointF(x + w * 0.82, y + h * 0.8))
        p.drawLine(QPointF(x + w * 0.18, y + h * 0.8), QPointF(x + w * 0.18, y + h * 0.2))
        pts = [QPointF(x + w * 0.25, y + h * 0.68), QPointF(x + w * 0.42, y + h * 0.5), QPointF(x + w * 0.57, y + h * 0.58), QPointF(x + w * 0.76, y + h * 0.31)]
        for a, b in zip(pts, pts[1:]):
            p.drawLine(a, b)
    elif name == "community":
        p.drawEllipse(QRectF(x + w * 0.38, y + h * 0.18, w * 0.24, h * 0.24))
        p.drawArc(QRectF(x + w * 0.25, y + h * 0.44, w * 0.5, h * 0.35), 0, 180 * 16)
        p.drawEllipse(QRectF(x + w * 0.12, y + h * 0.36, w * 0.2, h * 0.2))
        p.drawEllipse(QRectF(x + w * 0.68, y + h * 0.36, w * 0.2, h * 0.2))
    elif name == "resources":
        p.drawRoundedRect(QRectF(x + w * 0.23, y + h * 0.14, w * 0.5, h * 0.72), 3, 3)
        p.drawLine(QPointF(x + w * 0.32, y + h * 0.36), QPointF(x + w * 0.64, y + h * 0.36))
        p.drawLine(QPointF(x + w * 0.32, y + h * 0.52), QPointF(x + w * 0.64, y + h * 0.52))
        p.drawLine(QPointF(x + w * 0.32, y + h * 0.68), QPointF(x + w * 0.54, y + h * 0.68))
    elif name == "rina":
        p.drawRoundedRect(QRectF(x + w * 0.36, y + h * 0.13, w * 0.28, h * 0.48), 8, 8)
        p.drawArc(QRectF(x + w * 0.24, y + h * 0.39, w * 0.52, h * 0.34), 190 * 16, 160 * 16)
        p.drawLine(QPointF(cx, y + h * 0.72), QPointF(cx, y + h * 0.84))
        p.drawLine(QPointF(x + w * 0.38, y + h * 0.84), QPointF(x + w * 0.62, y + h * 0.84))
    elif name == "profile":
        p.drawEllipse(QRectF(x + w * 0.34, y + h * 0.18, w * 0.32, h * 0.32))
        p.drawArc(QRectF(x + w * 0.2, y + h * 0.48, w * 0.6, h * 0.42), 20 * 16, 140 * 16)
    elif name == "settings":
        p.drawEllipse(QRectF(x + w * 0.35, y + h * 0.35, w * 0.3, h * 0.3))
        for i in range(8):
            a = i * math.pi / 4
            p.drawLine(QPointF(cx + math.cos(a) * w * 0.26, cy + math.sin(a) * h * 0.26),
                       QPointF(cx + math.cos(a) * w * 0.38, cy + math.sin(a) * h * 0.38))
    elif name == "search":
        p.drawEllipse(QRectF(x + w * 0.18, y + h * 0.18, w * 0.45, h * 0.45))
        p.drawLine(QPointF(x + w * 0.58, y + h * 0.58), QPointF(x + w * 0.82, y + h * 0.82))
    elif name == "play":
        p.setBrush(QBrush(color))
        path = QPainterPath()
        path.moveTo(x + w * 0.34, y + h * 0.22)
        path.lineTo(x + w * 0.76, cy)
        path.lineTo(x + w * 0.34, y + h * 0.78)
        path.closeSubpath()
        p.drawPath(path)
    elif name == "sound":
        p.drawLine(QPointF(x + w * 0.2, y + h * 0.45), QPointF(x + w * 0.35, y + h * 0.45))
        p.drawLine(QPointF(x + w * 0.2, y + h * 0.55), QPointF(x + w * 0.35, y + h * 0.55))
        p.drawLine(QPointF(x + w * 0.35, y + h * 0.45), QPointF(x + w * 0.5, y + h * 0.3))
        p.drawLine(QPointF(x + w * 0.5, y + h * 0.3), QPointF(x + w * 0.5, y + h * 0.7))
        p.drawLine(QPointF(x + w * 0.5, y + h * 0.7), QPointF(x + w * 0.35, y + h * 0.55))
        p.drawArc(QRectF(x + w * 0.53, y + h * 0.32, w * 0.22, h * 0.36), -45 * 16, 90 * 16)
        p.drawArc(QRectF(x + w * 0.58, y + h * 0.22, w * 0.28, h * 0.56), -45 * 16, 90 * 16)
    elif name == "upload":
        p.drawLine(QPointF(cx, y + h * 0.18), QPointF(cx, y + h * 0.62))
        p.drawLine(QPointF(cx, y + h * 0.18), QPointF(x + w * 0.34, y + h * 0.34))
        p.drawLine(QPointF(cx, y + h * 0.18), QPointF(x + w * 0.66, y + h * 0.34))
        p.drawRoundedRect(QRectF(x + w * 0.18, y + h * 0.66, w * 0.64, h * 0.17), 3, 3)
    else:
        p.drawEllipse(QRectF(x + w * 0.22, y + h * 0.22, w * 0.56, h * 0.56))


def make_icon(name: str, color: str, size: int = 22) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    _draw_icon(painter, name, QRectF(2, 2, size - 4, size - 4), QColor(color), 1.8)
    painter.end()
    return QIcon(pix)


class SoundEngine:
    def __init__(self):
        self.enabled = False

    def play(self, kind: str = "click"):
        return

    def _play(self, kind: str):
        try:
            if os.name == "nt":
                import winsound

                sequences = {
                    "click": [(660, 35)],
                    "success": [(740, 55), (988, 85)],
                    "xp": [(523, 45), (659, 45), (784, 90)],
                    "error": [(220, 110)],
                }
                for freq, duration in sequences.get(kind, sequences["click"]):
                    winsound.Beep(freq, duration)
                    time.sleep(0.025)
            else:
                QApplication.beep()
        except Exception:
            try:
                QApplication.beep()
            except Exception:
                pass


class LearningBackground(QWidget):
    def __init__(self, t: dict, parent=None):
        super().__init__(parent)
        self.t = t
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._tick = 0.0
        self._timer = QTimer(self)

    def set_theme(self, t: dict):
        self.t = t
        self.update()

    def _step(self):
        return

    @safe_exec
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0.0, QColor(self.t["bg"]))
        bg.setColorAt(0.64, QColor(self.t["bg2"]))
        bg.setColorAt(1.0, QColor(self.t["warm"]))
        p.fillRect(self.rect(), bg)

        p.setPen(QPen(qcol(self.t["line"], 70), 1))
        for x in range(-80, w + 160, 104):
            p.drawLine(QPointF(x, 0), QPointF(x + 80, h))
        p.setPen(Qt.PenStyle.NoPen)
        wash = QLinearGradient(0, h * 0.18, w, h * 0.95)
        wash.setColorAt(0.0, qcol(self.t["sky"], 130))
        wash.setColorAt(0.46, QColor(255, 255, 255, 0))
        wash.setColorAt(1.0, qcol(self.t["warm"], 115))
        p.setBrush(QBrush(wash))
        p.drawRect(self.rect())


class Card(QFrame):
    def __init__(self, t: dict, name: str = "Card", elevated: bool = True, parent=None):
        super().__init__(parent)
        self.t = t
        self.setObjectName(name)
        self.setStyleSheet(self._style())
        if elevated:
            apply_shadow(self, t["shadow"], 28, 10, 28)

    def _style(self) -> str:
        return f"""
            QFrame#{self.objectName()} {{
                background: {self.t["card"]};
                border: 1px solid {self.t["line"]};
                border-radius: 8px;
            }}
            QFrame#{self.objectName()} QLabel {{
                background: transparent;
                border: none;
                color: {self.t["text"]};
            }}
        """


class ImageCard(Card):
    def __init__(self, t: dict, image_path: Path | None, title: str = "", subtitle: str = "", parent=None):
        super().__init__(t, "ImageCard", True, parent)
        self.image_path = image_path
        self.pix = QPixmap(str(image_path)) if image_path and image_path.exists() and image_path.stat().st_size > 0 else QPixmap()
        self.title = title
        self.subtitle = subtitle
        self.setMinimumHeight(190)

    @safe_exec
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, 8, 8)
        p.setClipPath(path)

        if not self.pix.isNull():
            scaled = self.pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
        else:
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(0, QColor(self.t["primary"]))
            grad.setColorAt(1, QColor(self.t["secondary"]))
            p.fillRect(self.rect(), grad)

        overlay = QLinearGradient(0, 0, self.width(), self.height())
        overlay.setColorAt(0.0, QColor(8, 18, 38, 185))
        overlay.setColorAt(0.55, QColor(8, 18, 38, 90))
        overlay.setColorAt(1.0, QColor(8, 18, 38, 30))
        p.fillRect(self.rect(), overlay)
        p.setClipping(False)
        p.setPen(QPen(QColor(self.t["line"]), 1))
        p.drawRoundedRect(r, 8, 8)


class AvatarWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, t: dict, profile: dict, size: int = 52, parent=None):
        super().__init__(parent)
        self.t = t
        self.profile = profile
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    @safe_exec
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        path = QPainterPath()
        path.addEllipse(r)
        p.setClipPath(path)

        avatar_path = self.profile.get("avatar_path", "")
        pix = QPixmap(avatar_path) if avatar_path and Path(avatar_path).exists() else QPixmap()
        if not pix.isNull():
            scaled = pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap((self.width() - scaled.width()) // 2, (self.height() - scaled.height()) // 2, scaled)
        else:
            c1 = QColor(self.profile.get("avatar_color", self.t["secondary"]))
            c2 = QColor(self.t["primary"])
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            p.fillRect(self.rect(), grad)
            initials = "".join([part[:1] for part in self.profile.get("username", "Student").split()[:2]]).upper() or "S"
            p.setPen(QColor("white"))
            p.setFont(app_font(max(11, self.width() // 4), QFont.Weight.Bold))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, initials)
        p.setClipping(False)
        p.setPen(QPen(QColor("#FFFFFF"), 3))
        p.drawEllipse(r)


class NavButton(QPushButton):
    def __init__(self, t: dict, key: str, label: str, icon: str, parent=None):
        super().__init__(label, parent)
        self.t = t
        self.key = key
        self.label_text = label
        self.icon_name = icon
        self.active = False
        self.compact = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setIconSize(QSize(22, 22))
        self.setFont(app_font(10, QFont.Weight.Medium))
        self.setToolTip(label)
        self.refresh()

    def set_active(self, active: bool):
        self.active = active
        self.refresh()

    def set_compact(self, compact: bool):
        self.compact = compact
        self.setText("" if compact else self.label_text)
        self.setFixedWidth(50 if compact else 230)
        self.refresh()

    def refresh(self):
        fg = "#FFFFFF" if self.active else self.t["muted"]
        bg = self.t["primary"] if self.active else "transparent"
        hover = self.t["surface2"]
        self.setIcon(make_icon(self.icon_name, fg if self.active else self.t["primary"], 22))
        pad = "0px" if self.compact else "0 14px"
        align = "center" if self.compact else "left"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: none;
                border-radius: 8px;
                padding: {pad};
                text-align: {align};
            }}
            QPushButton:hover {{
                background: {self.t["primary"] if self.active else hover};
                color: {fg if self.active else self.t["text"]};
            }}
        """)


class IconButton(QPushButton):
    def __init__(self, t: dict, label: str, icon: str, accent: str | None = None, parent=None):
        super().__init__(label, parent)
        self.t = t
        self.icon_name = icon
        self.accent = accent or t["primary"]
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIcon(make_icon(icon, self.accent, 21))
        self.setIconSize(QSize(21, 21))
        self.setFixedHeight(42)
        self.setFont(app_font(9, QFont.Weight.Bold))
        self.setStyleSheet(f"""
            QPushButton {{
                background: {t["surface"]};
                color: {t["text"]};
                border: 1px solid {t["line"]};
                border-radius: 8px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background: {t["surface2"]};
                border-color: {self.accent};
            }}
        """)


class PrimaryButton(QPushButton):
    def __init__(self, t: dict, label: str, icon: str | None = None, accent: str | None = None, parent=None):
        super().__init__(label, parent)
        self.t = t
        self.accent = accent or t["primary"]
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setFont(app_font(10, QFont.Weight.Bold))
        if icon:
            self.setIcon(make_icon(icon, "#FFFFFF", 22))
            self.setIconSize(QSize(22, 22))
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self.accent};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background: {t["primary2"]};
            }}
            QPushButton:disabled {{
                background: {t["line2"]};
                color: {t["faint"]};
            }}
        """)


class ProgressRing(QWidget):
    def __init__(self, t: dict, value: int, label: str, accent: str, parent=None):
        super().__init__(parent)
        self.t = t
        self.value = value
        self.label = label
        self.accent = accent
        self.setMinimumSize(118, 118)

    @safe_exec
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(14, 10, self.width() - 28, self.height() - 28)
        p.setPen(QPen(QColor(self.t["line"]), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(r, 0, 360 * 16)
        p.setPen(QPen(QColor(self.accent), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(r, 90 * 16, int(-360 * 16 * self.value / 100))
        p.setPen(QColor(self.t["text"]))
        p.setFont(app_font(18, QFont.Weight.Bold))
        p.drawText(QRectF(0, 24, self.width(), 34), Qt.AlignmentFlag.AlignCenter, f"{self.value}%")
        p.setPen(QColor(self.t["muted"]))
        p.setFont(app_font(8, QFont.Weight.Medium))
        p.drawText(QRectF(4, 64, self.width() - 8, 30), Qt.AlignmentFlag.AlignCenter, self.label)


class BarChart(QWidget):
    def __init__(self, t: dict, values: list[tuple[str, int, str]], parent=None):
        super().__init__(parent)
        self.t = t
        self.values = values
        self.setMinimumHeight(190)

    @safe_exec
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m = 28
        available = max(1, self.width() - m * 2)
        bar_w = max(18, min(54, available / max(1, len(self.values)) - 14))
        max_h = self.height() - 66
        x = m
        p.setFont(app_font(8, QFont.Weight.Medium))
        for label, value, color in self.values:
            h = max_h * value / 100
            r = QRectF(x, self.height() - 36 - h, bar_w, h)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(self.t["line"]))
            p.drawRoundedRect(QRectF(x, 20, bar_w, max_h), 6, 6)
            p.setBrush(QColor(color))
            p.drawRoundedRect(r, 6, 6)
            p.setPen(QColor(self.t["muted"]))
            p.drawText(QRectF(x - 10, self.height() - 30, bar_w + 20, 22), Qt.AlignmentFlag.AlignCenter, label)
            x += bar_w + 14


class VoiceWave(QWidget):
    def __init__(self, t: dict, parent=None):
        super().__init__(parent)
        self.t = t
        self.active = False
        self.phase = 0.0
        self.setMinimumHeight(150)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(45)

    def _step(self):
        self.phase += 0.12
        self.update()

    @safe_exec
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) * 0.34
        grad = QRadialGradient(center, radius * 1.9)
        grad.setColorAt(0.0, qcol(self.t["primary"], 70 if self.active else 35))
        grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(center, radius * 1.75, radius * 1.75)
        p.setBrush(QColor(self.t["surface"]))
        p.setPen(QPen(QColor(self.t["line"]), 1))
        p.drawEllipse(center, radius, radius)
        p.setPen(QPen(QColor(self.t["primary"]), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for i in range(9):
            x = center.x() - 42 + i * 10.5
            amp = 14 + (math.sin(self.phase + i * 0.7) + 1) * (16 if self.active else 4)
            p.drawLine(QPointF(x, center.y() - amp / 2), QPointF(x, center.y() + amp / 2))


class MathDiagramWidget(QWidget):
    """QPainter-rendered math diagram — unit circle, triangles, cartesian graphs,
    geometry figures, Venn diagrams, number lines, transformations, angle diagrams."""

    def __init__(self, t: dict, diagram_type: str = "unit_circle", params: dict | None = None, parent=None):
        super().__init__(parent)
        self.t = t
        self.diagram_type = diagram_type
        self.params = params or {}
        self.setMinimumSize(260, 200)
        self.setStyleSheet("background: transparent;")

    def set_diagram(self, diagram_type: str, params: dict | None = None):
        self.diagram_type = diagram_type
        if params:
            self.params.update(params)
        self.update()

    @safe_exec
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        method = getattr(self, f"_draw_{self.diagram_type}", None)
        if method:
            method(p)
        else:
            self._draw_label(p, f"Diagram: {self.diagram_type}")

    def _draw_label(self, p: QPainter, text: str):
        p.setPen(QColor(self.t["muted"]))
        p.setFont(QFont("Consolas", 9))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

    # ─── 1. UNIT CIRCLE ────────────────────────────────────────────────
    def _draw_unit_circle(self, p: QPainter):
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) * 0.38
        angle = self.params.get("angle", 45)
        show_sin = self.params.get("show_sin", True)
        show_cos = self.params.get("show_cos", True)
        show_tan = self.params.get("show_tan", False)

        # Axes
        p.setPen(QPen(QColor(self.t["line"]), 1))
        p.drawLine(QPointF(cx - r * 1.2, cy), QPointF(cx + r * 1.2, cy))
        p.drawLine(QPointF(cx, cy - r * 1.2), QPointF(cx, cy + r * 1.2))

        # Circle
        p.setPen(QPen(QColor(self.t["text"]), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Angle arc
        rad = math.radians(angle)
        arc_r = r * 0.18
        p.setPen(QPen(QColor(self.t["primary"]), 2))
        p.drawArc(QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2),
                  int(90 * 16), int(-angle * 16))

        # Terminal side
        tx = cx + r * math.cos(rad)
        ty = cy - r * math.sin(rad)
        p.setPen(QPen(QColor(self.t["primary"]), 2))
        p.drawLine(QPointF(cx, cy), QPointF(tx, ty))

        # Sin line (vertical)
        if show_sin:
            p.setPen(QPen(QColor("#E53935"), 2, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(tx, ty), QPointF(tx, cy))

        # Cos line (horizontal)
        if show_cos:
            p.setPen(QPen(QColor("#1E88E5"), 2, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(tx, cy), QPointF(cx, cy))

        # Tan line (tangent)
        if show_tan:
            tan_x = cx + r / math.cos(rad)
            tan_y = cy - r * math.tan(rad)
            p.setPen(QPen(QColor("#43A047"), 2, Qt.PenStyle.DashDotLine))
            p.drawLine(QPointF(cx, cy), QPointF(tan_x, tan_y))

        # Labels
        f = QFont("Consolas", 8)
        p.setFont(f)
        p.setPen(QColor(self.t["muted"]))
        p.drawText(QPointF(cx + r + 6, cy + 4), "(1,0)")
        p.drawText(QPointF(cx - 22, cy - r - 4), "(0,1)")
        # Angle label near arc
        p.setPen(QColor(self.t["primary"]))
        lbl_ang = arc_r * 1.5
        la = math.radians(45)
        p.drawText(QPointF(cx + lbl_ang * 0.7, cy - lbl_ang * 0.7), f"{angle}°")

        if show_sin:
            p.setPen(QColor("#E53935"))
            p.drawText(QPointF(tx + 4, (ty + cy) / 2), "sin")
        if show_cos:
            p.setPen(QColor("#1E88E5"))
            p.drawText(QPointF((tx + cx) / 2, cy + 14), "cos")

        # labels on axes
        axis_f = QFont("Consolas", 7)
        p.setFont(axis_f)
        p.setPen(QColor(self.t["muted"]))
        p.drawText(QPointF(cx - r - 6, cy + 4), "-1")
        p.drawText(QPointF(cx + r - 4, cy + 4), "1")
        p.drawText(QPointF(cx - 10, cy - r + 4), "1")
        p.drawText(QPointF(cx - 12, cy + r + 12), "-1")

    # ─── 2. TRIANGLE (right triangle with labels) ──────────────────────
    def _draw_triangle(self, p: QPainter):
        w, h = self.width(), self.height()
        pad = 36
        a = self.params.get("a", 3)
        b = self.params.get("b", 4)
        c = self.params.get("c", 5)
        angle_a = self.params.get("angle_A", None)

        max_side = max(a, b, c)
        scale = min((w - pad * 2) / max_side, (h - pad * 2) / max_side)
        # Right triangle with legs along axes
        x0, y0 = pad + 10, h - pad - 10  # origin (bottom-left)
        x1 = x0 + b * scale  # horizontal leg end
        y1 = y0  # same y
        x2 = x0  # same x
        y2 = y0 - a * scale  # vertical leg end

        p.setPen(QPen(QColor(self.t["text"]), 2))
        p.setBrush(QBrush(QColor(self.t["card"])))
        pts = [QPointF(x0, y0), QPointF(x1, y1), QPointF(x0, y2)]
        p.drawPolygon(*pts)

        # Right angle marker
        s = 8
        p.setPen(QPen(QColor(self.t["muted"]), 1))
        p.drawLine(QPointF(x0 + s, y0), QPointF(x0 + s, y0 - s))
        p.drawLine(QPointF(x0, y0 - s), QPointF(x0 + s, y0 - s))

        # Side labels
        f = QFont("Consolas", 9, QFont.Weight.Bold)
        p.setFont(f)
        p.setPen(QColor(self.t["text"]))
        # label a (vertical leg)
        p.drawText(QRectF(x0 - 30, (y0 + y2) / 2 - 10, 24, 20),
                   Qt.AlignmentFlag.AlignCenter, f"a = {a}")
        # label b (horizontal leg)
        p.drawText(QRectF((x0 + x1) / 2 - 20, y0 + 8, 40, 20),
                   Qt.AlignmentFlag.AlignCenter, f"b = {b}")
        # label c (hypotenuse)
        cmx, cmy = (x1 + x2) / 2, (y1 + y2) / 2
        p.drawText(QRectF(cmx + 6, cmy - 10, 40, 20),
                   Qt.AlignmentFlag.AlignCenter, f"c = {c}")

        # Angle labels
        sm_f = QFont("Consolas", 8)
        p.setFont(sm_f)
        p.setPen(QColor(self.t["primary"]))
        if angle_a is not None:
            p.drawText(QPointF(x0 + b * scale * 0.3 + 6, y0 - 8), f"θ = {angle_a}°")
        p.drawText(QPointF(x0 - 16, y0 - a * scale * 0.3 + 4), "α")

    # ─── 3. CARTESIAN GRAPH ────────────────────────────────────────────
    def _draw_cartesian(self, p: QPainter):
        w, h = self.width(), self.height()
        pad = 44
        gw = w - pad * 2
        gh = h - pad * 2
        x0, y0 = pad, h - pad  # origin (bottom-left)

        # Grid
        p.setPen(QPen(QColor(self.t["line"]), 1, Qt.PenStyle.DotLine))
        x_min = self.params.get("x_min", -5)
        x_max = self.params.get("x_max", 5)
        y_min = self.params.get("y_min", -5)
        y_max = self.params.get("y_max", 5)
        x_range = x_max - x_min
        y_range = y_max - y_min

        def to_screen(px, py):
            sx = x0 + (px - x_min) / x_range * gw
            sy = y0 - (py - y_min) / y_range * gh
            return sx, sy

        # Grid lines
        for v in range(x_min, x_max + 1):
            sx, _ = to_screen(v, 0)
            p.drawLine(QPointF(sx, pad), QPointF(sx, h - pad))
        for v in range(y_min, y_max + 1):
            _, sy = to_screen(0, v)
            p.drawLine(QPointF(pad, sy), QPointF(w - pad, sy))

        # Axes
        p.setPen(QPen(QColor(self.t["text"]), 1.5))
        ox, oy = to_screen(0, 0)
        p.drawLine(QPointF(pad, oy), QPointF(w - pad, oy))
        p.drawLine(QPointF(ox, pad), QPointF(ox, h - pad))

        # Tick labels
        f = QFont("Consolas", 7)
        p.setFont(f)
        p.setPen(QColor(self.t["muted"]))
        for v in range(max(x_min, -10), min(x_max + 1, 11)):
            if v == 0:
                continue
            sx, _ = to_screen(v, 0)
            p.drawText(QRectF(sx - 10, oy + 3, 20, 16),
                       Qt.AlignmentFlag.AlignCenter, str(v))
        for v in range(max(y_min, -10), min(y_max + 1, 11)):
            if v == 0:
                continue
            _, sy = to_screen(0, v)
            p.drawText(QRectF(ox - 22, sy - 8, 20, 16),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(v))

        # Plot points / function
        p.setPen(QPen(QColor(self.t["primary"]), 2.5))
        points = self.params.get("points", None)
        func_expr = self.params.get("function", None)

        if points:
            for pt in points:
                sx, sy = to_screen(pt[0], pt[1])
                p.drawEllipse(QPointF(sx, sy), 3, 3)

        if func_expr and func_expr == "linear":
            # Draw y = mx + c
            m = self.params.get("m", 1)
            c_val = self.params.get("c", 0)
            x1_p = x_min
            y1_p = m * x1_p + c_val
            x2_p = x_max
            y2_p = m * x2_p + c_val
            sx1, sy1 = to_screen(x1_p, y1_p)
            sx2, sy2 = to_screen(x2_p, y2_p)
            p.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

        if func_expr and func_expr == "quadratic":
            a_v = self.params.get("a", 1)
            b_v = self.params.get("b", 0)
            c_val = self.params.get("c", 0)
            steps = 80
            prev_sx, prev_sy = None, None
            for i in range(steps + 1):
                px = x_min + i / steps * x_range
                py = a_v * px * px + b_v * px + c_val
                sx, sy = to_screen(px, py)
                if prev_sx is not None and y_min <= py <= y_max:
                    p.drawLine(QPointF(prev_sx, prev_sy), QPointF(sx, sy))
                prev_sx, prev_sy = sx, sy

    # ─── 4. GEOMETRY FIGURE ────────────────────────────────────────────
    def _draw_geometry(self, p: QPainter):
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) * 0.36
        shape = self.params.get("shape", "circle")

        if shape == "circle":
            p.setPen(QPen(QColor(self.t["text"]), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r, r)

            # Center label
            p.setPen(QColor(self.t["muted"]))
            f = QFont("Consolas", 8)
            p.setFont(f)
            p.drawText(QPointF(cx - 4, cy + 4), "O")

            # Draw a diameter
            angle = self.params.get("diameter_angle", 30)
            rad = math.radians(angle)
            x1 = cx + r * math.cos(rad)
            y1 = cy - r * math.sin(rad)
            x2 = cx - r * math.cos(rad)
            y2 = cy + r * math.sin(rad)
            p.setPen(QPen(QColor(self.t["primary"]), 2, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        elif shape == "inscribed_triangle":
            p.setPen(QPen(QColor(self.t["text"]), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r, r)

            # Three points on circle
            ang = [0, 120, 240]
            pts = []
            for a in ang:
                rad2 = math.radians(a)
                pts.append(QPointF(cx + r * math.cos(rad2), cy - r * math.sin(rad2)))
            p.setPen(QPen(QColor(self.t["primary"]), 2))
            for i in range(3):
                j = (i + 1) % 3
                p.drawLine(pts[i], pts[j])

            # Vertex labels
            f = QFont("Consolas", 8)
            p.setFont(f)
            p.setPen(QColor(self.t["text"]))
            for i, label in enumerate(["A", "B", "C"]):
                dx = pts[i].x() - cx
                dy = pts[i].y() - cy
                off_x = 8 if dx > 0 else -20
                off_y = 10 if dy > 0 else -6
                p.drawText(QPointF(pts[i].x() + off_x, pts[i].y() + off_y), label)

        elif shape == "chords":
            p.setPen(QPen(QColor(self.t["text"]), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r, r)
            # Draw intersecting chords
            n = self.params.get("n", 4)
            chord_angles = [i * 360 / n for i in range(n)]
            pts = []
            for a in chord_angles:
                rad2 = math.radians(a)
                pts.append(QPointF(cx + r * math.cos(rad2), cy - r * math.sin(rad2)))
            p.setPen(QPen(QColor(self.t["primary"]), 1.5))
            for i in range(n):
                for j in range(i + 1, n):
                    p.drawLine(pts[i], pts[j])

    # ─── 5. VENN DIAGRAM ───────────────────────────────────────────────
    def _draw_venn(self, p: QPainter):
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        sets = self.params.get("sets", 2)
        values = self.params.get("values", {})
        r = min(w, h) * 0.2

        p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))

        if sets == 2:
            # Two overlapping circles
            dx = r * 0.45
            c1 = QPointF(cx - dx, cy)
            c2 = QPointF(cx + dx, cy)

            p.setPen(QPen(QColor(self.t["text"]), 1.5))
            p.setBrush(QBrush(QColor(self.t["surface"])))
            p.drawEllipse(c1, r, r)
            p.drawEllipse(c2, r, r)

            p.setPen(QColor(self.t["text"]))
            p.setFont(QFont("Consolas", 8))
            # Region labels (from values)
            only_a = values.get("A", "")
            only_b = values.get("B", "")
            both = values.get("AB", "")
            outside = values.get("outside", "")

            if only_a:
                p.drawText(QRectF(c1.x() - r, c1.y() - r, r * 0.8, r * 2),
                           Qt.AlignmentFlag.AlignCenter, str(only_a))
            if only_b:
                p.drawText(QRectF(c2.x() - r * 0.2, c2.y() - r, r * 0.8, r * 2),
                           Qt.AlignmentFlag.AlignCenter, str(only_b))
            if both:
                p.drawText(QRectF(c1.x() - 14, c1.y() - 10, 28, 20),
                           Qt.AlignmentFlag.AlignCenter, str(both))
            if outside:
                p.setPen(QColor(self.t["muted"]))
                p.drawText(QPointF(6, 14), str(outside))

            # Set labels
            p.setPen(QColor(self.t["primary"]))
            p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            p.drawText(QRectF(c1.x() - r, c1.y() - r - 16, r * 2, 14),
                       Qt.AlignmentFlag.AlignCenter, "A")
            p.drawText(QRectF(c2.x() - r, c2.y() - r - 16, r * 2, 14),
                       Qt.AlignmentFlag.AlignCenter, "B")

        elif sets == 3:
            # Three overlapping circles
            r2 = min(w, h) * 0.18
            d = r2 * 0.55
            centers = [
                QPointF(cx, cy - d),
                QPointF(cx - d * 1.1, cy + d * 0.6),
                QPointF(cx + d * 1.1, cy + d * 0.6),
            ]
            p.setPen(QPen(QColor(self.t["text"]), 1.5))
            p.setBrush(QBrush(QColor(self.t["surface"])))
            for c in centers:
                p.drawEllipse(c, r2, r2)

            p.setFont(QFont("Consolas", 8))
            p.setPen(QColor(self.t["text"]))
            vals = self.params.get("values", {})
            if vals.get("A"):
                p.drawText(QRectF(centers[0].x() - r2, centers[0].y() - r2, r2, r2),
                           Qt.AlignmentFlag.AlignCenter, str(vals["A"]))
            if vals.get("B"):
                p.drawText(QRectF(centers[1].x() - r2, centers[1].y() - r2, r2, r2),
                           Qt.AlignmentFlag.AlignCenter, str(vals["B"]))
            if vals.get("C"):
                p.drawText(QRectF(centers[2].x() - r2, centers[2].y() - r2, r2, r2),
                           Qt.AlignmentFlag.AlignCenter, str(vals["C"]))

            p.setPen(QColor(self.t["primary"]))
            p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            for i, lbl in enumerate(["A", "B", "C"]):
                c = centers[i]
                p.drawText(QRectF(c.x() - r2, c.y() - r2 - 14, r2 * 2, 14),
                           Qt.AlignmentFlag.AlignCenter, lbl)

    # ─── 6. NUMBER LINE ────────────────────────────────────────────────
    def _draw_number_line(self, p: QPainter):
        w, h = self.width(), self.height()
        pad = 36
        yc = h / 2
        x_min = self.params.get("min", -5)
        x_max = self.params.get("max", 5)
        marks = self.params.get("marks", [])
        if not marks:
            marks = list(range(x_min, x_max + 1))

        x_range = x_max - x_min
        if x_range == 0:
            x_range = 1
        gw = w - pad * 2

        def to_x(v):
            return pad + (v - x_min) / x_range * gw

        # Line
        p.setPen(QPen(QColor(self.t["text"]), 2))
        p.drawLine(QPointF(pad, yc), QPointF(w - pad, yc))

        # Arrowheads
        p.drawLine(QPointF(pad - 6, yc - 5), QPointF(pad, yc))
        p.drawLine(QPointF(pad - 6, yc + 5), QPointF(pad, yc))
        p.drawLine(QPointF(w - pad + 6, yc - 5), QPointF(w - pad, yc))
        p.drawLine(QPointF(w - pad + 6, yc + 5), QPointF(w - pad, yc))

        # Tick marks and labels
        f = QFont("Consolas", 8)
        p.setFont(f)
        for v in marks:
            if v < x_min or v > x_max:
                continue
            sx = to_x(v)
            p.setPen(QPen(QColor(self.t["text"]), 1.5))
            p.drawLine(QPointF(sx, yc - 6), QPointF(sx, yc + 6))
            if v != 0:
                p.setPen(QColor(self.t["muted"]))
                p.drawText(QRectF(sx - 14, yc + 10, 28, 16),
                           Qt.AlignmentFlag.AlignCenter, str(v))
            else:
                p.setPen(QColor(self.t["muted"]))
                p.drawText(QRectF(sx - 14, yc + 10, 28, 16),
                           Qt.AlignmentFlag.AlignCenter, "0")

        # Highlighted points
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(self.t["primary"])))
        highlighted = self.params.get("highlight", [])
        for v in highlighted:
            sx = to_x(v)
            p.drawEllipse(QPointF(sx, yc), 5, 5)

        p.setPen(QColor(self.t["primary"]))
        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        for v in highlighted:
            sx = to_x(v)
            p.drawText(QRectF(sx - 20, yc - 26, 40, 16),
                       Qt.AlignmentFlag.AlignCenter, str(v))

    # ─── 7. TRANSFORMATION ─────────────────────────────────────────────
    def _draw_transformation(self, p: QPainter):
        w, h = self.width(), self.height()
        pad = 30
        t_type = self.params.get("type", "translation")
        # Draw original shape (triangle) in primary, transformed in secondary

        def draw_shape(painter, pts, color, label=""):
            painter.setPen(QPen(QColor(color), 2))
            painter.setBrush(QBrush(QColor(color), Qt.BrushStyle.Dense4Pattern))
            qpts = [QPointF(x, y) for x, y in pts]
            if len(qpts) >= 3:
                painter.drawPolygon(*qpts)
            # Draw points
            for pt in qpts:
                painter.drawEllipse(pt, 3, 3)

        # Define original shape
        orig = self.params.get("shape", [(100, 140), (160, 140), (130, 80)])
        dx = self.params.get("dx", 80)
        dy = self.params.get("dy", 0)

        # Apply transformation to get new shape
        if t_type == "translation":
            transformed = [(x + dx, y + dy) for x, y in orig]
        elif t_type == "rotation":
            angle_deg = self.params.get("angle", 90)
            cx_t = sum(x for x, y in orig) / len(orig)
            cy_t = sum(y for x, y in orig) / len(orig)
            rad_r = math.radians(angle_deg)
            transformed = []
            for x, y in orig:
                xr = cx_t + (x - cx_t) * math.cos(rad_r) - (y - cy_t) * math.sin(rad_r)
                yr = cy_t + (x - cx_t) * math.sin(rad_r) + (y - cy_t) * math.cos(rad_r)
                transformed.append((xr, yr))
        elif t_type == "reflection":
            line = self.params.get("line", "x")  # "x" or "y"/"vertical"
            if line == "x":
                transformed = [(x, h - pad - (y - pad)) for x, y in orig]
            else:
                transformed = [(w - pad - (x - pad), y) for x, y in orig]
        else:
            transformed = orig

        draw_shape(p, orig, self.t["text"], "Original")
        draw_shape(p, transformed, self.t["primary"], "Transformed")

        p.setFont(QFont("Consolas", 8))
        p.setPen(QColor(self.t["muted"]))
        p.drawText(QPointF(pad, 14), f"Transformation: {t_type.title()}")

    # ─── 8. ANGLE DIAGRAM (parallel lines, transversal) ────────────────
    def _draw_angles(self, p: QPainter):
        w, h = self.width(), self.height()
        pad = 30
        angle_type = self.params.get("type", "parallel_lines")
        angle_val = self.params.get("angle", 60)

        if angle_type == "parallel_lines":
            # Two parallel lines with a transversal
            mid_x = w / 2
            top_y = pad + 20
            bot_y = h - pad - 20

            # Parallel lines
            p.setPen(QPen(QColor(self.t["text"]), 2))
            p.drawLine(QPointF(pad, top_y), QPointF(w - pad, top_y))
            p.drawLine(QPointF(pad, bot_y), QPointF(w - pad, bot_y))

            # Transversal (slanted line)
            rad_t = math.radians(angle_val)
            t_len = (w - pad * 2) * 0.8
            tx1 = mid_x - t_len * math.cos(rad_t) / 2
            ty1 = (top_y + bot_y) / 2 - t_len * math.sin(rad_t) / 2
            tx2 = mid_x + t_len * math.cos(rad_t) / 2
            ty2 = (top_y + bot_y) / 2 + t_len * math.sin(rad_t) / 2
            p.setPen(QPen(QColor(self.t["primary"]), 1.5))
            p.drawLine(QPointF(tx1, ty1), QPointF(tx2, ty2))

            # Angle arc at intersection
            int_x = mid_x
            int_y = (top_y + bot_y) / 2

            # Arc between transversal and parallel line
            arc_r2 = 16
            p.setPen(QPen(QColor("#E53935"), 1.5))
            # Top intersection angles
            start_a = int(math.degrees(math.atan2(top_y - int_y, tx1 - int_x)))
            p.drawArc(QRectF(int_x - arc_r2, top_y - arc_r2, arc_r2 * 2, arc_r2 * 2),
                      int(start_a * 16), int(angle_val * 16))

            # Label angle
            p.setPen(QColor("#E53935"))
            p.setFont(QFont("Consolas", 8))
            p.drawText(QPointF(int_x + 10, top_y - 8), f"{angle_val}°")
            p.drawText(QPointF(int_x - 28, bot_y + 18), f"{angle_val}°")

            # Arrow markers for parallel lines
            p.setPen(QPen(QColor(self.t["muted"]), 1.5))
            for y_pos in [top_y, bot_y]:
                for arr_x in [pad + 20, w - pad - 20]:
                    p.drawLine(QPointF(arr_x - 5, y_pos - 5), QPointF(arr_x, y_pos))
                    p.drawLine(QPointF(arr_x + 5, y_pos - 5), QPointF(arr_x, y_pos))

            # Labels
            p.setFont(QFont("Consolas", 8))
            p.setPen(QColor(self.t["muted"]))
            p.drawText(QPointF(pad, top_y - 8), "L₁")
            p.drawText(QPointF(pad, bot_y + 16), "L₂")

        elif angle_type == "vertical_angles":
            cx, cy = w / 2, h / 2
            r_va = min(w, h) * 0.3
            # Two intersecting lines
            p.setPen(QPen(QColor(self.t["text"]), 2))
            p.drawLine(QPointF(cx - r_va, cy), QPointF(cx + r_va, cy))
            p.drawLine(QPointF(cx, cy - r_va), QPointF(cx, cy + r_va))

            # Angle arcs
            arc_r2 = 20
            p.setPen(QPen(QColor("#E53935"), 2))
            p.drawArc(QRectF(cx - arc_r2, cy - arc_r2, arc_r2 * 2, arc_r2 * 2), 0, -90 * 16)
            p.setPen(QPen(QColor("#1E88E5"), 2))
            p.drawArc(QRectF(cx - arc_r2, cy - arc_r2, arc_r2 * 2, arc_r2 * 2), 180 * 16, -90 * 16)

            p.setFont(QFont("Consolas", 8))
            p.setPen(QColor("#E53935"))
            p.drawText(QPointF(cx + 8, cy - 10), "θ")
            p.setPen(QColor("#1E88E5"))
            p.drawText(QPointF(cx - 20, cy + 12), "θ")

            p.setPen(QColor(self.t["muted"]))
            p.drawText(QPointF(pad, 14), "Vertical angles are equal")


class ChatBubble(QWidget):
    def __init__(self, t: dict, role: str, text: str, parent=None):
        super().__init__(parent)
        self.t = t
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(8)

        bubble = QFrame()
        bubble.setMaximumWidth(720)
        is_user = role == "user"
        bg = t["primary"] if is_user else t["surface2"]
        fg = "#FFFFFF" if is_user else t["text"]
        bubble.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {t["line"] if not is_user else t["primary"]};
                border-radius: 8px;
            }}
            QLabel {{
                background: transparent;
                color: {fg};
                border: none;
            }}
        """)
        bl = QVBoxLayout(bubble)
        bl.setContentsMargins(14, 10, 14, 10)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setFont(app_font(10))
        bl.addWidget(label)

        if is_user:
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)


class LogWidget(QWidget):
    def __init__(self, t: dict, parent=None):
        super().__init__(parent)
        self.t = t
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.scroll.viewport().setStyleSheet("background: transparent;")
        shell = QWidget()
        shell.setStyleSheet("background: transparent;")
        self.messages = QVBoxLayout(shell)
        self.messages.setContentsMargins(12, 12, 12, 12)
        self.messages.setSpacing(2)
        self.messages.addStretch(1)
        self.scroll.setWidget(shell)
        root.addWidget(self.scroll)

    def append_log(self, text: str):
        role, body = self._classify(text)
        if not body:
            return
        bubble = ChatBubble(self.t, role, body)
        self.messages.insertWidget(max(0, self.messages.count() - 1), bubble)
        QTimer.singleShot(0, self._bottom)

    def clear(self):
        while self.messages.count() > 1:
            item = self.messages.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _classify(self, text: str):
        raw = (text or "").strip()
        shown = raw.replace("J.A.R.V.I.S", "RINA").replace("JARVIS", "RINA").replace("Jarvis", "Rina")
        low = shown.lower()
        if low.startswith("you:"):
            return "user", shown.split(":", 1)[1].strip()
        if low.startswith("rina:"):
            return "assistant", shown.split(":", 1)[1].strip()
        if low.startswith("err:"):
            return "assistant", "Error: " + shown.split(":", 1)[1].strip()
        if low.startswith("sys:"):
            return "assistant", shown.split(":", 1)[1].strip()
        if low.startswith("file:"):
            return "assistant", "File loaded: " + shown.split(":", 1)[1].strip()
        return "assistant", shown


class FileDropZone(QPushButton):
    file_selected = pyqtSignal(str)

    def __init__(self, t: dict, parent=None):
        super().__init__("Upload learning file", parent)
        self.t = t
        self._current_file: str | None = None
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIcon(make_icon("upload", t["primary"], 22))
        self.setIconSize(QSize(22, 22))
        self.setMinimumHeight(76)
        self.setFont(app_font(10, QFont.Weight.Bold))
        self.setStyleSheet(f"""
            QPushButton {{
                background: {t["surface2"]};
                color: {t["text"]};
                border: 1px dashed {t["line2"]};
                border-radius: 8px;
                padding: 12px;
            }}
            QPushButton:hover {{
                border-color: {t["primary"]};
                background: {t["sky"]};
            }}
        """)
        self.clicked.connect(self._browse)

    def current_file(self) -> str | None:
        return self._current_file

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self._set_file(path)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Upload file")
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self._current_file = path
        self.setText(Path(path).name)
        self.file_selected.emit(path)


class SetupOverlay(QWidget):
    done = pyqtSignal(str, str, str)

    def __init__(self, t: dict, parent=None):
        super().__init__(parent)
        self.t = t
        self._sel_os = "windows"
        self.setObjectName("SetupOverlay")
        self.setStyleSheet(f"""
            QWidget#SetupOverlay {{
                background: {t["surface"]};
                border: 1px solid {t["line2"]};
                border-radius: 8px;
            }}
            QLabel {{
                color: {t["text"]};
                background: transparent;
                border: none;
            }}
            QLineEdit {{
                background: {t["surface2"]};
                color: {t["text"]};
                border: 1px solid {t["line"]};
                border-radius: 8px;
                padding: 10px 12px;
            }}
            QLineEdit:focus {{
                border-color: {t["primary"]};
            }}
        """)
        apply_shadow(self, t["shadow"], 38, 14, 70)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 24)
        lay.setSpacing(14)
        title = QLabel("Connect Rina")
        title.setFont(app_font(23, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        sub = QLabel("Add your existing API keys. Learning pages work without starting voice.")
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(app_font(9))
        sub.setStyleSheet(f"color: {t['muted']};")
        lay.addWidget(sub)
        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("Gemini API key")
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self._key_input)
        self._or_input = QLineEdit()
        self._or_input.setPlaceholderText("OpenRouter API key")
        self._or_input.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self._or_input)
        os_row = QHBoxLayout()
        self._os_buttons = {}
        for key, label in [("windows", "Windows"), ("mac", "macOS"), ("linux", "Linux")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._sel(k))
            os_row.addWidget(btn)
            self._os_buttons[key] = btn
        lay.addLayout(os_row)
        self._sel("windows")
        submit = PrimaryButton(t, "Save and continue", "play")
        submit.clicked.connect(self._submit)
        lay.addWidget(submit)

    def _sel(self, key: str):
        self._sel_os = key
        for k, btn in self._os_buttons.items():
            selected = k == key
            btn.setChecked(selected)
            btn.setFont(app_font(9, QFont.Weight.Bold if selected else QFont.Weight.Medium))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {self.t["primary"] if selected else self.t["surface2"]};
                    color: {"#FFFFFF" if selected else self.t["text"]};
                    border: 1px solid {self.t["primary"] if selected else self.t["line"]};
                    border-radius: 8px;
                }}
            """)

    def _submit(self):
        key = self._key_input.text().strip()
        or_key = self._or_input.text().strip()
        if not key:
            self._key_input.setFocus()
            return
        if not or_key:
            self._or_input.setFocus()
            return
        self.done.emit(key, or_key, self._sel_os)


class ProfileOverlay(QWidget):
    done = pyqtSignal(dict)

    def __init__(self, t: dict, profile: dict | None = None, parent=None):
        super().__init__(parent)
        self.t = t
        self.profile = profile or {}
        self._avatar_path = self.profile.get("avatar_path", "")
        self._avatar_color = self.profile.get("avatar_color", t["secondary"])
        self.setObjectName("ProfileOverlay")
        self.setStyleSheet(f"""
            QWidget#ProfileOverlay {{
                background: {t["surface"]};
                border: 1px solid {t["line2"]};
                border-radius: 8px;
            }}
            QLabel {{
                color: {t["text"]};
                background: transparent;
                border: none;
            }}
            QLineEdit {{
                background: {t["surface2"]};
                color: {t["text"]};
                border: 1px solid {t["line"]};
                border-radius: 8px;
                padding: 11px 12px;
            }}
            QLineEdit:focus {{
                border-color: {t["primary"]};
            }}
        """)
        apply_shadow(self, t["shadow"], 38, 14, 72)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 28, 30, 26)
        lay.setSpacing(16)

        title = QLabel("Rahura AI Rina")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(app_font(23, QFont.Weight.Bold))
        lay.addWidget(title)
        sub = QLabel("Injira / Sign in — Voma Ubwenge. Study with structure before asking Rina.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        sub.setFont(app_font(10))
        sub.setStyleSheet(f"color: {t['muted']};")
        lay.addWidget(sub)

        self.avatar_preview = AvatarWidget(t, self._preview_profile(), 86)
        lay.addWidget(self.avatar_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Izina / Username")
        self.username.setText(self.profile.get("username", ""))
        lay.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Ijambo ry'ibanga / Password")
        lay.addWidget(self.password)

        hint = QLabel(
            "First sign-in on this device creates your local account. "
            "Murakoze — data stays on this computer only."
        )
        hint.setWordWrap(True)
        hint.setFont(app_font(8))
        hint.setStyleSheet(f"color: {t['muted']};")
        lay.addWidget(hint)

        colors = QHBoxLayout()
        colors.setSpacing(8)
        for color in [t["secondary"], t["primary"], t["teal"], t["green"], t["purple"], t["gold"]]:
            btn = QPushButton("")
            btn.setFixedSize(34, 34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"background: {color}; border: 2px solid #FFFFFF; border-radius: 17px;")
            btn.clicked.connect(lambda _=False, c=color: self._choose_color(c))
            colors.addWidget(btn)
        photo = IconButton(t, "Photo", "upload")
        photo.clicked.connect(self._choose_photo)
        colors.addWidget(photo)
        lay.addLayout(colors)

        save = PrimaryButton(t, "Injira / Sign in", "play", t["secondary"])
        save.clicked.connect(self._submit)
        lay.addWidget(save)

    def _preview_profile(self):
        return {
            "username": self.username.text() if hasattr(self, "username") else self.profile.get("username", "Student"),
            "avatar_path": self._avatar_path,
            "avatar_color": self._avatar_color,
        }

    def _choose_color(self, color: str):
        self._avatar_color = color
        self._avatar_path = ""
        self.avatar_preview.profile = self._preview_profile()
        self.avatar_preview.update()

    def _choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose profile photo", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            self._avatar_path = path
            self.avatar_preview.profile = self._preview_profile()
            self.avatar_preview.update()

    def _submit(self):
        name = self.username.text().strip()
        password = self.password.text().strip()
        if not name:
            self.username.setFocus()
            return
        if not password:
            self.password.setFocus()
            return
        ok, message, role = authenticate(name, password)
        if not ok:
            self.password.clear()
            self.password.setPlaceholderText(message[:80])
            self.password.setFocus()
            return
        profile = dict(self.profile)
        profile.update({
            "username": name,
            "avatar_path": self._avatar_path,
            "avatar_color": self._avatar_color,
            "xp": profile.get("xp", 0),
            "streak": profile.get("streak", 0),
            "theme": profile.get("theme", "light"),
            "sound": False,
            "authenticated": True,
            "role": role,
            "student_mode": role == "student",
            "completed_lessons": profile.get("completed_lessons", []),
            "quiz_scores": profile.get("quiz_scores", []),
        })
        self.done.emit(profile)


class MainWindow(QMainWindow):
    _log_sig = pyqtSignal(str)
    _state_sig = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rahura AI Rina")
        self.setMinimumSize(_MIN_W, _MIN_H)
        self.resize(_DEFAULT_W, _DEFAULT_H)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(max(0, (screen.width() - _DEFAULT_W) // 2), max(0, (screen.height() - _DEFAULT_H) // 2))

        self.profile = _load_json(PROFILE_FILE, {})
        self.dark = self.profile.get("theme", "light") == "dark"
        self.t = DARK if self.dark else LIGHT
        self.sound = SoundEngine()
        self.sound.enabled = False

        self.on_text_command = None
        self.on_lesson_selected = None
        self._muted = True
        self._state = "DORMANT"
        self._current_file: str | None = None
        self._overlay: QWidget | None = None
        self._api_after_save = None
        self._rina_started = threading.Event()
        self._pending_text: list[str] = []
        self._learn_path: list[str] = []
        self._lesson_detail_path: list[str] = []
        self._current_page = "home"
        self._compact = False
        self._rina_auto_activated = False
        self._thinking_dots = 0
        self._thinking_timer = QTimer(self)
        self._thinking_timer.setInterval(400)
        self._thinking_timer.timeout.connect(self._tick_thinking)

        central = LearningBackground(self.t)
        self._canvas = central
        self.setCentralWidget(central)
        self._root = QHBoxLayout(central)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(0)

        self._log_sig.connect(self._append_log)
        self._state_sig.connect(self._apply_state)

        if self.profile.get("authenticated"):
            self._build_app_shell()
        else:
            self._build_auth_landing()

        QShortcut(QKeySequence("F4"), self, activated=self._toggle_mute)
        QShortcut(QKeySequence("F11"), self, activated=self._toggle_fullscreen)

    def _clear_root_widgets(self):
        while self._root.count():
            item = self._root.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _build_app_shell(self):
        self._clear_root_widgets()
        self._sidebar = self._build_sidebar()
        self._root.addWidget(self._sidebar, stretch=0)
        self._main_area = self._build_main_area()
        self._root.addWidget(self._main_area, stretch=1)
        self._show_page(self._current_page)
        self._apply_compact(self.width() < 900)

    def _build_auth_landing(self):
        self._clear_root_widgets()
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        outer = QHBoxLayout(page)
        outer.setContentsMargins(34, 34, 34, 34)
        outer.setSpacing(22)

        visual = ImageCard(self.t, asset("rahura", "jean-michel-habineza.jpg"))
        visual.setMinimumWidth(420)
        visual.setMinimumHeight(560)
        vl = QVBoxLayout(visual)
        vl.setContentsMargins(30, 30, 30, 28)
        logo = QLabel()
        pix = QPixmap(str(asset("rahura", "rahura-logo.png")))
        if not pix.isNull():
            logo.setPixmap(pix.scaled(150, 58, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setStyleSheet("background: transparent; border: none;")
        vl.addWidget(logo)
        vl.addStretch(1)
        title = QLabel("Rahura AI Rina")
        title.setWordWrap(True)
        title.setFont(app_font(34, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        vl.addWidget(title)
        sub = QLabel("Voma Ubwenge. Study with structure before asking Rina.")
        sub.setWordWrap(True)
        sub.setFont(app_font(12, QFont.Weight.Bold))
        sub.setStyleSheet("color: rgba(255,255,255,230); background: transparent; border: none;")
        vl.addWidget(sub)

        auth = ProfileOverlay(self.t, self.profile)
        auth.done.connect(self._on_profile_done)
        auth.setMinimumWidth(430)
        outer.addWidget(visual, stretch=1)
        outer.addWidget(auth, stretch=0)
        self._auth_page = page
        self._root.addWidget(page, stretch=1)

    def _style_page_scroll(self, scroll: QScrollArea):
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.verticalScrollBar().setSingleStep(24)
        scroll.verticalScrollBar().setPageStep(240)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 10px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {self.t["line2"]};
                border-radius: 5px;
                min-height: 34px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        scroll.viewport().setStyleSheet("background: transparent;")

    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(_LEFT_W)
        side.setStyleSheet(f"""
            QWidget#Sidebar {{
                background: {self.t["surface"]};
                border-right: 1px solid {self.t["line"]};
            }}
        """)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(20, 22, 20, 18)
        lay.setSpacing(10)

        brand = QHBoxLayout()
        self._brand_logo = QLabel()
        logo = QPixmap(str(asset("rahura", "rahura-emblem.png")))
        if not logo.isNull():
            self._brand_logo.setPixmap(logo.scaled(38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self._brand_logo.setFixedSize(42, 42)
        brand.addWidget(self._brand_logo)
        brand_col = QVBoxLayout()
        self._brand_title = QLabel("Rahura AI Rina")
        self._brand_title.setFont(app_font(15, QFont.Weight.Bold))
        self._brand_title.setStyleSheet(f"color: {self.t['text']}; background: transparent;")
        self._brand_sub = QLabel("Voma Ubwenge")
        self._brand_sub.setFont(app_font(8, QFont.Weight.Medium))
        self._brand_sub.setStyleSheet(f"color: {self.t['secondary']}; background: transparent;")
        brand_col.addWidget(self._brand_title)
        brand_col.addWidget(self._brand_sub)
        brand.addLayout(brand_col)
        lay.addLayout(brand)
        lay.addSpacing(10)

        self._nav_buttons: dict[str, NavButton] = {}
        nav = [
            ("home", "Home", "home"),
            ("learn", "Learn", "learn"),
            ("classroom", "Classroom", "classroom"),
            ("quizzes", "Quizzes", "quizzes"),
            ("missions", "Missions", "missions"),
            ("progress", "Progress", "progress"),
            ("community", "Research Hub", "community"),
            ("resources", "Resources", "resources"),
            ("rina", "Talk To Rina", "rina"),
            ("profile", "Profile", "profile"),
            ("settings", "Settings", "settings"),
        ]
        for key, label, icon in nav:
            btn = NavButton(self.t, key, label, icon)
            btn.clicked.connect(lambda _=False, k=key: self._show_page(k))
            self._nav_buttons[key] = btn
            lay.addWidget(btn)
        lay.addStretch(1)

        profile_card = Card(self.t, "SidebarProfile", False)
        profile_card.setFixedHeight(74)
        pl = QHBoxLayout(profile_card)
        pl.setContentsMargins(10, 9, 10, 9)
        self._side_avatar = AvatarWidget(self.t, self._effective_profile(), 48)
        self._side_avatar.clicked.connect(lambda: self._show_page("profile"))
        pl.addWidget(self._side_avatar)
        pcol = QVBoxLayout()
        self._side_name = QLabel(self._effective_profile()["username"])
        self._side_name.setFont(app_font(9, QFont.Weight.Bold))
        self._side_name.setStyleSheet(f"color: {self.t['text']}; background: transparent;")
        self._side_stat = QLabel(f"{self.profile.get('streak', 0)} day streak")
        self._side_stat.setFont(app_font(8, QFont.Weight.Medium))
        self._side_stat.setStyleSheet(f"color: {self.t['muted']}; background: transparent;")
        pcol.addWidget(self._side_name)
        pcol.addWidget(self._side_stat)
        pl.addLayout(pcol)
        lay.addWidget(profile_card)
        self._profile_card = profile_card

        self._set_active_nav("home")
        return side

    def _build_main_area(self) -> QWidget:
        area = QWidget()
        area.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(area)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._build_topbar())

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QStackedWidget { background: transparent; border: none; }")
        self._pages = {
            "home": self._build_home_page(),
            "learn": self._build_learn_page(),
            "classroom": self._build_classroom_page(),
            "quizzes": self._build_quizzes_page(),
            "missions": self._build_missions_page(),
            "progress": self._build_progress_page(),
            "community": self._build_community_page(),
            "resources": self._build_resources_page(),
            "rina": self._build_rina_page(),
            "profile": self._build_profile_page(),
            "settings": self._build_settings_page(),
        }
        for page in self._pages.values():
            self._stack.addWidget(page)
        lay.addWidget(self._stack, stretch=1)
        return area

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(76)
        bar.setStyleSheet(f"background: {self.t['surface']}; border-bottom: 1px solid {self.t['line']};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 12, 24, 12)
        lay.setSpacing(12)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search REB lessons, books, homework, inventions...")
        self._search.setFixedHeight(46)
        self._search.setFont(app_font(10))
        self._search.addAction(make_icon("search", self.t["muted"], 20), QLineEdit.ActionPosition.LeadingPosition)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {self.t["surface2"]};
                color: {self.t["text"]};
                border: 1px solid {self.t["line"]};
                border-radius: 8px;
                padding: 0 14px;
            }}
            QLineEdit:focus {{
                border-color: {self.t["primary"]};
            }}
        """)
        lay.addWidget(self._search, stretch=1)

        self._xp_label = QLabel(f"{self.profile.get('xp', 0)} XP")
        self._xp_label.setFont(app_font(9, QFont.Weight.Bold))
        self._xp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._xp_label.setFixedHeight(36)
        self._xp_label.setStyleSheet(f"background: {self.t['warm']}; color: {self.t['secondary']}; border: 1px solid {self.t['line']}; border-radius: 8px; padding: 0 12px;")
        lay.addWidget(self._xp_label)

        streak = QLabel(f"{self.profile.get('streak', 0)} day streak")
        streak.setFont(app_font(9, QFont.Weight.Bold))
        streak.setAlignment(Qt.AlignmentFlag.AlignCenter)
        streak.setFixedHeight(36)
        streak.setStyleSheet(f"background: {self.t['success_bg']}; color: {self.t['green']}; border: 1px solid {self.t['line']}; border-radius: 8px; padding: 0 12px;")
        lay.addWidget(streak)
        self._top_streak = streak

        rina_btn = IconButton(self.t, "Rina", "rina", self.t["primary"])
        rina_btn.clicked.connect(lambda: self._show_page("rina"))
        lay.addWidget(rina_btn)

        self._top_avatar = AvatarWidget(self.t, self._effective_profile(), 46)
        self._top_avatar.clicked.connect(lambda: self._show_page("profile"))
        lay.addWidget(self._top_avatar)
        return bar

    def _effective_profile(self) -> dict:
        profile = dict(self.profile)
        profile.setdefault("username", "Student")
        profile.setdefault("avatar_color", self.t["secondary"])
        profile.setdefault("avatar_path", "")
        profile.setdefault("xp", 0)
        profile.setdefault("streak", 0)
        profile.setdefault("quiz_scores", [])
        profile.setdefault("role", "student")
        profile.setdefault("student_mode", True)
        profile.setdefault("completed_lessons", [])
        return profile

    def _page_shell(self, max_width: int = 1180) -> tuple[QWidget, QVBoxLayout]:
        scroll = QScrollArea()
        self._style_page_scroll(scroll)
        outer = QWidget()
        outer.setStyleSheet("background: transparent;")
        shell = QHBoxLayout(outer)
        shell.setContentsMargins(24, 24, 24, 30)
        content = QWidget()
        content.setMaximumWidth(max_width)
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        shell.addStretch(1)
        shell.addWidget(content, stretch=1)
        shell.addStretch(1)
        scroll.setWidget(outer)
        return scroll, layout

    def _headline(self, title: str, subtitle: str = "") -> QWidget:
        box = QWidget()
        box.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        h = QLabel(title)
        h.setWordWrap(True)
        h.setFont(app_font(22, QFont.Weight.Bold))
        h.setStyleSheet(f"color: {self.t['text']}; background: transparent;")
        lay.addWidget(h)
        if subtitle:
            s = QLabel(subtitle)
            s.setWordWrap(True)
            s.setFont(app_font(10))
            s.setStyleSheet(f"color: {self.t['muted']}; background: transparent;")
            lay.addWidget(s)
        return box

    def _section_header(self, title: str, action: str | None = None, handler=None) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setFont(app_font(14, QFont.Weight.Bold))
        label.setStyleSheet(f"color: {self.t['text']}; background: transparent;")
        lay.addWidget(label)
        lay.addStretch(1)
        if action:
            btn = IconButton(self.t, action, "play", self.t["primary"])
            btn.clicked.connect(handler or (lambda: None))
            lay.addWidget(btn)
        return row

    def _stat_card(self, title: str, value: str, note: str, accent: str, icon: str) -> QWidget:
        card = Card(self.t, "StatCard", True)
        card.setMinimumHeight(124)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        badge = QLabel()
        badge.setFixedSize(48, 48)
        badge.setPixmap(make_icon(icon, accent, 40).pixmap(40, 40))
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"background: {self.t['surface2']}; border-radius: 8px;")
        lay.addWidget(badge)
        col = QVBoxLayout()
        t = QLabel(title)
        t.setFont(app_font(9, QFont.Weight.Medium))
        t.setStyleSheet(f"color: {self.t['muted']}; background: transparent;")
        v = QLabel(value)
        v.setFont(app_font(21, QFont.Weight.Bold))
        v.setStyleSheet(f"color: {self.t['text']}; background: transparent;")
        n = QLabel(note)
        n.setWordWrap(True)
        n.setFont(app_font(8))
        n.setStyleSheet(f"color: {accent}; background: transparent;")
        col.addWidget(t)
        col.addWidget(v)
        col.addWidget(n)
        lay.addLayout(col, stretch=1)
        return card

    def _mini_progress(self, value: int, accent: str) -> QProgressBar:
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(value)
        bar.setTextVisible(False)
        bar.setFixedHeight(9)
        bar.setStyleSheet(f"""
            QProgressBar {{ background: {self.t['line']}; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background: {accent}; border-radius: 4px; }}
        """)
        return bar

    def _build_home_page(self) -> QWidget:
        page, root = self._page_shell(1220)

        hero = ImageCard(self.t, asset("rahura", "rah-21.jpg"))
        hero.setMinimumHeight(300)
        hlay = QVBoxLayout(hero)
        hlay.setContentsMargins(28, 28, 28, 26)
        hlay.setSpacing(12)
        logo = QPixmap(str(asset("rahura", "rahura-logo.png")))
        if not logo.isNull():
            logol = QLabel()
            logol.setPixmap(logo.scaled(122, 46, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            logol.setStyleSheet("background: transparent; border: none;")
            hlay.addWidget(logol)
        title = QLabel("Rahura AI Rina")
        title.setWordWrap(True)
        title.setFont(app_font(31, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        hlay.addWidget(title)
        sub = QLabel("A professional Rahura learning space for REB books, daily study order, research questions, homework support, and Rina when you choose to ask.")
        sub.setWordWrap(True)
        sub.setMaximumWidth(650)
        sub.setFont(app_font(11, QFont.Weight.Medium))
        sub.setStyleSheet("color: rgba(255,255,255,220); background: transparent; border: none;")
        hlay.addWidget(sub)
        actions = QHBoxLayout()
        learn = PrimaryButton(self.t, "Continue learning", "learn", self.t["secondary"])
        learn.clicked.connect(lambda: self._show_page("learn"))
        actions.addWidget(learn)
        mission = IconButton(self.t, "Today mission", "missions", self.t["gold"])
        mission.clicked.connect(lambda: self._show_page("missions"))
        actions.addWidget(mission)
        actions.addStretch(1)
        hlay.addLayout(actions)
        hlay.addStretch(1)
        root.addWidget(hero)

        stat_grid = QGridLayout()
        stat_grid.setHorizontalSpacing(14)
        stat_grid.setVerticalSpacing(14)
        stats = [
            ("Learning streak", f"{self.profile.get('streak', 0)} days", "Keep the rhythm", self.t["secondary"], "missions"),
            ("Lessons done", str(lessons_count(self.profile)), "Across REB and TVET", self.t["green"], "learn"),
            ("Quiz average", quiz_average(self.profile), "From your quiz history", self.t["purple"], "quizzes"),
            ("XP earned", f"{self.profile.get('xp', 0)}", "Earn XP from lessons and quizzes", self.t["gold"], "progress"),
        ]
        for idx, item in enumerate(stats):
            stat_grid.addWidget(self._stat_card(*item), idx // 4, idx % 4)
        root.addLayout(stat_grid)

        root.addWidget(self._daily_study_structure())
        root.addWidget(self._section_header("Continue Learning", "Open Learn", lambda: self._show_page("learn")))
        cont = QGridLayout()
        cont.setHorizontalSpacing(14)
        cont.setVerticalSpacing(14)
        courses = [
            ("Mathematics", "Linear equations and problem solving", 72, self.t["purple"], asset("rahura", "s-calculator-b.jpg")),
            ("Chemistry", "Matter, particles and lab safety", 58, self.t["teal"], asset("rahura", "exercise-book-green.jpg")),
            ("English", "Reading comprehension and summary", 81, self.t["secondary"], asset("rahura", "exercise-book-red.jpg")),
        ]
        for idx, (name, desc, prog, accent, img) in enumerate(courses):
            cont.addWidget(self._course_card(name, desc, prog, accent, img), 0, idx)
        root.addLayout(cont)

        lower = QGridLayout()
        lower.setHorizontalSpacing(14)
        lower.setVerticalSpacing(14)
        lower.addWidget(self._mission_preview(), 0, 0)
        lower.addWidget(self._achievement_preview(), 0, 1)
        lower.addWidget(self._recent_activity(), 1, 0)
        lower.addWidget(self._quick_actions(), 1, 1)
        root.addLayout(lower)
        root.addWidget(self._people_visual_band())
        return page

    def _course_card(self, name: str, desc: str, progress: int, accent: str, image: Path) -> QWidget:
        card = Card(self.t, "CourseCard", True)
        card.setMinimumHeight(220)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 16)
        img = ImageCard(self.t, image)
        img.setMinimumHeight(96)
        img.setMaximumHeight(110)
        lay.addWidget(img)
        body = QVBoxLayout()
        body.setContentsMargins(16, 0, 16, 0)
        title = QLabel(name)
        title.setFont(app_font(14, QFont.Weight.Bold))
        desc_l = QLabel(desc)
        desc_l.setWordWrap(True)
        desc_l.setFont(app_font(9))
        desc_l.setStyleSheet(f"color: {self.t['muted']};")
        body.addWidget(title)
        body.addWidget(desc_l)
        body.addWidget(self._mini_progress(progress, accent))
        foot = QHBoxLayout()
        pct = QLabel(f"{progress}% complete")
        pct.setFont(app_font(8, QFont.Weight.Bold))
        pct.setStyleSheet(f"color: {accent};")
        foot.addWidget(pct)
        foot.addStretch(1)
        btn = PrimaryButton(self.t, "Resume", "play", accent)
        btn.setFixedHeight(34)
        btn.clicked.connect(lambda: self._start_quick_access_lesson(name))
        foot.addWidget(btn)
        body.addLayout(foot)
        lay.addLayout(body)
        return card

    def _daily_study_structure(self, compact: bool = False) -> QWidget:
        card = Card(self.t, "DailyStudyStructure", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.setSpacing(10)
        lay.addWidget(self._section_header("Daily Study Order / Gahunda y'amasomo"))
        intro = QLabel(
            "REB order from P4–S6: read first, practise second, check mistakes, then ask Rina. "
            "Soma mbere, ukore imyitozo, ukosore amakosa, hanyuma ubaze Rina."
        )
        intro.setWordWrap(True)
        intro.setFont(app_font(9))
        intro.setStyleSheet(f"color: {self.t['muted']};")
        lay.addWidget(intro)
        if get_reb_level_summaries:
            reb_row = QVBoxLayout()
            reb_row.setSpacing(6)
            for level, focus, order in get_reb_level_summaries()[:4]:
                if not order:
                    continue
                row = QLabel(f"<b>{level}</b> — {focus}<br><span style='color:{self.t['muted']}'>{' → '.join(order[:6])}</span>")
                row.setWordWrap(True)
                row.setFont(app_font(8))
                reb_row.addWidget(row)
            lay.addLayout(reb_row)
        steps = [
            ("1. Plan", "Pick one REB topic and one outcome.", "missions"),
            ("2. Learn", "Read notes or textbook pages for 25 minutes.", "learn"),
            ("3. Practice", "Solve examples, homework, or past-paper items.", "quizzes"),
            ("4. Check", "Mark answers and list weak points.", "progress"),
            ("5. Research Hub", "Ask Rina questions, inventions, and curiosity prompts.", "community"),
        ]
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for idx, (title, body, page_key) in enumerate(steps):
            cell = Card(self.t, "StudyStep", False)
            cell.setMinimumHeight(82 if compact else 98)
            cell.setCursor(Qt.CursorShape.PointingHandCursor)
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(12, 10, 12, 10)
            h = QLabel(title)
            h.setFont(app_font(9, QFont.Weight.Bold))
            h.setStyleSheet(f"color: {self.t['primary']};")
            b = QLabel(body)
            b.setWordWrap(True)
            b.setFont(app_font(8))
            b.setStyleSheet(f"color: {self.t['muted']};")
            cl.addWidget(h)
            cl.addWidget(b)
            cell.mousePressEvent = lambda _e, p=page_key: self._show_page(p)
            grid.addWidget(cell, idx // (5 if compact else 3), idx % (5 if compact else 3))
        lay.addLayout(grid)
        return card

    def _mission_preview(self) -> QWidget:
        card = Card(self.t, "MissionPreview", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.setSpacing(10)
        lay.addWidget(self._section_header("Today's Mission"))
        title = QLabel("Complete two lessons and one knowledge check")
        title.setWordWrap(True)
        title.setFont(app_font(13, QFont.Weight.Bold))
        lay.addWidget(title)
        lay.addWidget(self._mini_progress(66, self.t["secondary"]))
        row = QHBoxLayout()
        row.addWidget(QLabel("+120 XP"))
        row.addStretch(1)
        btn = PrimaryButton(self.t, "Go", "missions", self.t["secondary"])
        btn.setFixedHeight(34)
        btn.clicked.connect(lambda: self._show_page("missions"))
        row.addWidget(btn)
        lay.addLayout(row)
        return card

    def _achievement_preview(self) -> QWidget:
        card = Card(self.t, "AchievementPreview", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.setSpacing(12)
        lay.addWidget(self._section_header("Achievements"))
        for title, detail, color in [
            ("Streak Keeper", f"{self.profile.get('streak', 0)} days of learning", self.t["gold"]),
            ("Science Starter", f"{lessons_count(self.profile)} lessons done", self.t["teal"]),
            ("Quiz Sharp", f"Average {quiz_average(self.profile)}", self.t["purple"]),
        ]:
            row = QHBoxLayout()
            badge = QLabel()
            badge.setFixedSize(34, 34)
            badge.setStyleSheet(f"background: {color}; border-radius: 8px;")
            row.addWidget(badge)
            col = QVBoxLayout()
            name = QLabel(title)
            name.setFont(app_font(9, QFont.Weight.Bold))
            note = QLabel(detail)
            note.setFont(app_font(8))
            note.setStyleSheet(f"color: {self.t['muted']};")
            col.addWidget(name)
            col.addWidget(note)
            row.addLayout(col)
            lay.addLayout(row)
        return card

    def _recent_activity(self) -> QWidget:
        card = Card(self.t, "ActivityCard", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.addWidget(self._section_header("Recent Activity"))
        for item in [
            "Finished ICT: Introduction to algorithms",
            "Scored 88% in Chemistry practice",
            "Joined Mathematics S3 classroom",
            "Saved English revision notes",
        ]:
            label = QLabel(item)
            label.setWordWrap(True)
            label.setFont(app_font(9))
            label.setStyleSheet(f"color: {self.t['muted']}; padding: 5px 0;")
            lay.addWidget(label)
        return card

    def _quick_actions(self) -> QWidget:
        card = Card(self.t, "QuickActionCard", True)
        lay = QGridLayout(card)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setHorizontalSpacing(10)
        lay.setVerticalSpacing(10)
        actions = [
            ("Start quiz", "quizzes", "quizzes"),
            ("Join class", "classroom", "classroom"),
            ("Upload notes", "resources", "upload"),
            ("Ask Rina", "rina", "rina"),
        ]
        for idx, (label, page, icon) in enumerate(actions):
            btn = IconButton(self.t, label, icon)
            btn.clicked.connect(lambda _=False, p=page: self._show_page(p))
            lay.addWidget(btn, idx // 2, idx % 2)
        return card

    def _people_visual_band(self) -> QWidget:
        card = Card(self.t, "PeopleVisualBand", True)
        lay = QGridLayout(card)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.setHorizontalSpacing(14)
        lay.setVerticalSpacing(14)
        copy = QVBoxLayout()
        h = QLabel("Learning made human")
        h.setWordWrap(True)
        h.setFont(app_font(19, QFont.Weight.Bold))
        h.setStyleSheet(f"color: {self.t['text']};")
        s = QLabel("Rina supports homework, research, and invention thinking, but the learner stays in control: choose a unit, study the content, practise, then discuss.")
        s.setWordWrap(True)
        s.setFont(app_font(10))
        s.setStyleSheet(f"color: {self.t['muted']};")
        btn = PrimaryButton(self.t, "Open Research Hub", "community", self.t["teal"])
        btn.clicked.connect(lambda: self._show_page("community"))
        copy.addWidget(h)
        copy.addWidget(s)
        copy.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)
        copy.addStretch(1)
        lay.addLayout(copy, 0, 0)
        for idx, img in enumerate(["jean-michel-habineza.jpg", "malaika.jpg", "christian.jpeg"]):
            tile = ImageCard(self.t, asset("rahura", img))
            tile.setMinimumHeight(190)
            lay.addWidget(tile, 0, idx + 1)
        lay.setColumnStretch(0, 2)
        lay.setColumnStretch(1, 1)
        lay.setColumnStretch(2, 1)
        lay.setColumnStretch(3, 1)
        return card

    def _build_learn_page(self) -> QWidget:
        page, root = self._page_shell(1220)
        self._learn_root = root
        self._render_learn()
        return page

    def _render_learn(self):
        if not hasattr(self, "_learn_root"):
            return
        clear_layout(self._learn_root)
        self._learn_root.addWidget(self._headline("Learn", "Follow a clear REB order from P4-P6 and S1-S6: read, practice, check, revise, then ask Rina."))
        self._learn_root.addWidget(self._daily_study_structure(compact=True))
        self._learn_root.addWidget(self._breadcrumb_widget())

        if not get_levels:
            self._learn_root.addWidget(self._empty_card("Curriculum files are unavailable."))
            return

        current = get_node_by_path(self._learn_path) if self._learn_path and get_node_by_path else None
        if current and current.node_type == "unit":
            self._learn_root.addWidget(self._unit_lesson_view(current))
            return

        children = get_children(current) if current and get_children else get_levels()
        if not children:
            self._learn_root.addWidget(self._empty_card("No curriculum entries were found here yet."))
            return

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for idx, node in enumerate(children):
            grid.addWidget(self._curriculum_card(node), idx // 3, idx % 3)
        self._learn_root.addLayout(grid)

        if not self._learn_path:
            self._learn_root.addWidget(self._section_header("Subject Categories"))
            subjects = QGridLayout()
            subjects.setHorizontalSpacing(14)
            subjects.setVerticalSpacing(14)
            for idx, item in enumerate([
                ("Mathematics", "Problem solving and numeracy", 72, self.t["purple"], asset("rahura", "s-calculator-b.jpg")),
                ("Physics", "Motion, energy and systems", 46, self.t["primary"], asset("rahura", "g-box-a.jpg")),
                ("Chemistry", "Matter, reactions and lab safety", 58, self.t["teal"], asset("rahura", "exercise-book-green.jpg")),
                ("Biology", "Life science and ecosystems", 64, self.t["green"], asset("rahura", "eb-blue-48-a.jpg")),
                ("ICT", "Digital skills and coding", 50, self.t["secondary"], asset("rahura", "colored-pencils.jpg")),
                ("TVET Courses", "Future-ready trade pathways", 35, self.t["gold"], asset("rahura", "1.jpg")),
            ]):
                subjects.addWidget(self._subject_card(*item), idx // 3, idx % 3)
            self._learn_root.addLayout(subjects)

    def _breadcrumb_widget(self) -> QWidget:
        box = QWidget()
        box.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        if self._learn_path or self._lesson_detail_path:
            back = IconButton(self.t, "Back", "play", self.t["secondary"])
            back.clicked.connect(self._go_learn_back)
            lay.addWidget(back)
        home = IconButton(self.t, "All levels", "learn")
        home.clicked.connect(lambda: self._set_learn_path([]))
        lay.addWidget(home)
        path = []
        for part in self._learn_path:
            path.append(part)
            node = get_node_by_path(path) if get_node_by_path else None
            label = _short(node.name if node else part, 24)
            btn = IconButton(self.t, label, "play")
            btn.clicked.connect(lambda _=False, p=path[:]: self._set_learn_path(p))
            lay.addWidget(btn)
        lay.addStretch(1)
        return box

    def _go_learn_back(self):
        if self._lesson_detail_path:
            unit_path = self._lesson_detail_path[:-1]
            self._lesson_detail_path = []
            self._set_learn_path(unit_path)
            return
        if self._learn_path:
            self._set_learn_path(self._learn_path[:-1])

    def _curriculum_card(self, node) -> QWidget:
        accent = self._accent_for(node.name)
        card = Card(self.t, "CurriculumCard", True)
        card.setMinimumHeight(190)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        badge = QLabel()
        badge.setFixedSize(46, 46)
        badge.setPixmap(make_icon(self._icon_for_type(node.node_type), accent, 38).pixmap(38, 38))
        badge.setStyleSheet(f"background: {self.t['surface2']}; border-radius: 8px;")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(badge)
        title = QLabel(node.name or "Untitled")
        title.setWordWrap(True)
        title.setFont(app_font(14, QFont.Weight.Bold))
        lay.addWidget(title)
        desc = QLabel(node.description or self._description_for(node.node_type))
        desc.setWordWrap(True)
        desc.setFont(app_font(9))
        desc.setStyleSheet(f"color: {self.t['muted']};")
        lay.addWidget(desc, stretch=1)
        foot = QHBoxLayout()
        diff = QLabel(self._difficulty_for(node.node_type))
        diff.setFont(app_font(8, QFont.Weight.Bold))
        diff.setStyleSheet(f"color: {accent};")
        foot.addWidget(diff)
        foot.addStretch(1)
        foot.addWidget(QLabel("Open"))
        lay.addLayout(foot)
        card.mousePressEvent = lambda _e, p=node.path[:]: self._set_learn_path(p)
        return card

    def _unit_lesson_view(self, node) -> QWidget:
        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)
        hero = Card(self.t, "UnitHero", True)
        hl = QGridLayout(hero)
        hl.setContentsMargins(22, 20, 22, 20)
        title = QLabel(node.name)
        title.setWordWrap(True)
        title.setFont(app_font(23, QFont.Weight.Bold))
        note = QLabel("Objectives, examples, practice, summary, and knowledge checks are organized lesson by lesson.")
        note.setWordWrap(True)
        note.setFont(app_font(10))
        note.setStyleSheet(f"color: {self.t['muted']};")
        hl.addWidget(title, 0, 0)
        hl.addWidget(note, 1, 0)
        ring = ProgressRing(self.t, 48, "unit mastery", self._accent_for(node.name))
        hl.addWidget(ring, 0, 1, 2, 1)
        lay.addWidget(hero)

        lessons = node.lessons or [
            "Lesson introduction",
            "Core concepts",
            "Worked examples",
            "Practice and knowledge check",
        ]
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for idx, lesson in enumerate(lessons):
            grid.addWidget(self._lesson_card(node, lesson, idx), idx // 2, idx % 2)
        lay.addLayout(grid)
        return wrap

    def _lesson_card(self, node, lesson: str, idx: int) -> QWidget:
        accent = self._accent_for(node.name)
        card = Card(self.t, "LessonCard", True)
        card.setMinimumHeight(180)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        label = QLabel(f"Lesson {idx + 1}")
        label.setFont(app_font(8, QFont.Weight.Bold))
        label.setStyleSheet(f"color: {accent};")
        lay.addWidget(label)
        title = QLabel(lesson)
        title.setWordWrap(True)
        title.setFont(app_font(14, QFont.Weight.Bold))
        lay.addWidget(title)
        meta = QLabel("Objectives | Visual content | Examples | Practice | Summary")
        meta.setWordWrap(True)
        meta.setFont(app_font(9))
        meta.setStyleSheet(f"color: {self.t['muted']};")
        lay.addWidget(meta, stretch=1)
        btn = PrimaryButton(self.t, "Start lesson", "play", accent)
        btn.clicked.connect(lambda: self._open_lesson(node.path + [lesson]))
        lay.addWidget(btn)
        return card

    def _open_lesson(self, path: list[str]):
        self.sound.play("click")
        self._lesson_detail_path = path[:]
        clear_layout(self._learn_root)
        title = path[-1]
        subject = next((part for part in reversed(path[:-1]) if part), "Lesson")
        self._learn_root.addWidget(self._breadcrumb_widget())
        self._learn_root.addWidget(self._lesson_detail(path, title, subject))

    def _get_lesson_content(self, path: list[str]) -> dict | None:
        lesson_name = path[-1]
        unit_name = path[-2] if len(path) >= 2 else ""
        subject_name = path[-3] if len(path) >= 3 else ""
        level_key = path[0] if path else ""

        # Try per-unit math files first
        if subject_name.lower() == "mathematics":
            unit_idx = self._find_math_unit_index(level_key, unit_name)
            if unit_idx is not None:
                prefix = self._math_level_prefix(level_key, path)
                unit_file = CURRICULUM_DIR / "math" / f"{prefix}_unit{unit_idx + 1}.json"
                try:
                    with open(unit_file, "r", encoding="utf-8") as f:
                        unit_data = json.load(f)
                except Exception:
                    pass
                else:
                    lessons = unit_data.get("lessons", [])
                    contents = unit_data.get("lessons_content", [])
                    for i, lname in enumerate(lessons):
                        if lname == lesson_name and i < len(contents) and contents[i]:
                            return self._normalize_lesson_content(dict(contents[i]))

        # Fallback: try high_school.json sections
        try:
            with open(CURRICULUM_DIR / "high_school.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return self._auto_lesson_content(lesson_name, unit_name)
        for sl in data.get("sub_levels", []):
            for subj in sl.get("subjects", []):
                if subj.get("name") == subject_name:
                    for unit in subj.get("units", []):
                        if unit.get("name") == unit_name:
                            lessons = unit.get("lessons", [])
                            contents = unit.get("lessons_content", [])
                            for i, lname in enumerate(lessons):
                                if lname == lesson_name and i < len(contents) and contents[i]:
                                    return self._normalize_lesson_content(dict(contents[i]))
        return self._auto_lesson_content(lesson_name, unit_name)

    @staticmethod
    def _normalize_lesson_content(data: dict) -> dict:
        """Convert list-type fields to formatted strings to prevent QLabel crashes."""
        text_fields = ("objectives", "reading", "examples", "practice", "summary", "practice_answers", "deep_explanation", "checkbox_answers")
        for field in text_fields:
            val = data.get(field)
            if isinstance(val, list):
                if field == "examples":
                    lines = []
                    for j, ex in enumerate(val):
                        if isinstance(ex, dict):
                            lines.append(f"Example {j + 1}: {ex.get('problem', '')}\nSolution:\n{ex.get('solution', '')}")
                        else:
                            lines.append(str(ex))
                    data[field] = "\n\n".join(lines)
                else:
                    data[field] = "\n".join(str(x) for x in val)
            elif val is not None and not isinstance(val, str):
                data[field] = str(val)
        # diagrams field stays as list of dicts
        if "diagrams" in data and not isinstance(data["diagrams"], list):
            data["diagrams"] = []
        return data

    @staticmethod
    def _math_level_prefix(level_key: str, path: list[str]) -> str:
        """Map path to level prefix for math unit files."""
        for p in path:
            if p == "primary_0":
                return "p1p3"
            if p == "primary_1":
                return "p4p6"
            if p == "high_school_0":
                return "s1"
            if p == "high_school_1":
                return "s2"
            if p == "high_school_2":
                return "s3"
        return level_key

    def _find_math_unit_index(self, level_key: str, unit_name: str) -> int | None:
        """Find the zero-based unit index within the mathematics subject."""
        try:
            with open(CURRICULUM_DIR / f"{level_key}.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None
        for sl in data.get("sub_levels", []):
            for subj in sl.get("subjects", []):
                if subj.get("name", "").lower() == "mathematics":
                    for idx, unit in enumerate(subj.get("units", [])):
                        if unit.get("name") == unit_name:
                            return idx
        # Fallback: search all subjects named mathematics
        for sl in data.get("sub_levels", []):
            for subj in sl.get("subjects", []):
                if subj.get("name", "").lower() == "mathematics":
                    for idx, unit in enumerate(subj.get("units", [])):
                        # try partial match
                        if unit_name.lower() in unit.get("name", "").lower() or unit.get("name", "").lower() in unit_name.lower():
                            return idx
        return None

    def _auto_lesson_content(self, lesson: str, unit: str) -> dict:
        t = lesson.lower()

        if "slope" in t or "intercept" in t or "straight line" in t:
            obj = "By the end of this lesson, you should be able to:\n- Calculate the slope of a line given two points\n- Write the equation of a straight line in slope-intercept form (y = mx + c)\n- Interpret the meaning of slope and intercept in real-life situations"
            reading = f"This lesson focuses on the equation of a straight line, one of the most practical tools in mathematics. In Rwanda, straight-line relationships appear everywhere — from calculating the cost of taxi fares in Kigali (where a fixed drop fee plus a per-kilometre charge forms a linear equation) to predicting crop yields based on fertiliser use. The general equation of a straight line is y = mx + c, where m is the gradient (slope) and c is the y-intercept. The slope tells us how steep the line is, while the intercept tells us where the line crosses the y-axis."
            ex = "Example 1: Find the equation of the line with slope 2 that passes through the point (1, 3).\nSolution:\nUse y = mx + c. We know m = 2 and the point (1,3) gives x = 1, y = 3.\nSubstitute: 3 = 2(1) + c → 3 = 2 + c → c = 1.\nTherefore the equation is y = 2x + 1.\n\nExample 2: A taxi company in Kigali charges a drop fee of 500 RWF plus 300 RWF per kilometre. Write an equation for the total fare in terms of distance travelled.\nSolution:\nLet y = total fare (RWF) and x = distance (km).\nFixed cost (intercept c) = 500 RWF.\nCost per km (slope m) = 300 RWF.\nTherefore the equation is y = 300x + 500."
            pr = "1. Find the slope of the line passing through (2, 5) and (6, 13).\n2. Write the equation of a line with slope -3 and y-intercept 7.\n3. A line passes through the point (4, -1) with slope 1/2. Find its equation.\n4. A mobile money agent earns a fixed daily wage of 2,000 RWF plus a commission of 500 RWF per transaction. Write a linear equation for daily earnings.\n5. Two lines have equations y = 2x + 3 and y = 2x - 1. Are they parallel, perpendicular, or neither? Explain."
            su = "* A straight line has the equation y = mx + c, where m is the slope and c is the y-intercept.\n* The slope m measures how steep the line is (rise over run).\n* The intercept c tells you where the line crosses the y-axis.\n* Linear equations model many real-world situations including costs, earnings, and growth."
            q = {"question": "What does the slope (m) represent in the equation y = mx + c?", "options": {"A": "Where the line crosses the x-axis", "B": "How steep the line is", "C": "The length of the line", "D": "The y-coordinate of the line"}, "answer": "B"}

        elif "trigonometr" in t or "sine" in t or "cosine" in t or "tangent" in t:
            obj = "By the end of this lesson, you should be able to:\n- Define sine, cosine and tangent ratios in a right triangle\n- Use trigonometric ratios to find unknown sides and angles\n- Apply trigonometry to solve real-world problems involving angles"
            reading = f"Trigonometry is the study of relationships between angles and sides of triangles. It has powerful real-world applications. In Rwanda, surveyors use trigonometry to measure land boundaries in hillside farming areas like the terraces of Northern Province. Architects use it to design stable roofs for buildings in Kigali. The three basic trigonometric ratios — sine (sin), cosine (cos), and tangent (tan) — relate an angle of a right triangle to the ratios of its sides."
            ex = "Example 1: In a right triangle, the side opposite angle A is 5 cm and the hypotenuse is 13 cm. Find sin A.\nSolution:\nsin A = opposite / hypotenuse = 5/13.\n\nExample 2: A ladder leans against a wall in a school in Kigali. The ladder is 5 m long and makes an angle of 60° with the ground. How high up the wall does the ladder reach?\nSolution:\nLet h = height up the wall.\nsin 60° = h / 5\nh = 5 × sin 60° = 5 × 0.8660 = 4.33 m.\nThe ladder reaches 4.33 m up the wall."
            pr = "1. In a right triangle, the side adjacent to angle B is 8 cm and the hypotenuse is 17 cm. Find cos B.\n2. Find tan 45° without a calculator.\n3. A flagpole at a school casts a 12 m shadow. The angle of elevation of the sun is 30°. How tall is the flagpole?\n4. From the top of a hill in Kabale, the angle of depression to a car is 20°. The hill is 50 m high. How far is the car from the base of the hill?\n5. Prove that sin²θ + cos²θ = 1."
            su = "* sin = opposite / hypotenuse, cos = adjacent / hypotenuse, tan = opposite / adjacent.\n* SOH CAH TOA is a useful memory aid.\n* Trigonometry is used in surveying, architecture, navigation and engineering."
            q = {"question": "What is the value of sin 30°?", "options": {"A": "0", "B": "0.5", "C": "0.866", "D": "1"}, "answer": "B"}

        elif "vector" in t:
            obj = "By the end of this lesson, you should be able to:\n- Define a vector and distinguish it from a scalar\n- Add and subtract vectors using graphical and component methods\n- Calculate the magnitude of a vector"
            reading = f"A vector is a quantity that has both magnitude (size) and direction. In Rwanda, vectors help us understand many things: the wind speed and direction affecting flights at Kigali International Airport, the force exerted by water flowing downhill in Rugengeri valley, or the displacement of a bus travelling from Kigali to Musanze. Scalars, in contrast, only have magnitude — like temperature (30°C) or mass (5 kg). Vectors are represented by arrows: the length shows magnitude, the arrowhead shows direction."
            ex = "Example 1: A student walks 3 km east from school (vector A) and then 4 km north (vector B). Find the resultant displacement.\nSolution:\nUsing Pythagoras: R² = 3² + 4² = 9 + 16 = 25, R = 5 km.\nDirection: tan θ = 4/3 → θ = 53.1° north of east.\n\nExample 2: Add vectors a = (3, 2) and b = (1, 5).\nSolution:\na + b = (3 + 1, 2 + 5) = (4, 7)."
            pr = "1. What is the difference between a scalar and a vector? Give two examples of each.\n2. Find the magnitude of the vector v = (6, 8).\n3. A minibus in Kigali travels 5 km east and then 12 km south. Find its displacement from the starting point.\n4. Subtract vector b = (4, 3) from a = (7, 9).\n5. A force of 10 N is applied at 60° to the horizontal. Find the horizontal and vertical components."
            su = "* Vectors have magnitude AND direction; scalars have magnitude only.\n* Vectors are added component-wise: (a,b) + (c,d) = (a+c, b+d).\n* Magnitude of (x,y) is √(x² + y²).\n* Vectors represent displacement, force, velocity and many other quantities."
            q = {"question": "Which of the following is a vector quantity?", "options": {"A": "Temperature", "B": "Mass", "C": "Velocity", "D": "Time"}, "answer": "C"}

        elif "profit" in t or "loss" in t or "discount" in t or "percent" in t or "interest" in t or "financial" in t or "business" in t or "tax" in t or "insurance" in t or "budget" in t:
            obj = "By the end of this lesson, you should be able to:\n- Calculate percentage profit and loss in buying and selling\n- Compute discounts and commissions in everyday transactions\n- Apply percentage concepts to real-life financial situations in Rwanda"
            reading = f"In Rwanda's growing economy, understanding percentages, profit and loss is essential for everyday life. Whether you are a market vendor at Kimironko calculating your daily profit, a student saving pocket money for school supplies, or a small business owner in Kigali tracking income and expenses, these concepts help you make informed financial decisions. Profit is made when the selling price exceeds the cost price. Loss occurs when the selling price is lower than the cost price. Percentages help us express these gains or losses in a standardised way."
            ex = "Example 1: A farmer in Musanze buys a bag of Irish potatoes for 15,000 RWF and sells it for 18,000 RWF. Find the percentage profit.\nSolution:\nProfit = 18,000 - 15,000 = 3,000 RWF.\nPercentage profit = (3,000 / 15,000) × 100 = 20%.\n\nExample 2: A shop in Kigali offers a 15% discount on a shirt that costs 12,000 RWF. What is the sale price?\nSolution:\nDiscount = 15% of 12,000 = (15/100) × 12,000 = 1,800 RWF.\nSale price = 12,000 - 1,800 = 10,200 RWF."
            pr = "1. Calculate 25% of 80,000 RWF.\n2. A trader buys 50 kg of rice at 600 RWF per kg and sells at 720 RWF per kg. Find the percentage profit.\n3. A shop offers a 20% discount on a television priced at 250,000 RWF. What is the discount amount?\n4. If a farmer loses 8% on a sale of 200,000 RWF worth of bananas, what was the cost price?\n5. A businesswoman earns a commission of 5% on every plot of land she sells. If she sells a plot for 3,500,000 RWF, how much commission does she earn?"
            su = "* Profit = Selling Price - Cost Price. Loss = Cost Price - Selling Price.\n* Percentage profit or loss is calculated relative to the cost price.\n* Discount = Percentage off × Original Price. Sale Price = Original - Discount.\n* These calculations are used daily in markets, shops and businesses across Rwanda."
            q = {"question": "A vendor buys oranges at 200 RWF each and sells them at 250 RWF each. What is the percentage profit?", "options": {"A": "20%", "B": "25%", "C": "50%", "D": "80%"}, "answer": "B"}

        elif "ratio" in t or "proportion" in t or "scale" in t:
            obj = "By the end of this lesson, you should be able to:\n- Express quantities as ratios in simplest form\n- Divide a quantity according to a given ratio\n- Apply ratios and proportions to real-world problems including map reading and sharing"
            reading = f"Ratios and proportions are used daily in Rwanda to compare quantities and share resources fairly. When a family in the village shares 10 litres of milk from their cow in the ratio of 3:2 between two neighbours, they are using ratios. When a construction worker in Kigali reads a blueprint with a scale of 1:100, they are applying proportional reasoning. A ratio compares two quantities. A proportion states that two ratios are equal."
            ex = "Example 1: A farmer's field has 15 cows and 10 goats. Express the ratio of cows to goats in simplest form.\nSolution:\nRatio = 15:10. Divide both by 5 → 3:2.\n\nExample 2: A mother divides 24,000 RWF between her two children in the ratio 5:3. How much does each child get?\nSolution:\nTotal parts = 5 + 3 = 8.\nOne part = 24,000 / 8 = 3,000 RWF.\nChild 1: 5 × 3,000 = 15,000 RWF.\nChild 2: 3 × 3,000 = 9,000 RWF."
            pr = "1. Simplify the ratio 36:24.\n2. Share 40 kg of maize in the ratio 3:2 between two families.\n3. On a map, 1 cm represents 5 km. What distance does 7 cm represent?\n4. The ratio of boys to girls in a Rwandan school is 5:4. If there are 360 girls, how many boys are there?\n5. Three friends invest 200,000 RWF, 300,000 RWF and 500,000 RWF in a small business in Kigali. At the end of the year, they make a profit of 250,000 RWF. How should they share the profit fairly?"
            su = "* A ratio compares two or more quantities of the same unit.\n* To divide in a ratio, add the parts then find the value of one part.\n* Proportions are equal ratios used in scale drawings, maps, and fair sharing."
            q = {"question": "A sum of 30,000 RWF is shared in the ratio 2:3. What is the larger share?", "options": {"A": "12,000 RWF", "B": "15,000 RWF", "C": "18,000 RWF", "D": "20,000 RWF"}, "answer": "C"}

        elif "similarity" in t or "congruence" in t or "congruent" in t or "similar" in t or "scale factor" in t:
            obj = "By the end of this lesson, you should be able to:\n- Identify congruent and similar shapes\n- Use scale factors to find unknown lengths in similar figures\n- Apply similarity and congruence to solve practical problems"
            reading = f"Two figures are congruent if they have exactly the same shape and size. Two figures are similar if they have the same shape but different sizes — like a small and a large photograph of the same view from Kigali's hilltop. In Rwanda, similarity appears when scaling building plans for houses in a new suburb, or when comparing maps of districts at different scales. Congruence ensures that manufactured products — like school desks or roof trusses — are identical in size and shape."
            ex = "Example 1: Triangle ABC has sides 3 cm, 4 cm, 5 cm. Triangle DEF has sides 6 cm, 8 cm, 10 cm. Are they similar?\nSolution:\nCheck ratios: 6/3 = 2, 8/4 = 2, 10/5 = 2. All ratios are equal (scale factor 2). So yes, they are similar.\n\nExample 2: A rectangular photo of the Gorilla Highlands is 10 cm by 15 cm. It is enlarged by a scale factor of 3. Find the new dimensions.\nSolution:\nNew width = 10 × 3 = 30 cm.\nNew height = 15 × 3 = 45 cm."
            pr = "1. Are two squares always similar? Explain.\n2. A triangle has sides 5 cm, 6 cm, 7 cm. A similar triangle has a shortest side of 15 cm. Find the scale factor and the other two sides.\n3. Two angles of one triangle are 45° and 65°. Two angles of another triangle are 45° and 70°. Are the triangles similar? Why or why not?\n4. A model of a school building in Kigali uses a scale of 1:50. If the model is 20 cm tall, how tall is the actual building?\n5. Prove that triangle ABC with vertices (0,0), (2,0), (0,3) is congruent to triangle DEF with vertices (1,1), (3,1), (1,4) using translation."
            su = "* Congruent figures have the same shape AND size.\n* Similar figures have the same shape but different sizes.\n* Scale factor = new length / original length.\n* Similarity and congruence are used in design, construction and modelling."
            q = {"question": "What is the scale factor if a 5 cm side becomes 15 cm?", "options": {"A": "1/3", "B": "3", "C": "10", "D": "5"}, "answer": "B"}

        elif "angle" in t or "point" in t or "line" in t or "circle" in t or "geometry" in t or "shape" in t or "solid" in t or "volume" in t or "surface area" in t:
            obj = "By the end of this lesson, you should be able to:\n- Identify and classify different types of angles and geometric shapes\n- Apply angle properties to solve geometric problems\n- Recognise geometric patterns in Rwandan art, architecture and nature"
            reading = f"Geometry is everywhere in Rwanda — from the triangular roof of a traditional house (nyakatsi) to the rectangular layout of a modern classroom in Kigali, from the circular weave of a traditional basket (agaseke) to the spherical shape of a football used in local matches. Understanding points, lines, angles and shapes helps us describe and make sense of the physical world. An angle is formed when two lines meet at a point. Angles are classified as acute (less than 90°), right (90°), obtuse (greater than 90°) or reflex (greater than 180°)."
            ex = "Example 1: Two angles are complementary. One is 35°. Find the other.\nSolution:\nComplementary angles add to 90°. So the other angle = 90° - 35° = 55°.\n\nExample 2: Find the volume of a rectangular water tank in a school in Kigali with length 2 m, width 1.5 m and height 1 m.\nSolution:\nVolume = length × width × height = 2 × 1.5 × 1 = 3 cubic metres. A cubic metre holds 1,000 litres, so the tank holds 3,000 litres."
            pr = "1. What type of angle is 120°?\n2. Two angles are supplementary. One is 108°. Find the other.\n3. Find the area of a triangle with base 12 cm and height 8 cm.\n4. A cylindrical water drum in a Rwandan household has radius 0.4 m and height 1.2 m. Find its volume (use π = 3.14).\n5. A traditional Rwandan basket (agaseke) has a diameter of 30 cm at its widest. Find its circumference."
            su = "* Angles are acute (< 90°), right (90°), obtuse (> 90°) or reflex (> 180°).\n* Complementary angles add to 90°. Supplementary angles add to 180°.\n* Volume of a rectangular prism = length × width × height.\n* Geometry connects to Rwandan culture through art, architecture and craft."
            q = {"question": "What is the complement of a 42° angle?", "options": {"A": "48°", "B": "138°", "C": "42°", "D": "90°"}, "answer": "A"}

        elif "statistics" in t or "data" in t or "mean" in t or "median" in t or "mode" in t or "bar graph" in t or "frequency" in t or "histogram" in t:
            obj = "By the end of this lesson, you should be able to:\n- Collect and organise data using frequency tables\n- Calculate measures of central tendency (mean, median and mode)\n- Interpret data presented in graphs and charts"
            reading = f"Statistics helps us make sense of information collected from the world around us. In Rwanda, the National Institute of Statistics (NISR) collects data on population, agriculture, education and health to help the government plan for the future. For example, data on school enrolment helps the Ministry of Education decide where to build new classrooms. In this lesson, we will learn how to organise data into frequency tables, create bar graphs and calculate averages. The three most common averages — the mean, median and mode — each tell us something different about a set of data."
            ex = "Example 1: Five students scored the following marks in a Mathematics test: 12, 15, 10, 18, 20. Find the mean.\nSolution:\nMean = (12 + 15 + 10 + 18 + 20) / 5 = 75 / 5 = 15.\n\nExample 2: The ages of 7 children in a village are: 8, 10, 12, 12, 14, 15, 18. Find the median and mode.\nSolution:\nMedian (middle value when sorted): 12.\nMode (most frequent value): 12 (appears twice)."
            pr = "1. Find the mean of: 6, 10, 14, 8, 12.\n2. The heights (cm) of 6 students are: 145, 150, 152, 148, 155, 150. Find the median.\n3. A farmer records the number of eggs collected daily: 20, 25, 30, 25, 35. What is the mode?\n4. Draw a frequency table for the following shoe sizes: 7, 8, 7, 9, 8, 7, 10, 8, 9, 7.\n5. A school in Kigali surveyed 30 students about their favourite subject and recorded: Math 12, Science 8, English 6, History 4. Draw a bar graph to represent this data."
            su = "* Mean = sum of all values divided by the number of values.\n* Median = the middle value when data is arranged in order.\n* Mode = the value that appears most frequently.\n* Data can be presented using frequency tables, bar graphs, histograms and many other formats."
            q = {"question": "What is the mode of this data set: 3, 7, 3, 9, 3, 7?", "options": {"A": "3", "B": "7", "C": "9", "D": "5.3"}, "answer": "A"}

        elif "probab" in t or "chance" in t or "event" in t or "sample space" in t or "tree diagram" in t:
            obj = "By the end of this lesson, you should be able to:\n- Define probability as a measure of the chance of an event occurring\n- Calculate simple probabilities using the formula P(event) = favourable outcomes / total outcomes\n- Use tree diagrams to find probabilities of combined events"
            reading = f"Probability is the branch of mathematics that deals with the likelihood of events happening. Every day in Rwanda, we make decisions based on probability: the chance of rain in the Northern Province during the wet season, the likelihood of a bus arriving on time at Kigali's main bus station, or the probability of winning a game. Probability values range from 0 (impossible) to 1 (certain). An event with probability 0.5 has an equal chance of happening or not happening — like a coin landing on heads."
            ex = "Example 1: A bag contains 3 red and 5 blue pencils. What is the probability of picking a red pencil?\nSolution:\nTotal pencils = 3 + 5 = 8.\nP(red) = 3/8.\n\nExample 2: A fair coin is tossed twice. Draw a tree diagram to find the probability of getting exactly one head.\nSolution:\nPossible outcomes: HH, HT, TH, TT (4 equally likely outcomes).\nExactly one head: HT, TH (2 outcomes).\nP(exactly one head) = 2/4 = 1/2 = 0.5."
            pr = "1. What is the probability of rolling a 4 on a standard dice?\n2. A bag has 6 white and 4 black marbles. Find P(black).\n3. A letter is chosen at random from the word 'RWANDA'. What is the probability it is a vowel?\n4. Two dice are rolled. What is the probability of getting a sum of 7?\n5. In a school in Butare, 60% of students play football, 30% play basketball and 10% play both. What is the probability that a randomly chosen student plays at least one of these sports?"
            su = "* Probability = favourable outcomes / total possible outcomes.\n* Values range from 0 (impossible) to 1 (certain).\n* Tree diagrams help visualise all possible outcomes of combined events.\n* Probability helps us make informed predictions in everyday life."
            q = {"question": "When flipping a fair coin, what is the probability of getting tails?", "options": {"A": "0", "B": "0.25", "C": "0.5", "D": "1"}, "answer": "C"}

        elif "matrix" in t or "matrices" in t or "determinant" in t or "transform" in t or "translation" in t or "reflection" in t or "rotation" in t or "enlargement" in t:
            obj = "By the end of this lesson, you should be able to:\n- Perform matrix operations (addition, subtraction and multiplication)\n- Calculate the determinant and inverse of a 2×2 matrix\n- Apply matrices to represent and solve transformations"
            reading = f"Matrices are rectangular arrays of numbers that are powerful tools for organising and manipulating data. In Rwanda, matrices can be used to represent data from different sectors: for example, a matrix could show the number of cows, goats and chickens owned by each district in the Eastern Province. Matrices are also essential in computer graphics — every image on a smartphone screen in Kigali is manipulated using matrix transformations. In this lesson, we will learn how to add, subtract and multiply matrices."
            ex = "Example 1: Add matrices A = [[1, 3], [5, 7]] and B = [[2, 4], [6, 8]].\nSolution:\nA + B = [[1+2, 3+4], [5+6, 7+8]] = [[3, 7], [11, 15]].\n\nExample 2: Find the determinant of matrix M = [[4, 3], [2, 5]].\nSolution:\ndet(M) = (4 × 5) - (3 × 2) = 20 - 6 = 14."
            pr = "1. Add the matrices: [[2, 5], [1, 3]] + [[4, 1], [2, 2]].\n2. Subtract: [[10, 8], [6, 4]] - [[3, 5], [1, 2]].\n3. Find the determinant of [[6, 2], [3, 4]].\n4. Multiply matrix A = [[1, 2], [3, 4]] by matrix B = [[2, 0], [1, 3]].\n5. A point (2, 3) is reflected in the y-axis. Use a matrix transformation to find the image coordinates."
            su = "* A matrix is a rectangular arrangement of numbers in rows and columns.\n* Addition and subtraction are performed element by element.\n* The determinant of [[a,b],[c,d]] is ad - bc.\n* Matrices are used in computer graphics, economics and engineering."
            q = {"question": "What is the determinant of [[5, 3], [2, 4]]?", "options": {"A": "14", "B": "26", "C": "20", "D": "7"}, "answer": "A"}

        elif "equation" in t or "inequality" in t or "algebra" in t or "expression" in t or "factor" in t or "quadratic" in t or "simultan" in t or "elimination" in t or "substitution" in t:
            obj = "By the end of this lesson, you should be able to:\n- Simplify and manipulate algebraic expressions\n- Solve linear and quadratic equations using appropriate methods\n- Apply algebraic techniques to solve real-world problems"
            reading = f"Algebra is a powerful language for describing patterns and solving problems. In Rwanda, algebraic thinking helps farmers calculate how much fertiliser to buy based on field size, helps business owners in Kigali determine pricing strategies, and helps students understand how quantities relate to each other. An equation states that two expressions are equal — like 2x + 3 = 7, meaning twice a number plus 3 equals 7. Solving equations means finding the unknown value that makes the statement true."
            ex = "Example 1: Solve 2x + 5 = 13.\nSolution:\n2x + 5 = 13 → 2x = 13 - 5 = 8 → x = 8 / 2 = 4.\nCheck: 2(4) + 5 = 8 + 5 = 13 ✓\n\nExample 2: Solve x² - 5x + 6 = 0 by factorisation.\nSolution:\nx² - 5x + 6 = (x - 2)(x - 3) = 0\nSo x - 2 = 0 or x - 3 = 0, meaning x = 2 or x = 3."
            pr = "1. Simplify: 3x + 2x - 5.\n2. Solve: 4x - 7 = 17.\n3. Solve: 3(x + 2) = 21.\n4. Factorise and solve: x² + 7x + 12 = 0.\n5. A farmer in the Eastern Province has a rectangular field. The length is 3 metres more than the width. The area is 70 m². Find the dimensions of the field."
            su = "* Algebra uses variables to represent unknown quantities.\n* Solve equations by isolating the variable on one side.\n* Quadratic equations can be solved by factorisation, completing the square, or the quadratic formula.\n* Algebraic methods help solve real problems in farming, business and everyday life."
            q = {"question": "Solve 3x - 5 = 10.", "options": {"A": "x = 3", "B": "x = 5", "C": "x = 15", "D": "x = 2"}, "answer": "B"}

        elif "function" in t or "graph" in t or "domain" in t or "range" in t or "relation" in t:
            obj = "By the end of this lesson, you should be able to:\n- Define a function and identify its domain and range\n- Represent functions using equations, tables and graphs\n- Interpret graphs of linear and quadratic functions"
            reading = f"A function is a special relationship where each input has exactly one output. Think of a function as a machine: you put something in, and it produces a predictable result. In Rwanda, functions can describe many real relationships: the cost of petrol as a function of the number of litres, the height of a growing maize plant as a function of time, or the temperature in Kigali as a function of the time of day. Functions can be represented in several ways — as equations, as tables of values, or as graphs on a coordinate plane."
            ex = "Example 1: If f(x) = 2x + 1, find f(3) and f(-2).\nSolution:\nf(3) = 2(3) + 1 = 6 + 1 = 7.\nf(-2) = 2(-2) + 1 = -4 + 1 = -3.\n\nExample 2: Plot the function f(x) = x + 2 for x = 0, 1, 2, 3, 4.\nSolution:\nCreate a table:\nx | 0 | 1 | 2 | 3 | 4\nf(x) | 2 | 3 | 4 | 5 | 6\nPlot these points and draw a straight line through them."
            pr = "1. If f(x) = 3x - 4, find f(0) and f(5).\n2. State the domain and range of f(x) = x².\n3. Complete the table for f(x) = 2x - 1: x = -1, 0, 1, 2, 3.\n4. Determine if the relation {(1,2), (2,4), (1,3), (3,6)} is a function. Explain.\n5. The cost of sending a parcel through a courier in Kigali is C(w) = 5,000 + 2,000w where w is the weight in kg. How much does it cost to send a 3 kg parcel?"
            su = "* A function gives exactly one output for each input.\n* Domain = set of all possible inputs. Range = set of all possible outputs.\n* Functions can be represented as equations, tables, or graphs.\n* Many real-world relationships in Rwanda can be modelled as functions."
            q = {"question": "If f(x) = 4x - 3, what is f(2)?", "options": {"A": "5", "B": "8", "C": "3", "D": "11"}, "answer": "A"}

        elif "sequence" in t or "pattern" in t or "arithmetic" in t or "geometric" in t or "nth term" in t or "sum" in t:
            obj = "By the end of this lesson, you should be able to:\n- Identify arithmetic and geometric sequences\n- Find the nth term of a sequence\n- Calculate sums of terms in arithmetic sequences"
            reading = f"Sequences and patterns are all around us in Rwanda. The rows of terraced farms on the hills of the Northern Province form a pattern. The amount of money saved each week by a student putting aside 500 RWF forms a sequence: 500, 1,000, 1,500, 2,000... An arithmetic sequence has a constant difference between consecutive terms. A geometric sequence has a constant ratio between consecutive terms. Understanding sequences helps us make predictions and find general rules."
            ex = "Example 1: Find the next three terms of the sequence: 3, 7, 11, 15, ...\nSolution:\nCommon difference = 4. Next terms: 19, 23, 27.\n\nExample 2: Find the nth term of the arithmetic sequence 5, 8, 11, 14, ...\nSolution:\nFirst term a = 5, common difference d = 3.\nnth term = a + (n-1)d = 5 + (n-1)3 = 5 + 3n - 3 = 3n + 2."
            pr = "1. Find the next three terms: 2, 6, 10, 14, ...\n2. Find the 10th term of the sequence: 1, 4, 7, 10, ...\n3. Is the sequence 2, 4, 8, 16, ... arithmetic or geometric? Explain.\n4. A student saves 1,000 RWF in week 1, 1,500 RWF in week 2, 2,000 RWF in week 3 and so on. How much will they save in week 10?\n5. Find the sum of the first 8 terms of the sequence: 2, 5, 8, 11, ..."
            su = "* Arithmetic sequences have a common difference (add/subtract).\n* Geometric sequences have a common ratio (multiply/divide).\n* nth term of an arithmetic sequence = a + (n-1)d.\n* Sequences model many real-life patterns including savings, growth and scheduling."
            q = {"question": "What is the common difference of the sequence 4, 9, 14, 19?", "options": {"A": "4", "B": "5", "C": "9", "D": "3"}, "answer": "B"}

        elif "number" in t or "natural" in t or "integer" in t or "rational" in t or "operation" in t or "order" in t or "number line" in t:
            obj = "By the end of this lesson, you should be able to:\n- Identify and classify different types of numbers (natural, integers, rational)\n- Perform operations on numbers including addition, subtraction, multiplication and division\n- Represent and compare numbers on a number line"
            reading = f"Numbers are the foundation of mathematics. In Rwanda, we use numbers for counting money in the market, measuring ingredients for cooking, telling time, and many other daily activities. Natural numbers (1, 2, 3...) are the counting numbers we learn first. Integers add negative numbers and zero to the set (...-2, -1, 0, 1, 2...). Rational numbers are numbers that can be written as fractions, like 1/2 or 0.75. Understanding these number sets helps us choose the right tool for each calculation."
            ex = "Example 1: Classify -5, 0, 8, 1/2 as natural numbers, integers or rational numbers.\nSolution:\n-5: integer and rational.\n0: integer and rational.\n8: natural, integer and rational.\n1/2: rational only.\n\nExample 2: Calculate: (-8) + 3 - (-2).\nSolution:\n(-8) + 3 = -5.\n-5 - (-2) = -5 + 2 = -3."
            pr = "1. Which of the following is a natural number: -3, 0, 5, 2.5?\n2. Arrange on a number line: -4, 1, -1, 3, 0.\n3. Calculate: 15 - (-3) + (-8).\n4. Write 0.25 as a fraction in simplest form.\n5. In Kigali, the temperature at night was 15°C. It dropped by 22°C by morning. What was the morning temperature?"
            su = "* Natural numbers: {1, 2, 3, ...}. Integers: {..., -2, -1, 0, 1, 2, ...}\n* Rational numbers can be written as fractions.\n* A number line helps visualise the order and relationships between numbers."
            q = {"question": "Which set does the number -7 belong to?", "options": {"A": "Natural numbers only", "B": "Integers only", "C": "Both integers and rational numbers", "D": "Natural numbers and integers"}, "answer": "C"}

        else:
            obj = f"By the end of this lesson on {lesson}, you should be able to:\n- Understand the key concepts related to {lesson}\n- Apply the principles of {lesson} to solve relevant problems\n- Recognise real-world applications of {lesson} in Rwanda and beyond"
            reading = f"This lesson explores the topic of {lesson}. Understanding this concept is important because it appears in many real-world contexts. In Rwanda, knowledge of topics like this helps students build a strong foundation for further study and practical application. As you work through this lesson, think about how {lesson} connects to your own experience — whether in the classroom, in the community, or in everyday problem-solving. Take time to understand each step before moving on."
            ex = f"Example 1: Work through a simple problem related to {lesson}.\nStep 1: Identify the given information and what you need to find.\nStep 2: Choose the appropriate method or formula.\nStep 3: Apply the method step by step, showing all working.\nStep 4: Check your answer for reasonableness.\n\nExample 2: Try a slightly more complex problem on {lesson}.\nStep 1: Break the problem into smaller parts.\nStep 2: Solve each part using the methods you have learned.\nStep 3: Combine the results to find the final answer."
            pr = f"1. What is the main idea behind {lesson}?\n2. Solve a basic problem related to {lesson}.\n3. Apply {lesson} to a real-world situation in Rwanda.\n4. Challenge yourself with a multi-step problem on {lesson}.\n5. Explain how {lesson} connects to other topics you have studied.\n\n(Consult your teacher or ask Rina for help if you are stuck on any question.)"
            su = f"* {lesson} is an important topic in the REB curriculum.\n* Mastering the fundamentals helps you build confidence for advanced topics.\n* Always check your work for accuracy.\n* Use real-world examples to deepen your understanding."
            q = {"question": f"Which of the following best describes {lesson}?", "options": {"A": "A mathematical concept used in problem-solving", "B": "A topic unrelated to everyday life", "C": "Only used in advanced mathematics", "D": "The same as all other lessons"}, "answer": "A"}

        return {
            "objectives": obj,
            "reading": reading,
            "examples": ex,
            "practice": pr,
            "summary": su,
            "quiz": q,
        }

    def _format_quiz(self, quiz) -> str:
        if isinstance(quiz, str):
            return quiz
        if isinstance(quiz, dict):
            lines = [quiz.get("question", "")]
            options = quiz.get("options", {})
            for k in sorted(options.keys()):
                lines.append(f"{k}. {options[k]}")
            answer = quiz.get("answer", "")
            if answer:
                lines.append(f"\nAnswer: {answer}")
            return "\n\n".join(lines)
        return ""

    def _lesson_detail(self, path: list[str], title: str, subject: str) -> QWidget:
        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)

        hero = ImageCard(self.t, self._image_for_subject(subject))
        hero.setMinimumHeight(250)
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(28, 26, 28, 24)
        h = QLabel(title)
        h.setWordWrap(True)
        h.setFont(app_font(27, QFont.Weight.Bold))
        h.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        s = QLabel("A guided lesson built for reading first, then practice, then Rina support only when requested.")
        s.setWordWrap(True)
        s.setMaximumWidth(720)
        s.setFont(app_font(11, QFont.Weight.Medium))
        s.setStyleSheet("color: rgba(255,255,255,225); background: transparent; border: none;")
        hl.addWidget(h)
        hl.addWidget(s)
        hl.addStretch(1)
        lay.addWidget(hero)

        content = self._get_lesson_content(path)

        # Progress stepper — visual guide to lesson structure
        lay.addWidget(self._build_section_stepper(
            ["Objectives", "Reading", "Examples", "Practice", "Summary"]
        ))

        toggle_row = QWidget()
        toggle_row.setStyleSheet("background: transparent;")
        tr = QHBoxLayout(toggle_row)
        tr.setContentsMargins(0, 0, 0, 0)
        show_sol = QCheckBox("Show Solutions")
        show_sol.setFont(app_font(10, QFont.Weight.Bold))
        show_sol.setStyleSheet(f"color: {self.t['text']}; padding: 8px;")
        tr.addWidget(show_sol)
        tr.addStretch(1)
        lay.addWidget(toggle_row)

        sol_card = Card(self.t, "SolutionsCard", True)
        sol_card.setVisible(False)
        sol_card.setStyleSheet(f"background: {self.t['surface2']}; border: 2px solid {self.t['green']}; border-radius: 12px;")
        sl = QVBoxLayout(sol_card)
        sl.setContentsMargins(22, 18, 22, 18)
        sl.setSpacing(10)
        st = QLabel("Solutions")
        st.setFont(app_font(15, QFont.Weight.Bold))
        st.setStyleSheet(f"color: {self.t['green']}; background: transparent; border: none;")
        sl.addWidget(st)

        prac_ans = content.get("practice_answers", "") if content else ""
        if prac_ans:
            pl = QLabel("Practice Answers")
            pl.setFont(app_font(12, QFont.Weight.Bold))
            pl.setStyleSheet(f"color: {self.t['text']}; background: transparent; border: none;")
            sl.addWidget(pl)
            pa = QLabel(prac_ans)
            pa.setWordWrap(True)
            pa.setFont(app_font(11))
            pa.setStyleSheet(f"color: {self.t['muted']}; background: transparent; border: none;")
            sl.addWidget(pa)

        quiz = content.get("quiz", {}) if content else {}
        if isinstance(quiz, dict) and quiz.get("answer"):
            qa = quiz.get("answer", "")
            opts = quiz.get("options", {})
            correct_text = opts.get(qa, "")
            ql = QLabel("Quiz Answer")
            ql.setFont(app_font(12, QFont.Weight.Bold))
            ql.setStyleSheet(f"color: {self.t['text']}; background: transparent; border: none;")
            sl.addWidget(ql)
            txt = f"Question: {quiz.get('question', '')}\nAnswer: {qa}. {correct_text}"
            la = QLabel(txt)
            la.setWordWrap(True)
            la.setFont(app_font(11))
            la.setStyleSheet(f"color: {self.t['green']}; background: transparent; border: none;")
            sl.addWidget(la)

        cb_ans = content.get("checkbox_answers", "") if content else ""
        if cb_ans:
            cl = QLabel("Checkbox Answers")
            cl.setFont(app_font(12, QFont.Weight.Bold))
            cl.setStyleSheet(f"color: {self.t['text']}; background: transparent; border: none;")
            sl.addWidget(cl)
            ca = QLabel(cb_ans)
            ca.setWordWrap(True)
            ca.setFont(app_font(11))
            ca.setStyleSheet(f"color: {self.t['muted']}; background: transparent; border: none;")
            sl.addWidget(ca)

        sl.addStretch(1)

        def _on_toggle(checked):
            sol_card.setVisible(checked)
        show_sol.toggled.connect(_on_toggle)

        # Diagrams section (rendered after reading material)
        diagrams_data = content.get("diagrams", []) if content else []
        if diagrams_data and isinstance(diagrams_data, list):
            for diag in diagrams_data:
                dtype = diag.get("type", "unit_circle")
                dparams = diag.get("params", {})
                dw = MathDiagramWidget(self.t, dtype, dparams)
                dw.setMinimumHeight(220)
                card = Card(self.t, "DiagramCard", True)
                card.setStyleSheet(f"background: {self.t['card']}; border-radius: 12px;")
                cl = QVBoxLayout(card)
                cl.setContentsMargins(22, 18, 22, 18)
                cl.setSpacing(10)
                h = QLabel("Diagram")
                h.setFont(app_font(15, QFont.Weight.Bold))
                h.setStyleSheet(f"color: {self.t['text']}; background: transparent; border: none;")
                cl.addWidget(h)
                cl.addWidget(dw)
                if diag.get("caption"):
                    cap = QLabel(diag["caption"])
                    cap.setWordWrap(True)
                    cap.setFont(QFont("Consolas", 9))
                    cap.setStyleSheet(f"color: {self.t['muted']}; background: transparent; border: none;")
                    cl.addWidget(cap)
                lay.addWidget(card)

        sections = [
            ("Objectives", content.get("objectives", "") if content else "", "objectives"),
            ("Reading Material", content.get("reading", "") if content else "", "reading"),
            ("Worked Examples", content.get("examples", "") if content else "", "examples"),
            ("Practice Questions", content.get("practice", "") if content else "", "practice"),
            ("Summary", content.get("summary", "") if content else "", "summary"),
            ("Deep Explanation", content.get("deep_explanation", "") if content else "", "deep"),
            ("Knowledge Check", self._format_quiz(content.get("quiz", "")) if content else "", "quiz"),
        ]
        for name, body, stype in sections:
            if body:
                lay.addWidget(self._lesson_section(name, body, stype))

        lay.addWidget(sol_card)

        actions = QHBoxLayout()
        complete = PrimaryButton(self.t, "Mark complete", "quizzes", self.t["green"])
        complete.clicked.connect(lambda: self._complete_lesson(path))
        actions.addWidget(complete)
        ask = PrimaryButton(self.t, "Ask Rina about this", "rina", self.t["primary"])
        ask.clicked.connect(lambda: self._ask_rina_about_lesson(path))
        actions.addWidget(ask)
        actions.addStretch(1)
        lay.addLayout(actions)
        return wrap

    def _build_section_stepper(self, names: list[str]) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        for i, name in enumerate(names):
            step = QWidget()
            step.setStyleSheet("background: transparent;")
            sl = QVBoxLayout(step)
            sl.setContentsMargins(4, 0, 4, 0)
            sl.setSpacing(2)
            sl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot = QLabel("\u25CF")
            dot.setStyleSheet(f"color: {self.t['primary']}; font-size: 14px; background: transparent;")
            sl.addWidget(dot, alignment=Qt.AlignmentFlag.AlignCenter)
            label = QLabel(name)
            label.setFont(app_font(9))
            label.setStyleSheet(f"color: {self.t['muted']}; background: transparent;")
            sl.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(step)
            if i < len(names) - 1:
                arr = QLabel("\u2192")
                arr.setStyleSheet(f"color: {self.t['line2']}; font-size: 12px; background: transparent; padding: 0 4px;")
                lay.addWidget(arr)
        return w

    def _lesson_section(self, title: str, body: str, section_type: str = "reading") -> QWidget:
        ACCENT_MAP = {
            "objectives": "purple",
            "reading": "primary",
            "examples": "green",
            "practice": "secondary",
            "summary": "gold",
            "deep": "teal",
        }
        accent = self.t.get(ACCENT_MAP.get(section_type, "primary"), self.t["primary"])
        card = Card(self.t, "LessonSection", True)
        card.setStyleSheet(f"""
            background: {self.t['card']};
            border-left: 4px solid {accent};
            border-top: 1px solid {self.t['line']};
            border-right: 1px solid {self.t['line']};
            border-bottom: 1px solid {self.t['line']};
            border-radius: 0 8px 8px 0;
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(10)
        h = QLabel(title)
        h.setFont(app_font(15, QFont.Weight.Bold))
        h.setStyleSheet(f"color: {self.t['text']}; background: transparent; border: none;")
        lay.addWidget(h)

        raw = str(body) if body is not None else ""
        b = QLabel()
        b.setWordWrap(True)
        b.setFont(app_font(11))
        b.setStyleSheet(f"color: {self.t['text']}; background: transparent; border: none;")

        if "<html>" in raw:
            css = f"""<style>
                body {{ font-family: 'Segoe UI', sans-serif; font-size: 11pt; line-height: 170%; }}
                h3 {{ font-size: 14pt; font-weight: 700; margin: 0 0 14px 0; color: {self.t['primary']}; }}
                h4 {{ font-size: 12pt; font-weight: 600; margin: 18px 0 8px 0; color: {self.t['primary2']}; }}
                p {{ margin: 0 0 10px 0; }}
                ul, ol {{ margin: 6px 0 10px 0; padding-left: 22px; }}
                li {{ margin: 3px 0; }}
                .competence {{ background: {self.t['sky']}; border-left: 4px solid {self.t['primary']}; border-radius: 4px; padding: 10px 14px; margin: 10px 0; }}
                strong {{ font-weight: 700; }}
            </style>"""
            if "</head>" in raw:
                raw = raw.replace("</head>", css + "</head>")
            elif "<html>" in raw:
                raw = raw.replace("<html>", "<html>" + css)
            b.setTextFormat(Qt.TextFormat.RichText)
            b.setText(raw)
        else:
            b.setTextFormat(Qt.TextFormat.PlainText)
            b.setText(raw)

        lay.addWidget(b)
        return card

    def _complete_lesson(self, path: list[str]):
        key = " > ".join(path)
        completed = self.profile.setdefault("completed_lessons", [])
        if key not in completed:
            completed.append(key)
            self.profile["xp"] = int(self.profile.get("xp", 0)) + 40
            touch_study_day(self.profile)
            _save_json(PROFILE_FILE, self.profile)
            self._refresh_profile_labels()
        self.sound.play("xp")
        self._append_log(f"SYS: Lesson complete. +40 XP for {path[-1]}.")

    def _ask_rina_about_lesson(self, path: list[str]):
        self._show_page("rina")
        self._request_rina_activation(voice=False)
        topic = " > ".join(path)
        self._queue_text(f"I am studying {topic}. Explain it with objectives, examples, practice, summary, and a knowledge check.")
        if self.on_lesson_selected:
            try:
                threading.Thread(target=self.on_lesson_selected, args=(path,), daemon=True).start()
            except Exception:
                pass

    def _subject_card(self, name: str, desc: str, progress: int, accent: str, image: Path) -> QWidget:
        card = self._course_card(name, desc, progress, accent, image)
        return card

    def _empty_card(self, text: str) -> QWidget:
        card = Card(self.t, "EmptyCard", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 22, 22, 22)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(app_font(11))
        label.setStyleSheet(f"color: {self.t['muted']};")
        lay.addWidget(label)
        return card

    def _build_quizzes_page(self) -> QWidget:
        page, root = self._page_shell(1120)
        root.addWidget(self._headline("Quizzes", "A premium testing flow with analysis, revision advice, and next lessons."))
        shell = Card(self.t, "QuizShell", True)
        lay = QVBoxLayout(shell)
        lay.setContentsMargins(22, 20, 22, 22)
        lay.setSpacing(16)
        self._quiz_answers = {}
        questions = [
            ("mcq1", "Multiple choice", "Which subject is best for practicing equations?", ["Mathematics", "English", "Art", "History"], "Mathematics"),
            ("tf1", "True or false", "A good lesson should include objectives before practice.", ["True", "False"], "True"),
            ("fill1", "Fill in the blank", "REB stands for Rwanda Education ____.", [], "Board"),
            ("match1", "Matching", "Match Chemistry with the closest learning focus.", ["Matter and reactions", "Grammar", "Business plans"], "Matter and reactions"),
        ]
        for key, kind, prompt, options, answer in questions:
            lay.addWidget(self._quiz_question(key, kind, prompt, options, answer))
        essay = QLabel("Short answer: What topic do you want to revise next?")
        essay.setFont(app_font(10, QFont.Weight.Bold))
        lay.addWidget(essay)
        self._short_answer = QTextEdit()
        self._short_answer.setPlaceholderText("Write one or two sentences...")
        self._short_answer.setFixedHeight(92)
        self._short_answer.setStyleSheet(f"background: {self.t['surface2']}; color: {self.t['text']}; border: 1px solid {self.t['line']}; border-radius: 8px; padding: 8px;")
        lay.addWidget(self._short_answer)
        submit = PrimaryButton(self.t, "Submit quiz", "quizzes", self.t["secondary"])
        submit.clicked.connect(self._submit_quiz)
        lay.addWidget(submit, alignment=Qt.AlignmentFlag.AlignRight)
        self._quiz_result_box = QVBoxLayout()
        lay.addLayout(self._quiz_result_box)
        root.addWidget(shell)
        return page

    def _quiz_question(self, key: str, kind: str, prompt: str, options: list[str], answer: str) -> QWidget:
        card = Card(self.t, "QuizQuestion", False)
        self._quiz_answers[key] = {"answer": answer, "value": None}
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        tag = QLabel(kind)
        tag.setFont(app_font(8, QFont.Weight.Bold))
        tag.setStyleSheet(f"color: {self.t['secondary']};")
        lay.addWidget(tag)
        q = QLabel(prompt)
        q.setWordWrap(True)
        q.setFont(app_font(12, QFont.Weight.Bold))
        lay.addWidget(q)
        if key == "fill1":
            inp = QLineEdit()
            inp.setPlaceholderText("Type your answer")
            inp.setStyleSheet(f"background: {self.t['surface2']}; color: {self.t['text']}; border: 1px solid {self.t['line']}; border-radius: 8px; padding: 10px;")
            inp.textChanged.connect(lambda txt, k=key: self._set_quiz_value(k, txt))
            lay.addWidget(inp)
        elif key == "match1":
            combo = QComboBox()
            combo.addItems(["Choose one"] + options)
            combo.setStyleSheet(f"background: {self.t['surface2']}; color: {self.t['text']}; border: 1px solid {self.t['line']}; border-radius: 8px; padding: 8px;")
            combo.currentTextChanged.connect(lambda txt, k=key: self._set_quiz_value(k, "" if txt == "Choose one" else txt))
            lay.addWidget(combo)
        else:
            group = QButtonGroup(card)
            row = QGridLayout()
            for idx, opt in enumerate(options):
                btn = QPushButton(opt)
                btn.setCheckable(True)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setMinimumHeight(40)
                btn.setFont(app_font(9, QFont.Weight.Bold))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {self.t['surface2']};
                        color: {self.t['text']};
                        border: 1px solid {self.t['line']};
                        border-radius: 8px;
                    }}
                    QPushButton:checked {{
                        background: {self.t['primary']};
                        color: white;
                        border-color: {self.t['primary']};
                    }}
                """)
                group.addButton(btn)
                btn.clicked.connect(lambda _=False, k=key, value=opt: self._set_quiz_value(k, value))
                row.addWidget(btn, idx // 2, idx % 2)
            lay.addLayout(row)
        return card

    def _set_quiz_value(self, key: str, value: str):
        self._quiz_answers[key]["value"] = value.strip()

    def _submit_quiz(self):
        clear_layout(self._quiz_result_box)
        total = len(self._quiz_answers)
        correct = 0
        for item in self._quiz_answers.values():
            if (item["value"] or "").lower() == item["answer"].lower():
                correct += 1
        score = int(correct / total * 100)
        record_quiz_score(self.profile, score)
        touch_study_day(self.profile)
        _save_json(PROFILE_FILE, self.profile)
        self._refresh_profile_labels()
        self.sound.play("success" if score >= 70 else "error")
        result = Card(self.t, "QuizResult", True)
        lay = QGridLayout(result)
        lay.setContentsMargins(18, 18, 18, 18)
        ring = ProgressRing(self.t, score, "score", self.t["green"] if score >= 70 else self.t["warning"])
        lay.addWidget(ring, 0, 0, 2, 1)
        h = QLabel("Performance Analysis")
        h.setFont(app_font(16, QFont.Weight.Bold))
        lay.addWidget(h, 0, 1)
        body = QLabel(
            "Strengths: lesson structure and subject recognition.\n"
            "Weaknesses: revise any missed definition before the next quiz.\n"
            "Recommended revision: open Learn and review the current unit summary.\n"
            "Next suggested lesson: Worked examples."
        )
        body.setWordWrap(True)
        body.setFont(app_font(10))
        body.setStyleSheet(f"color: {self.t['muted']};")
        lay.addWidget(body, 1, 1)
        self._quiz_result_box.addWidget(result)

    def _build_missions_page(self) -> QWidget:
        page, root = self._page_shell(1180)
        root.addWidget(self._headline("Missions", "Daily, weekly, and monthly goals make progress visible and rewarding."))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        missions = [
            ("Daily Mission", "Complete 2 lessons", 66, "+120 XP", self.t["secondary"]),
            ("Weekly Mission", "Score 80% in 3 quizzes", 40, "+300 XP", self.t["purple"]),
            ("Monthly Goal", "Master one subject unit", 72, "Certificate", self.t["green"]),
            ("Community Mission", "Help one peer in a study group", 25, "+80 XP", self.t["teal"]),
        ]
        for idx, item in enumerate(missions):
            grid.addWidget(self._mission_card(*item), idx // 2, idx % 2)
        root.addLayout(grid)
        badges = Card(self.t, "BadgeWall", True)
        bl = QGridLayout(badges)
        bl.setContentsMargins(20, 18, 20, 20)
        for idx, (name, color) in enumerate([("Focus Star", self.t["gold"]), ("Quiz Sharp", self.t["purple"]), ("REB Explorer", self.t["teal"]), ("TVET Builder", self.t["green"])]):
            badge = QLabel(name)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setMinimumHeight(76)
            badge.setFont(app_font(11, QFont.Weight.Bold))
            badge.setStyleSheet(f"background: {color}; color: white; border-radius: 8px;")
            bl.addWidget(badge, idx // 4, idx % 4)
        root.addWidget(self._section_header("Badges and Achievements"))
        root.addWidget(badges)
        return page

    def _mission_card(self, title: str, desc: str, value: int, reward: str, accent: str) -> QWidget:
        card = Card(self.t, "MissionCard", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 18)
        h = QLabel(title)
        h.setFont(app_font(15, QFont.Weight.Bold))
        lay.addWidget(h)
        d = QLabel(desc)
        d.setWordWrap(True)
        d.setFont(app_font(10))
        d.setStyleSheet(f"color: {self.t['muted']};")
        lay.addWidget(d)
        lay.addWidget(self._mini_progress(value, accent))
        row = QHBoxLayout()
        row.addWidget(QLabel(reward))
        row.addStretch(1)
        btn = PrimaryButton(self.t, "Claim", "missions", accent)
        btn.setFixedHeight(34)
        btn.clicked.connect(lambda: self.sound.play("xp"))
        row.addWidget(btn)
        lay.addLayout(row)
        return card

    def _build_progress_page(self) -> QWidget:
        page, root = self._page_shell(1180)
        root.addWidget(self._headline("Progress", "Subject mastery, quiz scores, study time, XP, and achievements at a glance."))
        stats = QGridLayout()
        stats.setHorizontalSpacing(14)
        stats.setVerticalSpacing(14)
        for idx, item in enumerate([
            ("Study time", "—", "Track via lessons & quizzes", self.t["primary"], "progress"),
            ("Lessons completed", str(lessons_count(self.profile)), "From your profile", self.t["green"], "learn"),
            ("Quiz scores", quiz_average(self.profile), "Average", self.t["purple"], "quizzes"),
            ("XP earned", f"{self.profile.get('xp', 0)}", "Lessons + quizzes", self.t["gold"], "missions"),
        ]):
            stats.addWidget(self._stat_card(*item), idx // 4, idx % 4)
        root.addLayout(stats)
        charts = QGridLayout()
        charts.setHorizontalSpacing(14)
        charts.setVerticalSpacing(14)
        mastery = Card(self.t, "MasteryCard", True)
        ml = QHBoxLayout(mastery)
        ml.setContentsMargins(16, 16, 16, 16)
        for value, label, color in [(72, "Math", self.t["purple"]), (58, "Chem", self.t["teal"]), (81, "Eng", self.t["secondary"]), (50, "ICT", self.t["primary"])]:
            ml.addWidget(ProgressRing(self.t, value, label, color))
        charts.addWidget(mastery, 0, 0)
        chart = Card(self.t, "TrendCard", True)
        cl = QVBoxLayout(chart)
        cl.setContentsMargins(18, 16, 18, 18)
        cl.addWidget(self._section_header("Study Trend"))
        cl.addWidget(BarChart(self.t, [("Mon", 40, self.t["primary"]), ("Tue", 56, self.t["teal"]), ("Wed", 75, self.t["secondary"]), ("Thu", 62, self.t["purple"]), ("Fri", 90, self.t["green"])]))
        charts.addWidget(chart, 0, 1)
        root.addLayout(charts)
        return page

    def _build_classroom_page(self) -> QWidget:
        page, root = self._page_shell(1180)
        root.addWidget(self._headline("Answer Checker", "Work through practice questions, then check your answers here. Tick each one when your answer matches."))

        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setFont(app_font(10))
        tree.setStyleSheet(f"""
            QTreeWidget {{ background: {self.t['card']}; border: 1px solid {self.t['line']}; border-radius: 10px; padding: 6px; }}
            QTreeWidget::item {{ padding: 6px 0px; }}
            QTreeWidget::item:selected {{ background: {self.t['primary']}40; }}
        """)
        tree.setAnimated(True)
        tree.setIndentation(20)
        tree.setExpandsOnDoubleClick(True)
        tree.setColumnCount(1)

        math_dir = Path(__file__).resolve().parent / "data" / "curriculum" / "math"
        level_order = {"s1": "Senior 1", "s2": "Senior 2", "s3": "Senior 3"}

        for prefix, level_label in level_order.items():
            level_item = QTreeWidgetItem(tree)
            level_item.setText(0, level_label)
            level_item.setFont(0, app_font(11, QFont.Weight.Bold))
            level_item.setForeground(0, QColor(self.t["text"]))

            for fpath in sorted(math_dir.glob(f"{prefix}_unit*.json")):
                try:
                    with open(fpath, encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue
                unit_name = data.get("name", fpath.stem)
                unit_item = QTreeWidgetItem(level_item)
                unit_item.setText(0, unit_name)
                unit_item.setFont(0, app_font(10, QFont.Weight.Bold))
                unit_item.setForeground(0, QColor(self.t["primary"]))

                lessons_content = data.get("lessons_content", [])
                lessons = data.get("lessons", [])
                for li, lesson_content in enumerate(lessons_content):
                    lesson_name = lessons[li] if li < len(lessons) else f"Lesson {li+1}"
                    cb = lesson_content.get("checkbox_answers", "")
                    if cb and len(cb) > 20:
                        lesson_item = QTreeWidgetItem(unit_item)
                        lesson_item.setText(0, lesson_name)
                        lesson_item.setFont(0, app_font(9))
                        lesson_item.setForeground(0, QColor(self.t["text"]))

                        lines = cb.replace("<h3>", "").replace("</h3>", "").split("\n")
                        for line in lines:
                            s = line.strip()
                            if s:
                                # Parse: <p><b>Exercise X.Y:</b> answer text</p>
                                clean = re.sub(r'<[^>]+>', '', s).strip()
                                if clean:
                                    sub_item = QTreeWidgetItem(lesson_item)
                                    cb_widget = QWidget()
                                    cb_lay = QHBoxLayout(cb_widget)
                                    cb_lay.setContentsMargins(0, 0, 0, 0)
                                    checkbox = QCheckBox()
                                    label = QLabel(clean)
                                    label.setWordWrap(True)
                                    label.setFont(app_font(9))
                                    label.setStyleSheet(f"color: {self.t['muted']}; background: transparent; border: none;")
                                    cb_lay.addWidget(checkbox)
                                    cb_lay.addWidget(label, 1)
                                    tree.setItemWidget(sub_item, 0, cb_widget)

        tree.expandToDepth(1)
        root.addWidget(tree)
        return page

    def _build_community_page(self) -> QWidget:
        page, root = self._page_shell(1180)
        root.addWidget(self._headline("Research Hub", "Click a hub to discuss questions, homework, curiosity, and invention ideas with Rina."))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for idx, item in enumerate([
            ("Homework Clinic", "Bring a question, show your attempt, get guided correction", self.t["purple"]),
            ("Curiosity Lab", "Ask why things work and connect ideas across subjects", self.t["teal"]),
            ("Invention Studio", "Turn project ideas into research plans and prototypes", self.t["secondary"]),
            ("Exam Research Desk", "Compare notes, past papers, and weak topics", self.t["green"]),
        ]):
            grid.addWidget(self._community_card(*item), idx // 2, idx % 2)
        root.addLayout(grid)
        root.addWidget(self._discussion_panel("Research Prompts", ["Explain this homework step by step without giving away the answer first.", "Help me design an invention that solves a school or community problem.", "What should I research before starting my science project?"]))
        return page

    def _community_card(self, title: str, desc: str, accent: str) -> QWidget:
        card = Card(self.t, "CommunityCard", True)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        icon = QLabel()
        icon.setFixedSize(52, 52)
        icon.setPixmap(make_icon("community", accent, 44).pixmap(44, 44))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"background: {self.t['surface2']}; border-radius: 8px;")
        lay.addWidget(icon)
        col = QVBoxLayout()
        h = QLabel(title)
        h.setFont(app_font(14, QFont.Weight.Bold))
        d = QLabel(desc)
        d.setWordWrap(True)
        d.setFont(app_font(9))
        d.setStyleSheet(f"color: {self.t['muted']};")
        col.addWidget(h)
        col.addWidget(d)
        lay.addLayout(col, stretch=1)
        join = PrimaryButton(self.t, "Discuss", "rina", accent)
        join.setFixedWidth(92)
        join.clicked.connect(lambda: self._open_research_hub(title))
        lay.addWidget(join)
        return card

    def _open_research_hub(self, title: str):
        self._show_page("rina")
        self._request_rina_activation(voice=False)
        self._queue_text(f"Open the {title} research hub. Help me discuss questions, homework, curiosity, and invention ideas using a professional learning structure.")

    def _discussion_panel(self, title: str, items: list[str]) -> QWidget:
        card = Card(self.t, "DiscussionPanel", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.addWidget(self._section_header(title))
        for item in items:
            row = QLabel(item)
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            row.setWordWrap(True)
            row.setFont(app_font(10))
            row.setStyleSheet(f"background: {self.t['surface2']}; color: {self.t['text']}; border: 1px solid {self.t['line']}; border-radius: 8px; padding: 12px;")
            row.mousePressEvent = lambda _e, prompt=item: self._open_prompt_discussion(prompt)
            lay.addWidget(row)
        return card

    def _open_prompt_discussion(self, prompt: str):
        self._show_page("rina")
        self._request_rina_activation(voice=False)
        self._queue_text(prompt)

    def _build_resources_page(self) -> QWidget:
        page, root = self._page_shell(1180)
        root.addWidget(self._headline("Resources", "Official REB learning materials, Rahura study tools, uploads, and clear revision structure."))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        resources = [
            ("REB Books P4-P6", "Primary 4 to Primary 6 documents organized for daily study.", asset("rahura", "exercise-book-red.jpg"), self.t["secondary"]),
            ("REB Books S1-S6", "Secondary school materials and revision structure from S1 to S6.", asset("rahura", "exercise-book-green.jpg"), self.t["green"]),
            ("Stationery Toolkit", "Rahura notebooks, pencils, calculator, and planning boards.", asset("rahura", "colored-pencils.jpg"), self.t["gold"]),
        ]
        for idx, (title, desc, img, color) in enumerate(resources):
            grid.addWidget(self._resource_card(title, desc, img, color), 0, idx)
        root.addLayout(grid)
        root.addWidget(self._reb_library_panel())
        upload = Card(self.t, "UploadPanel", True)
        ul = QVBoxLayout(upload)
        ul.setContentsMargins(18, 16, 18, 18)
        ul.addWidget(self._section_header("Upload a learning file"))
        self._drop_zone = FileDropZone(self.t)
        self._drop_zone.file_selected.connect(self._on_file_selected)
        ul.addWidget(self._drop_zone)
        root.addWidget(upload)
        return page

    def _reb_library_panel(self) -> QWidget:
        card = Card(self.t, "RebLibrary", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.setSpacing(10)
        lay.addWidget(self._section_header("REB Book Library"))
        note = QLabel("P4-P6 and S1-S6 are structured here for official REB documents. Use the REB e-learning portal for downloads, then upload files here so Rina can help you study them.")
        note.setWordWrap(True)
        note.setFont(app_font(9))
        note.setStyleSheet(f"color: {self.t['muted']};")
        lay.addWidget(note)
        levels = ["P4", "P5", "P6", "S1", "S2", "S3", "S4", "S5", "S6"]
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for idx, level in enumerate(levels):
            btn = IconButton(self.t, level, "book", self.t["primary"])
            btn.clicked.connect(lambda _=False, lv=level: self._ask_rina_for_reb_level(lv))
            grid.addWidget(btn, idx // 3, idx % 3)
        lay.addLayout(grid)
        links = QLabel("Official sources: reb.gov.rw/publications | elearning.reb.rw")
        links.setFont(app_font(8, QFont.Weight.Bold))
        links.setStyleSheet(f"color: {self.t['primary']};")
        lay.addWidget(links)
        return card

    def _ask_rina_for_reb_level(self, level: str):
        self._show_page("rina")
        self._request_rina_activation(voice=False)
        self._queue_text(f"Build my daily REB study plan for {level}. Organize books/documents, subjects, weekly order, practice, homework help, and revision checks.")

    def _resource_card(self, title: str, desc: str, image: Path, accent: str) -> QWidget:
        card = Card(self.t, "ResourceCard", True)
        card.setMinimumHeight(260)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 16)
        img = ImageCard(self.t, image)
        img.setMinimumHeight(120)
        img.setMaximumHeight(140)
        lay.addWidget(img)
        body = QVBoxLayout()
        body.setContentsMargins(16, 0, 16, 0)
        h = QLabel(title)
        h.setWordWrap(True)
        h.setFont(app_font(14, QFont.Weight.Bold))
        d = QLabel(desc)
        d.setWordWrap(True)
        d.setFont(app_font(9))
        d.setStyleSheet(f"color: {self.t['muted']};")
        body.addWidget(h)
        body.addWidget(d)
        btn = PrimaryButton(self.t, "Open", "resources", accent)
        btn.clicked.connect(lambda: self._open_resource(title))
        body.addWidget(btn)
        lay.addLayout(body)
        return card

    def _open_resource(self, title: str):
        if "P4" in title:
            self._ask_rina_for_reb_level("P4-P6")
        elif "S1" in title:
            self._ask_rina_for_reb_level("S1-S6")
        else:
            self._show_page("learn")

    def _build_rina_page(self) -> QWidget:
        page, root = self._page_shell(1140)
        root.addWidget(self._headline("Talk To Rina", "Type by default, or toggle Speak when you want microphone and voice mode."))
        shell = Card(self.t, "RinaShell", True)
        lay = QGridLayout(shell)
        lay.setContentsMargins(20, 18, 20, 20)
        lay.setHorizontalSpacing(18)
        lay.setVerticalSpacing(14)

        voice = Card(self.t, "VoicePanel", False)
        vl = QVBoxLayout(voice)
        vl.setContentsMargins(18, 16, 18, 18)
        self._voice_wave = VoiceWave(self.t)
        vl.addWidget(self._voice_wave)
        self._rina_state_label = QLabel("Rina is dormant")
        self._rina_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rina_state_label.setFont(app_font(12, QFont.Weight.Bold))
        self._rina_state_label.setStyleSheet(f"color: {self.t['muted']};")
        vl.addWidget(self._rina_state_label)
        mode = QLabel("Chat mode")
        mode.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode.setFont(app_font(9, QFont.Weight.Bold))
        mode.setStyleSheet(f"color: {self.t['text']};")
        vl.addWidget(mode)
        text_mode = PrimaryButton(self.t, "Type", "play", self.t["primary"])
        text_mode.clicked.connect(lambda: self._request_rina_activation(voice=False))
        vl.addWidget(text_mode)
        self._speak_toggle = QCheckBox("Speak")
        self._speak_toggle.setFont(app_font(10, QFont.Weight.Bold))
        self._speak_toggle.setStyleSheet(f"color: {self.t['text']}; padding: 8px;")
        self._speak_toggle.toggled.connect(lambda checked: self._request_rina_activation(voice=checked))
        vl.addWidget(self._speak_toggle)
        lay.addWidget(voice, 0, 0)

        chat = Card(self.t, "RinaChat", False)
        cl = QVBoxLayout(chat)
        cl.setContentsMargins(0, 0, 0, 0)
        header = QWidget()
        header.setStyleSheet(f"background: {self.t['surface2']}; border-bottom: 1px solid {self.t['line']};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 12, 14, 12)
        avatar = QLabel()
        avatar.setFixedSize(38, 38)
        avatar.setPixmap(make_icon("rina", self.t["primary"], 32).pixmap(32, 32))
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"background: {self.t['surface']}; border-radius: 8px;")
        hl.addWidget(avatar)
        hcol = QVBoxLayout()
        name = QLabel("Rina")
        name.setFont(app_font(12, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {self.t['text']};")
        status = QLabel("REB tutor | Homework | Research | Inventions")
        status.setFont(app_font(8))
        status.setStyleSheet(f"color: {self.t['muted']};")
        hcol.addWidget(name)
        hcol.addWidget(status)
        hl.addLayout(hcol)
        hl.addStretch(1)
        cl.addWidget(header)
        self._log = LogWidget(self.t)
        cl.addWidget(self._log)
        input_row = QHBoxLayout()
        input_row.setContentsMargins(12, 0, 12, 12)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a question, homework prompt, or research idea...")
        self._input.returnPressed.connect(self._send)
        self._input.setStyleSheet(f"background: {self.t['surface2']}; color: {self.t['text']}; border: 1px solid {self.t['line']}; border-radius: 8px; padding: 0 14px;")
        self._input.setFixedHeight(44)
        input_row.addWidget(self._input)
        send = PrimaryButton(self.t, "Send", "play", self.t["primary"])
        send.clicked.connect(self._send)
        input_row.addWidget(send)
        cl.addLayout(input_row)
        lay.addWidget(chat, 0, 1)
        lay.setColumnStretch(0, 1)
        lay.setColumnStretch(1, 2)
        root.addWidget(shell)
        return page

    def _build_profile_page(self) -> QWidget:
        page, root = self._page_shell(1120)
        root.addWidget(self._headline("Profile", "Your avatar, goals, achievements, certificates, and learning summary."))
        card = Card(self.t, "ProfileHero", True)
        lay = QGridLayout(card)
        lay.setContentsMargins(24, 22, 24, 22)
        av = AvatarWidget(self.t, self._effective_profile(), 108)
        lay.addWidget(av, 0, 0, 2, 1)
        name = QLabel(self._effective_profile()["username"])
        name.setFont(app_font(24, QFont.Weight.Bold))
        lay.addWidget(name, 0, 1)
        meta = QLabel(f"{self.profile.get('xp', 0)} XP | {self.profile.get('streak', 0)} day streak | Inzira y'amashuri mu Rwanda")
        meta.setFont(app_font(10))
        meta.setStyleSheet(f"color: {self.t['muted']};")
        lay.addWidget(meta, 1, 1)
        edit = PrimaryButton(self.t, "Edit profile", "profile", self.t["secondary"])
        edit.clicked.connect(self._show_profile_overlay)
        lay.addWidget(edit, 0, 2)
        root.addWidget(card)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for idx, item in enumerate([
            ("Completed lessons", str(lessons_count(self.profile)), "Keep building", self.t["green"], "learn"),
            ("Current goal", "Master Chemistry Unit 1", "72% complete", self.t["teal"], "missions"),
            ("Badges", "8", "3 new this month", self.t["gold"], "progress"),
            ("Certificates", "2", "Math foundation, ICT basics", self.t["purple"], "resources"),
        ]):
            grid.addWidget(self._stat_card(*item), idx // 4, idx % 4)
        root.addLayout(grid)
        return page

    def _build_settings_page(self) -> QWidget:
        page, root = self._page_shell(980)
        root.addWidget(self._headline("Settings", "Theme, accessibility, profile, and existing AI connection settings."))
        card = Card(self.t, "SettingsCard", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 20)
        dark = QCheckBox("Dark mode")
        dark.setChecked(self.dark)
        dark.setFont(app_font(10, QFont.Weight.Bold))
        dark.setStyleSheet(f"color: {self.t['text']};")
        dark.toggled.connect(self._toggle_dark_mode)
        lay.addWidget(dark)
        high = QCheckBox("High contrast focus states")
        high.setChecked(True)
        high.setFont(app_font(10, QFont.Weight.Bold))
        high.setStyleSheet(f"color: {self.t['text']};")
        lay.addWidget(high)
        api = PrimaryButton(self.t, "Configure AI keys", "settings", self.t["primary"])
        api.clicked.connect(self._show_setup)
        lay.addWidget(api)
        signout = PrimaryButton(self.t, "Sign out / Sohoka", "settings", self.t["error"])
        signout.clicked.connect(self._sign_out)
        lay.addWidget(signout)
        root.addWidget(card)
        return page

    def _sign_out(self):
        self.profile["authenticated"] = False
        _save_json(PROFILE_FILE, self.profile)
        self._rebuild_interface()

    def _set_learn_path(self, path: list[str]):
        self._learn_path = path
        self._lesson_detail_path = []
        self._render_learn()
        self.sound.play("click")

    def _show_page(self, key: str):
        if key == "learn":
            self._render_learn()
        self._current_page = key
        self._stack.setCurrentWidget(self._pages[key])
        self._set_active_nav(key)
        self.sound.play("click")
        if key == "rina" and not getattr(self, "_rina_auto_activated", False):
            self._rina_auto_activated = True
            self._request_rina_activation(voice=False)

    def _set_active_nav(self, key: str):
        for k, btn in getattr(self, "_nav_buttons", {}).items():
            btn.set_active(k == key)

    def _start_quick_access_lesson(self, subject: str):
        self._show_page("learn")
        self._open_lesson(["Quick Access", subject, f"{subject} learning path"])

    def _request_rina_activation(self, voice: bool):
        if not self._check_config():
            self._api_after_save = lambda: self._request_rina_activation(voice)
            self._show_setup()
            return
        if voice:
            self._muted = False
            self._apply_state("LISTENING")
            self._append_log("SYS: Voice mode started. Microphone controls are now active.")
        else:
            self._muted = True
            self._apply_state("TEXT_READY")
        self._rina_started.set()
        self._flush_pending_text()

    def _send(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._append_log(f"You: {text}")
        self._request_rina_activation(voice=False)
        self._queue_text(text)

    def _queue_text(self, text: str):
        if self.on_text_command:
            try:
                threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()
            except Exception as e:
                self._append_log(f"ERR: {e}")
        else:
            self._pending_text.append(text)
            self._append_log("SYS: Rina is starting. Your message will be sent when the AI session is ready.")

    def _flush_pending_text(self):
        if not self.on_text_command:
            return
        while self._pending_text:
            text = self._pending_text.pop(0)
            try:
                threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()
            except Exception as e:
                self._append_log(f"ERR: {e}")

    def set_text_command_handler(self, cb):
        self.on_text_command = cb
        self._flush_pending_text()

    def _append_log(self, text: str):
        if hasattr(self, "_log"):
            self._log.append_log(text)

    def _apply_state(self, state: str):
        self._state = state
        if hasattr(self, "_voice_wave"):
            self._voice_wave.active = state in {"LISTENING", "SPEAKING", "THINKING", "PROCESSING"}
            self._voice_wave.update()
        if hasattr(self, "_rina_state_label"):
            if state == "THINKING":
                self._thinking_dots = 0
                self._thinking_timer.start()
                self._rina_state_label.setText("Thinking")
            else:
                self._thinking_timer.stop()
                self._thinking_dots = 0
                label = {
                    "DORMANT": "Rina is dormant",
                    "TEXT_READY": "Text mode ready",
                    "LISTENING": "Listening",
                    "SPEAKING": "Speaking",
                    "PROCESSING": "Working",
                    "MUTED": "Muted",
                }.get(state, state.title())
                self._rina_state_label.setText(label)
            color = self.t["secondary"] if state in {"LISTENING", "SPEAKING"} else self.t["muted"]
            self._rina_state_label.setStyleSheet(f"color: {color};")

    def _tick_thinking(self):
        self._thinking_dots = (self._thinking_dots % 3) + 1
        self._rina_state_label.setText("Thinking" + "." * self._thinking_dots)

    def _on_file_selected(self, path: str):
        self._current_file = path
        p = Path(path)
        size = self._fmt_size(p.stat().st_size) if p.exists() else "unknown size"
        self._append_log(f"FILE: {p.name} ({size}) loaded")
        if self.on_text_command:
            msg = (
                f"[FILE_UPLOADED] path={path} | name={p.name} | size={size} | "
                f"Tell the student you can see the uploaded file and ask how to use it for learning."
            )
            threading.Thread(target=self.on_text_command, args=(msg,), daemon=True).start()

    def _fmt_size(self, size: int) -> str:
        n = float(size)
        for unit in ["B", "KB", "MB", "GB"]:
            if n < 1024 or unit == "GB":
                return f"{int(n)}{unit}" if unit == "B" else f"{n:.1f}{unit}"
            n /= 1024
        return f"{size}B"

    def _toggle_mute(self):
        self._muted = not self._muted
        self._apply_state("MUTED" if self._muted else "LISTENING")
        self._append_log("SYS: Microphone muted." if self._muted else "SYS: Microphone active.")

    def _toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def _toggle_dark_mode(self, checked: bool):
        self.profile["theme"] = "dark" if checked else "light"
        _save_json(PROFILE_FILE, self.profile)
        self.dark = checked
        self.t = DARK if self.dark else LIGHT
        self._canvas.set_theme(self.t)
        self._rebuild_interface()

    def _toggle_sound(self, checked: bool):
        self.sound.enabled = checked
        self.profile["sound"] = checked
        _save_json(PROFILE_FILE, self.profile)
        if checked:
            self.sound.play("success")

    def _rebuild_interface(self):
        if self.profile.get("authenticated"):
            self._build_app_shell()
        else:
            self._build_auth_landing()

    def _refresh_profile_labels(self):
        profile = self._effective_profile()
        self._side_avatar.profile = profile
        self._side_avatar.update()
        self._top_avatar.profile = profile
        self._top_avatar.update()
        self._side_name.setText(profile["username"])
        self._side_stat.setText(f"{profile.get('streak', 0)} day streak")
        self._xp_label.setText(f"{profile.get('xp', 0)} XP")
        self._top_streak.setText(f"{profile.get('streak', 0)} day streak")

    def _show_profile_overlay(self):
        self._clear_overlay()
        ov = ProfileOverlay(self.t, self.profile, self.centralWidget())
        ov.done.connect(self._on_profile_done)
        self._overlay = ov
        self._center_overlay(520, 480)
        ov.show()
        ov.raise_()

    def _on_profile_done(self, profile: dict):
        self.profile = profile
        self._clear_overlay()
        self.profile["sound"] = False
        self.sound.enabled = False
        _save_json(PROFILE_FILE, self.profile)
        if hasattr(self, "_stack"):
            self._refresh_profile_labels()
        self._rebuild_interface()

    def _show_setup(self):
        self._clear_overlay()
        ov = SetupOverlay(self.t, self.centralWidget())
        ov.done.connect(self._on_setup_done)
        self._overlay = ov
        self._center_overlay(500, 420)
        ov.show()
        ov.raise_()

    def _on_setup_done(self, key: str, or_key: str, os_name: str):
        _save_json(API_FILE, {"gemini_api_key": key, "openrouter_api_key": or_key, "os_system": os_name})
        self._clear_overlay()
        self._append_log("SYS: AI keys saved. Rina can start when requested.")
        cb = self._api_after_save
        self._api_after_save = None
        if cb:
            cb()

    def _clear_overlay(self):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None

    def _center_overlay(self, w: int | None = None, h: int | None = None):
        if not self._overlay:
            return
        if w is None:
            w = self._overlay.width() or 500
        if h is None:
            h = self._overlay.height() or 430
        cw = self.centralWidget()
        self._overlay.setGeometry(max(8, (cw.width() - w) // 2), max(8, (cw.height() - h) // 2), min(w, cw.width() - 16), min(h, cw.height() - 16))

    def _check_config(self) -> bool:
        data = _load_json(API_FILE, {})
        return bool(data.get("gemini_api_key")) and bool(data.get("openrouter_api_key")) and bool(data.get("os_system"))

    def wait_for_api_key(self):
        while not self._check_config():
            time.sleep(0.1)

    def wait_for_rina_activation(self):
        self._rina_started.wait()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center_overlay()
        if hasattr(self, "_sidebar"):
            self._apply_compact(self.width() < 900)

    def _apply_compact(self, compact: bool):
        if not hasattr(self, "_sidebar"):
            return
        if getattr(self, "_compact", None) == compact and self._sidebar.width() in {_LEFT_W, _LEFT_W_COMPACT}:
            return
        self._compact = compact
        self._sidebar.setFixedWidth(_LEFT_W_COMPACT if compact else _LEFT_W)
        self._brand_title.setVisible(not compact)
        self._brand_sub.setVisible(not compact)
        self._profile_card.setVisible(not compact)
        for btn in self._nav_buttons.values():
            btn.set_compact(compact)

    def closeEvent(self, event):
        try:
            self._canvas._timer.stop()
        except Exception:
            pass
        super().closeEvent(event)

    def _accent_for(self, name: str) -> str:
        low = (name or "").lower()
        if "math" in low:
            return self.t["purple"]
        if "chem" in low or "science" in low or "physics" in low:
            return self.t["teal"]
        if "english" in low:
            return self.t["secondary"]
        if "ict" in low or "computer" in low:
            return self.t["primary"]
        if "tvet" in low or "trade" in low:
            return self.t["gold"]
        if "bio" in low:
            return self.t["green"]
        return self.t["primary"]

    def _image_for_subject(self, name: str) -> Path:
        low = (name or "").lower()
        if "math" in low or "ict" in low:
            return asset("rahura", "s-calculator-b.jpg")
        if "chem" in low or "science" in low or "bio" in low:
            return asset("rahura", "exercise-book-green.jpg")
        if "english" in low:
            return asset("rahura", "exercise-book-red.jpg")
        if "community" in low or "class" in low:
            return asset("rahura", "2.jpg")
        return asset("rahura", "1.jpg")

    def _icon_for_type(self, node_type: str) -> str:
        return {
            "level": "learn",
            "sublevel": "classroom",
            "alevel_category": "progress",
            "tvet_category": "missions",
            "combination": "community",
            "trade_group": "classroom",
            "trade": "resources",
            "subject": "book",
            "unit": "learn",
        }.get(node_type, "book")

    def _description_for(self, node_type: str) -> str:
        return {
            "level": "Choose a learning level.",
            "sublevel": "Open subjects and learning pathways.",
            "subject": "Explore units and topic lessons.",
            "unit": "Start structured lessons and practice.",
            "trade": "Build practical TVET skills.",
        }.get(node_type, "Open this curriculum pathway.")

    def _difficulty_for(self, node_type: str) -> str:
        return {
            "level": "Pathway",
            "sublevel": "Program",
            "subject": "Core subject",
            "unit": "Lesson unit",
            "trade": "TVET skill",
        }.get(node_type, node_type.replace("_", " ").title())


class _RootShim:
    def __init__(self, app: QApplication):
        self._app = app

    def mainloop(self):
        self._app.exec()

    def protocol(self, *_):
        pass


class JarvisUI:
    def __init__(self):
        self._app = QApplication.instance() or QApplication(sys.argv)
        self._app.setStyle("Fusion")
        self._win = MainWindow()
        self._win.show()
        self.root = _RootShim(self._app)

    @property
    def muted(self) -> bool:
        return self._win._muted

    @muted.setter
    def muted(self, value: bool):
        self._win._muted = bool(value)
        self._win._apply_state("MUTED" if value else "LISTENING")

    def flush_pending_text(self):
        self._win._flush_pending_text()

    @property
    def current_file(self) -> str | None:
        return self._win._current_file

    @property
    def on_text_command(self):
        return self._win.on_text_command

    @on_text_command.setter
    def on_text_command(self, cb):
        self._win.set_text_command_handler(cb)

    @property
    def on_lesson_selected(self):
        return self._win.on_lesson_selected

    @on_lesson_selected.setter
    def on_lesson_selected(self, cb):
        self._win.on_lesson_selected = cb

    def set_state(self, state: str):
        self._win._state_sig.emit(state)

    def write_log(self, text: str):
        self._win._log_sig.emit(text)

    def wait_for_api_key(self):
        self._win.wait_for_api_key()

    def wait_for_rina_activation(self):
        self._win.wait_for_rina_activation()

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        if not self.muted:
            self.set_state("LISTENING")
