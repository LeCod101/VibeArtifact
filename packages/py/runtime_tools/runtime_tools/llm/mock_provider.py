"""
测试用 Mock LLM Provider。

提供可预设响应的 LLM Provider 实现，
用于单元测试和集成测试，无需真实 API 调用。
"""

from __future__ import annotations

from typing import Any

from .provider import BaseLLMProvider
from .schemas import LLMRequest, LLMResponse, LLMUsage


class MockLLMProvider(BaseLLMProvider):
    """
    测试用 Mock LLM Provider。

    返回预设的固定响应，支持按模型名区分不同响应，
    并记录所有调用历史供测试断言使用。
    """

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        default_response: str = "{}",
    ):
        self._responses: dict[str, str] = responses or {}
        self._default = default_response
        self._call_history: list[LLMRequest] = []

    def _make_response(self, request: LLMRequest) -> LLMResponse:
        content = self._responses.get(request.model, self._default)
        return LLMResponse(
            content=content,
            model=request.model,
            provider="mock",
            usage=LLMUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
            ),
            latency_ms=1.0,
            cost=0.001,
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        self._call_history.append(request)
        return self._make_response(request)

    async def complete_raw(self, request: LLMRequest) -> Any:
        """返回模拟的原始响应结构（仅用于测试）。"""
        self._call_history.append(request)
        content = self._responses.get(request.model, self._default)

        class _Msg:
            def __init__(self) -> None:
                self.content = content
                self.tool_calls = None

        class _Choice:
            def __init__(self) -> None:
                self.message = _Msg()

        class _Raw:
            def __init__(self) -> None:
                self.choices = [_Choice()]
                self.model = request.model
                self.usage = type("U", (), {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                })()
                self._hidden_params = {}

        return _Raw()

    def set_response(self, content: str, model: str | None = None) -> None:
        if model:
            self._responses[model] = content
        else:
            self._default = content
