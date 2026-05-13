"""
长期优化模块
包含运行时保证、长期一致性保证等功能
"""

from .runtime_guarantee_system import RuntimeGuaranteeSystem
from .long_term_consistency_system import LongTermConsistencySystem

__all__ = [
    'RuntimeGuaranteeSystem',
    'LongTermConsistencySystem'
]
