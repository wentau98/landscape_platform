# ui/style.py
GLOBAL_STYLE = """
QMainWindow { background-color: #F5F7FA; }
QListWidget {
    background-color: #2C3E50;
    color: #ECF0F1;
    border: none;
    font-size: 14px;
    outline: none;
}
QListWidget::item {
    padding: 15px;
    border-left: 5px solid transparent;
}
QListWidget::item:selected {
    background-color: #34495E;
    border-left: 5px solid #27AE60;
    color: #27AE60;
}
QWidget#ContentArea {
    background-color: white;
    border-radius: 10px;
    margin: 10px;
}
QPushButton {
    background-color: #27AE60;
    color: white;
    border-radius: 5px;
    padding: 10px;
    font-weight: bold;
}
QPushButton:hover { background-color: #2ECC71; }
QLabel#Header {
    font-size: 18px;
    font-weight: bold;
    color: #2C3E50;
    padding: 10px;
}

"""
# ui/style.py

LANDSCAPE_THEME = """
QDialog {
    background-color: #FFFFFF;
    border-radius: 12px;
}
#LeftPanel {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 #2D5A27, stop:1 #1E3D1A);
    border-top-left-radius: 12px;
    border-bottom-left-radius: 12px;
}
#RightPanel {
    background-color: #FDFDFD;
    border-top-right-radius: 12px;
    border-bottom-right-radius: 12px;
}
QLabel#Title {
    font-size: 24px;
    font-family: "Microsoft YaHei";
    font-weight: bold;
    color: #2D5A27;
}
QLabel#SubTitle {
    font-size: 12px;
    color: #7F8C8D;
}
QLineEdit {
    border: 1px solid #DCDFE6;
    border-radius: 4px;
    padding: 10px;
    background: #FFFFFF;
    selection-background-color: #2D5A27;
}
QLineEdit:focus {
    border: 1px solid #2D5A27;
}
QPushButton#PrimaryBtn {
    background-color: #2D5A27;
    color: white;
    border-radius: 4px;
    padding: 12px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#PrimaryBtn:hover {
    background-color: #3D7A35;
}
QPushButton#SecondaryBtn {
    color: #2D5A27;
    border: none;
    background: transparent;
    font-size: 12px;
}
"""
# ui/style.py

LANDSCAPE_THEME = """
QDialog {
    background-color: transparent;
}

/* 主容器：高级感的核心在于大圆角与深邃阴影 */
#MainContainer {
    background-color: #FFFFFF;
    border-radius: 24px;
}

/* 左侧面板：活泼的渐变与端庄的构图 */
#LeftPanel {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 #064E3B, stop:0.5 #065F46, stop:1 #10B981);
    border-top-left-radius: 24px;
    border-bottom-left-radius: 24px;
}

/* 装饰性光圈 */
#GlassCard {
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px;
}

QLabel#LogoText {
    color: white;
    font-size: 38px;
    font-family: "Segoe UI Black", "Microsoft YaHei";
    font-weight: 900;
    letter-spacing: 2px;
}

QLabel#BrandSub {
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
    font-family: "Microsoft YaHei Light";
    line-height: 150%;
}

/* 右侧面板：简洁高效 */
#RightPanel {
    background-color: #FAFAFA;
    border-top-right-radius: 24px;
    border-bottom-right-radius: 24px;
}

QLabel#Title {
    font-size: 28px;
    font-weight: 800;
    color: #1E293B;
    font-family: "Microsoft YaHei UI";
}

QLabel#SubTitle {
    font-size: 13px;
    color: #94A3B8;
    margin-bottom: 20px;
}

/* 输入框：端庄的边框与活泼的焦点色 */
QLineEdit {
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 12px 16px;
    background: #FFFFFF;
    font-size: 14px;
    color: #334155;
}
QLineEdit:focus {
    border: 2px solid #10B981;
    background: #F0FDF4;
}

/* 按钮：高级渐变与活泼的动效 */
QPushButton#PrimaryBtn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #059669, stop:1 #10B981);
    color: white;
    border-radius: 12px;
    padding: 14px;
    font-size: 15px;
    font-weight: bold;
    border: none;
}
QPushButton#PrimaryBtn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #047857, stop:1 #059669);
}

QPushButton#SecondaryBtn {
    color: #64748B;
    border: none;
    background: transparent;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#SecondaryBtn:hover {
    color: #10B981;
}

QPushButton#CloseBtn {
    color: #CBD5E1;
    font-size: 18px;
    font-weight: bold;
}
QPushButton#CloseBtn:hover {
    color: #EF4444;
}
"""