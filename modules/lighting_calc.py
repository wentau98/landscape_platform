import sys
import math
import uuid
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QSlider, QGroupBox, QTextEdit, 
                             QProgressBar, QComboBox, QLCDNumber, QSplitter,
                             QGridLayout, QFormLayout, QLineEdit, QHeaderView, 
                             QTableWidget, QTableWidgetItem, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QSize, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPolygonF, QPainterPath

# =================================================================
# 1. 样式规范：现代数字化看板风格 (Tailwind-Base)
# =================================================================
LIGHTING_STYLE = """
QWidget#LightingModule { background-color: #F8FAFC; }
QFrame#ControlPanel { background-color: white; border-right: 1px solid #E2E8F0; }
QFrame#PropPanel { background-color: white; border-left: 1px solid #E2E8F0; }

QLabel#Title { font-size: 18px; font-weight: 800; color: #1E293B; margin-bottom: 10px; }
QLabel#SubTitle { font-size: 12px; color: #64748B; font-weight: bold; text-transform: uppercase; }

/* 按钮体系 */
QPushButton#PrimaryBtn {
    background-color: #6366F1; color: white; border-radius: 8px;
    padding: 10px; font-weight: bold; border: none;
}
QPushButton#PrimaryBtn:hover { background-color: #4F46E5; }

QPushButton#DangerBtn {
    background-color: #FFF1F2; color: #E11D48; border: 1px solid #FDA4AF;
    border-radius: 8px; padding: 10px; font-weight: bold;
}
QPushButton#DangerBtn:hover { background-color: #E11D48; color: white; }

QPushButton#SuccessBtn {
    background-color: #10B981; color: white; border-radius: 8px;
    padding: 10px; font-weight: bold; border: none;
}

/* 输入控件 */
QLineEdit, QComboBox {
    border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px; background: #F8FAFC;
}
QLineEdit:focus { border: 1px solid #6366F1; background: white; }

QTableWidget { border: none; gridline-color: #F1F5F9; font-size: 12px; }
QTableWidget::item { padding: 5px; }

QProgressBar { background-color: #F1F5F9; border: none; border-radius: 4px; text-align: center; color: transparent; }
QProgressBar::chunk { background-color: #10B981; }
"""

# =================================================================
# 2. 核心逻辑层：资产模型与天文引擎
# =================================================================

class AssetLibrary:
    """资产元数据字典：定义不同类别的物理与生物特性"""
    SCHEMA = {
        "地标建筑": {"cat": "建筑", "h": 35.0, "color": "#1E293B", "opacity": 220, "min_sun": 0, "shape": "rect"},
        "景观连廊": {"cat": "建筑", "h": 4.5, "color": "#475569", "opacity": 180, "min_sun": 0, "shape": "rect"},
        "孤植名木": {"cat": "植被", "h": 12.0, "color": "#065F46", "opacity": 110, "min_sun": 6, "shape": "circle"},
        "组团灌木": {"cat": "植被", "h": 1.5, "color": "#059669", "opacity": 130, "min_sun": 4, "shape": "circle"},
        "漫步路人": {"cat": "人文", "h": 1.8, "color": "#4338CA", "opacity": 160, "min_sun": 0, "shape": "human"}
    }

class LightingAsset:
    """资产实例实体：维护实时位置、状态与审计数据"""
    def __init__(self, name: str, x: float, y: float, type_key: str):
        self.uid = str(uuid.uuid4())[:8]
        self.name = name
        self.x, self.y = x, y
        self.type_key = type_key
        
        # 加载元数据
        config = AssetLibrary.SCHEMA[type_key]
        self.category = config["cat"]
        self.height = config["h"]
        self.color = QColor(config["color"])
        self.opacity = config["opacity"]
        self.min_sun = config["min_sun"]
        self.shape_type = config["shape"]
        
        # 实时状态
        self.is_selected = False
        self.audit_res = "待扫描"
        self.total_sun_hours = 0.0

    def get_rect(self) -> QRectF:
        w, h = (40, 40) if self.category != "人文" else (18, 45)
        return QRectF(self.x, self.y, w, h)

class SolarDynamics:
    """高精度太阳动力学引擎"""
    def __init__(self, latitude: float = 31.23):
        self.lat = latitude

    def get_position(self, dt: datetime) -> Tuple[float, float]:
        """核心算法：计算太阳高度角与方位角 (SPA 简化模型)"""
        day_of_year = dt.timetuple().tm_yday
        hour = dt.hour + dt.minute / 60.0
        
        # 赤纬与时角计算
        decl = 23.45 * math.sin(math.radians(360 / 365 * (day_of_year - 81)))
        hour_angle = (hour - 12) * 15
        
        phi = math.radians(self.lat)
        delta = math.radians(decl)
        omega = math.radians(hour_angle)
        
        sin_alt = math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.cos(omega)
        alt = math.asin(max(-1.0, min(1.0, sin_alt)))
        
        cos_azi = (math.sin(delta) - math.sin(alt) * math.sin(phi)) / (math.cos(alt) * math.cos(phi))
        azi = math.acos(max(-1.0, min(1.0, cos_azi)))
        if hour_angle > 0: azi = 2 * math.pi - azi
        
        return alt, azi

