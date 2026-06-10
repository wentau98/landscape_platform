import sys
import uuid
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTreeWidget, QTreeWidgetItem, QHeaderView, 
                             QFrame, QProgressBar, QLineEdit, QComboBox, 
                             QDialog, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QBrush, QFont

# =================================================================
# 视觉风格：极致简约与行内操作样式
# =================================================================
AUDIT_STYLE = """
QWidget#MaterialModule { background-color: #FDFDFD; }
QFrame#MetricCard {
    background-color: white;
    border: 1px solid #EDF2F7;
    border-radius: 12px;
}
QLabel#MetricTitle { color: #718096; font-size: 11px; font-weight: 800; }
QLabel#MetricValue { color: #1A202C; font-size: 24px; font-weight: bold; font-family: 'Consolas'; }

QTreeWidget {
    background-color: white;
    border: 1px solid #EDF2F7;
    border-radius: 12px;
    outline: none;
}
QTreeWidget::item { height: 45px; border-bottom: 1px solid #F7FAFC; }

QPushButton#EditBtn {
    background-color: #EBF8FF;
    color: #3182CE;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: none;
}
QPushButton#EditBtn:hover { background-color: #3182CE; color: white; }

QPushButton#DelBtn {
    background-color: #FFF5F5;
    color: #E53E3E;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: none;
}
QPushButton#DelBtn:hover { background-color: #E53E3E; color: white; }

QPushButton#ActionBtn {
    background-color: #38A169;
    color: white;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
}
"""

# =================================================================
# 弹出框：编辑矩阵
# =================================================================

class MaterialEditDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("数据同步矩阵")
        self.setFixedSize(360, 420)
        layout = QFormLayout(self)
        layout.setSpacing(15)
        
        self.name_in = QLineEdit(initial_data['name'] if initial_data else "")
        self.price_in = QLineEdit(str(initial_data['price']) if initial_data else "0.0")
        self.qty_in = QLineEdit(str(initial_data['qty']) if initial_data else "0.0")
        self.cat_in = QComboBox()
        self.cat_in.addItems(["乔木类", "灌木类", "铺装类", "水景设备"])
        if initial_data: self.cat_in.setCurrentText(initial_data['cat'])

        layout.addRow("材料名称:", self.name_in)
        layout.addRow("定额分类:", self.cat_in)
        layout.addRow("单价:", self.price_in)
        layout.addRow("工程量:", self.qty_in)

        self.btn_confirm = QPushButton("保存修改")
        self.btn_confirm.setFixedHeight(40)
        self.btn_confirm.clicked.connect(self.accept)
        layout.addRow(self.btn_confirm)

    def get_data(self):
        return {
            "name": self.name_in.text(),
            "cat": self.cat_in.currentText(),
            "price": float(self.price_in.text() or 0),
            "qty": float(self.qty_in.text() or 0),
            "status": "待审计"
        }

# =================================================================
# 主模块：带行内操作的审计平台
# =================================================================

class MetricCard(QFrame):
    def __init__(self, title, value):
        super().__init__()
        self.setObjectName("MetricCard")
        l = QVBoxLayout(self)
        self.t = QLabel(title.upper()); self.t.setObjectName("MetricTitle")
        self.v = QLabel(value); self.v.setObjectName("MetricValue")
        l.addWidget(self.t); l.addWidget(self.v)

