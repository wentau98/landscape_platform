import hashlib
import uuid
import platform
import time

class SecurityCore:
    """科技感核心：模拟硬件指纹与高级会话加密"""
    
    @staticmethod
    def get_hardware_fingerprint():
        """获取机器唯一标识，模拟授权设备校验"""
        node_id = platform.node()
        processor = platform.processor()
        # 产生一个基于机器硬件的伪指纹
        return hashlib.sha1(f"{node_id}{processor}".encode()).hexdigest()[:16].upper()

    @staticmethod
    def encrypt_session(username):
        """模拟生成动态访问令牌 (Token)"""
        timestamp = str(int(time.time()))
        token = hashlib.md5(f"{username}{timestamp}{uuid.uuid4()}".encode()).hexdigest()
        return f"TK_{token[:12]}"

class SessionVault:
    """状态流转：会话保险箱，管理登录后的生命周期"""
    _instance = None
    
    def __init__(self):
        self.active_session = None
        self.login_time = 0

    @classmethod
    def get_current(cls):
        if not cls._instance:
            cls._instance = SessionVault()
        return cls._instance

    def create_session(self, user):
        self.active_session = SecurityCore.encrypt_session(user)
        self.login_time = time.time()
        return self.active_session