"""
Agent 基础类型模块。

定义所有 Agent 共用的基础数据结构，包括：
- MessageSlice：对话消息切片
- AgentRunMeta：Agent 运行元信息
- AgentInput：Agent 统一输入基类
- AgentOutput：Agent 统一输出基类
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from ir_core.schema.data import IREdgeData, IRNodeData
from pydantic import BaseModel


class MessageSlice(BaseModel):
    """
    对话消息切片，用于 Agent 上下文注入。

    每条消息包含角色、内容和可选的时间戳。
    - role: 消息角色，取值 "user" / "assistant" / "system"
    - content: 消息文本内容
    - timestamp: 消息产生的时间戳（可选）
    """

    role: str
    content: str
    timestamp: datetime | None = None


class AgentRunMeta(BaseModel):
    """
    Agent 运行元信息。

    记录一次 Agent 调用的模型、token 用量、成本和延迟等指标，
    用于 cost tracking 和性能监控。
    - model: 使用的模型名称
    - provider: 模型提供商（如 "openai", "anthropic"）
    - prompt_tokens: 输入 token 数
    - completion_tokens: 输出 token 数
    - total_cost: 本次调用的总费用（美元）
    - latency_ms: 调用耗时（毫秒）
    """

    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    latency_ms: float = 0.0


class AgentInput(BaseModel):
    """
    Agent 统一输入基类。

    所有具体 Agent 的输入类型都继承此基类。包含项目上下文、
    IR 快照数据、对话历史和任务描述。
    - project_id: 项目唯一标识
    - snapshot_id: 当前快照唯一标识
    - ir_nodes: 当前快照的节点列表
    - ir_edges: 当前快照的边列表
    - conversation_context: 对话上下文消息列表（可选）
    - task_description: 本次任务的描述
    - extra: 扩展字段，用于传递额外参数
    """

    project_id: UUID
    snapshot_id: UUID
    ir_nodes: list[IRNodeData]
    ir_edges: list[IREdgeData]
    conversation_context: list[MessageSlice] = []
    task_description: str
    extra: dict[str, Any] = {}


class AgentOutput(BaseModel):
    """
    Agent 统一输出基类。

    所有具体 Agent 的输出类型都继承此基类。包含推理摘要、
    置信度、警告信息和运行元信息。
    - reasoning: 推理过程摘要
    - confidence: 0-1 之间的置信度
    - warnings: 警告信息列表
    - meta: Agent 运行元信息（可选）
    """

    reasoning: str
    confidence: float
    warnings: list[str] = []
    meta: AgentRunMeta | None = None
