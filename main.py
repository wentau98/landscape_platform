import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

# ---------------------------------------------------------
# 开发环境工具导入 (打包后这些不会被运行)
# ---------------------------------------------------------
try:
    from hot_reloader import ModuleReloader
    from watchdog.observers import Observer
except ImportError:
    pass # 打包环境可能没安装 watchdog

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 

    # 1. 登录验证阶段
    login = LoginWindow()
    if login.exec() == LoginWindow.DialogCode.Accepted:
        
        # 2. 实例化主窗口 (此时 main_win 变量在函数作用域内生效)
        main_win = MainWindow()
        
        # 3. 环境识别逻辑：判断是否是打包后的 exe
        # 如果 sys.frozen 存在，说明是打包后的环境，此时禁用热更新
        is_frozen = getattr(sys, 'frozen', False)
        
        if not is_frozen:
            print(">>> 检测到开发环境，正在注入热更新模块...")
            try:
                # 传入主窗口实例进行监听
                reloader = ModuleReloader(main_win)
                observer = Observer()
                # 监控 modules 文件夹
                observer.schedule(reloader, path='modules', recursive=False)
                observer.start()
                
                # 确保程序退出时关闭监听线程
                app.aboutToQuit.connect(lambda: (observer.stop(), observer.join()))
            except Exception as e:
                print(f"热更新监听启动失败: {e}")

        # 4. 显示主界面
        main_win.show()
        sys.exit(app.exec())
        
    else:
        # 登录被取消或关闭
        sys.exit(0)

if __name__ == "__main__":
    main()