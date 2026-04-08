"""VibeArtifact Agent 主类。

单一 Agent，通过 System Prompt 获得能力，通过 Tools 与外部系统交互。
参考 Anything.com 的架构设计。
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from runtime_tools.cost.tracker import CostTracker
from runtime_tools.llm.config import LLMConfig
from runtime_tools.llm.provider import BaseLLMProvider

from agents.modes import AgentMode, ModeConfig, get_mode_config
from agents.system_prompt import SystemPromptBuilder
from agents.tool_executor import ToolExecutor, ToolResult
from agents.tools import ToolRegistry

logger = logging.getLogger(__name__)

# 单轮对话中最多执行的工具调用轮数，防止无限循环
_MAX_TOOL_ROUNDS = 10


class VibeArtifactAgent:
    """VibeArtifact 核心 Agent。

    接收用户消息，通过 LLM + 工具循环产出流式 SSE 事件。
    每轮对话流程：
        1. 组装 messages（system prompt + history + user message）
        2. 调用 LLM（带 tools）
        3. 若 LLM 返回 tool_calls → 执行工具 → 将结果追加到 messages → 回到 2
        4. 若无 tool_calls → 输出文本内容 → 结束
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self._provider = llm_provider
        self._cost_tracker = cost_tracker
        self._registry = ToolRegistry()
        self._executor = ToolExecutor(self._registry)
        self._prompt_builder = SystemPromptBuilder()

        # 从 provider 获取配置；若 provider 没有 config 属性则回退到环境变量
        self._config: LLMConfig = getattr(llm_provider, "config", None) or LLMConfig.from_env()

    async def chat(
        self,
        user_message: str,
        conversation_history: list[dict[str, Any]],
        project_context: dict[str, Any] | None = None,
        mode: str = "auto",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """处理用户消息，返回 SSE 事件流。

        Args:
            user_message: 用户输入的文本
            conversation_history: 历史对话消息列表（OpenAI message 格式）
            project_context: 项目上下文（含 project_id、tech_stacks 等）
            mode: 运行模式，取值 auto / discussion / thinking

        Yields:
            SSE 事件字典，event 字段标识类型，data 字段携带数据：
            - ``{"event": "thinking", "data": {"content": ...}}``
            - ``{"event": "tool_call", "data": {"tool": ..., "args": ...}}``
            - ``{"event": "tool_result", "data": {"tool": ..., "result": ...}}``
            - ``{"event": "content", "data": {"content": ...}}``
            - ``{"event": "done", "data": {}}``
        """
        mode_config = get_mode_config(AgentMode(mode))
        context = project_context or {}

        tools_description = self._format_tools_description()
        system_prompt = self._prompt_builder.build(
            tools_description=tools_description,
            tech_stacks=context.get("tech_stacks", ""),
            coding_standards=context.get("coding_standards", ""),
        )

        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        tools_schema = self._get_tools_for_mode(mode_config)

        for _round in range(_MAX_TOOL_ROUNDS):
            yield {"event": "thinking", "data": {"content": "正在思考..."}}

            start_ts = time.monotonic()
            response = await self._call_llm(messages, tools_schema, mode_config)
            elapsed_ms = (time.monotonic() - start_ts) * 1000

            # 成本追踪是非关键路径，失败不应中断对话
            try:
                await self._track_cost(response, elapsed_ms, context.get("project_id", ""))
            except Exception:
                logger.warning("成本追踪失败，不影响对话继续", exc_info=True)

            # 防御 LLM API 返回空 choices
            if not getattr(response, "choices", None):
                yield {"event": "content", "data": {"content": "AI 服务返回异常，请稍后重试。"}}
                yield {"event": "done", "data": {}}
                return

            choice = response.choices[0]
            msg = choice.message
            tool_calls = getattr(msg, "tool_calls", None)

            if not tool_calls:
                content = getattr(msg, "content", "") or ""
                yield {"event": "content", "data": {"content": content}}
                yield {"event": "done", "data": {}}
                return

            # 将带 tool_calls 的 assistant 消息追加到历史
            messages.append(self._serialize_assistant_message(msg))

            for tc in tool_calls:
                func_name = tc.function.name

                # 防御 LLM 返回畸形 JSON 参数
                try:
                    func_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    logger.warning("工具 %s 的参数 JSON 解析失败: %s", func_name, tc.function.arguments)
                    func_args = {}

                yield {"event": "tool_call", "data": {"tool": func_name, "args": func_args}}

                result = await self._executor.execute(func_name, func_args)

                serialized = self._serialize_tool_result(result)
                yield {"event": "tool_result", "data": {"tool": func_name, "result": serialized}}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(serialized, ensure_ascii=False),
                })

        # 达到最大轮次
        yield {"event": "content", "data": {"content": "已达到最大工具调用轮次，请简化请求后重试。"}}
        yield {"event": "done", "data": {}}

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    async def _call_llm(
        self,
        messages: list[dict[str, Any]],
        tools_schema: list[dict[str, Any]] | None,
        mode_config: ModeConfig,
    ) -> Any:
        """直接调用 litellm，绕过现有 Provider 以支持 tools 参数。

        现有 LiteLLMProvider 尚未支持 tools 字段，
        这里复用其 config 直接调用 litellm.acompletion。
        待 Provider 升级后可切换回 provider.complete()。
        """
        import litellm

        model = mode_config.model_override or self._config.generation_model

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": mode_config.temperature,
            "max_tokens": self._config.default_max_tokens,
        }

        if tools_schema:
            kwargs["tools"] = tools_schema

        # 注入 API Key
        model_provider = model.split("/")[0] if "/" in model else ""
        provider_env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "azure": "AZURE_API_KEY",
        }
        env_var = provider_env_map.get(model_provider, "")
        if env_var and env_var in self._config.api_keys:
            kwargs["api_key"] = self._config.api_keys[env_var]

        return await litellm.acompletion(**kwargs)

    async def _track_cost(self, response: Any, elapsed_ms: float, project_id: str) -> None:
        """记录本次 LLM 调用的成本。"""
        if not self._cost_tracker:
            return

        usage = getattr(response, "usage", None)
        hidden = getattr(response, "_hidden_params", {}) or {}

        pid = project_id or "00000000-0000-0000-0000-000000000000"
        try:
            pid_uuid = UUID(pid)
        except ValueError:
            pid_uuid = UUID(int=0)

        await self._cost_tracker.record(
            agent_id="vibe-artifact-agent",
            project_id=pid_uuid,
            model=getattr(response, "model", ""),
            provider=hidden.get("custom_llm_provider", ""),
            prompt_tokens=getattr(usage, "prompt_tokens", 0),
            completion_tokens=getattr(usage, "completion_tokens", 0),
            total_cost=hidden.get("response_cost", 0.0),
            latency_ms=elapsed_ms,
        )

    def _get_tools_for_mode(self, mode_config: ModeConfig) -> list[dict[str, Any]] | None:
        """根据模式配置获取可用的工具列表。"""
        if not mode_config.tools_enabled:
            return None

        all_tools = self._registry.get_openai_tools_schema()

        if mode_config.allowed_tools is not None:
            return [t for t in all_tools if t["function"]["name"] in mode_config.allowed_tools]

        return all_tools

    def _format_tools_description(self) -> str:
        """将注册表中的工具格式化为自然语言描述文本。"""
        lines: list[str] = []
        for td in self._registry.get_all_tools():
            params = ", ".join(td.parameters.get("properties", {}).keys())
            lines.append(f"- **{td.name}**({params}): {td.description}")
        return "\n".join(lines)

    @staticmethod
    def _serialize_assistant_message(msg: Any) -> dict[str, Any]:
        """将 litellm 返回的 assistant message 序列化为 dict。"""
        result: dict[str, Any] = {
            "role": "assistant",
            "content": getattr(msg, "content", "") or "",
        }
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ]
        return result

    @staticmethod
    def _serialize_tool_result(result: ToolResult) -> dict[str, Any]:
        """将 ToolResult 序列化为可 JSON 化的 dict。"""
        if result.success:
            return {"success": True, "data": result.data}
        return {"success": False, "error": result.error}
