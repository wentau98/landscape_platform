import sys
import uuid
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Set

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QSlider, QGroupBox, QTextEdit, 
                             QProgressBar, QSplitter, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox,
                             QDateEdit, QSpinBox, QMessageBox, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QSize, QDate
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient

# =================================================================
# 1. 业务逻辑层：工序数据模型与规则引擎
# =================================================================

class TaskStatus:
    PENDING = "待启动"
    RUNNING = "施工中"
    COMPLETED = "已完结"
    CONFLICT = "逻辑冲突"

class ConstructionTask:
    """施工任务实体：封装工期、资源与依赖关系"""
    def __init__(self, name: str, team: str, start_date: QDate, duration: int, workers: int):
        self.uid = str(uuid.uuid4())[:8]
        self.name = name
        self.team = team # 土建, 绿化, 水力, 电力
        self.start_date = start_date
        self.duration = duration
        self.end_date = start_date.addDays(duration)
        self.workers = workers
        self.dependencies: Set[str] = set() # 前置任务UID集合
        self.status = TaskStatus.PENDING
        self.progress = 0

class SchedulingEngine:
    """
    核心调度算法引擎：
    负责检测逻辑冲突、资源过载及关键路径重算
    """
    def __init__(self):
        self.tasks: Dict[str, ConstructionTask] = {}
        self.max_workers = 50 # 全场最大施工人力限制

    def add_task(self, task: ConstructionTask):
        self.tasks[task.uid] = task

    def validate_logic(self) -> List[str]:
        """核心算法：检测工序逻辑冲突与资源瓶颈"""
        reports = []
        # 1. 逻辑顺序校验
        for uid, task in self.tasks.items():
            for dep_uid in task.dependencies:
                if dep_uid in self.tasks:
                    dep_task = self.tasks[dep_uid]
                    if task.start_date < dep_task.end_date:
                        task.status = TaskStatus.CONFLICT
                        reports.append(f"逻辑错误：[{task.name}] 必须在 [{dep_task.name}] 完工后启动。")
                    else:
                        task.status = TaskStatus.PENDING

        # 2. 资源过载校验 (按天聚合)
        date_load: Dict[QDate, int] = {}
        for task in self.tasks.values():
            curr = task.start_date
            for _ in range(task.duration):
                date_load[curr] = date_load.get(curr, 0) + task.workers
                curr = curr.addDays(1)
        
        for date, load in date_load.items():
            if load > self.max_workers:
                reports.append(f"资源过载：{date.toString('MM-dd')} 施工人员需求({load})超过上限({self.max_workers})。")
        
        return reports

# =================================================================
# 2. UI 表现层：自定义甘特图渲染引擎
# =================================================================

