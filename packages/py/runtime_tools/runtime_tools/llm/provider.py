"""
LLM Provider 核心实现。

定义 LLM 调用的抽象基类和基于 LiteLLM 的具体实现。
LiteLLMProvider 通过 LiteLLM 库统一对接各家 LLM API。
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable

from .config import LLMConfig
from .schemas import LLMRequest, LLMResponse, LLMToolCall, LLMUsage

logger = logging.getLogger(__name__)

_PROVIDER_ENV_MAP: dict[str, str] = {
    # 国产模型
    "deepseek": "DEEPSEEK_API_KEY",
    "zai": "GLM_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    # 海外模型
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "azure": "AZURE_API_KEY",
}


class BaseLLMProvider(ABC):
    """
    LLM 调用的抽象基类。

    所有 LLM Provider 实现都必须继承此类，
    并实现 complete 和 complete_raw 方法。
    """

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """调用 LLM 并返回统一响应。"""
        ...

    @abstractmethod
    async def complete_raw(self, request: LLMRequest) -> Any:
        """调用 LLM 并返回原始响应对象（含 choices[0].message 结构）。

        供 Agent 工具循环使用，需要完整的 tool_calls 信息。
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
        self.config = config or LLMConfig.from_env()
        self._usage_callback = usage_callback

    def _build_kwargs(self, request: LLMRequest) -> dict[str, Any]:
        """从 LLMRequest 构建 litellm.acompletion 参数字典。"""
        # raw_messages 优先（工具循环中包含 tool/assistant+tool_calls 等复杂角色）
        if request.raw_messages is not None:
            msgs = request.raw_messages
        else:
            msgs = [m.model_dump() for m in request.messages]

        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": msgs,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.response_format is not None:
            kwargs["response_format"] = request.response_format

        if request.tools:
            kwargs["tools"] = request.tools
        if request.tool_choice:
            kwargs["tool_choice"] = request.tool_choice

        model_provider = request.model.split("/")[0] if "/" in request.model else ""
        env_var = _PROVIDER_ENV_MAP.get(model_provider, "")
        if env_var and env_var in self.config.api_keys:
            kwargs["api_key"] = self.config.api_keys[env_var]

        return kwargs

    async def complete_raw(self, request: LLMRequest) -> Any:
        """调用 litellm 并返回原始响应。

        供 Agent 工具调用循环使用，保留完整的
        ``choices[0].message.tool_calls`` 结构。
        """
        import litellm

        kwargs = self._build_kwargs(request)
        return await litellm.acompletion(**kwargs)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """调用 litellm 并返回统一封装的 LLMResponse。"""
        import litellm

        kwargs = self._build_kwargs(request)
        start = time.monotonic()
        response = await litellm.acompletion(**kwargs)
        elapsed_ms = (time.monotonic() - start) * 1000

        choice = response.choices[0] if response.choices else None
        msg = choice.message if choice else None

        content = getattr(msg, "content", "") or ""

        # 提取 tool_calls
        raw_tool_calls = getattr(msg, "tool_calls", None)
        tool_calls: list[LLMToolCall] | None = None
        if raw_tool_calls:
            tool_calls = [
                LLMToolCall(
                    id=tc.id,
                    function_name=tc.function.name,
                    function_arguments=tc.function.arguments,
                )
                for tc in raw_tool_calls
            ]

        usage = response.usage
        llm_usage = LLMUsage(
            prompt_tokens=getattr(usage, "prompt_tokens", 0),
            completion_tokens=getattr(usage, "completion_tokens", 0),
            total_tokens=getattr(usage, "total_tokens", 0),
        )

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
            tool_calls=tool_calls,
        )

        if self._usage_callback is not None:
            try:
                self._usage_callback(llm_response)
            except Exception as exc:
                logger.warning("用量回调执行失败: %s", exc)

        return llm_response
