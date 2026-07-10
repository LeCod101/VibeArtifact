"""
模型路由配置。

管理 LLM 模型选择与 API 密钥配置，
支持按模型档位（推理型/生成型）自动路由到国产模型。
"""

from __future__ import annotations

import os
from enum import StrEnum

from pydantic import BaseModel

# provider 名称 -> API Key 环境变量名
_PROVIDER_KEY_ENV_VARS: dict[str, str] = {
    "deepseek": "DEEPSEEK_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",  # 通义千问
    "moonshot": "MOONSHOT_API_KEY",  # Kimi
    "minimax": "MINIMAX_API_KEY",
}

# provider 名称 -> 自定义 endpoint 环境变量名（可选覆盖）
_PROVIDER_BASE_ENV_VARS: dict[str, str] = {
    p: f"{p.upper()}_API_BASE" for p in _PROVIDER_KEY_ENV_VARS
}


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

    从环境变量读取模型选择和 API 密钥配置。不写死任何厂商默认值——
    推理型/生成型的 provider 和 model 均需显式配置，未配置时留空，
    调用时报错提示用户设置对应环境变量。

    Attributes:
        reasoning_provider: 推理型 provider 名称（如 "deepseek"）
        reasoning_model: 推理型模型标识（如 "deepseek-chat"）
        generation_provider: 生成型 provider 名称
        generation_model: 生成型模型标识
        default_temperature: 默认采样温度
        default_max_tokens: 默认最大生成 token 数
        api_keys: provider 名称到 API 密钥的映射
        api_base: provider 名称到自定义 endpoint 的映射（可选覆盖）
    """

    reasoning_provider: str = ""
    reasoning_model: str = ""
    generation_provider: str = ""
    generation_model: str = ""
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    api_keys: dict[str, str] = {}
    api_base: dict[str, str] = {}

    @classmethod
    def from_env(cls) -> LLMConfig:
        """
        从环境变量构建 LLM 配置。

        读取以下环境变量：
        - REASONING_PROVIDER / REASONING_MODEL: 推理型 provider + 模型标识
        - GENERATION_PROVIDER / GENERATION_MODEL: 生成型 provider + 模型标识
        - DEFAULT_TEMPERATURE: 默认采样温度
        - DEFAULT_MAX_TOKENS: 默认最大 token 数
        - DEEPSEEK_API_KEY / DASHSCOPE_API_KEY / MOONSHOT_API_KEY / MINIMAX_API_KEY
        - <PROVIDER>_API_BASE（可选，自定义 endpoint 覆盖）

        Returns:
            从环境变量填充的 LLMConfig 实例
        """
        api_keys: dict[str, str] = {}
        for provider, var_name in _PROVIDER_KEY_ENV_VARS.items():
            value = os.environ.get(var_name, "")
            if value:
                api_keys[provider] = value

        api_base: dict[str, str] = {}
        for provider, var_name in _PROVIDER_BASE_ENV_VARS.items():
            value = os.environ.get(var_name, "")
            if value:
                api_base[provider] = value

        default_temperature = float(
            os.environ.get("DEFAULT_TEMPERATURE", "0.7"),
        )
        default_max_tokens = int(
            os.environ.get("DEFAULT_MAX_TOKENS", "4096"),
        )

        return cls(
            reasoning_provider=os.environ.get("REASONING_PROVIDER", ""),
            reasoning_model=os.environ.get("REASONING_MODEL", ""),
            generation_provider=os.environ.get("GENERATION_PROVIDER", ""),
            generation_model=os.environ.get("GENERATION_MODEL", ""),
            default_temperature=default_temperature,
            default_max_tokens=default_max_tokens,
            api_keys=api_keys,
            api_base=api_base,
        )


def get_model_for_tier(config: LLMConfig, tier: ModelTier) -> tuple[str, str]:
    """
    根据模型档位返回对应的 (provider, model) 二元组。

    不做"是否已配置"的校验——留空的 provider/model 会在实际构造
    LangChain ChatModel 时（chat_model_factory.get_chat_model）报错，
    这样测试可以用空档位的 LLMConfig() 搭配 mock provider 而不必报错。

    Args:
        config: LLM 配置实例
        tier: 模型档位（推理型或生成型）

    Returns:
        (provider, model) 二元组，未配置时为空字符串

    Raises:
        ValueError: 未知的模型档位
    """
    if tier == ModelTier.REASONING:
        return config.reasoning_provider, config.reasoning_model
    if tier == ModelTier.GENERATION:
        return config.generation_provider, config.generation_model
    raise ValueError(f"未知的模型档位: {tier}")
