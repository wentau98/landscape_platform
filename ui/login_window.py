from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QWidget, QStackedWidget, 
                             QGraphicsDropShadowEffect, QFrame,QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor 
from ui.style import LANDSCAPE_THEME
from core.auth_manager import AuthManager

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.auth_engine = AuthManager()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(900, 560)
        self.init_ui()
        self.setStyleSheet(LANDSCAPE_THEME)

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        
        # 整体容器
        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setXOffset(0); shadow.setYOffset(10)
        self.container.setGraphicsEffect(shadow)

        # === 1. 左侧面板 (视觉品牌区) ===
        self.left_panel = QWidget()
        self.left_panel.setObjectName("LeftPanel")
        self.left_panel.setFixedWidth(400)
        left_v = QVBoxLayout(self.left_panel)
        left_v.setContentsMargins(40, 60, 40, 60)

        logo = QLabel("ECO-DESIGN")
        logo.setObjectName("LogoText")
        
        sub_title = QLabel("园林景观方案智能设计平台\nProfessional Landscape Intelligence")
        sub_title.setObjectName("BrandSub")
        
        # 模拟“高级感”的自检终端逻辑
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setObjectName("GlassCard")
        self.terminal.setStyleSheet("color: #D1FAE5; font-family: Consolas; font-size: 10px; border: none; background: rgba(0,0,0,0.2);")
        self.terminal.setFixedSize(320, 150)
        
        left_v.addWidget(logo)
        left_v.addWidget(sub_title)
        left_v.addStretch()
        left_v.addWidget(self.terminal)
        
        # === 2. 右侧面板 (操作区) ===
        self.right_panel = QWidget()
        self.right_panel.setObjectName("RightPanel")
        right_v = QVBoxLayout(self.right_panel)
        right_v.setContentsMargins(60, 40, 60, 40)

        # 顶部操作
        top_h = QHBoxLayout()
        top_h.addStretch()
        btn_close = QPushButton("×")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedSize(30, 30)
        btn_close.clicked.connect(self.reject)
        top_h.addWidget(btn_close)

        # 表单
        form_v = QVBoxLayout()
        form_v.setSpacing(10)
        title = QLabel("欢迎回来")
        title.setObjectName("Title")
        sub = QLabel("探索算法与自然的平衡之美")
        sub.setObjectName("SubTitle")

        self.u_input = QLineEdit(); self.u_input.setPlaceholderText("Designer ID")
        self.p_input = QLineEdit(); self.p_input.setPlaceholderText("Access Token")
        self.p_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # 默认填充
        self.u_input.setText("admin")
        self.p_input.setText("admin123")

        btn_login = QPushButton("登录")
        btn_login.setObjectName("PrimaryBtn")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self.handle_login)

        btn_reg = QPushButton("注册")
        btn_reg.setObjectName("SecondaryBtn")

        form_v.addWidget(title)
        form_v.addWidget(sub)
        form_v.addSpacing(30)
        form_v.addWidget(self.u_input)
        form_v.addWidget(self.p_input)
        form_v.addSpacing(20)
        form_v.addWidget(btn_login)
        form_v.addWidget(btn_reg, alignment=Qt.AlignmentFlag.AlignCenter)

        right_v.addLayout(top_h)
        right_v.addStretch()
        right_v.addLayout(form_v)
        right_v.addStretch()

        container_layout.addWidget(self.left_panel)
        container_layout.addWidget(self.right_panel)
        self.main_layout.addWidget(self.container)

        # 启动左侧终端动画
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self._update_terminal)
        self.log_timer.start(800)
        self.log_lines = [
            "> INITIALIZING ECO-ENGINE...",
            "> LOADING TERRAIN AGENTS...",
            "> SYNCING PLANT DATABASE...",
            "> SECURITY PROTOCOL ACTIVE.",
            "> SYSTEM READY."
        ]
        self.current_line = 0

    def _update_terminal(self):
        if self.current_line < len(self.log_lines):
            self.terminal.append(self.log_lines[self.current_line])
            self.current_line += 1
        else:
            self.log_timer.stop()

    def handle_login(self):
        # 活泼的交互反馈
        self.terminal.append(f"> VERIFYING USER: {self.u_input.text()}...")
        if self.auth_engine.authenticate(self.u_input.text(), self.p_input.text()):
            self.accept()
        else:
            self.u_input.setStyleSheet("border: 2px solid #EF4444;")
            self.terminal.append("> ACCESS DENIED: INVALID TOKEN.")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()