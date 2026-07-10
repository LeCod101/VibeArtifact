"""
Agent 基础类型模块。

定义所有 Agent 共用的基础数据结构，包括：
- MessageSlice：对话消息切片
- AgentRunMeta：Agent 运行元信息
- AgentInput：Agent 统一输入基类
- AgentOutput：Agent 统一输出基类
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from agents.schemas.workspace import WorkspaceFileData


class MessageSlice(BaseModel):
    """
    对话消息切片，用于 Agent 上下文注入。

    每条消息包含角色、内容和可选的时间戳。
    - role: 消息角色，取值 "user" / "assistant" / "system"
    - content: 消息文本内容
    - timestamp: 消息产生的时间戳（可选）
    """

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime | None = None


class AgentRunMeta(BaseModel):
    """
    Agent 运行元信息。

    记录一次 Agent 调用的模型、token 用量、成本和延迟等指标，
    用于 cost tracking 和性能监控。
    - model: 使用的模型名称
    - provider: 模型提供商（如 "deepseek", "dashscope"）
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
    工作区文件、上游 Agent 输出、对话历史和任务描述。
    - project_id: 项目唯一标识
    - run_id: 本次运行唯一标识（可选，聊天模式下可为空）
    - workspace_files: 当前工作区的文件列表（供上下文参考）
    - upstream_outputs: 上游 Agent 的高层输出（agent_id → 输出字典）
    - conversation_context: 对话上下文消息列表（可选）
    - task_description: 本次任务的描述
    - extra: 扩展字段，用于传递额外参数
    """

    project_id: UUID
    run_id: UUID | None = None
    workspace_files: list[WorkspaceFileData] = []
    upstream_outputs: dict[str, Any] = {}
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
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    warnings: list[str] = []
    meta: AgentRunMeta | None = None
