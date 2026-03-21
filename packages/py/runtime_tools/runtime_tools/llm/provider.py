"""
LLM Provider 核心实现。

定义 LLM 调用的抽象基类和基于 LiteLLM 的具体实现。
LiteLLMProvider 通过 LiteLLM 库统一对接各家 LLM API。
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Callable

from .config import LLMConfig
from .schemas import LLMRequest, LLMResponse, LLMUsage

logger = logging.getLogger(__name__)


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


class LiteLLMProvider(BaseLLMProvider):
    """
    基于 LiteLLM 的统一 LLM 调用实现。

    通过 LiteLLM 库的 acompletion 接口，
    统一对接 Anthropic、OpenAI、Google 等各家 LLM API。
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        usage_callback: Callable[[LLMResponse], None] | None = None,
    ):
        """
        初始化 LiteLLM Provider。

        参数:
            config: LLM 配置，为 None 时从环境变量自动读取
            usage_callback: 用量回调函数，每次 LLM 调用后回调（可选）
        """
        self.config = config or LLMConfig.from_env()
        self._usage_callback = usage_callback

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        调用 LiteLLM completion API。

        执行流程：
        1. 构建 LiteLLM 调用参数
        2. 调用 litellm.acompletion 异步接口
        3. 记录 token 用量、成本、耗时
        4. 包装为 LLMResponse 返回

        Args:
            request: 统一的 LLM 调用请求

        Returns:
            包含内容、用量、耗时等信息的统一响应
        """
        # 延迟导入 litellm，避免未安装时影响其他模块
        import litellm

        # 构建调用参数
        kwargs: dict = {
            "model": request.model,
            "messages": [m.model_dump() for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        # 仅在指定 response_format 时传入
        if request.response_format is not None:
            kwargs["response_format"] = request.response_format

        # 如果配置中有对应 provider 的 API Key，直接传给 litellm
        model_provider = request.model.split("/")[0] if "/" in request.model else ""
        provider_env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "azure": "AZURE_API_KEY",
        }
        env_var = provider_env_map.get(model_provider, "")
        if env_var and env_var in self.config.api_keys:
            kwargs["api_key"] = self.config.api_keys[env_var]

        # 记录开始时间
        start = time.monotonic()

        # 调用 LiteLLM 异步接口
        response = await litellm.acompletion(**kwargs)

        # 计算耗时（毫秒）
        elapsed_ms = (time.monotonic() - start) * 1000

        # 提取响应内容
        content = response.choices[0].message.content or ""

        # 提取 token 用量
        usage = response.usage
        llm_usage = LLMUsage(
            prompt_tokens=getattr(usage, "prompt_tokens", 0),
            completion_tokens=getattr(usage, "completion_tokens", 0),
            total_tokens=getattr(usage, "total_tokens", 0),
        )

        # 提取 provider 信息和成本
        hidden_params = getattr(response, "_hidden_params", {}) or {}
        provider_name = hidden_params.get("custom_llm_provider", "")
        response_cost = hidden_params.get("response_cost", 0.0)

        llm_response = LLMResponse(
            content=content,
            model=response.model or request.model,
            provider=provider_name,
            usage=llm_usage,
            latency_ms=elapsed_ms,
            cost=response_cost,
        )

        # 调用用量回调（如果配置了）
        if self._usage_callback is not None:
            try:
                self._usage_callback(llm_response)
            except Exception as exc:
                logger.warning("用量回调执行失败: %s", exc)

        return llm_response
