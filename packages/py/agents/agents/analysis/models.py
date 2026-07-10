"""
影响分析数据模型模块。

定义影响分析系统所需的数据结构：
- ChangeScope: 变更范围枚举（全量/局部/表面）
- ImpactReport: 影响分析报告（ImpactAnalyzer 的输出）
- ChangeSummary: 变更摘要（返回给用户的最终结果）
"""

from enum import StrEnum

from pydantic import BaseModel


class ChangeScope(StrEnum):
    """
    变更范围枚举。

    描述本次用户请求对项目的影响范围：
    - FULL: 全量重建（冷启动、重大需求变更）
    - PARTIAL: 局部修改（只影响部分产物）
    - COSMETIC: 表面修改（文案、样式、配置微调）
    """

    FULL = "full"
    PARTIAL = "partial"
    COSMETIC = "cosmetic"


class ImpactReport(BaseModel):
    """
    影响分析报告。

    由 ImpactAnalyzer 生成，描述用户消息对项目的影响：
    - change_scope: 变更范围（FULL/PARTIAL/COSMETIC）
    - requires_cold_start: 是否需要冷启动（工作区为空时）
    - affected_areas: 受影响的产物领域列表
    - affected_agents: 需要执行的 Agent 列表
    - reasoning: 分析推理过程（便于调试）
    - user_intent_summary: 用户意图摘要（截取前 100 字符）
    """

    change_scope: ChangeScope
    requires_cold_start: bool
    affected_areas: list[str] = []
    affected_agents: list[str]
    reasoning: str
    user_intent_summary: str


class ChangeSummary(BaseModel):
    """
    变更摘要（返回给用户）。

    Agent 执行完成后，汇总本次变更的结果：
    - summary: 变更描述
    - affected_areas: 受影响的功能区域
    - operations_count: 本次产生/更新的输出对象数量（文件 + 决策输出）
    - agents_executed: 实际执行的 Agent 列表
    - warnings: 警告信息列表
    """

    summary: str
    affected_areas: list[str]
    operations_count: int
    agents_executed: list[str]
    warnings: list[str] = []
