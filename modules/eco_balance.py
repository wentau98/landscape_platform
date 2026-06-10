import sys
import uuid
import math
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from PyQt6.QtWidgets import (QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QProgressBar, QTreeWidget, 
                             QTreeWidgetItem, QHeaderView, QSplitter, QGroupBox,
                             QDialog, QFormLayout, QLineEdit, QComboBox, 
                             QScrollArea, QMessageBox, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QSize, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient, QConicalGradient

# =================================================================
# 核心视觉风格：生态极简主义
# =================================================================
ECO_STYLE = """
QWidget#EcoModule { background-color: #F8FAF9; }
QFrame#MetricTile {
    background-color: white;
    border: 1px solid #E9EDEA;
    border-radius: 12px;
}
QLabel#MetricLabel { color: #8C948E; font-size: 11px; font-weight: bold; }
QLabel#MetricValue { color: #2D3A30; font-size: 20px; font-weight: 800; font-family: 'Inter', 'Segoe UI'; }

QTreeWidget {
    background-color: white;
    border: 1px solid #E9EDEA;
    border-radius: 12px;
    outline: none;
}
QTreeWidget::item { height: 46px; border-bottom: 1px solid #F2F5F3; }
QTreeWidget::item:selected { background-color: #F0F7F2; color: #10B981; }

QPushButton#PrimaryAction {
    background-color: #10B981;
    color: white;
    border-radius: 8px;
    padding: 12px;
    font-weight: bold;
}
QPushButton#PrimaryAction:hover { background-color: #059669; }

QProgressBar {
    background-color: #E2E8F0;
    border: none;
    border-radius: 4px;
    text-align: center;
}
QProgressBar::chunk { background-color: #10B981; }
"""

# =================================================================
# 核心引擎：碳汇与足迹计算逻辑
# =================================================================

class EcoMetricEngine:
    """
    生态足迹计算引擎：基于 IPCC 标准与园林生命周期评价 (LCA)
    """
    def __init__(self):
        # 物种固碳系数 (kg CO2/m2/year)
        self.sequestration_factors = {
            "阔叶乔木": 4.5,
            "针叶乔木": 3.2,
            "常绿灌木": 2.1,
            "生态草坪": 0.8
        }
        # 建材碳足迹系数 (kg CO2/unit)
        self.carbon_cost_factors = {
            "透水砖": 12.5,  # 每平米
            "花岗岩": 45.2,  # 每平米
            "普通混凝土": 180.0, # 每立方
            "再生木材": 5.2    # 每平米
        }

    def calculate_annual_sequestration(self, area: float, category: str) -> float:
        factor = self.sequestration_factors.get(category, 0.5)
        return area * factor

    def calculate_material_carbon(self, amount: float, category: str) -> float:
        factor = self.carbon_cost_factors.get(category, 10.0)
        return amount * factor

class SustainabilityAudit:
    """业务规则引擎：方案等级评定逻辑"""
    @staticmethod
    def get_rating(net_carbon: float) -> Tuple[str, QColor]:
        if net_carbon < -1000: return "碳中和金奖", QColor("#10B981")
        if net_carbon < 0: return "低碳先锋", QColor("#34D399")
        if net_carbon < 5000: return "环境友好", QColor("#FBBF24")
        return "高环境影响", QColor("#F87171")

# =================================================================
# UI 组件：动态生态仪表盘
# =================================================================

# 修改后的 EcoDonutChart 类
class EcoDonutChart(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(260, 260)
        # 定义核心色系：绿(汇)、红(排)、蓝(耗)
        self.categories = [
            {"label": "年度固碳量", "color": QColor("#10B981"), "value": 0.0},
            {"label": "隐含碳排放", "color": QColor("#F43F5E"), "value": 0.0},
            {"label": "资源能源耗", "color": QColor("#3B82F6"), "value": 0.0}
        ]

    def update_data(self, seq, cost, other):
        total = seq + cost + other
        if total == 0: return
        self.categories[0]["value"] = seq / total
        self.categories[1]["value"] = cost / total
        self.categories[2]["value"] = other / total
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. 绘制环形图主体
        rect = QRectF(30, 10, 200, 200)
        start_angle = 90 * 16
        
        for cat in self.categories:
            span_angle = int(cat["value"] * 360 * 16)
            if span_angle == 0: continue
            
            painter.setBrush(QBrush(cat["color"]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(rect, start_angle, span_angle)
            start_angle += span_angle

        # 2. 绘制中心孔洞 (形成 Donut 效果)
        hole_size = 120
        hole_rect = QRectF(30 + (200-hole_size)/2, 10 + (200-hole_size)/2, hole_size, hole_size)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(hole_rect)

        # 3. 绘制下方图例 (解决你反馈的颜色识别问题)
        legend_y = 225
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        
        spacing = 85
        for i, cat in enumerate(self.categories):
            x_pos = 10 + i * spacing
            # 颜色小方块
            painter.setBrush(QBrush(cat["color"]))
            painter.drawRoundedRect(int(x_pos), legend_y, 12, 12, 3, 3)
            # 文字说明
            painter.setPen(QPen(QColor("#64748B")))
            painter.drawText(int(x_pos + 18), legend_y + 10, cat["label"])

# =================================================================
# 主分析模块
# =================================================================

class MetricTile(QFrame):
    def __init__(self, title, value, unit=""):
        super().__init__()
        self.setObjectName("MetricTile")
        l = QVBoxLayout(self)
        self.t = QLabel(title.upper()); self.t.setObjectName("MetricLabel")
        self.v = QLabel(f"{value} {unit}"); self.v.setObjectName("MetricValue")
        l.addWidget(self.t); l.addWidget(self.v)

class EcoBalanceModule(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("EcoModule")
        self.setStyleSheet(ECO_STYLE)
        self.engine = EcoMetricEngine()
        self.assets = {} # 存储生态资产：{id: {name, cat, value, type}}
        
        self.init_ui()
        self._seed_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        # 1. 顶部数字化看板
        header_h = QHBoxLayout()
        self.m1 = MetricTile("年度总固碳量", "0", "kg CO2")
        self.m2 = MetricTile("隐含碳排总计", "0", "kg CO2")
        self.m3 = MetricTile("生态净收益", "0", "kg")
        header_h.addWidget(self.m1); header_h.addWidget(self.m2); header_h.addWidget(self.m3)
        self.main_layout.addLayout(header_h)

        # 2. 中部核心分析区
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：资产明细编辑器
        self.asset_card = QFrame()
        self.asset_card.setObjectName("MetricTile")
        asset_v = QVBoxLayout(self.asset_card)
        asset_v.addWidget(QLabel("方案生态资产明细", styleSheet="font-weight: bold; color: #2D3A30;"))
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["资源名称", "分类", "规模/用量", "碳影响 (kg)"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        asset_v.addWidget(self.tree)
        
        op_h = QHBoxLayout()
        self.btn_add = QPushButton("+ 注入新资产")
        self.btn_add.setObjectName("PrimaryAction")
        self.btn_add.clicked.connect(self.on_add_asset)
        self.btn_del = QPushButton("移除选中")
        self.btn_del.clicked.connect(self.on_delete_asset)
        op_h.addWidget(self.btn_add); op_h.addWidget(self.btn_del)
        asset_v.addLayout(op_h)
        
        # 右侧：可视化诊断区
        self.diag_card = QFrame()
        self.diag_card.setObjectName("MetricTile")
        diag_v = QVBoxLayout(self.diag_card)
        diag_v.addWidget(QLabel("方案生态诊断看板", styleSheet="font-weight: bold; color: #2D3A30;"))
        
        self.chart = EcoDonutChart()
        diag_v.addWidget(self.chart, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 评分指示
        self.rating_box = QGroupBox("方案可持续性评分")
        rb_v = QVBoxLayout(self.rating_box)
        self.rating_lbl = QLabel("等 待 诊 断")
        self.rating_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rating_lbl.setStyleSheet("font-size: 18px; font-weight: 900; color: #94A3B8;")
        rb_v.addWidget(self.rating_lbl)
        diag_v.addWidget(self.rating_box)
        
        # 智能建议日志
        self.eco_log = QTextEdit()
        self.eco_log.setReadOnly(True)
        self.eco_log.setStyleSheet("background: #F9FAFB; border: none; font-size: 11px; color: #4B5563;")
        diag_v.addWidget(self.eco_log)

        self.content_splitter.addWidget(self.asset_card)
        self.content_splitter.addWidget(self.diag_card)
        self.content_splitter.setStretchFactor(0, 3)
        self.content_splitter.setStretchFactor(1, 2)
        self.main_layout.addWidget(self.content_splitter)

    # ---------------- 核心业务逻辑 ----------------

    def refresh_engine(self):
        """数据一致性处理：全局重算并同步 UI"""
        self.tree.clear()
        total_seq = 0.0
        total_cost = 0.0
        
        groups = {
            "植被汇": QTreeWidgetItem(self.tree, ["生态植被汇总"]),
            "工程源": QTreeWidgetItem(self.tree, ["工程材料汇总"])
        }
        
        for aid, a in self.assets.items():
            impact = 0
            if a['type'] == 'VEG':
                impact = self.engine.calculate_annual_sequestration(a['val'], a['cat'])
                total_seq += impact
                parent = groups["植被汇"]
            else:
                impact = self.engine.calculate_material_carbon(a['val'], a['cat'])
                total_cost += impact
                parent = groups["工程源"]
            
            item = QTreeWidgetItem(parent, [a['name'], a['cat'], f"{a['val']} unit", f"{impact:+.1f}"])
            item.setData(0, Qt.ItemDataRole.UserRole, aid)
            if impact > 0 and a['type'] == 'MAT': item.setForeground(3, QBrush(QColor("#EF4444")))
            if a['type'] == 'VEG': item.setForeground(3, QBrush(QColor("#10B981")))

        self.tree.expandAll()
        
        # 更新看板
        net = total_seq - total_cost
        self.m1.v.setText(f"{total_seq:,.1f}")
        self.m2.v.setText(f"{total_cost:,.1f}")
        self.m3.v.setText(f"{net:,.1f}")
        self.m3.v.setStyleSheet(f"color: {'#10B981' if net > 0 else '#EF4444'}")
        
        # 核心修复：看板色系联动
        self.m1.v.setText(f"{total_seq:,.1f}")
        self.m1.v.setStyleSheet("color: #10B981;") # 固碳量设为绿色
        
        self.m2.v.setText(f"{total_cost:,.1f}")
        self.m2.v.setStyleSheet("color: #F43F5E;") # 排放量设为红色
        
        net = total_seq - total_cost
        self.m3.v.setText(f"{net:,.1f}")
        # 根据净值正负流转颜色状态
        self.m3.v.setStyleSheet(f"color: {'#10B981' if net > 0 else '#EF4444'};")
        
        # 更新图表 (传入固碳、排放、以及一个模拟的资源消耗值)
        self.chart.update_data(total_seq, total_cost, 80.0) 
        # 更新图表
        self.chart.update_data(total_seq, total_cost, 500) # 假定水耗500
        
        # 更新等级评分
        rating, color = SustainabilityAudit.get_rating(net)
        self.rating_lbl.setText(rating)
        self.rating_lbl.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {color.name()};")
        
        # 智能诊断日志
        self.eco_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 诊断：碳汇抵消率为 {abs(total_seq/total_cost*100 if total_cost > 0 else 0):.1f}%")

    def on_add_asset(self):
        """交互：增加新生态资产"""
        uid = str(uuid.uuid4())[:8]
        # 简单模拟弹窗输入逻辑
        new_asset = {"name": f"资产-{uid}", "cat": "阔叶乔木", "val": 150.0, "type": "VEG"}
        self.assets[uid] = new_asset
        self.refresh_engine()

    def on_delete_asset(self):
        """交互：删除选中资产"""
        items = self.tree.selectedItems()
        for item in items:
            aid = item.data(0, Qt.ItemDataRole.UserRole)
            if aid in self.assets:
                del self.assets[aid]
        self.refresh_engine()

    def _seed_data(self):
        """注入种子数据，展现初始逻辑状态"""
        seeds = [
            ("中央香樟林", "阔叶乔木", 450, "VEG"),
            ("生态草坪区", "生态草坪", 1200, "VEG"),
            ("主广场铺装", "花岗岩", 800, "MAT"),
            ("亲水平台", "再生木材", 120, "MAT")
        ]
        for n, c, v, t in seeds:
            uid = str(uuid.uuid4())[:8]
            self.assets[uid] = {"name": n, "cat": c, "val": float(v), "type": t}
        self.refresh_engine()

def get_widget():
    w = EcoBalanceModule()
    w._module_identifier = "eco_balance"
    return w