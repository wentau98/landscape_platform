import sys
import time
import math
import random
import uuid
from typing import List, Dict, Optional, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QFrame, QSlider, QGroupBox, QTextEdit, 
                             QProgressBar, QComboBox, QCheckBox, QLCDNumber)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QSize, QTimer, QThread, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPolygonF

# =================================================================
# 核心逻辑层：水动力学节点与物理引擎
# =================================================================

class HydroCell:
    """水力单元格：封装水位、流速、压强及渗透率"""
    def __init__(self, x: int, y: int, elevation: float):
        self.x, self.y = x, y
        self.elevation = elevation  # 地面标高
        self.water_depth = 0.0      # 当前积水深度
        self.velocity = [0.0, 0.0]  # 流速矢量 (vx, vy)
        self.is_obstacle = False    # 是否为堰坝/阻碍
        self.is_drain = False       # 是否为排水口
        self.saturation = 0.1       # 土壤饱和度 (影响渗透)

class HydroEngine:
    """
    非稳态水动力模拟引擎：
    采用基于坡度梯度的离散流向算法 (D8 Flow Model 变体)
    """
    def __init__(self, rows: int, cols: int):
        self.rows, self.cols = rows, cols
        self.grid = [[HydroCell(i, j, 10.0 - (i+j)*0.1) for j in range(cols)] for i in range(rows)]
        self.rain_rate = 0.0  # mm/h
        self.evaporation = 0.005
        self.simulation_step = 0
        
        # 业务规则：排涝等级定义
        self.drainage_rules = {
            "低强度(2年一遇)": 15.0,
            "中强度(10年一遇)": 45.0,
            "高强度(50年一遇)": 120.0
        }

    def reset_water(self):
        for row in self.grid:
            for cell in row:
                cell.water_depth = 0.0
                cell.velocity = [0.0, 0.0]

    def apply_rain(self, rate: float):
        """核心逻辑：模拟降雨过程中的水力入流"""
        increment = rate / 3600.0 # 转换为秒增量
        for row in self.grid:
            for cell in row:
                if not cell.is_obstacle:
                    cell.water_depth += increment

    def compute_flow(self):
        """
        核心算法：基于动能定理的浅水方程简化模拟
        计算单元格间的水位平衡与动量转移
        """
        new_depths = [[self.grid[i][j].water_depth for j in range(self.cols)] for i in range(self.rows)]
        
        for i in range(self.rows):
            for j in range(self.cols):
                curr = self.grid[i][j]
                if curr.water_depth < 0.001 or curr.is_obstacle: continue
                
                # 检查8邻域，寻找势能差
                neighbors = []
                for di, dj in [(-1,0), (1,0), (0,-1), (0,1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < self.rows and 0 <= nj < self.cols:
                        target = self.grid[ni][nj]
                        if target.is_obstacle: continue
                        
                        # 总水头 H = Elevation + WaterDepth
                        head_diff = (curr.elevation + curr.water_depth) - (target.elevation + target.water_depth)
                        if head_diff > 0:
                            neighbors.append((ni, nj, head_diff))
                
                if not neighbors: continue
                
                # 流量分配算法：按势能梯度比例分配
                total_diff = sum(n[2] for n in neighbors)
                flow_out = curr.water_depth * 0.2 # 假设每步流出20%
                
                for ni, nj, h in neighbors:
                    ratio = h / total_diff
                    transfer = flow_out * ratio
                    new_depths[i][j] -= transfer
                    new_depths[ni][nj] += transfer
                    
                    # 更新流速矢量用于可视化
                    self.grid[i][j].velocity[0] += (ni - i) * ratio
                    self.grid[i][j].velocity[1] += (nj - j) * ratio

        # 应用排水口逻辑 (数据一致性)
        for i in range(self.rows):
            for j in range(self.cols):
                cell = self.grid[i][j]
                cell.water_depth = max(0, new_depths[i][j] - (0.05 if cell.is_drain else 0))
                # 蒸发与渗透一致性处理
                cell.water_depth = max(0, cell.water_depth - self.evaporation)

# =================================================================
# UI 表现层：水系动态可视化画布
# =================================================================

class HydroCanvas(QFrame):
    """
    交互式流体画布：
    实现水位热力图、流向箭头矢量及交互式堰坝绘制
    """
    cell_clicked = pyqtSignal(int, int)

    def __init__(self, engine: HydroEngine):
        super().__init__()
        self.engine = engine
        self.setMinimumSize(600, 600)
        self.setMouseTracking(True)
        self.draw_vectors = True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        dx = self.width() / self.engine.cols
        dy = self.height() / self.engine.rows

        for i in range(self.engine.rows):
            for j in range(self.engine.cols):
                cell = self.engine.grid[i][j]
                rect = QRectF(i*dx, j*dy, dx, dy)
                
                # 1. 绘制底色（地形高度）
                green_val = int(255 - cell.elevation * 15)
                painter.fillRect(rect, QColor(green_val, green_val - 20, 150))
                
                # 2. 绘制水层 (透明度随深度变化)
                if cell.water_depth > 0.01:
                    alpha = min(255, int(cell.water_depth * 100))
                    water_color = QColor(0, 100, 255, alpha)
                    painter.fillRect(rect, water_color)
                
                # 3. 绘制特殊设施
                if cell.is_obstacle:
                    painter.fillRect(rect, QColor(60, 60, 60)) # 堰坝
                if cell.is_drain:
                    painter.setPen(QPen(Qt.GlobalColor.white, 2))
                    painter.drawRect(rect.adjusted(2,2,-2,-2)) # 排水口

                # 4. 动态流向矢量渲染
                if self.draw_vectors and abs(cell.velocity[0]) + abs(cell.velocity[1]) > 0.1:
                    self._draw_arrow(painter, rect.center(), cell.velocity)

    def _draw_arrow(self, painter, center, velocity):
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1))
        angle = math.atan2(velocity[1], velocity[0])
        mag = min(15, math.sqrt(velocity[0]**2 + velocity[1]**2) * 5)
        
        painter.save()
        painter.translate(center)
        painter.rotate(math.degrees(angle))
        painter.drawLine(0, 0, int(mag), 0)
        painter.restore()

    def mousePressEvent(self, event):
        ix = int(event.position().x() / (self.width() / self.engine.cols))
        iy = int(event.position().y() / (self.height() / self.engine.rows))
        if 0 <= ix < self.engine.rows and 0 <= iy < self.engine.cols:
            self.cell_clicked.emit(ix, iy)

