"""
LLM Provider Adapter 包。

提供统一的 LLM 调用接口，通过 LangChain 原生集成对接国产 LLM API
（DeepSeek/通义千问/Moonshot/MiniMax）。包含数据模型、配置管理、
Provider 实现和测试用 Mock。
"""

from .chat_model_factory import get_chat_model
from .config import LLMConfig, ModelTier, get_model_for_tier
from .mock_provider import MockLLMProvider
from .provider import BaseLLMProvider, LangChainProvider
from .schemas import LLMMessage, LLMRequest, LLMResponse, LLMUsage

__all__ = [
    "BaseLLMProvider",
    "LLMConfig",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "LLMUsage",
    "LangChainProvider",
    "MockLLMProvider",
    "ModelTier",
    "get_chat_model",
    "get_model_for_tier",
]
