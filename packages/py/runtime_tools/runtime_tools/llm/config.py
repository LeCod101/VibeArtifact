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
    默认使用国产模型（DeepSeek），支持 DeepSeek/GLM/Qwen 及海外模型。

    Attributes:
        reasoning_model: 推理模型标识（深度思考场景）
        generation_model: 生成模型标识（代码/文档生成场景）
        default_temperature: 默认采样温度
        default_max_tokens: 默认最大生成 token 数
        api_keys: provider 环境变量名到 API 密钥值的映射
    """

    reasoning_model: str = "deepseek/deepseek-reasoner"
    generation_model: str = "deepseek/deepseek-chat"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    api_keys: dict[str, str] = {}

    key_source: str = "platform"

    # 所有已知 provider 的 API 密钥环境变量名
    _KNOWN_KEY_VARS: list[str] = [
        # 国产模型
        "DEEPSEEK_API_KEY",
        "GLM_API_KEY",
        "DASHSCOPE_API_KEY",
        # 海外模型
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "AZURE_API_KEY",
    ]

    @classmethod
    def from_env(cls) -> LLMConfig:
        """
        从环境变量构建 LLM 配置。

        支持的模型示例：
        - DeepSeek: deepseek/deepseek-chat, deepseek/deepseek-reasoner
        - 智谱 GLM: zai/glm-4, zai/glm-4.5
        - 通义千问: dashscope/qwen-max, dashscope/qwen-plus
        - Anthropic: anthropic/claude-sonnet-4-20250514
        - OpenAI: openai/gpt-4o
        """
        api_keys: dict[str, str] = {}
        for var_name in cls._KNOWN_KEY_VARS:
            value = os.environ.get(var_name, "")
            if value:
                api_keys[var_name] = value

        reasoning_model = os.environ.get(
            "REASONING_MODEL",
            "deepseek/deepseek-reasoner",
        )
        generation_model = os.environ.get(
            "GENERATION_MODEL",
            "deepseek/deepseek-chat",
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

    @classmethod
    def from_user(
        cls,
        user_api_keys: dict[str, str],
        reasoning_model: str | None = None,
        generation_model: str | None = None,
    ) -> LLMConfig:
        """
        从用户配置构建 LLM 配置，回退到环境变量。

        优先使用用户提供的 API 密钥和模型偏好，
        如果用户未配置则回退到环境变量默认值。

        参数:
            user_api_keys: 用户的 API 密钥映射（环境变量名 → 密钥值）
            reasoning_model: 用户选择的推理模型（None 时使用默认值）
            generation_model: 用户选择的生成模型（None 时使用默认值）

        返回:
            合并后的 LLMConfig 实例
        """
        # 先从环境变量获取基准配置
        env_config = cls.from_env()

        # 用户密钥覆盖环境变量密钥
        merged_keys = dict(env_config.api_keys)
        merged_keys.update(user_api_keys)

        # 判断密钥来源
        key_source = "user" if user_api_keys else "platform"

        return cls(
            reasoning_model=reasoning_model or env_config.reasoning_model,
            generation_model=generation_model or env_config.generation_model,
            default_temperature=env_config.default_temperature,
            default_max_tokens=env_config.default_max_tokens,
            api_keys=merged_keys,
            key_source=key_source,
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
