"""测试 VibeArtifact Agent（mock LLM）。"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest


def _make_text_response(text: str) -> SimpleNamespace:
    """构造一个不含 tool_calls 的 LLM 响应。"""
    msg = SimpleNamespace(content=text, tool_calls=None)
    choice = SimpleNamespace(message=msg)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    return SimpleNamespace(choices=[choice], usage=usage, model="mock/test-model", _hidden_params={})


def _make_tool_call_response(tool_name: str, arguments: dict) -> SimpleNamespace:
    """构造一个包含 tool_calls 的 LLM 响应。"""
    func = SimpleNamespace(name=tool_name, arguments=json.dumps(arguments))
    tc = SimpleNamespace(id="call_001", function=func)
    msg = SimpleNamespace(content="", tool_calls=[tc])
    choice = SimpleNamespace(message=msg)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    return SimpleNamespace(choices=[choice], usage=usage, model="mock/test-model", _hidden_params={})


class TestVibeArtifactAgent:
    """验证 Agent 的对话、工具调用和 SSE 事件流。"""

    @pytest.fixture(autouse=True)
    def _setup(self, mock_provider, mock_litellm) -> None:
        self.mock_litellm = mock_litellm
        self.provider = mock_provider
        from agents.agent import VibeArtifactAgent

        self.agent = VibeArtifactAgent(llm_provider=self.provider)

    async def _collect_events(self, **chat_kwargs: Any) -> list[dict[str, Any]]:
        """调用 chat 并收集全部 SSE 事件。"""
        events: list[dict[str, Any]] = []
        async for event in self.agent.chat(**chat_kwargs):
            events.append(event)
        return events

    async def test_simple_conversation(self) -> None:
        """无 tool_calls 时应返回 thinking -> content -> done。"""
        self.mock_litellm.acompletion.return_value = _make_text_response("你好！")

        events = await self._collect_events(user_message="你好", conversation_history=[])

        event_types = [e["event"] for e in events]
        assert event_types == ["thinking", "content", "done"]
        assert events[1]["data"]["content"] == "你好！"

    async def test_tool_call_flow(self) -> None:
        """LLM 返回 tool_call 后应执行工具，再次调用 LLM 获取最终回复。"""
        self.mock_litellm.acompletion.side_effect = [
            _make_tool_call_response("explain_code", {"code": "x=1", "language": "python"}),
            _make_text_response("这段代码将 1 赋值给变量 x。"),
        ]

        events = await self._collect_events(user_message="解释这段代码: x=1", conversation_history=[])

        event_types = [e["event"] for e in events]
        assert "tool_call" in event_types
        assert "tool_result" in event_types
        assert event_types[-1] == "done"

        # 验证 tool_call 事件数据
        tc_event = next(e for e in events if e["event"] == "tool_call")
        assert tc_event["data"]["tool"] == "explain_code"

    async def test_sse_event_order(self) -> None:
        """SSE 事件应按 thinking -> tool_call -> tool_result -> thinking -> content -> done 排列。"""
        self.mock_litellm.acompletion.side_effect = [
            _make_tool_call_response("web_search", {"query": "pytest"}),
            _make_text_response("搜索完成。"),
        ]

        events = await self._collect_events(user_message="搜索 pytest", conversation_history=[])

        event_types = [e["event"] for e in events]
        assert event_types == ["thinking", "tool_call", "tool_result", "thinking", "content", "done"]

    async def test_max_tool_rounds(self) -> None:
        """工具调用超过 _MAX_TOOL_ROUNDS 轮时应停止并给出提示。"""
        self.mock_litellm.acompletion.return_value = _make_tool_call_response("web_search", {"query": "loop"})

        events = await self._collect_events(user_message="无限循环", conversation_history=[])

        event_types = [e["event"] for e in events]
        assert event_types[-1] == "done"

        content_events = [e for e in events if e["event"] == "content"]
        assert len(content_events) == 1
        assert "最大工具调用轮次" in content_events[0]["data"]["content"]

        # 应恰好调用 10 轮 LLM
        assert self.mock_litellm.acompletion.call_count == 10
