"""
LLM Provider Adapter 包。

提供统一的 LLM 调用接口，通过 LiteLLM 对接各家 LLM API。
包含数据模型、配置管理、Provider 实现和测试用 Mock。
"""

from .config import LLMConfig, ModelTier, get_model_for_tier
from .mock_provider import MockLLMProvider
from .provider import BaseLLMProvider, LiteLLMProvider
from .schemas import LLMMessage, LLMRequest, LLMResponse, LLMUsage

__all__ = [
    "BaseLLMProvider",
    "LLMConfig",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "LLMUsage",
    "LiteLLMProvider",
    "MockLLMProvider",
    "ModelTier",
    "get_model_for_tier",
]
