"""
测试用 Mock LLM Provider。

提供可预设响应的 LLM Provider 实现，
用于单元测试和集成测试，无需真实 API 调用。
"""

from __future__ import annotations

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
        """
        初始化 Mock Provider。

        Args:
            responses: 模型名到响应内容的映射，按 model 区分返回不同内容
            default_response: 默认响应内容，当 responses 中无对应 model 时使用
        """
        self._responses: dict[str, str] = responses or {}
        self._default = default_response
        # 记录所有调用请求，供测试断言使用
        self._call_history: list[LLMRequest] = []

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        返回预设的 Mock 响应。

        将请求记录到调用历史中，然后返回预设的响应内容。
        如果 responses 中有对应 model 的预设，则返回该预设；
        否则返回 default_response。

        Args:
            request: 统一的 LLM 调用请求

        Returns:
            预设的 Mock 响应
        """
        # 记录调用历史
        self._call_history.append(request)

        # 按 model 查找预设响应，找不到则用默认值
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

    def set_response(self, content: str, model: str | None = None) -> None:
        """
        设置 Mock 响应内容。

        可以设置全局默认响应，也可以按 model 设置特定响应。

        Args:
            content: 要返回的响应内容
            model: 指定 model 名称；为 None 时设置默认响应
        """
        if model:
            self._responses[model] = content
        else:
            self._default = content