class MaterialAuditModule(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MaterialModule")
        self.setStyleSheet(AUDIT_STYLE)
        self.material_data = {}
        self.init_ui()
        self._load_seeds()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        # 1. 顶部看板
        h_cards = QHBoxLayout()
        self.c1 = MetricCard("总合价", "¥ 0")
        self.c2 = MetricCard("风险项", "0")
        self.c3 = MetricCard("预算余额", "¥ 500,000")
        h_cards.addWidget(self.c1); h_cards.addWidget(self.c2); h_cards.addWidget(self.c3)
        self.main_layout.addLayout(h_cards)

        # 2. 搜索栏
        search_h = QHBoxLayout()
        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("🔍 快速搜索材料...")
        self.search_in.setFixedHeight(35)
        self.search_in.textChanged.connect(self.on_search)
        self.btn_new = QPushButton("+ 新增项")
        self.btn_new.setObjectName("ActionBtn")
        self.btn_new.clicked.connect(self.on_add)
        search_h.addWidget(self.search_in)
        search_h.addWidget(self.btn_new)
        self.main_layout.addLayout(search_h)

        # 3. 核心表格
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["材料名称 / 编码", "单价", "工程量", "小计", "状态", "操作"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tree.header().resizeSection(5, 150) # 为操作列预留空间
        self.main_layout.addWidget(self.tree)

        # 4. 底部
        footer = QHBoxLayout()
        self.btn_audit = QPushButton("启动智能合规诊断")
        self.btn_audit.setObjectName("ActionBtn")
        self.btn_audit.clicked.connect(self.run_audit)
        footer.addStretch(); footer.addWidget(self.btn_audit)
        self.main_layout.addLayout(footer)

    # ---------------- 功能实现 ----------------

    def refresh_view(self):
        self.tree.clear()
        total_sum = 0
        risks = 0
        
        # 按分类建组
        cats = {}
        for m_id, d in self.material_data.items():
            if d['cat'] not in cats:
                cats[d['cat']] = QTreeWidgetItem(self.tree, [d['cat']])
                cats[d['cat']].setFirstColumnSpanned(True)
                cats[d['cat']].setBackground(0, QBrush(QColor("#F8FAFC")))
            
            parent = cats[d['cat']]
            cost = d['price'] * d['qty']
            item = QTreeWidgetItem(parent, [
                d['name'], f"¥{d['price']:,}", str(d['qty']), f"¥{cost:,}", d['status'], ""
            ])
            
            # --- 注入行内操作按钮 ---
            self._add_action_buttons(item, m_id)
            # ---------------------
            
            if "异常" in d['status']: risks += 1
            total_sum += cost

        self.tree.expandAll()
        self.c1.v.setText(f"¥ {total_sum:,}")
        self.c2.v.setText(str(risks))
        self.c3.v.setText(f"¥ {max(0, 500000 - total_sum):,}")

    def _add_action_buttons(self, item, m_id):
        """核心交互：增大按钮尺寸以确保文字可见"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 2, 10, 2) # 增加左右边距
        layout.setSpacing(10)                  # 增加按钮间距

        edit_btn = QPushButton("编辑")
        edit_btn.setObjectName("EditBtn")
        edit_btn.setFixedSize(70, 30)          # 宽度从50增加到70，高度从24增加到30
        edit_btn.clicked.connect(lambda: self.on_edit(m_id))

        del_btn = QPushButton("删除")
        del_btn.setObjectName("DelBtn")
        del_btn.setFixedSize(70, 30)          # 宽度从50增加到70，高度从24增加到30
        del_btn.clicked.connect(lambda: self.on_delete(m_id))

        layout.addWidget(edit_btn)
        layout.addWidget(del_btn)
        
        self.tree.setItemWidget(item, 5, container)

    def on_add(self):
        d = MaterialEditDialog(self)
        if d.exec():
            uid = str(uuid.uuid4())
            data = d.get_data()
            data['code'] = f"LY-{random.randint(10,99)}"
            self.material_data[uid] = data
            self.refresh_view()

    def on_edit(self, m_id):
        d = MaterialEditDialog(self, self.material_data[m_id])
        if d.exec():
            self.material_data[m_id].update(d.get_data())
            self.refresh_view()

    def on_delete(self, m_id):
        if QMessageBox.question(self, "确认", "确定删除该材料吗？") == QMessageBox.StandardButton.Yes:
            del self.material_data[m_id]
            self.refresh_view()

    def on_search(self, t):
        for i in range(self.tree.topLevelItemCount()):
            p = self.tree.topLevelItem(i)
            match_any = False
            for j in range(p.childCount()):
                c = p.child(j)
                show = t.lower() in c.text(0).lower()
                c.setHidden(not show)
                if show: match_any = True
            p.setHidden(not match_any)

    def run_audit(self):
        for m_id in self.material_data:
            if self.material_data[m_id]['price'] > 3000:
                self.material_data[m_id]['status'] = "价格异常"
            else:
                self.material_data[m_id]['status'] = "审计通过"
        self.refresh_view()

    def _load_seeds(self):
        seeds = [("特等银杏", "乔木类", 2800, 20), ("普通香樟", "乔木类", 850, 45), ("花岗岩", "铺装类", 185, 1500)]
        for n, c, p, q in seeds:
            uid = str(uuid.uuid4())
            self.material_data[uid] = {"name": n, "cat": c, "price": p, "qty": q, "status": "通过"}
        self.refresh_view()

def get_widget():
    w = MaterialAuditModule()
    w._module_identifier = "material_audit"
    return w