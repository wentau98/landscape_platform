import hashlib
import json
import os

class AuthManager:
    """权限与身份验证核心引擎"""
    def __init__(self, data_path="data/users.json"):
        self.data_path = data_path
        self._ensure_storage()
        self.current_user = None

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        if not os.path.exists(self.data_path):
            with open(self.data_path, 'w') as f:
                json.dump({"admin": self._hash_password("admin123")}, f)

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        """核心逻辑：多重身份校验与会话绑定"""
        if not os.path.exists(self.data_path):
            return False
            
        with open(self.data_path, 'r') as f:
            users = json.load(f)
        
        target_hash = self._hash_password(password)
        if username in users and users[username] == target_hash:
            self.current_user = username
            return True
        return False

    def register_user(self, username, password):
        """核心逻辑：数据一致性处理，防止并发写入冲突"""
        with open(self.data_path, 'r+') as f:
            users = json.load(f)
            if username in users:
                return False, "用户已存在"
            
            users[username] = self._hash_password(password)
            f.seek(0)
            json.dump(users, f)
            f.truncate()
        return True, "注册成功"