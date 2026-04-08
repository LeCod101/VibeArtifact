"""测试公共 fixtures。"""

from __future__ import annotations

import sys
import types
from typing import Any
from unittest.mock import AsyncMock

import pytest
from runtime_tools.llm.config import LLMConfig
from runtime_tools.llm.provider import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """测试用 LLM Provider，不依赖真实 API。"""

    def __init__(self) -> None:
        self.config = LLMConfig(
            reasoning_model="mock/test-model",
            generation_model="mock/test-model",
            api_keys={},
        )
        self.mock_complete = AsyncMock()

    async def complete(self, request: Any) -> Any:
        return await self.mock_complete(request)


@pytest.fixture
def mock_provider() -> MockLLMProvider:
    """提供一个 mock LLM provider。"""
    return MockLLMProvider()


@pytest.fixture
def fresh_registry():
    """提供一个干净的 ToolRegistry，绕过单例模式以避免测试污染。"""
    from agents.tools import ToolRegistry

    registry = object.__new__(ToolRegistry)
    registry._tools = {}
    return registry


@pytest.fixture
def mock_litellm(monkeypatch):
    """Mock litellm 模块，避免真实 API 调用。"""
    fake_litellm = types.ModuleType("litellm")
    fake_litellm.acompletion = AsyncMock()
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)
    return fake_litellm
