"""
设置相关的请求和响应 Schema。

包含 API 密钥管理、模型偏好、用量统计等数据结构。
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ──────────────────────────────────────
# API 密钥相关
# ──────────────────────────────────────

class ApiKeyCreateRequest(BaseModel):
    """
    添加/更新 API 密钥请求。

    字段:
        provider: 提供商标识（anthropic / openai / google / azure）
        api_key: 明文 API 密钥（仅在请求中传输，不会存储明文）
        display_label: 用户自定义标签（可选）
    """

    provider: str = Field(..., pattern=r"^(anthropic|openai|google|azure)$")
    api_key: str = Field(..., min_length=1, max_length=500)
    display_label: str | None = None


class ApiKeyResponse(BaseModel):
    """
    API 密钥响应（掩码显示，不返回明文）。

    字段:
        id: 密钥记录 ID
        provider: 提供商标识
        masked_key: 掩码后的密钥
        display_label: 用户自定义标签
        is_active: 是否启用
        is_valid: 是否通过验证
        last_validated_at: 上次验证时间
        created_at: 创建时间
    """

    id: UUID
    provider: str
    masked_key: str
    display_label: str | None
    is_active: bool
    is_valid: bool | None
    last_validated_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyValidateResponse(BaseModel):
    """
    密钥验证结果响应。

    字段:
        key_id: 密钥记录 ID
        provider: 提供商
        is_valid: 验证结果
        message: 验证消息
    """

    key_id: UUID
    provider: str
    is_valid: bool
    message: str


# ──────────────────────────────────────
# 模型偏好相关
# ──────────────────────────────────────

class ModelPreferenceRequest(BaseModel):
    """
    更新模型偏好请求。

    字段:
        reasoning_model: 推理模型标识（可选）
        generation_model: 生成模型标识（可选）
    """

    reasoning_model: str | None = None
    generation_model: str | None = None


class ModelPreferenceResponse(BaseModel):
    """
    模型偏好响应。

    字段:
        reasoning_model: 推理模型标识
        generation_model: 生成模型标识
    """

    reasoning_model: str | None
    generation_model: str | None

    model_config = {"from_attributes": True}


# ──────────────────────────────────────
# 用量统计相关
# ──────────────────────────────────────

class ProviderUsageSummary(BaseModel):
    """
    按提供商汇总的用量。

    字段:
        provider: 提供商标识
        total_prompt_tokens: 总输入 token
        total_completion_tokens: 总输出 token
        total_cost: 总费用
        call_count: 调用次数
    """

    provider: str
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost: float
    call_count: int


class UsageSummaryResponse(BaseModel):
    """
    用量汇总响应（30 天）。

    字段:
        total_prompt_tokens: 总输入 token
        total_completion_tokens: 总输出 token
        total_cost: 总费用
        call_count: 总调用次数
        by_provider: 按提供商分组的用量
    """

    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost: float
    call_count: int
    by_provider: list[ProviderUsageSummary]


# ──────────────────────────────────────
# 可用模型相关
# ──────────────────────────────────────

class AvailableModel(BaseModel):
    """
    可用模型条目。

    字段:
        id: 模型标识（如 anthropic/claude-sonnet-4-20250514）
        name: 模型显示名称
        provider: 提供商标识
        tier: 模型档位（reasoning / generation / both）
    """

    id: str
    name: str
    provider: str
    tier: str
