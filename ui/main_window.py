from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QListWidget, QHBoxLayout, QVBoxLayout, QWidget
import importlib
import sys

from ui.style import GLOBAL_STYLE

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(GLOBAL_STYLE) # 应用全局样式
        self.setWindowTitle("园林景观方案智能设计平台")
        self.resize(1200, 800)
        
        self.central_widget = QWidget()
        self.layout = QHBoxLayout(self.central_widget)
        
        # 左侧导航菜单
        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(200)
        
        # 右侧内容区 (动态堆叠)
        self.content_stack = QStackedWidget()
        
        self.layout.addWidget(self.menu_list)
        self.layout.addWidget(self.content_stack)
        self.setCentralWidget(self.central_widget)
        
        self.module_map = {}
        self.init_menus()
        self.menu_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        # 为内容区域添加一个容器，使其看起来有“浮动感”
        self.container = QWidget()
        self.container.setObjectName("ContentArea")
        container_layout = QVBoxLayout(self.container)
        container_layout.addWidget(self.content_stack)
        
        self.layout.addWidget(self.menu_list)
        self.layout.addWidget(self.container) # 将带样式的容器加入布局
    def reload_module(self, mod_name):
        print(f"DEBUG: 开始寻找并重载模块 [{mod_name}]")
        try:
            full_path = f"modules.{mod_name}"
            
            # 1. 强制刷新 Python 缓存
            if full_path in sys.modules:
                importlib.reload(sys.modules[full_path])
            else:
                importlib.import_module(full_path)
            
            new_module = sys.modules[full_path]
            
            # 2. 遍历堆栈寻找对应的旧组件
            for i in range(self.content_stack.count()):
                old_widget = self.content_stack.widget(i)
                
                # 检查这个组件是否有我们打的标签
                identifier = getattr(old_widget, "_module_identifier", "Unknown")
                
                if identifier == mod_name:
                    print(f"DEBUG: 命中目标组件，正在执行物理替换...")
                    
                    # 创建新组件实例
                    new_widget = new_module.get_widget()
                    # --- 重要：给新组件也打上标签，否则下次热更新就失效了 ---
                    new_widget._module_identifier = mod_name 
                    
                    # 记录当前显示状态
                    is_active = (self.content_stack.currentIndex() == i)
                    
                    # 执行替换
                    self.content_stack.removeWidget(old_widget)
                    self.content_stack.insertWidget(i, new_widget)
                    
                    if is_active:
                        self.content_stack.setCurrentIndex(i)
                    
                    old_widget.deleteLater()
                    print(f"SUCCESS: {mod_name} 热更新完成并已渲染。")
                    return # 成功后退出循环
            
            print(f"ERROR: 在界面堆栈中未找到标识为 {mod_name} 的组件。")

        except Exception as e:
            print(f"RELOAD ERROR: {str(e)}")
    def init_menus(self):
        # 10个核心功能模块定义
        modules_info = [
            ("地形建模引擎", "terrain_engine"),
            ("植物生态算法", "plant_logic"),
            ("水系动力模拟", "hydrology_sim"),
            ("路径覆盖规划", "path_planner"),
            ("材料预决算", "material_audit"),
            ("多级审批流", "workflow_appr"),
            ("生态足迹分析", "eco_balance"),
            ("三维光影计算", "lighting_calc"),
            ("施工冲突调度", "construction"),
            ("版本数据回溯", "version_control")
        ]
        
        for name, mod_name in modules_info:
            self.menu_list.addItem(name)
            # 动态导入模块逻辑
            try:
                module = importlib.import_module(f"modules.{mod_name}")
                # 假设每个模块都有一个 get_widget 方法
                widget = module.get_widget() 
                widget._module_identifier = mod_name 
                # widget._module_name = mod_name  <-- 必须加这一行，重载时才找得到
                widget._module_name = mod_name
                self.content_stack.addWidget(widget)
                self.module_map[mod_name] = widget
            except Exception as e:
                print(f"加载模块 {mod_name} 失败: {e}")