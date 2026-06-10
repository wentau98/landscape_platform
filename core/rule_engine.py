import uuid
from datetime import datetime

class DesignRuleEngine:
    """园林景观规范校验引擎"""
    def __init__(self):
        self.rules = []
        self._load_standard_rules()

    def _load_standard_rules(self):
        # 预载入行业标准，如绿地率、建筑退界等
        pass

    def validate_plant_spacing(self, plant_type, position, neighbors):
        """核心算法：基于植物生长习性的空间竞争冲突检测"""
        for neighbor in neighbors:
            dist = ((position[0]-neighbor[0])**2 + (position[1]-neighbor[1])**2)**0.5
            if dist < 2.5:  # 假设最小乔木间距规则
                return False, "空间生长冲突：间距小于安全阈值"
        return True, "符合规范"

class ProjectStateMachine:
    """方案状态机：处理 概念->初稿->评审->定案 的流转逻辑"""
    STATES = ['DRAFT', 'ANALYZING', 'PENDING_APPROVAL', 'APPROVED', 'LOCKED']
    
    def __init__(self, current_state='DRAFT'):
        self.current_state = current_state

    def transit_to(self, next_state, operator_role):
        """权限与状态双重校验逻辑"""
        if operator_role != 'CHIEF_DESIGNER' and next_state == 'APPROVED':
            raise PermissionError("权限不足：仅总工可核准方案")
        self.current_state = next_state
        return True