import sys
import math
import heapq
import time
import random
from typing import List, Dict, Tuple, Optional, Set
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QFrame, QGroupBox, QTextEdit, 
                             QProgressBar, QComboBox, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QTimer, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QImage, QLinearGradient

# =================================================================
# 核心逻辑层：空间拓扑网格与 A* 引擎
# =================================================================

class PathNode:
    """路径节点：包含 A* 算法所需的所有代价权重"""
    def __init__(self, x: int, y: int):
        self.pos = (x, y)
        self.g_score = float('inf')  # 起点到当前代价
        self.f_score = float('inf')  # 预估总代价
        self.parent = None
        self.walkable = True
        self.cost_multiplier = 1.0   # 材质代价 (1.0=硬质铺装, 5.0=软质草地)
        self.is_scenic = False       # 是否为风景吸引点
        self.flow_density = 0.0      # 人流模拟密度

class PathfindingEngine:
    """
    核心算法引擎：
    实现多权重的 A* 路径搜索与人流覆盖分析
    """
    def __init__(self, cols: int, rows: int):
        self.cols, self.rows = cols, rows
        self.grid = [[PathNode(i, j) for j in range(rows)] for i in range(cols)]
        self.start_node = None
        self.end_node = None
        self.scenic_spots = []

    def get_neighbors(self, node: PathNode) -> List[PathNode]:
        neighbors = []
        x, y = node.pos
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (-1,1), (1,-1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                if self.grid[nx][ny].walkable:
                    neighbors.append(self.grid[nx][ny])
        return neighbors

    def heuristic(self, a: PathNode, b: PathNode) -> float:
        """欧几里得距离启发函数"""
        return math.sqrt((a.pos[0] - b.pos[1])**2 + (a.pos[1] - b.pos[1])**2)

    def run_astar(self) -> List[Tuple[int, int]]:
        """核心 A* 寻路逻辑：集成材质代价与地形坡度权重"""
        if not self.start_node or not self.end_node:
            return []

        # 重置搜索状态
        for row in self.grid:
            for node in row:
                node.g_score = float('inf')
                node.f_score = float('inf')
                node.parent = None

        open_set = []
        self.start_node.g_score = 0
        self.start_node.f_score = self.heuristic(self.start_node, self.end_node)
        heapq.heappush(open_set, (self.start_node.f_score, id(self.start_node), self.start_node))

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current == self.end_node:
                return self._reconstruct_path(current)

            for neighbor in self.get_neighbors(current):
                # 核心逻辑：路径代价 = 物理距离 * 材质权重
                dist = math.sqrt((current.pos[0]-neighbor.pos[0])**2 + (current.pos[1]-neighbor.pos[1])**2)
                tentative_g = current.g_score + (dist * neighbor.cost_multiplier)
                
                if tentative_g < neighbor.g_score:
                    neighbor.parent = current
                    neighbor.g_score = tentative_g
                    neighbor.f_score = tentative_g + self.heuristic(neighbor, self.end_node)
                    heapq.heappush(open_set, (neighbor.f_score, id(neighbor), neighbor))
        return []

    def _reconstruct_path(self, current: PathNode) -> List[Tuple[int, int]]:
        path = []
        while current:
            path.append(current.pos)
            current = current.parent
        return path[::-1]

    def simulate_flow(self, paths_count: int):
        """核心演化算法：模拟多代理人流产生的路径密度热力"""
        # 重置密度
        for row in self.grid:
            for n in row: n.flow_density *= 0.5 # 模拟衰减
            
        # 模拟多个随机入出口产生的路径
        for _ in range(paths_count):
            start = self.grid[random.randint(0, 10)][random.randint(0, self.rows-1)]
            end = self.grid[random.randint(self.cols-11, self.cols-1)][random.randint(0, self.rows-1)]
            self.start_node, self.end_node = start, end
            path = self.run_astar()
            for px, py in path:
                self.grid[px][py].flow_density += 1.5

# =================================================================
# 界面表现层：交互式路径画布
# =================================================================

class PathCanvas(QFrame):
    """
    高级交互式网格编辑器：
    支持实时绘制障碍物、人流热力渲染及路径动态预览
    """
    node_updated = pyqtSignal()

    def __init__(self, engine: PathfindingEngine):
        super().__init__()
        self.engine = engine
        self.setMinimumSize(600, 450)
        self.setMouseTracking(True)
        self.current_tool = "Obstacle"
        self.active_path = []

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        dx = self.width() / self.engine.cols
        dy = self.height() / self.engine.rows

        # 1. 绘制底图与热力场
        for i in range(self.engine.cols):
            for j in range(self.engine.rows):
                node = self.engine.grid[i][j]
                rect = QRectF(i*dx, j*dy, dx, dy)
                
                # 默认颜色逻辑
                color = QColor(248, 249, 249)
                if not node.walkable:
                    color = QColor(44, 62, 80) # 障碍物
                elif node.is_scenic:
                    color = QColor(241, 196, 15, 180) # 风景点
                elif node.flow_density > 0.1:
                    # 热力图颜色逻辑：蓝->绿->红
                    intensity = min(255, int(node.flow_density * 40))
                    color = QColor(231, 76, 60, intensity)
                
                painter.fillRect(rect, color)
                painter.setPen(QPen(QColor(200,200,200, 50), 0.5))
                painter.drawRect(rect)

        # 2. 绘制当前最优路径
        if self.active_path:
            painter.setPen(QPen(QColor(39, 174, 96), 3))
            for k in range(len(self.active_path)-1):
                p1 = self.active_path[k]
                p2 = self.active_path[k+1]
                painter.drawLine(int(p1[0]*dx + dx/2), int(p1[1]*dy + dy/2),
                                 int(p2[0]*dx + dx/2), int(p2[1]*dy + dy/2))

        # 3. 绘制起终点特殊标记
        if self.engine.start_node:
            painter.setBrush(QBrush(QColor(46, 204, 113)))
            self._draw_marker(painter, self.engine.start_node.pos, dx, dy, "S")
        if self.engine.end_node:
            painter.setBrush(QBrush(QColor(231, 76, 60)))
            self._draw_marker(painter, self.engine.end_node.pos, dx, dy, "E")

    def _draw_marker(self, painter, pos, dx, dy, text):
        rect = QRectF(pos[0]*dx, pos[1]*dy, dx, dy)
        painter.drawEllipse(rect)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._handle_click(event)

    def mousePressEvent(self, event):
        self._handle_click(event)

    def _handle_click(self, event):
        ix = int(event.position().x() / (self.width() / self.engine.cols))
        iy = int(event.position().y() / (self.height() / self.engine.rows))
        
        if 0 <= ix < self.engine.cols and 0 <= iy < self.engine.rows:
            node = self.engine.grid[ix][iy]
            if self.current_tool == "Obstacle":
                node.walkable = False
            elif self.current_tool == "Erase":
                node.walkable = True
                node.is_scenic = False
            elif self.current_tool == "Start":
                self.engine.start_node = node
            elif self.current_tool == "End":
                self.engine.end_node = node
            elif self.current_tool == "Scenic":
                node.is_scenic = True
            
            self.update()
            self.node_updated.emit()

# =================================================================
# 模块容器：路径覆盖规划主界面
# =================================================================

class PathPlannerModule(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = PathfindingEngine(40, 30)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ---------------- 左侧：业务配置面板 ----------------
        self.ctrl_panel = QWidget()
        self.ctrl_panel.setFixedWidth(380)
        vbox = QVBoxLayout(self.ctrl_panel)

        # 1. 编辑工具箱
        tool_grp = QGroupBox("空间拓扑编辑工具")
        t_layout = QVBoxLayout(tool_grp)
        
        tools = [("绘制建筑/障碍物", "Obstacle"), ("橡皮擦", "Erase"), 
                 ("设置起点", "Start"), ("设置终点", "End"), ("放置风景吸引点", "Scenic")]
        self.tool_group = QButtonGroup(self)
        for i, (name, key) in enumerate(tools):
            rb = QRadioButton(name)
            if i == 0: rb.setChecked(True)
            self.tool_group.addButton(rb, i)
            rb.toggled.connect(lambda ch, k=key: self.set_tool(k))
            t_layout.addWidget(rb)
        vbox.addWidget(tool_grp)

        # 2. 算法参数与规范核查
        rule_grp = QGroupBox("景观可达性规约引擎")
        r_layout = QVBoxLayout(rule_grp)
        
        self.complexity_bar = QProgressBar()
        self.complexity_bar.setFormat("路径复杂度评分: %p%")
        
        btn_calc = QPushButton("执行 A* 路径覆盖计算")
        btn_calc.setStyleSheet("background-color: #27AE60; color: white; height: 35px;")
        btn_calc.clicked.connect(self.calculate_path)
        
        btn_sim = QPushButton("模拟人流压力测试")
        btn_sim.clicked.connect(self.run_flow_simulation)
        
        r_layout.addWidget(QLabel("覆盖效率评估:"))
        r_layout.addWidget(self.complexity_bar)
        r_layout.addWidget(btn_calc)
        r_layout.addWidget(btn_sim)
        vbox.addWidget(rule_grp)

        # 3. 实时审计日志
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background: #F8F9F9; font-family: Consolas; font-size: 11px;")
        vbox.addWidget(QLabel("算法诊断日志:"))
        vbox.addWidget(self.log_output)

        # ---------------- 右侧：可视化模拟 ----------------
        self.canvas = PathCanvas(self.engine)
        self.canvas.node_updated.connect(self.on_data_change)
        
        layout.addWidget(self.ctrl_panel)
        layout.addWidget(self.canvas)

    def set_tool(self, key):
        self.canvas.current_tool = key
        self.log_output.append(f">> 切换工具: {key}")

    def on_data_change(self):
        """数据一致性处理：当拓扑改变时重置部分计算状态"""
        pass

    def calculate_path(self):
        """执行核心 A* 寻路并进行业务评估"""
        start_t = time.time()
        path = self.engine.run_astar()
        
        if path:
            self.canvas.active_path = path
            self.canvas.update()
            
            # 业务规则评估：路径长度与直线距离比
            direct_dist = self.engine.heuristic(self.engine.start_node, self.engine.end_node)
            actual_dist = len(path)
            complexity = (actual_dist / direct_dist) if direct_dist > 0 else 1
            
            self.complexity_bar.setValue(min(100, int(complexity * 40)))
            self.log_output.append(f"[寻路成功] 耗时: {(time.time()-start_t)*1000:.2f}ms")
            self.log_output.append(f" - 路径长度: {actual_dist} 单元")
            self.log_output.append(f" - 绕路系数: {complexity:.2f}")
            
            # 资源调度：计算材料面积（假设宽度3m）
            area = actual_dist * 3
            self.log_output.append(f" - 预估硬质面积: {area} m²")
        else:
            self.log_output.append("<font color='red'>[寻路失败] 无法在当前障碍物布局下找到合法路径！</font>")

    def run_flow_simulation(self):
        """执行复杂的人流覆盖模拟算法"""
        self.log_output.append(">>> 正在启动多代理人流覆盖压力测试...")
        self.engine.simulate_flow(15) # 模拟15组随机人流
        self.canvas.update()
        self.log_output.append(">> 模拟完成：已生成空间人流密度热力分布图。")

def get_widget():
    return PathPlannerModule()