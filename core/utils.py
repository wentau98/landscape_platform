import os
import sys

def get_resource_path(relative_path):
    """ 获取资源绝对路径，适配开发环境和 PyInstaller 打包环境 """
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        base_path = sys._MEIPASS
    else:
        # 开发环境路径
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)