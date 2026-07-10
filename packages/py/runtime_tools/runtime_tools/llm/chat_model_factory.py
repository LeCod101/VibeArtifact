"""
LangChain ChatModel 工厂模块。

按 provider 名称构造对应的 LangChain ChatModel 实例，
统一封装国产模型的接入方式。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

# DashScope（通义千问）OpenAI 兼容模式默认 endpoint
_DASHSCOPE_DEFAULT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
# MiniMax OpenAI 兼容模式默认 endpoint（国内 minimaxi.com 域名；
# 海外版为 api.minimax.io，可通过 api_base 覆盖）
_MINIMAX_DEFAULT_BASE = "https://api.minimaxi.com/v1"

_OPENAI_COMPATIBLE_DEFAULTS: dict[str, str] = {
    "dashscope": _DASHSCOPE_DEFAULT_BASE,
    "minimax": _MINIMAX_DEFAULT_BASE,
}


def get_chat_model(
    provider: str,
    model: str,
    api_key: str,
    api_base: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> BaseChatModel:
    """
    按 provider 名称构造 LangChain ChatModel 实例。

    - deepseek: 官方 langchain-deepseek 集成（ChatDeepSeek）
    - moonshot: 官方 langchain-moonshot 集成（ChatMoonshot）
    - dashscope（通义千问）/ minimax: 均走 OpenAI 兼容模式
      （ChatOpenAI + 自定义 base_url），因为它们没有可靠维护的
      LangChain 原生集成（langchain-community 的 ChatTongyi 已标注 sunset）

    - provider: provider 名称（deepseek/dashscope/moonshot/minimax）
    - model: 模型标识
    - api_key: API 密钥
    - api_base: 自定义 endpoint，为 None 时对 openai 兼容 provider 使用默认值
    - temperature: 采样温度
    - max_tokens: 最大生成 token 数
    - 返回: BaseChatModel 实例

    Raises:
        ValueError: 不支持的 provider 名称
    """
    if provider == "deepseek":
        from langchain_deepseek import ChatDeepSeek

        return ChatDeepSeek(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "moonshot":
        from langchain_moonshot import ChatMoonshot

        return ChatMoonshot(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider in _OPENAI_COMPATIBLE_DEFAULTS:
        from langchain_openai import ChatOpenAI

        base_url = api_base or _OPENAI_COMPATIBLE_DEFAULTS[provider]
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise ValueError(
        f"不支持的 LLM provider: '{provider}'，"
        f"目前支持: deepseek, moonshot, dashscope, minimax"
    )
