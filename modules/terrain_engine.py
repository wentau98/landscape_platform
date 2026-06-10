import sys
import random
import math
import time
from typing import List, Dict, Optional, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QFrame, QSlider, QGroupBox, QTextEdit, 
                             QProgressBar, QComboBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QSize, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon

# =================================================================
# 核心逻辑层：地形几何与规则引擎
# =================================================================

class TerrainNode:
    """地形空间节点：封装坐标与属性"""
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z
        self.slope = 0.0          # 局部坡度
        self.suitability = 1.0     # 建设适宜性评分 (0.0-1.0)
        self.is_violation = False  # 是否违反设计规范

class TerrainLogicEngine:
    """
    核心业务引擎：负责地形插值、土方计算及规则校验
    包含项目核心算法：反距离加权插值 (IDW) 与 坡度矢量分析
    """
    def __init__(self, grid_res: int = 20):
        self.grid_res = grid_res
        self.nodes: List[List[TerrainNode]] = []
        self.survey_points: List[Tuple[float, float, float]] = []
        
        # 业务规则定义：不同景观功能的坡度限制
        self.rules = {
            "无障碍步道": (0.01, 0.05), # 1% - 5%
            "排水草沟": (0.02, 0.10),   # 2% - 10%
            "建筑基座": (0.0, 0.02),    # 0% - 2%
            "生态护坡": (0.15, 0.50)    # 15% - 50%
        }

    def initialize_grid(self):
        """状态初始化：构建空间网格阵列"""
        self.nodes = []
        for i in range(self.grid_res):
            row = []
            for j in range(self.grid_res):
                row.append(TerrainNode(float(i), float(j), 0.0))
            self.nodes.append(row)

    def add_survey_point(self, x: float, y: float, z: float):
        """数据一致性处理：同步更新测绘点"""
        self.survey_points.append((x, y, z))

    def run_idw_interpolation(self):
        """
        核心算法：反距离加权插值 (Inverse Distance Weighting)
        将离散测绘点数据映射到连续的空间网格中
        """
        if not self.survey_points:
            return

        for i in range(self.grid_res):
            for j in range(self.grid_res):
                target_node = self.nodes[i][j]
                weights_sum = 0.0
                values_sum = 0.0
                
                for px, py, pz in self.survey_points:
                    dist = math.sqrt((i - px)**2 + (j - py)**2)
                    if dist < 0.1: # 极近距离处理
                        target_node.z = pz
                        break
                    weight = 1.0 / (dist ** 2)
                    weights_sum += weight
                    values_sum += pz * weight
                else:
                    target_node.z = values_sum / weights_sum

        self._analyze_slopes()

    def _analyze_slopes(self):
        """内部逻辑：基于中值定理的坡度矢量计算"""
        for i in range(self.grid_res - 1):
            for j in range(self.grid_res - 1):
                # 计算X与Y方向的梯度
                dz_dx = self.nodes[i+1][j].z - self.nodes[i][j].z
                dz_dy = self.nodes[i][j+1].z - self.nodes[i][j].z
                slope = math.sqrt(dz_dx**2 + dz_dy**2)
                self.nodes[i][j].slope = slope
                
                # 默认根据排水规范初步判定
                if slope < 0.02 or slope > 0.3:
                    self.nodes[i][j].is_violation = True
                else:
                    self.nodes[i][j].is_violation = False

    def calculate_earthwork(self, target_z: float) -> Dict[str, float]:
        """
        资源调度算法：计算相对于基准标高的挖填方量
        体现数据一致性与资源核算逻辑
        """
        total_cut = 0.0
        total_fill = 0.0
        cell_area = 1.0 # 假设单位网格面积
        
        for row in self.nodes:
            for node in row:
                diff = node.z - target_z
                if diff > 0:
                    total_cut += diff * cell_area
                else:
                    total_fill += abs(diff) * cell_area
                    
        return {"挖方": total_cut, "填方": total_fill, "净土方": total_cut - total_fill}

# =================================================================
# 界面表现层：自定义可视化控件
# =================================================================

