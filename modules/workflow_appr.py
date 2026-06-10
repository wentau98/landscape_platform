import sys
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QProgressBar, QTextEdit, 
                             QListWidget, QListWidgetItem, QScrollArea,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QSize

# =================================================================
# 视觉风格：工业级数字化审计工作台
# =================================================================
APPR_STYLE = """
QWidget#WorkflowModule { background-color: #F8FAFC; }

/* 状态标签样式 */
QLabel#Tag_待处理 { background-color: #F1F5F9; color: #64748B; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold; }
QLabel#Tag_审核中 { background-color: #DBEAFE; color: #1E40AF; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold; }
QLabel#Tag_通过 { background-color: #DCFCE7; color: #15803D; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold; }
QLabel#Tag_驳回 { background-color: #FEE2E2; color: #B91C1C; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold; }

QFrame#MetricCard { background-color: white; border-radius: 12px; border: 1px solid #E2E8F0; }
QFrame#LogItem { background-color: #FFFFFF; border-bottom: 1px solid #F1F5F9; padding: 12px; }

QTextEdit#OpinionArea { 
    border: 1px solid #CBD5E1; border-radius: 8px; 
    background-color: white; font-size: 13px; padding: 8px;
}

QListWidget#Inbox { background-color: white; border: none; border-right: 1px solid #E2E8F0; outline: none; }
"""

# =================================================================
# 核心业务模型
# =================================================================

class ApprNode:
    def __init__(self, role, user):
        self.role, self.user = role, user
        self.status = "待处理" # 待处理, 审核中, 通过, 驳回
        self.opinion = ""
        self.timestamp = "" # 完整的审计时间戳

class ProposalEntity:
    def __init__(self, title, budget, owner):
        self.id = f"PJ-{random.randint(100,999)}"
        self.title = title
        self.budget = budget
        self.owner = owner
        
        # 核心逻辑：根据已有的模拟数据，自动判断当前应该轮到哪个节点审批
        # 我们假设前两个节点已经办结
        self.current_idx = 2 
        
        self.created_at = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
        
        # 模拟花费明细
        self.cost_breakdown = {
            "植物群落配置": budget * 0.35,
            "硬质铺装工程": budget * 0.40,
            "水泵及过滤系统": budget * 0.15,
            "智能照明系统": budget * 0.10
        }
        
        # --- 构造带历史记录的审批节点 ---
        
        # 节点1：已办结
        node1 = ApprNode("技术初审", "张工")
        node1.status = "通过"
        node1.opinion = "方案空间布局合理，植被覆盖率满足园林规范要求，水系结构自洽。"
        node1.timestamp = (datetime.now() - timedelta(days=1, hours=5)).strftime("%Y-%m-%d %H:%M:%S")

        # 节点2：已办结
        node2 = ApprNode("造价复核", "李经理")
        node2.status = "通过"
        node2.opinion = "材料定额单价符合本季度市场信息价，分项工程量计算无误，准予通过。"
        node2.timestamp = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")

        # 节点3：待办（当前环节）
        node3 = ApprNode("总工办签批", "王总工")
        node3.status = "待处理" # 进入界面后将自动流转为“审核中”

        self.nodes: List[ApprNode] = [node1, node2, node3]

# =================================================================
# 交互式对话框：方案详情与花费透视
# =================================================================

