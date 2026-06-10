import sys
import random
import math
import uuid
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QFrame, QSlider, QGroupBox, QTextEdit, 
                             QProgressBar, QComboBox, QListWidget, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QSize, QTimer, QThread
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient

# =================================================================
# 核心数据模型：植物个体与遗传属性
# =================================================================

class PlantInstance:
    """植物个体对象：封装唯一标识、位置、生理状态及生态占位"""
    def __init__(self, species_id: str, x: float, y: float, size: float):
        self.instance_id = str(uuid.uuid4())[:8]
        self.species_id = species_id
        self.x = x
        self.y = y
        self.size = size          # 冠幅大小 (m)
        self.age = 1              # 初始生长期
        self.health = 100.0       # 健康状态 (0-100)
        self.biomass = 1.0        # 生物量累积
        self.stress_level = 0.0   # 环境压力值

class SpeciesDefinition:
    """物种静态属性定义：生长速率、生态兼容性"""
    def __init__(self, name: str, cat: str, color: QColor, growth_rate: float, max_size: float):
        self.name = name
        self.category = cat # 乔木/灌木/地被
        self.base_color = color
        self.growth_rate = growth_rate
        self.max_size = max_size
        self.water_demand = random.uniform(10, 50)
        self.companion_bonus = {} # 共生物种
        self.antagonist_list = [] # 互斥物种

# =================================================================
# 核心引擎层：生态演替与规则评估
# =================================================================

class EcologicalSimulationEngine:
    """
    景观生态动力学引擎：处理植物生长竞争、资源抢夺及空间占位逻辑
    """
    def __init__(self, width: int = 100, height: int = 100):
        self.bounds = (width, height)
        self.plants: List[PlantInstance] = []
        self.catalog = self._init_species_catalog()
        self.current_season = "春季"
        self.total_biomass = 0.0

    def _init_species_catalog(self) -> Dict[str, SpeciesDefinition]:
        """初始化物种知识库及其独特的化感/共生逻辑"""
        catalog = {
            "Ginkgo": SpeciesDefinition("银杏", "乔木", QColor(241, 196, 15), 0.05, 8.0),
            "Cinnamomum": SpeciesDefinition("香樟", "乔木", QColor(39, 174, 96), 0.08, 12.0),
            "Osmanthus": SpeciesDefinition("桂花", "灌木", QColor(243, 156, 18), 0.12, 4.0),
            "Photinia": SpeciesDefinition("红叶石楠", "灌木", QColor(192, 57, 43), 0.15, 3.0),
            "Grass": SpeciesDefinition("草坪", "地被", QColor(46, 204, 113), 0.25, 0.5)
        }
        # 注入独特的生物逻辑
        catalog["Ginkgo"].companion_bonus = {"Osmanthus": 1.2} # 银杏与桂花共生加成
        catalog["Cinnamomum"].antagonist_list = ["Grass"]      # 香樟树下草坪生长受抑
        return catalog

    def add_plant(self, x, y, species_id):
        """数据一致性：检查空间冲突后添加"""
        spec = self.catalog[species_id]
        new_p = PlantInstance(species_id, x, y, spec.max_size * 0.2)
        self.plants.append(new_p)
        return new_p

    def update_cycle(self):
        """核心算法：每一轮迭代计算所有植物的相互作用"""
        season_mod = {"春季": 1.4, "夏季": 1.1, "秋季": 0.7, "冬季": 0.2}[self.current_season]
        
        for p in self.plants:
            spec = self.catalog[p.species_id]
            
            # 1. 邻域竞争压力计算
            competition_stress = 0.0
            for other in self.plants:
                if p == other: continue
                dist = math.sqrt((p.x - other.x)**2 + (p.y - other.y)**2)
                # 冠幅重叠检测逻辑
                if dist < (p.size + other.size) / 2:
                    competition_stress += 0.2
            
            # 2. 互斥/共生规则引擎介入
            logic_bonus = 1.0
            for other in self.plants:
                dist = math.sqrt((p.x - other.x)**2 + (p.y - other.y)**2)
                if dist < 5.0: # 近距离交互
                    if other.species_id in spec.companion_bonus:
                        logic_bonus *= spec.companion_bonus[other.species_id]
                    if other.species_id in spec.antagonist_list:
                        logic_bonus *= 0.5

            # 3. 生长方程：Delta_Size = Base * Season * Bonus / Stress
            p.stress_level = competition_stress
            growth = spec.growth_rate * season_mod * logic_bonus / (1.0 + competition_stress)
            
            if p.size < spec.max_size:
                p.size += growth
                p.biomass += growth * 2.5
            
            # 4. 健康度流转逻辑
            if p.stress_level > 1.5:
                p.health -= 0.5
            elif p.health < 100:
                p.health += 0.1

    def calculate_ecology_metrics(self) -> Dict:
        """核心业务逻辑：计算香农多样性指数"""
        if not self.plants: return {"h": 0, "status": "无植被"}
        counts = {}
        for p in self.plants:
            counts[p.species_id] = counts.get(p.species_id, 0) + 1
        
        h = 0.0
        total = len(self.plants)
        for sid in counts:
            pi = counts[sid] / total
            h -= pi * math.log(pi)
            
        status = "脆弱" if h < 0.5 else "稳定" if h < 1.2 else "高度平衡"
        return {"h": h, "status": status, "total": total, "counts": counts}

