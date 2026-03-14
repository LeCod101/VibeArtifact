"""
LLM 请求/响应数据结构。

定义统一的 LLM 调用接口数据模型，
所有 Provider 实现都基于这些 schema 进行输入输出。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """
    LLM 对话消息。

    Attributes:
        role: 消息角色，取值 "system" | "user" | "assistant"
        content: 消息文本内容
    """

    role: str
    content: str


class LLMRequest(BaseModel):
    """
    统一 LLM 调用请求。

    封装发送给 LLM Provider 的所有参数，
    与具体 Provider 实现无关。

    Attributes:
        messages: 对话消息列表
        model: LiteLLM 模型标识，如 "anthropic/claude-sonnet-4-20250514"
        temperature: 采样温度，控制输出随机性
        max_tokens: 最大生成 token 数
        response_format: JSON schema，structured output 时使用
        metadata: 透传元数据，如 agent_id、project_id 等
    """

    messages: list[LLMMessage]
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    response_format: dict | None = None
    metadata: dict[str, Any] = {}


class LLMUsage(BaseModel):
    """
    LLM 调用用量统计。

    Attributes:
        prompt_tokens: 输入 token 数
        completion_tokens: 输出 token 数
        total_tokens: 总 token 数
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """
    统一 LLM 调用响应。

    封装 LLM Provider 返回的所有信息，
    包括内容、用量、耗时、成本等。

    Attributes:
        content: 模型返回的文本内容
        model: 实际使用的模型标识
        provider: 实际使用的 provider 名称
        usage: token 用量统计
        latency_ms: 调用耗时（毫秒）
        cost: 本次调用成本（美元）
        raw_response: 原始响应，调试用
    """

    content: str
    model: str
    provider: str = ""
    usage: LLMUsage = LLMUsage()
    latency_ms: float = 0.0
    cost: float = 0.0
    raw_response: dict | None = None