class TerrainCanvas(QFrame):
    """
    交互式绘图引擎：使用 QPainter 实现地形热力与坡度警告预览
    """
    node_selected = pyqtSignal(int, int, float)

    def __init__(self, engine: TerrainLogicEngine):
        super().__init__()
        self.engine = engine
        self.setMinimumSize(500, 500)
        self.setMouseTracking(True)
        self.show_violation = True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        res = self.engine.grid_res
        dx = w / res
        dy = h / res

        # 绘制网格背景与海拔热力
        for i in range(res):
            for j in range(res):
                node = self.engine.nodes[i][j]
                # 海拔越高，绿色越深
                color_val = int(max(0, min(255, node.z * 10)))
                base_color = QColor(100, 150 + int(color_val/3), 100)
                
                if self.show_violation and node.is_violation:
                    base_color = QColor(231, 76, 60, 150) # 红色警告

                painter.setBrush(QBrush(base_color))
                painter.setPen(QPen(QColor(255,255,255, 30)))
                painter.drawRect(QRect(int(i*dx), int(j*dy), int(dx), int(dy)))

        # 绘制原始测绘点轨迹
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        for px, py, pz in self.engine.survey_points:
            painter.setBrush(QBrush(QColor(241, 196, 15)))
            painter.drawEllipse(QPoint(int(px*dx), int(py*dy)), 4, 4)

    def mousePressEvent(self, event):
        res = self.engine.grid_res
        ix = int(event.position().x() / (self.width() / res))
        iy = int(event.position().y() / (self.height() / res))
        
        if 0 <= ix < res and 0 <= iy < res:
            z = self.engine.nodes[ix][iy].z
            self.node_selected.emit(ix, iy, z)

# =================================================================
# 模块容器：地形建模引擎主界面
# =================================================================