# =================================================================
# 3. 渲染引擎：形象化交互画布
# =================================================================

class InteractiveCanvas(QFrame):
    """交互渲染引擎：支持多态阴影渲染与实时拖拽"""
    object_selected = pyqtSignal(LightingAsset)
    scene_modified = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.assets: List[LightingAsset] = []
        self.sun_alt = 0.5
        self.sun_azi = 0.0
        self.drag_obj: Optional[LightingAsset] = None
        self.offset = QPointF(0, 0)
        self.setMouseTracking(True)
        self.setMinimumSize(600, 600)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. 绘制环境基底 (模拟草地网格)
        painter.fillRect(self.rect(), QColor("#F1F5F9"))
        painter.setPen(QPen(QColor(0,0,0,10)))
        for i in range(0, self.width(), 40): painter.drawLine(i, 0, i, self.height())
        for j in range(0, self.height(), 40): painter.drawLine(0, j, self.width(), j)

        # 计算通用阴影偏移向量 (L = H / tan(alt))
        l_weight = 1.0 / math.tan(self.sun_alt) if self.sun_alt > 0.08 else 8.0
        l_weight = min(10.0, l_weight)
        ox = math.sin(self.sun_azi + math.pi) * l_weight
        oy = math.cos(self.sun_azi + math.pi) * l_weight

        # 2. 渲染阴影层
        if self.sun_alt > 0:
            for a in self.assets: self._draw_asset_shadow(painter, a, ox, oy)
        
        # 3. 渲染本体层
        for a in self.assets: self._draw_asset_body(painter, a)

    def _draw_asset_shadow(self, painter, a, ox, oy):
        painter.save()
        color = QColor(0, 0, 0, a.opacity // 2)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        rect = a.get_rect()
        path = QPainterPath()
        
        if a.shape_type == "rect":
            path.moveTo(rect.left(), rect.bottom())
            path.lineTo(rect.right(), rect.bottom())
            path.lineTo(rect.right() + ox * a.height, rect.bottom() + oy * a.height)
            path.lineTo(rect.left() + ox * a.height, rect.bottom() + oy * a.height)
        elif a.shape_type == "circle":
            s_rect = rect.translated(ox * a.height * 0.5, oy * a.height * 0.5)
            path.addEllipse(s_rect)
        elif a.shape_type == "human":
            painter.setPen(QPen(color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(int(rect.center().x()), int(rect.bottom()), 
                             int(rect.center().x() + ox * a.height), int(rect.bottom() + oy * a.height))
            painter.restore(); return

        painter.drawPath(path)
        painter.restore()

    def _draw_asset_body(self, painter, a):
        rect = a.get_rect()
        painter.save()
        
        # 选中描边
        if a.is_selected:
            painter.setPen(QPen(QColor("#6366F1"), 3))
        else:
            painter.setPen(QPen(Qt.GlobalColor.white, 1))

        if a.shape_type == "circle":
            painter.setBrush(QBrush(a.color))
            painter.drawEllipse(rect)
            painter.setBrush(QBrush(a.color.lighter(130)))
            painter.drawEllipse(rect.adjusted(6,6,-6,-6))
        else:
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0, a.color); grad.setColorAt(1, a.color.darker(130))
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(rect, 4, 4)

        # 文字信息
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.drawText(int(rect.left()), int(rect.top()-5), a.name)
        
        # 审计标签显示
        if a.audit_res != "待扫描":
            c = "#10B981" if "通过" in a.audit_res or "合格" in a.audit_res else "#E11D48"
            if a.audit_res == "无需评估": c = "#64748B"
            painter.setPen(QColor(c))
            painter.drawText(int(rect.left()), int(rect.bottom()+15), f"● {a.audit_res}")

        painter.restore()

    # 拖拽交互逻辑
    def mousePressEvent(self, event):
        pos = event.position()
        self.drag_obj = None
        for a in reversed(self.assets):
            a.is_selected = False
            if a.get_rect().contains(pos):
                a.is_selected = True
                self.drag_obj = a
                self.offset = pos - QPointF(a.x, a.y)
                self.object_selected.emit(a)
                break
        self.update()

    def mouseMoveEvent(self, event):
        if self.drag_obj:
            new_p = event.position() - self.offset
            self.drag_obj.x, self.drag_obj.y = new_p.x(), new_p.y()
            self.scene_modified.emit()
            self.update()

    def mouseReleaseEvent(self, event):
        self.drag_obj = None

# =================================================================
# 4. 主界面：三维光影审计工作台
# =================================================================

class LightingCalcModule(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("LightingModule")
        self.setStyleSheet(LIGHTING_STYLE)
        
        # 引擎与数据初始化
        self.solar = SolarDynamics()
        self.sim_time = datetime(2023, 6, 21, 10, 0)
        self.init_ui()
        self._seed_mock_data()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        # ---------------- 1. 左侧控制台 ----------------
        self.ctrl_frame = QFrame(); self.ctrl_frame.setObjectName("ControlPanel"); self.ctrl_frame.setFixedWidth(340)
        cv = QVBoxLayout(self.ctrl_frame)
        
        cv.addWidget(QLabel("光气候调度中心", objectName="Title"))
        
        # 时间控制器
        time_grp = QGroupBox("时空维度流转")
        tl = QVBoxLayout(time_grp)
        self.time_lbl = QLabel("模拟时间: 10:00")
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(420, 1080); self.time_slider.setValue(600)
        self.time_slider.valueChanged.connect(self.sync_physics)
        tl.addWidget(self.time_lbl); tl.addWidget(self.time_slider)
        
        lcd_h = QHBoxLayout()
        self.lcd_alt = QLCDNumber(); self.lcd_azi = QLCDNumber()
        for l in [self.lcd_alt, self.lcd_azi]: l.setFixedHeight(35); l.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        lcd_h.addWidget(QLabel("高度角:")); lcd_h.addWidget(self.lcd_alt)
        lcd_h.addWidget(QLabel("方位角:")); lcd_h.addWidget(self.lcd_azi)
        tl.addLayout(lcd_h)
        cv.addWidget(time_grp)

        # 审计列表
        audit_grp = QGroupBox("生境光照合规性审计")
        al = QVBoxLayout(audit_grp)
        self.audit_table = QTableWidget(0, 3)
        self.audit_table.setHorizontalHeaderLabels(["资产名称", "标准(h)", "结果"])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.audit_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        al.addWidget(self.audit_table)
        cv.addWidget(audit_grp)

        # 诊断日志
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; font-size: 11px;")
        cv.addWidget(QLabel("智能审计追踪:", objectName="SubTitle"))
        cv.addWidget(self.log_area)
        
        self.btn_scan = QPushButton("执行全天候生境扫描 (24H)")
        self.btn_scan.setObjectName("PrimaryBtn")
        self.btn_scan.clicked.connect(self.perform_full_audit)
        cv.addWidget(self.btn_scan)

        self.main_layout.addWidget(self.ctrl_frame)

        # ---------------- 2. 中间：工作画布 ----------------
        self.canvas = InteractiveCanvas()
        self.canvas.object_selected.connect(self.on_asset_picked)
        self.canvas.scene_modified.connect(lambda: self.log_area.append(">> 检测到空间变动，光影场重构中..."))
        self.main_layout.addWidget(self.canvas, 1)

        # ---------------- 3. 右侧：属性矩阵 ----------------
        self.prop_frame = QFrame(); self.prop_frame.setObjectName("PropPanel"); self.prop_frame.setFixedWidth(280)
        pv = QVBoxLayout(self.prop_frame)
        pv.addWidget(QLabel("资产属性编辑矩阵", objectName="Title"))

        self.form = QFormLayout()
        self.in_name = QLineEdit()
        self.in_h = QLineEdit()
        self.in_type = QComboBox(); self.in_type.addItems(list(AssetLibrary.SCHEMA.keys()))
        self.form.addRow("识别名称:", self.in_name)
        self.form.addRow("空间高度(m):", self.in_h)
        self.form.addRow("属性预设:", self.in_type)
        pv.addLayout(self.form)

        self.btn_sync = QPushButton("同步资产物理参数")
        self.btn_sync.setObjectName("SuccessBtn")
        self.btn_sync.clicked.connect(self.sync_properties)
        
        self.btn_add = QPushButton("+ 注入新景观组件")
        self.btn_add.clicked.connect(self.inject_asset)
        
        self.btn_del = QPushButton("× 销毁选中空间资产")
        self.btn_del.setObjectName("DangerBtn")
        self.btn_del.clicked.connect(self.destroy_asset)

        pv.addWidget(self.btn_sync); pv.addSpacing(20)
        pv.addWidget(self.btn_add); pv.addWidget(self.btn_del)
        pv.addStretch()
        self.main_layout.addWidget(self.prop_frame)

    # ---------------- 核心算法与交互实现 ----------------

    def sync_physics(self, m):
        self.sim_time = datetime(2023, 6, 21, 0, 0) + timedelta(minutes=m)
        self.time_lbl.setText(f"模拟时间: {self.sim_time.strftime('%H:%M')}")
        alt, azi = self.solar.get_position(self.sim_time)
        self.lcd_alt.display(f"{math.degrees(alt):.1f}")
        self.lcd_azi.display(f"{math.degrees(azi):.1f}")
        self.canvas.sun_alt, self.canvas.sun_azi = alt, azi
        self.canvas.update()

    def on_asset_picked(self, a):
        self.in_name.setText(a.name)
        self.in_h.setText(str(a.height))
        self.in_type.setCurrentText(a.type_key)
        self.log_area.append(f"审计追踪：选中对象 {a.uid}")

    def sync_properties(self):
        target = next((a for a in self.canvas.assets if a.is_selected), None)
        if not target: return
        try:
            target.name = self.in_name.text()
            target.height = float(self.in_h.text() or 1)
            new_key = self.in_type.currentText()
            if new_key != target.type_key:
                # 重新应用预设逻辑
                target.type_key = new_key
                config = AssetLibrary.SCHEMA[new_key]
                target.category = config["cat"]; target.color = QColor(config["color"])
                target.opacity = config["opacity"]; target.min_sun = config["min_sun"]
                target.shape_type = config["shape"]
            target.audit_res = "待扫描"
            self.canvas.update(); self.refresh_audit_table()
            self.log_area.append(f"数据一致性：组件 {target.uid} 参数已锁定。")
        except: pass

    def perform_full_audit(self):
        """核心业务规则引擎：全天生境审计"""
        self.log_area.append(">>> 启动全量时空光流场审计引擎...")
        self.btn_scan.setEnabled(False); self.btn_scan.setText("正在计算...")
        
        # 模拟全天采样 (08:00 - 18:00, 20min步长)
        for a in self.canvas.assets: a.total_sun_hours = 0.0
        
        for m in range(480, 1081, 20):
            dt = datetime(2023, 6, 21, 0, 0) + timedelta(minutes=m)
            alt, _ = self.solar.get_position(dt)
            if math.degrees(alt) > 15: # 有效日照高度阈值
                for a in self.canvas.assets: a.total_sun_hours += 1/3.0 # 20分钟 = 1/3小时

        for a in self.canvas.assets:
            if a.category == "植被":
                a.audit_res = "合格" if a.total_sun_hours >= a.min_sun else "光照不足"
            else:
                a.audit_res = "无需评估"
            self.log_area.append(f" - {a.name}: 累计受光 {a.total_sun_hours:.1f}h ({a.audit_res})")
            
        self.refresh_audit_table(); self.canvas.update()
        self.btn_scan.setEnabled(True); self.btn_scan.setText("执行全天候生境扫描 (24H)")

    def refresh_audit_table(self):
        self.audit_table.setRowCount(0)
        for a in self.canvas.assets:
            row = self.audit_table.rowCount(); self.audit_table.insertRow(row)
            self.audit_table.setItem(row, 0, QTableWidgetItem(a.name))
            self.audit_table.setItem(row, 1, QTableWidgetItem(f"{a.total_sun_hours:.1f}/{a.min_sun}h"))
            res_item = QTableWidgetItem(a.audit_res)
            if a.audit_res == "合格": res_item.setForeground(QBrush(QColor("#10B981")))
            elif a.audit_res == "光照不足": res_item.setForeground(QBrush(QColor("#E11D48")))
            self.audit_table.setItem(row, 2, res_item)

    def inject_asset(self):
        new_a = LightingAsset(f"新组件-{random.randint(10,99)}", 300, 300, "地标建筑")
        self.canvas.assets.append(new_a); self.canvas.update(); self.refresh_audit_table()

    def destroy_asset(self):
        self.canvas.assets = [a for a in self.canvas.assets if not a.is_selected]
        self.canvas.update(); self.refresh_audit_table()
        self.log_area.append("场景变更：已销毁空间资产及关联阴影场。")

    def _seed_mock_data(self):
        self.canvas.assets = [
            LightingAsset("主塔楼", 80, 80, "地标建筑"),
            LightingAsset("孤植银杏", 320, 180, "孤植名木"),
            LightingAsset("漫步设计师", 450, 420, "漫步路人")
        ]
        self.sync_physics(600); self.refresh_audit_table()

def get_widget():
    w = LightingCalcModule(); w._module_identifier = "lighting_calc"; return w