"""
影响分析系统模块。

提供用户消息的影响分析、Agent 选择和冷启动引导功能：
- ImpactAnalyzer: 分析用户消息对 IR 图的影响（纯规则匹配）
- AgentSelector: 根据影响报告生成分层执行计划
- ImpactReport: 影响分析报告数据结构
- ChangeSummary: 变更摘要数据结构（返回给用户）
- ChangeScope: 变更范围枚举
- ColdStartBootstrap: 项目 IR 为空时执行最小 Agent 链路
- ColdStartResult: 冷启动执行结果
"""

from agents.analysis.agent_selector import AgentSelector
from agents.analysis.cold_start import ColdStartBootstrap, ColdStartResult
from agents.analysis.impact_analyzer import ImpactAnalyzer
from agents.analysis.models import ChangeSummary, ChangeScope, ImpactReport

__all__ = [
    "ImpactAnalyzer",
    "ImpactReport",
    "AgentSelector",
    "ChangeSummary",
    "ChangeScope",
    "ColdStartBootstrap",
    "ColdStartResult",
]
