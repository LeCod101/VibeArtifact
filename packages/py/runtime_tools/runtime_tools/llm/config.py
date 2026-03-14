"""
模型路由配置。

管理 LLM 模型选择与 API 密钥配置，
支持按模型档位（推理型/生成型）自动路由。
"""

from __future__ import annotations

import os
from enum import StrEnum

from pydantic import BaseModel


class ModelTier(StrEnum):
    """
    模型档位枚举。

    - REASONING: 推理型，用于 planning/intent/contraction/schema/qa 等需要深度思考的任务
    - GENERATION: 生成型，用于 backend/frontend/doc/diagram/export 等内容生成任务
    """

    REASONING = "reasoning"
    GENERATION = "generation"


class LLMConfig(BaseModel):
    """
    LLM 配置模型。

    从环境变量读取模型选择和 API 密钥配置。

    Attributes:
        reasoning_model: 推理模型标识
        generation_model: 生成模型标识
        default_temperature: 默认采样温度
        default_max_tokens: 默认最大生成 token 数
        api_keys: provider 名称到 API 密钥的映射
    """

    reasoning_model: str = "anthropic/claude-sonnet-4-20250514"
    generation_model: str = "anthropic/claude-sonnet-4-20250514"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    api_keys: dict[str, str] = {}

    @classmethod
    def from_env(cls) -> LLMConfig:
        """
        从环境变量构建 LLM 配置。

        读取以下环境变量：
        - REASONING_MODEL: 推理模型标识
        - GENERATION_MODEL: 生成模型标识
        - DEFAULT_TEMPERATURE: 默认采样温度
        - DEFAULT_MAX_TOKENS: 默认最大 token 数
        - ANTHROPIC_API_KEY: Anthropic API 密钥
        - OPENAI_API_KEY: OpenAI API 密钥

        Returns:
            从环境变量填充的 LLMConfig 实例
        """
        # 收集所有已知 provider 的 API 密钥
        api_keys: dict[str, str] = {}

        # 遍历已知的 provider 密钥环境变量名
        known_key_vars = [
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "AZURE_API_KEY",
        ]
        for var_name in known_key_vars:
            value = os.environ.get(var_name, "")
            if value:
                api_keys[var_name] = value

        # 读取模型配置，未设置时使用默认值
        reasoning_model = os.environ.get(
            "REASONING_MODEL",
            "anthropic/claude-sonnet-4-20250514",
        )
        generation_model = os.environ.get(
            "GENERATION_MODEL",
            "anthropic/claude-sonnet-4-20250514",
        )

        # 读取默认参数
        default_temperature = float(
            os.environ.get("DEFAULT_TEMPERATURE", "0.7"),
        )
        default_max_tokens = int(
            os.environ.get("DEFAULT_MAX_TOKENS", "4096"),
        )

        return cls(
            reasoning_model=reasoning_model,
            generation_model=generation_model,
            default_temperature=default_temperature,
            default_max_tokens=default_max_tokens,
            api_keys=api_keys,
        )


def get_model_for_tier(config: LLMConfig, tier: ModelTier) -> str:
    """
    根据模型档位返回对应的模型标识。

    Args:
        config: LLM 配置实例
        tier: 模型档位（推理型或生成型）

    Returns:
        对应档位的模型标识字符串

    Raises:
        ValueError: 未知的模型档位
    """
    if tier == ModelTier.REASONING:
        return config.reasoning_model
    if tier == ModelTier.GENERATION:
        return config.generation_model
    raise ValueError(f"未知的模型档位: {tier}")
