import os
import importlib
from PyQt6.QtCore import QObject, pyqtSignal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReloaderSignals(QObject):
    """定义一个信号，用于跨线程通讯"""
    module_changed = pyqtSignal(str)

class ModuleReloader(FileSystemEventHandler):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.signals = ReloaderSignals()
        # 将信号连接到主窗口的重载方法
        self.signals.module_changed.connect(self.main_window.reload_module)

    def on_modified(self, event):
        # 兼容 Windows 和 Linux 的路径处理
        if event.src_path.endswith(".py") and "modules" in event.src_path:
            # 使用 os.path 自动处理分隔符
            filename = os.path.basename(event.src_path)
            module_name = filename.replace(".py", "")
            
            if module_name != "__init__":
                print(f"核心引擎监测到逻辑变更: {module_name}，正在同步状态机...")
                # 必须通过信号发射，不能直接调用
                self.signals.module_changed.emit(module_name)