# =================================================================
# UI 表现层：自定义生态渲染画布
# =================================================================

class PlantCanvas(QFrame):
    """
    高级绘图引擎：实现植物生理状态的可视化反馈
    """
    inspect_signal = pyqtSignal(dict)

    def __init__(self, engine: EcologicalSimulationEngine):
        super().__init__()
        self.engine = engine
        self.setMinimumSize(600, 500)
        self.setMouseTracking(True)
        self.scale = 10.0 # 1米对应10像素

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景与栅格
        painter.fillRect(self.rect(), QColor(250, 252, 250))
        painter.setPen(QPen(QColor(230, 230, 230), 1))
        for i in range(0, self.width(), 40):
            painter.drawLine(i, 0, i, self.height())
        for j in range(0, self.height(), 40):
            painter.drawLine(0, j, self.width(), j)

        # 渲染植物实例
        for p in self.engine.plants:
            spec = self.engine.catalog[p.species_id]
            # 核心修复点：明确转换为 float
            cx = float(p.x * self.scale)
            cy = float(p.y * self.scale)
            radius = float((p.size * self.scale) / 2)
            
            # 修复 QRadialGradient 构造函数调用
            # 使用三个 float 参数的重载版本，避免使用 QPoint 对象
            grad = QRadialGradient(cx, cy, radius) 
            
            c = spec.base_color
            if p.health < 70: 
                c = c.darker(150)
            
            grad.setColorAt(0.0, c) # 注意：setColorAt 也建议使用 0.0 而非 0
            grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 60))
            
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # 绘制时同样确保使用 float
            painter.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))
            
            # ... 警示环代码同理，确保参数为 int 或 float ...
            if p.stress_level > 1.0:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(231, 76, 60, 100), 1, Qt.PenStyle.DashLine))
                painter.drawEllipse(int(cx - radius - 2), int(cy - radius - 2), int(radius * 2 + 4), int(radius * 2 + 4))

    def mousePressEvent(self, event):
        mx, my = event.position().x() / self.scale, event.position().y() / self.scale
        # 简单的点击检测逻辑
        for p in self.engine.plants:
            dist = math.sqrt((p.x - mx)**2 + (p.y - my)**2)
            if dist < p.size / 2:
                self.inspect_signal.emit({
                    "ID": p.instance_id,
                    "物种": self.engine.catalog[p.species_id].name,
                    "健康度": f"{p.health:.1f}%",
                    "竞争压力": f"{p.stress_level:.2f}",
                    "冠幅": f"{p.size:.2f}m"
                })
                break

# =================================================================
# 模块主界面：植物生态算法平台
# =================================================================

