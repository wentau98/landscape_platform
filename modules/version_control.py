import sys
import uuid
import json
import random
import math
import copy
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QSlider, QGroupBox, QTextEdit, 
                             QProgressBar, QSplitter, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QListWidget, QListWidgetItem, QScrollArea,
                             QInputDialog, QMessageBox, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QSize, QDateTime
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPolygonF

# =================================================================
# 1. 业务逻辑层：快照模型与比对引擎
# =================================================================

class LandscapeSnapshot:
    """方案快照实体：记录园林设计的全维度状态"""
    def __init__(self, commit_msg: str, author: str, data_blob: Dict[str, Any]):
        self.version_id = f"REV-{str(uuid.uuid4())[:6].upper()}"
        self.timestamp = datetime.now()
        self.commit_msg = commit_msg
        self.author = author
        # 核心数据：包含地形参数、植物布局、材料清单等
        self.data_blob = copy.deepcopy(data_blob)
        self.parent_id: Optional[str] = None
        self.tags: List[str] = []

class VersionDiffEngine:
    """
    语义化差异分析引擎：
    计算两个版本之间的物理资产变动与概算偏移
    """
    @staticmethod
    def compare(old_blob: Dict, new_blob: Dict) -> Dict[str, List[str]]:
        changes = {"added": [], "removed": [], "modified": [], "stats": []}
        
        # 1. 对比资产数量与类型
        old_assets = old_blob.get("assets", {})
        new_assets = new_blob.get("assets", {})
        
        all_keys = set(old_assets.keys()) | set(new_assets.keys())
        for key in all_keys:
            if key not in old_assets:
                changes["added"].append(f"新增资产单元: {new_assets[key]['name']}")
            elif key not in new_assets:
                changes["removed"].append(f"销毁资产单元: {old_assets[key]['name']}")
            elif old_assets[key] != new_assets[key]:
                # 识别具体属性变更
                diff_fields = []
                for attr in old_assets[key]:
                    if old_assets[key].get(attr) != new_assets[key].get(attr):
                        diff_fields.append(attr)
                changes["modified"].append(f"重构 [{new_assets[key]['name']}] 的 {', '.join(diff_fields)} 属性")

        # 2. 概算偏移逻辑
        old_cost = old_blob.get("total_budget", 0)
        new_cost = new_blob.get("total_budget", 0)
        if old_cost != new_cost:
            delta = new_cost - old_cost
            changes["stats"].append(f"概算变动: ¥{delta:+,.2f}")
            
        return changes

# =================================================================
# 2. UI 表现层：交互式时间轴画布
# =================================================================

class VersionTimelineCanvas(QFrame):
    """
    自定义渲染引擎：
    绘制非线性版本拓扑图，支持节点点击与历史回溯
    """
    node_selected = pyqtSignal(str) # 发射 version_id

    def __init__(self):
        super().__init__()
        self.versions: List[LandscapeSnapshot] = []
        self.setMinimumHeight(200)
        self.active_id = ""
        self.setStyleSheet("background: white; border: 1px solid #E2E8F0; border-radius: 12px;")

    def paintEvent(self, event):
        if not self.versions: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        margin_x, spacing_x = 60, 120
        y_center = self.height() // 2
        
        # 绘制演进主线
        painter.setPen(QPen(QColor("#E2E8F0"), 3, Qt.PenStyle.DashLine))
        painter.drawLine(margin_x, y_center, margin_x + (len(self.versions)-1)*spacing_x, y_center)
        
        # 绘制版本节点
        for i, v in enumerate(self.versions):
            x = margin_x + i * spacing_x
            is_active = v.version_id == self.active_id
            
            # 绘制节点圆影
            painter.setBrush(QBrush(QColor("#6366F1" if is_active else "#94A3B8")))
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawEllipse(QPointF(x, y_center), 12, 12)
            
            # 绘制版本标签
            painter.setPen(QPen(QColor("#1E293B")))
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.drawText(int(x - 30), y_center + 30, v.version_id)
            
            # 时间戳
            painter.setPen(QPen(QColor("#94A3B8")))
            painter.setFont(QFont("Segoe UI", 7))
            painter.drawText(int(x - 35), y_center - 20, v.timestamp.strftime("%H:%M:%S"))

    def mousePressEvent(self, event):
        # 简易点击检测
        margin_x, spacing_x = 60, 120
        y_center = self.height() // 2
        for i, v in enumerate(self.versions):
            x = margin_x + i * spacing_x
            if math.sqrt((event.position().x() - x)**2 + (event.position().y() - y_center)**2) < 15:
                self.active_id = v.version_id
                self.node_selected.emit(v.version_id)
                self.update()
                break