class TerrainModelingModule(QWidget):
    """
    地形建模引擎主模块：集成数据录入、算法触发与状态流转逻辑
    """
    def __init__(self):
        super().__init__()
        self.engine = TerrainLogicEngine(grid_res=25)
        self.engine.initialize_grid()
        self.current_workflow = "数据输入阶段"
        self.init_ui()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)

        # ---------------- 左侧：数据控制中心 ----------------
        self.ctrl_panel = QWidget()
        self.ctrl_panel.setFixedWidth(400)
        self.ctrl_layout = QVBoxLayout(self.ctrl_panel)

        # 1. 业务流程状态指示
        self.status_grp = QGroupBox("当前工作流状态")
        status_vbox = QVBoxLayout(self.status_grp)
        self.state_lbl = QLabel(f"核心状态: {self.current_workflow}")
        self.state_lbl.setStyleSheet("color: #2D5A27; font-weight: bold; font-size: 14px;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 4)
        self.progress_bar.setValue(1)
        status_vbox.addWidget(self.state_lbl)
        status_vbox.addWidget(self.progress_bar)
        self.ctrl_layout.addWidget(self.status_grp)

        # 2. 测绘数据CRUD
        self.data_grp = QGroupBox("原始测绘数据管理 (增删改查)")
        data_vbox = QVBoxLayout(self.data_grp)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["X坐标", "Y坐标", "标高(m)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        btn_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("添加测绘点")
        self.clear_btn = QPushButton("清空数据")
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addWidget(self.clear_btn)
        
        data_vbox.addLayout(btn_layout)
        data_vbox.addWidget(self.table)
        self.ctrl_layout.addWidget(self.data_grp)

        # 3. 算法参数与规则引擎控制
        self.rule_grp = QGroupBox("业务规则与算法引擎")
        rule_vbox = QVBoxLayout(self.rule_grp)
        
        rule_vbox.addWidget(QLabel("景观功能选型 (触发规则引擎):"))
        self.func_combo = QComboBox()
        self.func_combo.addItems(["无障碍步道", "排水草沟", "建筑基座", "生态护坡"])
        rule_vbox.addWidget(self.func_combo)
        
        rule_vbox.addWidget(QLabel("IDW 插值权重系数:"))
        self.weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.weight_slider.setRange(1, 5)
        self.weight_slider.setValue(2)
        rule_vbox.addWidget(self.weight_slider)
        
        self.run_btn = QPushButton("执行地形重构算法")
        self.run_btn.setFixedHeight(40)
        self.run_btn.setStyleSheet("background-color: #27AE60; color: white;")
        rule_vbox.addWidget(self.run_btn)
        
        self.ctrl_layout.addWidget(self.rule_grp)

        # ---------------- 右侧：可视化反馈中心 ----------------
        self.view_panel = QSplitter(Qt.Orientation.Vertical)
        
        # 实时渲染画布
        self.canvas_frame = QFrame()
        self.canvas_frame.setFrameShape(QFrame.Shape.StyledPanel)
        canvas_v = QVBoxLayout(self.canvas_frame)
        canvas_v.setContentsMargins(0,0,0,0)
        self.canvas = TerrainCanvas(self.engine)
        canvas_v.addWidget(self.canvas)
        
        # 智能诊断日志输出
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("算法引擎诊断日志输出区域...")
        self.log_output.setStyleSheet("background: #F8F9F9; color: #2C3E50; font-family: 'Consolas';")
        
        self.view_panel.addWidget(self.canvas_frame)
        self.view_panel.addWidget(self.log_output)
        self.view_panel.setStretchFactor(0, 3)
        self.view_panel.setStretchFactor(1, 1)

        self.main_layout.addWidget(self.ctrl_panel)
        self.main_layout.addWidget(self.view_panel)

        # 信号绑定
        self.add_row_btn.clicked.connect(self.on_add_row)
        self.clear_btn.clicked.connect(self.on_clear_data)
        self.run_btn.clicked.connect(self.execute_engine)
        self.canvas.node_selected.connect(self.show_node_detail)
        
        # 初始化一些模拟数据
        self._seed_mock_data()

    def _seed_mock_data(self):
        """填充初始测绘数据，展现数据一致性逻辑"""
        mock_points = [(5,5,12.5), (10,18,8.2), (20,3,15.7), (15,12,10.0), (2,22,14.2)]
        for x, y, z in mock_points:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(x)))
            self.table.setItem(row, 1, QTableWidgetItem(str(y)))
            self.table.setItem(row, 2, QTableWidgetItem(str(z)))
            self.engine.add_survey_point(x, y, z)

    def on_add_row(self):
        """CRUD: 增加一行测绘点数据"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem("0"))
        self.table.setItem(row, 1, QTableWidgetItem("0"))
        self.table.setItem(row, 2, QTableWidgetItem("10.0"))

    def on_clear_data(self):
        """CRUD: 清空数据并重置状态流转"""
        self.table.setRowCount(0)
        self.engine.survey_points = []
        self.engine.initialize_grid()
        self.current_workflow = "数据输入阶段"
        self.update_workflow_state()
        self.canvas.update()

    def update_workflow_state(self):
        """状态机流转显示逻辑"""
        self.state_lbl.setText(f"核心状态: {self.current_workflow}")
        states = ["数据输入阶段", "插值重构阶段", "规范校验阶段", "成果优化阶段"]
        if self.current_workflow in states:
            self.progress_bar.setValue(states.index(self.current_workflow) + 1)

    def execute_engine(self):
        """
        核心动作：触发大规模空间计算
        包含：数据同步 -> 算法重构 -> 规则校验 -> 日志反馈
        """
        start_time = time.time()
        self.log_output.append(f"[{time.strftime('%H:%M:%S')}] 启动地形建模算法引擎...")
        
        # 1. 数据同步一致性处理
        self.engine.survey_points = []
        try:
            for r in range(self.table.rowCount()):
                x = float(self.table.item(r, 0).text())
                y = float(self.table.item(r, 1).text())
                z = float(self.table.item(r, 2).text())
                self.engine.add_survey_point(x, y, z)
        except ValueError:
            self.log_output.append("<font color='red'>错误：数据格式异常，请确保输入为数值。</font>")
            return

        # 2. 状态流转：进入重构
        self.current_workflow = "插值重构阶段"
        self.update_workflow_state()
        self.engine.run_idw_interpolation()
        
        # 3. 业务规则引擎介入
        self.current_workflow = "规范校验阶段"
        self.update_workflow_state()
        
        selected_mode = self.func_combo.currentText()
        min_s, max_s = self.engine.rules[selected_mode]
        
        violations = 0
        for i in range(self.engine.grid_res):
            for j in range(self.engine.grid_res):
                node = self.engine.nodes[i][j]
                if node.slope < min_s or node.slope > max_s:
                    node.is_violation = True
                    violations += 1
                else:
                    node.is_violation = False

        # 4. 计算资源统计 (土方平衡)
        stats = self.engine.calculate_earthwork(target_z=10.0)
        
        elapsed = (time.time() - start_time) * 1000
        self.log_output.append(f"建模完成！耗时: {elapsed:.2f}ms")
        self.log_output.append(f"规则校验报告 [{selected_mode}]:")
        self.log_output.append(f" - 采样总数: {self.engine.grid_res**2}")
        self.log_output.append(f" - 规范违规区域: {violations} 处")
        self.log_output.append(f" - 资源预估: 挖方 {stats['挖方']:.1f}m³, 填方 {stats['填方']:.1f}m³")
        
        if violations > (self.engine.grid_res**2 * 0.3):
            self.log_output.append("<font color='orange'>预警：该地形与[{}]功能适配度极低，建议大幅调整标高。</font>".format(selected_mode))
            self.current_workflow = "数据输入阶段"
        else:
            self.current_workflow = "成果优化阶段"
            
        self.update_workflow_state()
        self.canvas.update()

    def show_node_detail(self, x, y, z):
        """交互功能：点击显示局部空间属性"""
        self.log_output.append(f">> 选中网格点({x},{y}): 海拔 {z:.2f}m, 局部坡度 {self.engine.nodes[x][y].slope:.1%}")

def get_widget():
    """工厂方法：由主程序动态调用"""
    return TerrainModelingModule()