class DetailPopup(QDialog):
    def __init__(self, p: ProposalEntity, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"方案审计底稿 - {p.id}")
        self.setFixedSize(550, 480)
        self.setStyleSheet("background-color: white;")
        
        l = QVBoxLayout(self)
        l.setContentsMargins(25, 25, 25, 25)
        
        # 基础信息
        l.addWidget(QLabel(f"方案名称: {p.title}", styleSheet="font-size: 18px; font-weight: bold; color: #1E293B;"))
        l.addWidget(QLabel(f"提交时间: {p.created_at} | 提交人: {p.owner}", styleSheet="color: #64748B; margin-bottom: 10px;"))
        
        # 花费拆解表 (Cost Breakdown Table)
        l.addWidget(QLabel("方案概算各子项花费明细:", styleSheet="font-weight: bold; color: #334155;"))
        self.table = QTableWidget(len(p.cost_breakdown), 2)
        self.table.setHorizontalHeaderLabels(["子项说明", "核算金额 (元)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        for i, (item, cost) in enumerate(p.cost_breakdown.items()):
            self.table.setItem(i, 0, QTableWidgetItem(item))
            cost_item = QTableWidgetItem(f"¥{cost:,.2f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, cost_item)
            
        l.addWidget(self.table)
        
        # 汇总提示
        total_lbl = QLabel(f"总计概算: ¥{p.budget:,.2f}")
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #10B981; margin-top: 5px;")
        l.addWidget(total_lbl)
        
        btn = QPushButton("关闭透视窗")
        btn.clicked.connect(self.close)
        btn.setStyleSheet("background: #64748B; color: white; padding: 10px; border-radius: 6px; margin-top: 15px;")
        l.addWidget(btn)

# =================================================================
# 主审批模块实现
# =================================================================

class WorkflowApprModule(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("WorkflowModule")
        self.setStyleSheet(APPR_STYLE)
        self.data: Dict[str, ProposalEntity] = {}
        self.active_id = None
        
        self._init_mock_data()
        self.init_ui()

    def _init_mock_data(self):
        seeds = [
            ("中央绿轴动态水系方案", 850000, "陈技术"), 
            ("林下空间生态修复工程", 1500000, "周主创"), 
            ("科技园区智慧照明设计", 320000, "吴造价")
        ]
        for t, b, o in seeds:
            p = ProposalEntity(t, b, o)
            self.data[p.id] = p

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        # 1. 左侧待办收件箱
        inbox_panel = QWidget()
        inbox_panel.setFixedWidth(320)
        inbox_v = QVBoxLayout(inbox_panel)
        inbox_v.addWidget(QLabel("方案待办收件箱", styleSheet="font-weight: bold; font-size: 15px; padding: 10px; color: #1E293B;"))
        
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("Inbox")
        self.list_widget.itemSelectionChanged.connect(self.switch_proposal)
        
        for pid, p in self.data.items():
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(300, 100)) # 稍微增加项的总高度
            item.setData(Qt.ItemDataRole.UserRole, pid)
            
            # 主容器
            w = QWidget()
            # 设置容器边距，让文字离边框远一点，看起来更舒服
            wl = QVBoxLayout(w)
            wl.setContentsMargins(15, 12, 15, 12) 
            wl.setSpacing(8) # 标题和副标题之间的间距

            # 1. 标题行
            title = QLabel(p.title)
            title.setStyleSheet("font-weight: bold; color: #1E293B; font-size: 14px;")
            wl.addWidget(title)

            # 2. 副标题与按钮行
            sub = QHBoxLayout()
            # --- 核心修复：强制该行所有控件在垂直方向居中对齐 ---
            sub.setAlignment(Qt.AlignmentFlag.AlignVCenter) 
            sub.setSpacing(0)

            # 信息标签
            info_lbl = QLabel(f"ID: {pid} | ¥{p.budget:,.0f}")
            info_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
            sub.addWidget(info_lbl)

            # 弹簧，把按钮推到最右边
            sub.addStretch()

            # 详情透视按钮
            btn_det = QPushButton("查看详情")
            # 增加一点宽度和高度，给 Emoji 和文字留足空间
            btn_det.setFixedSize(90, 32) 
            btn_det.setCursor(Qt.CursorShape.PointingHandCursor)
            
            btn_det.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    color: #475569;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 5px; /* 增加左右内边距，防止文字挨边 */
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                    color: #6366F1;
                }
                QPushButton:pressed {
                    background-color: #CBD5E1;
                }
            """)
            
            # 绑定点击事件
            btn_det.clicked.connect(lambda ch, target_p=p: DetailPopup(target_p, self).exec())
            
            sub.addWidget(btn_det)
            wl.addLayout(sub)

            self.list_widget.setItemWidget(item, w)
            
        inbox_v.addWidget(self.list_widget)
        layout.addWidget(inbox_panel)

        # 2. 右侧工作台
        work_panel = QWidget()
        work_v = QVBoxLayout(work_panel)
        work_v.setContentsMargins(25, 25, 25, 25)
        work_v.setSpacing(15)

        # A. 顶部概况
        self.top_card = QFrame()
        self.top_card.setObjectName("MetricCard")
        self.top_card.setFixedHeight(80)
        top_h = QHBoxLayout(self.top_card)
        self.info_lbl = QLabel("请从左侧选择待处理方案")
        self.info_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #1E293B;")
        self.prog_bar = QProgressBar()
        self.prog_bar.setFixedWidth(180); self.prog_bar.setFixedHeight(8)
        top_h.addWidget(self.info_lbl)
        top_h.addStretch()
        top_h.addWidget(QLabel("方案流转进度:")); top_h.addWidget(self.prog_bar)
        work_v.addWidget(self.top_card)

        # B. 中部：流转日志流水线 (展示精确时间)
        self.log_card = QFrame()
        self.log_card.setObjectName("MetricCard")
        log_v = QVBoxLayout(self.log_card)
        log_v.addWidget(QLabel("方案全生命周期流转日志", styleSheet="color: #64748B; font-weight: bold; font-size: 13px;"))
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.addStretch()
        self.scroll.setWidget(self.log_container)
        log_v.addWidget(self.scroll)
        work_v.addWidget(self.log_card)

        # C. 底部：评审决策区 (紧凑型布局)
        self.input_card = QFrame()
        self.input_card.setObjectName("MetricCard")
        self.input_card.setFixedHeight(200)
        input_v = QVBoxLayout(self.input_card)
        
        self.opinion_in = QTextEdit()
        self.opinion_in.setObjectName("OpinionArea")
        self.opinion_in.setPlaceholderText("请输入该环节的专业审计意见、费用合规性说明或驳回修正要求...")
        
        btn_h = QHBoxLayout()
        self.btn_rej = QPushButton("驳回方案")
        self.btn_rej.setStyleSheet("background: #EF4444; color: white; padding: 12px; border-radius: 6px; font-weight: bold;")
        self.btn_rej.clicked.connect(lambda: self.submit_appr("驳回"))
        
        self.btn_ok = QPushButton("准予通过")
        self.btn_ok.setStyleSheet("background: #10B981; color: white; padding: 12px; border-radius: 6px; font-weight: bold;")
        self.btn_ok.clicked.connect(lambda: self.submit_appr("通过"))
        
        btn_h.addStretch(); btn_h.addWidget(self.btn_rej); btn_h.addWidget(self.btn_ok)
        
        input_v.addWidget(QLabel("当前节点审批决策:", styleSheet="font-weight: bold; color: #334155;"))
        input_v.addWidget(self.opinion_in)
        input_v.addLayout(btn_h)
        work_v.addWidget(self.input_card)

        layout.addWidget(work_panel)

    # ---------------- 核心业务处理 ----------------

    def switch_proposal(self):
        items = self.list_widget.selectedItems()
        if not items: return
        self.active_id = items[0].data(Qt.ItemDataRole.UserRole)
        self.refresh_ui()

    def refresh_ui(self):
        p = self.data[self.active_id]
        self.info_lbl.setText(f"{p.title} | {p.id}")
        
        # 清理旧日志节点
        for i in reversed(range(self.log_layout.count())):
            w = self.log_layout.itemAt(i).widget()
            if w: w.deleteLater()
            
        # 重新渲染日志节点
        for idx, n in enumerate(p.nodes):
            # 自动标识当前活跃节点
            if idx == p.current_idx and n.status == "待处理": 
                n.status = "审核中"
                n.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 给当前动作一个开始时间
            item_f = QFrame()
            item_f.setObjectName("LogItem")
            il = QHBoxLayout(item_f)
            
            info = QVBoxLayout()
            info.addWidget(QLabel(f"<b>{n.role}</b> · {n.user}", styleSheet="color: #1E293B; font-size: 14px;"))
            
            op_text = n.opinion if n.opinion else "（等待操作中）"
            info.addWidget(QLabel(f"评审意见: {op_text}", styleSheet="color: #475569; font-size: 12px; font-style: italic;"))
            
            il.addLayout(info)
            il.addStretch()
            
            # 显示完整时间戳逻辑
            time_lbl = QLabel(n.timestamp if n.timestamp else "Processing...")
            time_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; margin-right: 15px;")
            il.addWidget(time_lbl)
            
            tag = QLabel(n.status)
            tag.setObjectName(f"Tag_{n.status}")
            il.addWidget(tag)
            
            self.log_layout.insertWidget(idx, item_f)
        self.log_layout.insertStretch(-1)
        
        # 状态机锁定：已完结方案不可操作
        is_end = p.current_idx >= len(p.nodes) or any(n.status == "驳回" for n in p.nodes)
        self.btn_ok.setEnabled(not is_end)
        self.btn_rej.setEnabled(not is_end)
        
        # 计算全局进度
        done = sum(1 for n in p.nodes if n.status in ["通过", "驳回"])
        self.prog_bar.setValue(int(done / len(p.nodes) * 100))

    def submit_appr(self, result):
        if not self.active_id: return
        p = self.data[self.active_id]
        node = p.nodes[p.current_idx]
        
        # 核心逻辑：注入此时此刻的时间戳
        node.status = result
        node.opinion = self.opinion_in.toPlainText() or ("准予核准，请转入下一阶段。" if result=="通过" else "方案不合规，退回设计部修改。")
        node.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if result == "通过" and p.current_idx < len(p.nodes) - 1:
            p.current_idx += 1
            
        self.opinion_in.clear()
        self.refresh_ui()

def get_widget():
    w = WorkflowApprModule()
    w._module_identifier = "workflow_appr"
    return w