# =================================================================
# 3. 主模块：方案版本数据回溯中心
# =================================================================

class VersionControlModule(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("VersionModule")
        
        # 1. 核心状态初始化
        self.history: List[LandscapeSnapshot] = []
        self.current_state = self._get_initial_blob()
        self.diff_engine = VersionDiffEngine()
        
        self.init_ui()
        self.setStyleSheet(self._get_style())
        
        # 2. 注入初始快照
        self.commit_changes("系统初始化快照")

    def _get_initial_blob(self) -> Dict:
        """模拟当前设计平台的完整内存状态数据结构"""
        return {
            "project_name": "滨水绿地公园-A区",
            "total_budget": 1250000.0,
            "assets": {
                "UID-01": {"name": "中心香樟", "h": 12.0, "type": "植被"},
                "UID-02": {"name": "景观连廊", "h": 4.5, "type": "建筑"}
            },
            "terrain_res": 25
        }

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(20)

        # --- 顶部：版本演进时间轴 ---
        self.timeline_grp = QGroupBox("方案演进拓扑时间轴")
        tl_layout = QVBoxLayout(self.timeline_grp)
        self.canvas = VersionTimelineCanvas()
        self.canvas.node_selected.connect(self.on_version_selected)
        tl_layout.addWidget(self.canvas)
        self.main_layout.addWidget(self.timeline_grp)

        # --- 中部：比对工作台 ---
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：差异分析报告
        self.diff_card = QFrame()
        self.diff_card.setObjectName("ModernCard")
        diff_v = QVBoxLayout(self.diff_card)
        diff_v.addWidget(QLabel("语义化差异分析分析报告", styleSheet="font-weight: bold; color: #475569;"))
        
        self.diff_table = QTableWidget(0, 2)
        self.diff_table.setHorizontalHeaderLabels(["变更维度", "变动明细说明"])
        self.diff_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.diff_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        diff_v.addWidget(self.diff_table)
        
        # 右侧：审计跟踪与元数据
        self.meta_card = QFrame()
        self.meta_card.setObjectName("ModernCard")
        meta_v = QVBoxLayout(self.meta_card)
        meta_v.addWidget(QLabel("版本元数据审计追踪", styleSheet="font-weight: bold; color: #475569;"))
        
        self.meta_log = QTextEdit()
        self.meta_log.setReadOnly(True)
        self.meta_log.setStyleSheet("background: #F8FAFC; border: none; font-family: Consolas; font-size: 11px;")
        meta_v.addWidget(self.meta_log)

        self.content_splitter.addWidget(self.diff_card)
        self.content_splitter.addWidget(self.meta_card)
        self.main_layout.addWidget(self.content_splitter)

        # --- 底部：动作控制栏 ---
        self.footer = QHBoxLayout()
        self.status_lbl = QLabel("当前分支: MASTER | 状态: 数据已同步")
        self.status_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        
        self.btn_commit = QPushButton("提交当前更改")
        self.btn_commit.setObjectName("PrimaryAction")
        self.btn_commit.clicked.connect(self.on_commit_clicked)
        
        self.btn_rollback = QPushButton("执行数据回溯")
        self.btn_rollback.setObjectName("DangerAction")
        self.btn_rollback.setEnabled(False)
        self.btn_rollback.clicked.connect(self.on_rollback_clicked)

        self.footer.addWidget(self.status_lbl)
        self.footer.addStretch()
        self.footer.addWidget(self.btn_commit)
        self.footer.addWidget(self.btn_rollback)
        self.main_layout.addLayout(self.footer)

    # ---------------- 核心业务算法实现 ----------------

    def commit_changes(self, msg: str):
        """核心动作：捕获当前系统状态并入库"""
        new_snap = LandscapeSnapshot(msg, "高级设计师-Admin", self.current_state)
        if self.history:
            new_snap.parent_id = self.history[-1].version_id
            
        self.history.append(new_snap)
        self.canvas.versions = self.history
        self.canvas.active_id = new_snap.version_id
        self.canvas.update()
        
        self.meta_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 新版本已提交: {new_snap.version_id}")
        self.refresh_diff_view(new_snap)

    def on_version_selected(self, vid: str):
        """交互：查看选中版本与最新版本的差异"""
        target = next((v for v in self.history if v.version_id == vid), None)
        if not target: return
        
        self.refresh_diff_view(target)
        # 只有选中的不是当前最新版，才允许回溯
        self.btn_rollback.setEnabled(vid != self.history[-1].version_id)
        self.meta_log.append(f">> 正在透视快照: {vid} | 作者: {target.author}")

    def refresh_diff_view(self, target_snap: LandscapeSnapshot):
        """执行语义比对算法并刷新 UI"""
        self.diff_table.setRowCount(0)
        # 比对当前工作区与选中快照
        diff = self.diff_engine.compare(target_snap.data_blob, self.history[-1].data_blob)
        
        for cat, items in diff.items():
            if cat == "stats": continue
            for info in items:
                row = self.diff_table.rowCount()
                self.diff_table.insertRow(row)
                self.diff_table.setItem(row, 0, QTableWidgetItem(cat.upper()))
                self.diff_table.setItem(row, 1, QTableWidgetItem(info))
        
        # 资源统计变动高亮
        for stat in diff["stats"]:
            row = self.diff_table.rowCount()
            self.diff_table.insertRow(row)
            item_s = QTableWidgetItem("财务概算偏差")
            item_v = QTableWidgetItem(stat)
            item_v.setForeground(QBrush(QColor("#EF4444")))
            self.diff_table.setItem(row, 0, item_s)
            self.diff_table.setItem(row, 1, item_v)

    def on_commit_clicked(self):
        msg, ok = QInputDialog.getText(self, "快照提交", "请输入本次设计变更的语义描述:")
        if ok and msg:
            # 模拟随机改动数据，体现“智能”
            self.current_state["total_budget"] += random.randint(-5000, 15000)
            if random.random() > 0.5:
                uid = f"UID-{random.randint(10,99)}"
                self.current_state["assets"][uid] = {"name": "新增绿化组团", "h": 2.5, "type": "植被"}
            
            self.commit_changes(msg)

    def on_rollback_clicked(self):
        """核心动作：版本回溯与数据一致性还原"""
        vid = self.canvas.active_id
        confirm = QMessageBox.question(self, "数据回溯确认", 
                                     f"确定要将当前方案全量还原至版本 [{vid}] 吗？\n当前未提交的改动将丢失。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            target = next((v for v in self.history if v.version_id == vid), None)
            # 执行数据还原一致性协议
            self.current_state = copy.deepcopy(target.data_blob)
            self.meta_log.append(f"<font color='#EF4444'>CRITICAL: 系统已执行回溯，数据同步至 {vid}</font>")
            
            # 回溯后通常会产生一个新的“恢复”版本
            self.commit_changes(f"恢复至版本 {vid}")
            self.btn_rollback.setEnabled(False)

    def _get_style(self):
        return """
            QWidget#VersionModule { background-color: #F8FAFC; }
            QFrame#ModernCard { background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; }
            QPushButton#PrimaryAction { background: #6366F1; color: white; border-radius: 6px; padding: 10px 20px; font-weight: bold; }
            QPushButton#DangerAction { background: #FFF1F2; color: #E11D48; border: 1px solid #FDA4AF; border-radius: 6px; padding: 10px 20px; font-weight: bold; }
            QPushButton#DangerAction:disabled { background: #F1F5F9; color: #94A3B8; border: none; }
        """

def get_widget():
    w = VersionControlModule()
    w._module_identifier = "version_control"
    return w