# =================================================================
# 模块容器：水系动力模拟主界面
# =================================================================

class HydrologyModule(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = HydroEngine(30, 30)
        self.is_simulating = False
        self.init_ui()
        
        # 模拟主定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_step)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # ---------------- 左侧：调度与规则中心 ----------------
        self.ctrl_panel = QWidget()
        self.ctrl_panel.setFixedWidth(420)
        vbox = QVBoxLayout(self.ctrl_panel)

        # 1. 实时水文监测仪
        monitor_grp = QGroupBox("实时监控：水文动力参数")
        mon_layout = QVBoxLayout(monitor_grp)
        
        h_box = QHBoxLayout()
        self.lcd_depth = QLCDNumber()
        self.lcd_depth.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        h_box.addWidget(QLabel("全场平均水位(m):"))
        h_box.addWidget(self.lcd_depth)
        mon_layout.addLayout(h_box)
        
        self.risk_bar = QProgressBar()
        self.risk_bar.setFormat("内涝风险等级: %p%")
        mon_layout.addWidget(self.risk_bar)
        vbox.addWidget(monitor_grp)

        # 2. 模拟工况设置 (状态流转逻辑)
        scenario_grp = QGroupBox("降雨工况与资源调度")
        sce_layout = QVBoxLayout(scenario_grp)
        
        sce_layout.addWidget(QLabel("当前模拟降雨强度:"))
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(list(self.engine.drainage_rules.keys()))
        sce_layout.addWidget(self.scenario_combo)
        
        self.rain_slider = QSlider(Qt.Orientation.Horizontal)
        self.rain_slider.setRange(0, 200)
        self.rain_slider.valueChanged.connect(self.on_rain_changed)
        sce_layout.addWidget(self.rain_slider)
        
        self.btn_toggle = QPushButton("启动非稳态演进模拟")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setStyleSheet("height: 45px; font-weight: bold; background-color: #2980B9; color: white;")
        self.btn_toggle.clicked.connect(self.toggle_sim)
        sce_layout.addWidget(self.btn_toggle)
        
        self.btn_reset = QPushButton("重置水利状态")
        self.btn_reset.clicked.connect(self.reset_system)
        sce_layout.addWidget(self.btn_reset)
        vbox.addWidget(scenario_grp)

        # 3. 交互式编辑器 (CRUD：添加堰坝/排水口)
        edit_grp = QGroupBox("水利设施拓扑编辑器")
        edit_layout = QVBoxLayout(edit_grp)
        self.radio_obstacle = QCheckBox("绘制堰坝/驳岸 (阻碍物)")
        self.radio_drain = QCheckBox("布置智能出水口 (海绵点)")
        edit_layout.addWidget(self.radio_obstacle)
        edit_layout.addWidget(self.radio_drain)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background: #FDFEFE; font-size: 10px; color: #34495E;")
        edit_layout.addWidget(QLabel("事件审计日志:"))
        edit_layout.addWidget(self.log_output)
        vbox.addWidget(edit_grp)

        # ---------------- 右侧：可视化模拟 ----------------
        self.canvas = HydroCanvas(self.engine)
        self.canvas.cell_clicked.connect(self.handle_canvas_click)
        
        layout.addWidget(self.ctrl_panel)
        layout.addWidget(self.canvas)

    def on_rain_changed(self, val):
        self.engine.rain_rate = val
        self.log_output.append(f">> 调整降雨荷载: {val} mm/h")

    def toggle_sim(self):
        if self.btn_toggle.isChecked():
            self.timer.start(50)
            self.btn_toggle.setText("停止模拟")
            self.btn_toggle.setStyleSheet("height: 45px; background-color: #C0392B; color: white;")
        else:
            self.timer.stop()
            self.btn_toggle.setText("启动非稳态演进模拟")
            self.btn_toggle.setStyleSheet("height: 45px; background-color: #2980B9; color: white;")

    def reset_system(self):
        self.engine.reset_water()
        self.canvas.update()
        self.log_output.append(">> 系统状态已重置：水利平衡归零。")

    def handle_canvas_click(self, x, y):
        """交互逻辑：在画布上进行资源部署"""
        cell = self.engine.grid[x][y]
        if self.radio_obstacle.isChecked():
            cell.is_obstacle = not cell.is_obstacle
            self.log_output.append(f"审计：节点({x},{y}) 地表属性变更为 [驳岸]")
        elif self.radio_drain.isChecked():
            cell.is_drain = not cell.is_drain
            self.log_output.append(f"审计：节点({x},{y}) 已部署 [智能排水口]")
        self.canvas.update()

    def run_step(self):
        """核心业务循环：计算 -> 校验规则 -> 更新状态 -> 渲染"""
        self.engine.apply_rain(self.engine.rain_rate)
        self.engine.compute_flow()
        self.canvas.update()
        
        # 规则引擎校验
        total_depth = 0.0
        max_d = 0.0
        for row in self.engine.grid:
            for cell in row:
                total_depth += cell.water_depth
                max_d = max(max_d, cell.water_depth)
        
        avg_depth = total_depth / (self.engine.rows * self.engine.cols)
        self.lcd_depth.display(f"{avg_depth:.3f}")
        
        # 风险评估状态流转
        risk_val = int(min(100, avg_depth * 500))
        self.risk_bar.setValue(risk_val)
        
        if max_d > 0.8:
            self.log_output.append("<font color='red'>警告：局部区域水位超标，触发洪峰预警！</font>")
            # 自动资源调度：如果水位过高且有排水口，增加排水口效率
            self.engine.evaporation = 0.02 # 模拟泵站全力开启

def get_widget():
    return HydrologyModule()