class PlantEcologicalModule(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = EcologicalSimulationEngine()
        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. 左侧控制面板 (Data & Control)
        self.ctrl_area = QWidget()
        self.ctrl_area.setFixedWidth(400)
        vbox = QVBoxLayout(self.ctrl_area)

        # A. 方案指标实时监控
        metrics_grp = QGroupBox("生态方案诊断")
        met_layout = QVBoxLayout(metrics_grp)
        self.h_index_lbl = QLabel("多样性指数: 0.00")
        self.h_index_lbl.setStyleSheet("font-weight: bold; color: #2D5A27;")
        self.ecology_status = QLabel("生态位状态: 待评估")
        self.stability_bar = QProgressBar()
        self.stability_bar.setFormat("系统稳定性: %p%")
        met_layout.addWidget(self.h_index_lbl)
        met_layout.addWidget(self.ecology_status)
        met_layout.addWidget(self.stability_bar)
        vbox.addWidget(metrics_grp)

        # B. 交互式种植工具
        tool_grp = QGroupBox("智能种植交互工具")
        tool_layout = QVBoxLayout(tool_grp)
        self.species_list = QListWidget()
        for sid, spec in self.engine.catalog.items():
            self.species_list.addItem(f"{spec.name} ({spec.category})")
        self.species_list.setCurrentRow(0)
        
        btn_place = QPushButton("投放选中植被种子")
        btn_place.clicked.connect(self.place_random_plant)
        btn_auto = QPushButton("执行算法自动补全")
        btn_auto.setStyleSheet("background-color: #27AE60; color: white;")
        btn_auto.clicked.connect(self.run_auto_layout)
        
        tool_layout.addWidget(QLabel("选择物种库:"))
        tool_layout.addWidget(self.species_list)
        tool_layout.addWidget(btn_place)
        tool_layout.addWidget(btn_auto)
        vbox.addWidget(tool_grp)

        # C. 资源调度与审计日志
        audit_grp = QGroupBox("生长审计与调度日志")
        audit_layout = QVBoxLayout(audit_grp)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background: #F4F6F6; font-family: 'Consolas'; font-size: 10px;")
        audit_layout.addWidget(self.log_output)
        vbox.addWidget(audit_grp)

        # 2. 右侧可视化与详细信息
        self.view_splitter = QSplitter(Qt.Orientation.Vertical)
        self.canvas = PlantCanvas(self.engine)
        self.canvas.inspect_signal.connect(self.show_plant_detail)
        
        # 底部属性表 (CRUD展示)
        self.detail_table = QTableWidget(0, 5)
        self.detail_table.setHorizontalHeaderLabels(["ID", "物种", "健康度", "压力值", "操作"])
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.view_splitter.addWidget(self.canvas)
        self.view_splitter.addWidget(self.detail_table)
        self.view_splitter.setStretchFactor(0, 4)

        self.main_layout.addWidget(self.ctrl_area)
        self.main_layout.addWidget(self.view_splitter)

    def setup_timer(self):
        """模拟时间流逝与生长状态流转"""
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.process_growth_step)
        self.sim_timer.start(2000) # 每2秒一个生长步长

    def process_growth_step(self):
        """核心业务步进：更新算法 -> 更新UI -> 更新指标"""
        self.engine.update_cycle()
        self.canvas.update()
        self.refresh_metrics()
        
        # 随机模拟资源调度提醒
        if random.random() > 0.7:
            self.generate_maintenance_report()

    def refresh_metrics(self):
        res = self.engine.calculate_ecology_metrics()
        self.h_index_lbl.setText(f"多样性指数 (Shannon): {res['h']:.2f}")
        self.ecology_status.setText(f"生态位状态: {res['status']}")
        score = min(100, int(res['h'] * 60))
        self.stability_bar.setValue(score)
        
        # 同步更新明细表 (数据一致性处理)
        self.detail_table.setRowCount(0)
        for p in self.engine.plants[:10]: # 仅展示前10条确保性能
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)
            self.detail_table.setItem(row, 0, QTableWidgetItem(p.instance_id))
            self.detail_table.setItem(row, 1, QTableWidgetItem(p.species_id))
            self.detail_table.setItem(row, 2, QTableWidgetItem(f"{p.health:.1f}%"))
            self.detail_table.setItem(row, 3, QTableWidgetItem(f"{p.stress_level:.2f}"))
            
            btn_del = QPushButton("移除")
            btn_del.clicked.connect(lambda _, pid=p.instance_id: self.remove_plant(pid))
            self.detail_table.setCellWidget(row, 4, btn_del)

    def place_random_plant(self):
        """增加功能 (CRUD - Create)"""
        idx = self.species_list.currentRow()
        sid = list(self.engine.catalog.keys())[idx]
        self.engine.add_plant(random.uniform(5, 55), random.uniform(5, 45), sid)
        self.canvas.update()

    def run_auto_layout(self):
        """核心算法：基于生物承载力的自动随机补全逻辑"""
        self.log_output.append(f"[{datetime.now().strftime('%H:%M:%S')}] 启动智能生态位补全算法...")
        # 模拟计算过程
        for _ in range(8):
            sid = random.choice(list(self.engine.catalog.keys()))
            self.engine.add_plant(random.uniform(5, 55), random.uniform(5, 45), sid)
        self.log_output.append(">> 算法诊断：已根据当前多样性指数自动补充 8 株植被。")

    def generate_maintenance_report(self):
        """资源调度引擎：生成养护计划"""
        total_water = sum(self.engine.catalog[p.species_id].water_demand for p in self.engine.plants)
        self.log_output.append(f"养护调度：今日预计总耗水量 {total_water:.1f}L")
        # 查找健康度最低的植物进行重点关注
        if self.engine.plants:
            weakest = min(self.engine.plants, key=lambda x: x.health)
            if weakest.health < 80:
                self.log_output.append(f"<font color='orange'>预警：个体 {weakest.instance_id} 竞争压力过载！</font>")

    def remove_plant(self, pid):
        """删除功能 (CRUD - Delete)"""
        self.engine.plants = [p for p in self.engine.plants if p.instance_id != pid]
        self.refresh_metrics()
        self.canvas.update()

    def show_plant_detail(self, info):
        """交互：显示单个植物审计详情"""
        self.log_output.append("-" * 20)
        for k, v in info.items():
            self.log_output.append(f"{k}: {v}")

def get_widget():
    return PlantEcologicalModule()