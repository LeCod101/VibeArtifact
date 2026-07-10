"""
LLM Provider 核心实现。

定义 LLM 调用的抽象基类和基于 LangChain 的具体实现。
LangChainProvider 通过 chat_model_factory 构造对应国产模型的
LangChain ChatModel 并调用，统一对接 DeepSeek、通义千问（DashScope）、
Moonshot（Kimi）、MiniMax 等国产模型。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from .chat_model_factory import get_chat_model
from .config import LLMConfig
from .schemas import LLMRequest, LLMResponse, LLMUsage


class BaseLLMProvider(ABC):
    """
    LLM 调用的抽象基类。

    所有 LLM Provider 实现都必须继承此类，
    并实现 complete 方法。
    """

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        调用 LLM 并返回响应。

        Args:
            request: 统一的 LLM 调用请求

        Returns:
            统一的 LLM 调用响应
        """
        ...


class LangChainProvider(BaseLLMProvider):
    """
    基于 LangChain 的统一 LLM 调用实现。

    通过 chat_model_factory 按 provider 名称构造对应的 LangChain
    ChatModel（DeepSeek/Moonshot/DashScope/MiniMax），调用后手工计算成本
    （LangChain 原生集成不像 LiteLLM 那样自带价格表，见 cost.pricing）。
    """

    def __init__(self, config: LLMConfig | None = None):
        """
        初始化 LangChain Provider。

        Args:
            config: LLM 配置，为 None 时从环境变量自动读取
        """
        self.config = config or LLMConfig.from_env()

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        调用 LangChain ChatModel 完成一次请求。

        执行流程：
        1. 从 request.model（"provider/model" 格式）解析出 provider 和 model
        2. 通过 chat_model_factory 构造 ChatModel
        3. 调用 ainvoke 获取 AIMessage
        4. 提取内容、usage_metadata，通过 pricing 计算成本
        5. 包装为 LLMResponse 返回

        Args:
            request: 统一的 LLM 调用请求，request.model 格式为 "provider/model"

        Returns:
            包含内容、用量、耗时等信息的统一响应
        """
        from runtime_tools.cost.pricing import calculate_cost

        provider, model = request.model.split("/", 1)

        chat_model = get_chat_model(
            provider=provider,
            model=model,
            api_key=self.config.api_keys.get(provider, ""),
            api_base=self.config.api_base.get(provider),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # 转换为 LangChain 消息对象
        from langchain_core.messages import HumanMessage, SystemMessage

        role_to_message = {
            "system": SystemMessage,
            "user": HumanMessage,
        }
        lc_messages = [
            role_to_message.get(m.role, HumanMessage)(content=m.content)
            for m in request.messages
        ]

        start = time.monotonic()
        ai_message = await chat_model.ainvoke(lc_messages)
        elapsed_ms = (time.monotonic() - start) * 1000

        content = ai_message.content if isinstance(ai_message.content, str) else str(ai_message.content)

        usage_metadata = getattr(ai_message, "usage_metadata", None) or {}
        prompt_tokens = usage_metadata.get("input_tokens", 0)
        completion_tokens = usage_metadata.get("output_tokens", 0)
        llm_usage = LLMUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=usage_metadata.get(
                "total_tokens", prompt_tokens + completion_tokens,
            ),
        )

        cost = calculate_cost(provider, model, prompt_tokens, completion_tokens)

        return LLMResponse(
            content=content,
            model=model,
            provider=provider,
            usage=llm_usage,
            latency_ms=elapsed_ms,
            cost=cost,
        )
