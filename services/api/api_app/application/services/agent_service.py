"""Agent 服务层。

集成 VibeArtifactAgent 与数据库，处理对话消息、
Agent 调用和 Artifact 持久化的完整流程。
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from platform_data.models.conversation import Message
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.application.services.conversation_service import ConversationService
from api_app.application.services.message_service import MessageService
from api_app.application.services.project_service import ProjectService
from api_app.application.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

_HISTORY_LIMIT = 20


class AgentService:
    """Agent 集成服务，串联消息持久化、Agent 调用和 Artifact 创建。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._msg_service = MessageService(db)
        self._conv_service = ConversationService(db)
        self._project_service = ProjectService(db)
        self._settings_service = SettingsService(db)

    async def process_message(
        self,
        project_id: UUID,
        conversation_id: UUID,
        user_message: str,
        user: User,
        mode: str = "auto",
    ) -> AsyncGenerator[str, None]:
        """处理用户消息的完整流程，以 SSE 事件流形式返回。

        流程：
        1. 保存用户消息
        2. 加载对话历史（排除刚保存的用户消息，由 Agent 自行追加）
        3. 构建项目上下文
        4. 构建 Agent（含 ToolContext 和 CostTracker）
        5. 调用 Agent.chat() 并流式返回
        6. 保存助手消息
        """
        # ── 步骤 1: 保存用户消息 ──
        await self._msg_service.save_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
        )
        await self.db.commit()

        # ── 步骤 2: 加载对话历史（排除最新一条，避免与 agent.chat 重复） ──
        history_messages = await self._msg_service.list_recent(
            conversation_id=conversation_id,
            limit=_HISTORY_LIMIT + 1,
        )
        # 去掉列表末尾刚保存的用户消息（list_recent 按时间升序，最新在末尾）
        if (
            history_messages
            and history_messages[-1].role.value == "user"
            and history_messages[-1].content == user_message
        ):
            history_messages = history_messages[:-1]
        conversation_history = self._build_openai_history(history_messages)

        # ── 步骤 3: 构建项目上下文 ──
        project = await self._project_service.get_project(project_id)
        project_context = self._build_project_context(project)

        # ── 步骤 4: 创建 Agent ──
        agent = await self._create_agent(user, project_id)

        # ── 步骤 5-6: 调用 Agent 并流式返回 ──
        full_content = ""
        tool_calls_log: list[dict[str, Any]] = []
        artifacts_created: list[str] = []

        try:
            async for event in agent.chat(
                user_message=user_message,
                conversation_history=conversation_history,
                project_context=project_context,
                mode=mode,
            ):
                event_type = event.get("event", "")
                event_data = event.get("data", {})

                if event_type == "content":
                    full_content += event_data.get("content", "")

                if event_type == "tool_call":
                    tool_calls_log.append(event_data)

                # 工具现在内部创建 Artifact，直接读取 artifact_id
                if event_type == "tool_result":
                    artifact_id = self._extract_artifact_id(event_data)
                    if artifact_id:
                        artifacts_created.append(artifact_id)

                yield self._format_sse(event)

        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            logger.exception("Agent 调用异常")
            await self.db.rollback()
            yield self._format_sse({
                "event": "error",
                "data": {"message": "AI 处理出现异常，请稍后重试"},
            })
            return

        # ── 步骤 7: 保存助手消息 ──
        if full_content:
            await self._msg_service.save_assistant_message(
                conversation_id=conversation_id,
                content=full_content,
                tool_calls={"calls": tool_calls_log} if tool_calls_log else None,
                artifacts_created=artifacts_created or None,
            )

        await self.db.commit()

    async def _create_agent(self, user: User, project_id: UUID) -> Any:
        """构建 Agent 实例，注入 LLM Provider、CostTracker 和 ToolContext。"""
        from agents.agent import VibeArtifactAgent
        from agents.tools.context import ToolContext
        from runtime_tools.cost.tracker import CostTracker
        from runtime_tools.llm.config import LLMConfig
        from runtime_tools.llm.provider import LiteLLMProvider

        user_keys = await self._settings_service.get_user_api_keys_decrypted(user.id)
        pref = await self._settings_service.get_model_preference(user.id)

        config = LLMConfig.from_user(
            user_api_keys=user_keys,
            reasoning_model=pref.reasoning_model,
            generation_model=pref.generation_model,
        )

        provider = LiteLLMProvider(config=config)
        cost_tracker = CostTracker()
        tool_context = ToolContext(
            db=self.db,
            project_id=project_id,
            user_id=user.id,
        )

        return VibeArtifactAgent(
            llm_provider=provider,
            cost_tracker=cost_tracker,
            tool_context=tool_context,
        )

    @staticmethod
    def _extract_artifact_id(event_data: dict[str, Any]) -> str | None:
        """从 tool_result 事件中提取 artifact_id（工具内部创建的）。"""
        result = event_data.get("result", {})
        if not result.get("success"):
            return None
        data = result.get("data", {})
        if not isinstance(data, dict):
            return None
        return data.get("artifact_id")

    @staticmethod
    def _build_openai_history(messages: list[Message]) -> list[dict[str, Any]]:
        """将数据库消息记录转为 OpenAI message 格式。"""
        history: list[dict[str, Any]] = []
        for msg in messages:
            history.append({
                "role": msg.role.value,
                "content": msg.content,
            })
        return history

    @staticmethod
    def _build_project_context(project: Any) -> dict[str, Any]:
        """从 Project ORM 对象构建 Agent 所需的项目上下文。"""
        if project is None:
            return {}
        return {
            "project_id": str(project.id),
            "project_name": project.name,
            "project_type": project.project_type,
            # Agent 期望的字段名
            "tech_stacks": project.tech_requirements or "",
            "coding_standards": "",
            "course_name": project.course_name or "",
        }

    @staticmethod
    def _format_sse(event: dict[str, Any]) -> str:
        """将事件字典格式化为 SSE 文本。"""
        event_type = event.get("event", "message")
        data_payload = json.dumps(event.get("data", {}), ensure_ascii=False)
        return f"event: {event_type}\ndata: {data_payload}\n\n"