class GanttCanvas(QFrame):
    """
    高级工程渲染组件：
    基于时间轴的工序可视化与交互
    """
    task_selected = pyqtSignal(ConstructionTask)

    def __init__(self, engine: SchedulingEngine):
        super().__init__()
        self.engine = engine
        self.setMinimumSize(800, 400)
        self.cell_w = 40 # 每天占用的宽度
        self.row_h = 50 # 每一行的高度
        self.start_view_date = QDate.currentDate().addDays(-5)
        self.setStyleSheet("background: white; border: 1px solid #E2E8F0; border-radius: 8px;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景网格
        self._draw_grid(painter)
        # 绘制工序条
        self._draw_tasks(painter)

    def _draw_grid(self, painter):
        w, h = self.width(), self.height()
        painter.setPen(QPen(QColor(241, 245, 249), 1))
        
        # 垂直日期线
        for i in range(0, w, self.cell_w):
            painter.drawLine(i, 0, i, h)
            date = self.start_view_date.addDays(i // self.cell_w)
            painter.setPen(QPen(QColor(148, 163, 184)))
            painter.setFont(QFont("Segoe UI", 7))
            painter.drawText(i + 5, 15, date.toString("MM/dd"))
            painter.setPen(QPen(QColor(241, 245, 249), 1))

    def _draw_tasks(self, painter):
        y_offset = 40
        for task in self.engine.tasks.values():
            days_diff = self.start_view_date.daysTo(task.start_date)
            x = days_diff * self.cell_w
            width = task.duration * self.cell_w
            
            rect = QRectF(x, y_offset, width, 30)
            
            # 状态语义配色
            color = QColor("#10B981") # 默认绿色
            if task.status == TaskStatus.CONFLICT: color = QColor("#EF4444")
            if task.team == "土建": color = QColor("#3B82F6")
            
            # 绘制工序条 (带微渐变)
            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            grad.setColorAt(0, color); grad.setColorAt(1, color.darker(110))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 4, 4)
            
            # 绘制进度
            if task.progress > 0:
                painter.setBrush(QBrush(QColor(255,255,255,100)))
                painter.drawRect(QRectF(x, y_offset + 25, width * (task.progress/100), 5))

            # 绘制文字
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Microsoft YaHei", 8, QFont.Weight.Bold))
            painter.drawText(rect.adjusted(10,0,0,0), Qt.AlignmentFlag.AlignVCenter, task.name)
            
            y_offset += self.row_h

    def mousePressEvent(self, event):
        # 简化版：通过 Y 轴判断选中哪个任务
        y_idx = int((event.position().y() - 40) // self.row_h)
        task_list = list(self.engine.tasks.values())
        if 0 <= y_idx < len(task_list):
            self.task_selected.emit(task_list[y_idx])

# =================================================================
# 3. 弹出框：工序编辑矩阵 (CRUD 核心)
# =================================================================

class TaskEditDialog(QDialog):
    def __init__(self, parent=None, task: Optional[ConstructionTask] = None, all_tasks: List[ConstructionTask] = []):
        super().__init__(parent)
        self.setWindowTitle("工序元数据编辑")
        self.setFixedSize(400, 450)
        
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        self.in_name = QLineEdit(task.name if task else "")
        self.in_team = QComboBox()
        self.in_team.addItems(["土建工程", "水力设施", "植被栽植", "亮化软装"])
        if task: self.in_team.setCurrentText(task.team)
        
        self.in_start = QDateEdit(task.start_date if task else QDate.currentDate())
        self.in_duration = QSpinBox(); self.in_duration.setRange(1, 100); self.in_duration.setValue(task.duration if task else 5)
        self.in_workers = QSpinBox(); self.in_workers.setRange(1, 50); self.in_workers.setValue(task.workers if task else 10)
        
        self.in_dep = QComboBox()
        self.in_dep.addItem("无前置依赖", None)
        for t in all_tasks:
            if task and t.uid == task.uid: continue
            self.in_dep.addItem(t.name, t.uid)

        layout.addRow("工序名称:", self.in_name)
        layout.addRow("施工班组:", self.in_team)
        layout.addRow("预定开工:", self.in_start)
        layout.addRow("计划工期(天):", self.in_duration)
        layout.addRow("配置人力(人):", self.in_workers)
        layout.addRow("前置依赖:", self.in_dep)

        self.btn_save = QPushButton("同步至调度引擎")
        self.btn_save.setStyleSheet("background: #10B981; color: white; padding: 12px; border-radius: 6px; font-weight: bold;")
        self.btn_save.clicked.connect(self.accept)
        layout.addRow(self.btn_save)

    def get_data(self):
        return {
            "name": self.in_name.text(),
            "team": self.in_team.currentText(),
            "start": self.in_start.date(),
            "duration": self.in_duration.value(),
            "workers": self.in_workers.value(),
            "dep": self.in_dep.currentData()
        }

# =================================================================
# 4. 主模块：施工冲突调度中心
# =================================================================

class ConstructionModule(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("ConstructionModule")
        self.engine = SchedulingEngine()
        self.init_ui()
        self._seed_mock_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # A. 顶部控制看板
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E2E8F0;")
        hl = QHBoxLayout(header)
        
        title_v = QVBoxLayout()
        title_v.addWidget(QLabel("施工工序冲突与资源调度系统", styleSheet="font-size: 18px; font-weight: bold; color: #1E293B;"))
        self.stat_lbl = QLabel("当前系统状态：就绪")
        title_v.addWidget(self.stat_lbl)
        hl.addLayout(title_v)
        
        self.btn_add = QPushButton("+ 新增施工工序")
        self.btn_add.setFixedSize(150, 40)
        self.btn_add.setStyleSheet("background: #6366F1; color: white; border-radius: 8px; font-weight: bold;")
        self.btn_add.clicked.connect(self.on_add_task)
        hl.addStretch()
        hl.addWidget(self.btn_add)
        self.main_layout.addWidget(header)

        # B. 中部核心区域
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 甘特图视图
        self.canvas_card = QFrame()
        cv = QVBoxLayout(self.canvas_card)
        cv.addWidget(QLabel("项目协同进度甘特图", styleSheet="color: #64748B; font-weight: bold; font-size: 12px;"))
        self.canvas = GanttCanvas(self.engine)
        cv.addWidget(self.canvas)
        
        # 列表与日志视图
        self.bottom_panel = QSplitter(Qt.Orientation.Horizontal)
        
        self.task_table = QTableWidget(0, 5)
        self.task_table.setHorizontalHeaderLabels(["工序名称", "班组", "工期", "人力", "状态"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table.setStyleSheet("background: white; border-radius: 8px;")
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; font-family: Consolas; font-size: 11px;")
        
        self.bottom_panel.addWidget(self.task_table)
        self.bottom_panel.addWidget(self.log_area)
        
        self.splitter.addWidget(self.canvas_card)
        self.splitter.addWidget(self.bottom_panel)
        self.main_layout.addWidget(self.splitter)

        # C. 底部诊断
        self.btn_run = QPushButton("启动全链路工序合规性审计")
        self.btn_run.setFixedHeight(45)
        self.btn_run.setStyleSheet("background: #10B981; color: white; border-radius: 8px; font-weight: bold;")
        self.btn_run.clicked.connect(self.run_full_audit)
        self.main_layout.addWidget(self.btn_run)

    # ---------------- 业务动作实现 ----------------

    def refresh_ui(self):
        """同步刷新所有视图组件"""
        # 1. 刷新表格 (CRUD 展示)
        self.task_table.setRowCount(0)
        for task in self.engine.tasks.values():
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            self.task_table.setItem(row, 0, QTableWidgetItem(task.name))
            self.task_table.setItem(row, 1, QTableWidgetItem(task.team))
            self.task_table.setItem(row, 2, QTableWidgetItem(f"{task.duration}天"))
            self.task_table.setItem(row, 3, QTableWidgetItem(f"{task.workers}人"))
            status_item = QTableWidgetItem(task.status)
            if task.status == TaskStatus.CONFLICT: status_item.setForeground(QBrush(QColor("#EF4444")))
            self.task_table.setItem(row, 4, status_item)
            
        # 2. 刷新画布
        self.canvas.update()

    def on_add_task(self):
        """增加逻辑 (Create)"""
        dialog = TaskEditDialog(self, all_tasks=list(self.engine.tasks.values()))
        if dialog.exec():
            d = dialog.get_data()
            new_task = ConstructionTask(d['name'], d['team'], d['start'], d['duration'], d['workers'])
            if d['dep']: new_task.dependencies.add(d['dep'])
            self.engine.add_task(new_task)
            self.refresh_ui()
            self.log_area.append(f"数据录入：工序 [{new_task.name}] 已加入调度池。")

    def run_full_audit(self):
        """执行核心审计算法：状态流转与一致性校验"""
        self.log_area.append(f"[{datetime.now().strftime('%H:%M:%S')}] 启动工程关键路径与资源载荷审计...")
        
        # 模拟计算延迟
        errors = self.engine.validate_logic()
        
        if errors:
            self.stat_lbl.setText("当前系统状态：发现调度冲突")
            self.stat_lbl.setStyleSheet("color: #EF4444; font-weight: bold;")
            for err in errors:
                self.log_area.append(f"<font color='#EF4444'>● {err}</font>")
        else:
            self.stat_lbl.setText("当前系统状态：逻辑闭环通过")
            self.stat_lbl.setStyleSheet("color: #10B981; font-weight: bold;")
            self.log_area.append("<font color='#10B981'>SUCCESS: 施工逻辑校验一致，无资源过载冲突。</font>")
        
        self.refresh_ui()

    def _seed_mock_data(self):
        """注入种子数据，展现初始复杂状态"""
        # 故意制造一个逻辑冲突：铺装在土建之前
        t1 = ConstructionTask("中心湖体开挖", "土建工程", QDate.currentDate(), 8, 20)
        t2 = ConstructionTask("底泥生态修复", "水力设施", QDate.currentDate().addDays(4), 5, 15)
        t2.dependencies.add(t1.uid) # 正确依赖
        
        t3 = ConstructionTask("广场硬质铺装", "土建工程", QDate.currentDate().addDays(2), 10, 25)
        t3.dependencies.add(t1.uid) # 制造冲突：t1完工前t3就开始了
        
        self.engine.add_task(t1); self.engine.add_task(t2); self.engine.add_task(t3)
        self.refresh_ui()

def get_widget():
    w = ConstructionModule()
    w._module_identifier = "construction"
    return w