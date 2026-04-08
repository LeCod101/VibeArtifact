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

from platform_data.models.artifact import Artifact
from platform_data.models.conversation import Message
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.application.services.conversation_service import ConversationService
from api_app.application.services.message_service import MessageService
from api_app.application.services.project_service import ProjectService
from api_app.application.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

# 加载历史消息的默认条数
_HISTORY_LIMIT = 20

# 工具结果中标识 artifact 创建的类型集合
_ARTIFACT_TOOL_TYPES = {"code", "document", "diagram", "database_schema"}


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
        1. 保存用户消息到 messages 表
        2. 加载对话历史（最近 N 条消息）
        3. 构建项目上下文
        4. 构建 LLMConfig（优先用户 Key，回退平台 Key）
        5. 调用 VibeArtifactAgent.chat()
        6. 逐个 yield SSE 事件
        7. Agent 回复完毕后，保存助手消息
        8. 处理工具结果中的 artifact 创建

        参数:
            project_id: 项目 UUID
            conversation_id: 对话 UUID
            user_message: 用户输入文本
            user: 当前认证用户
            mode: 运行模式（auto / discussion / thinking）

        Yields:
            SSE 格式的事件字符串（data: {json}\n\n）
        """
        # ── 步骤 1: 保存用户消息并提交（确保消息不会因后续异常丢失）──
        await self._msg_service.save_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
        )
        await self.db.commit()

        # ── 步骤 2: 加载对话历史 ──
        history_messages = await self._msg_service.list_recent(
            conversation_id=conversation_id,
            limit=_HISTORY_LIMIT,
        )
        conversation_history = self._build_openai_history(history_messages)

        # ── 步骤 3: 构建项目上下文 ──
        project = await self._project_service.get_project(project_id)
        project_context = self._build_project_context(project)

        # ── 步骤 4: 构建 LLMConfig 并创建 Agent ──
        agent = await self._create_agent(user)

        # ── 步骤 5-6: 调用 Agent 并流式返回 SSE 事件 ──
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

                # 从工具结果中检测 artifact 创建
                if event_type == "tool_result":
                    artifact_id = await self._handle_tool_result(
                        project_id=project_id,
                        tool_name=event_data.get("tool", ""),
                        result=event_data.get("result", {}),
                    )
                    if artifact_id:
                        artifacts_created.append(str(artifact_id))
                        event_data["artifact_id"] = str(artifact_id)

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

    async def _create_agent(self, user: User) -> Any:
        """构建 LLMConfig 并创建 VibeArtifactAgent 实例。

        优先使用用户的 API Key，回退到平台配置。
        """
        from agents.agent import VibeArtifactAgent
        from runtime_tools.llm.config import LLMConfig
        from runtime_tools.llm.provider import LiteLLMProvider

        # 获取用户自定义 API Key
        user_keys = await self._settings_service.get_user_api_keys_decrypted(user.id)

        # 获取用户模型偏好
        pref = await self._settings_service.get_model_preference(user.id)

        config = LLMConfig.from_user(
            user_api_keys=user_keys,
            reasoning_model=pref.reasoning_model,
            generation_model=pref.generation_model,
        )

        provider = LiteLLMProvider(config=config)
        return VibeArtifactAgent(llm_provider=provider)

    async def _handle_tool_result(
        self,
        project_id: UUID,
        tool_name: str,
        result: dict[str, Any],
    ) -> UUID | None:
        """从工具结果中检测并创建 Artifact。

        当 result.data 包含 artifact_type 且在支持的类型中时，
        创建 Artifact 记录并返回其 ID。
        """
        if not result.get("success"):
            return None

        data = result.get("data", {})
        if not isinstance(data, dict):
            return None

        artifact_type = data.get("artifact_type", "")
        if artifact_type not in _ARTIFACT_TOOL_TYPES:
            return None

        artifact = Artifact(
            project_id=project_id,
            artifact_type=artifact_type,
            title=data.get("title", f"由 {tool_name} 生成"),
            content=data.get("content", ""),
            file_path=data.get("file_path"),
            language=data.get("language"),
        )
        self.db.add(artifact)
        await self.db.flush()
        await self.db.refresh(artifact)

        return artifact.id

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
            "tech_requirements": project.tech_requirements or "",
            "course_name": project.course_name or "",
        }

    @staticmethod
    def _format_sse(event: dict[str, Any]) -> str:
        """将事件字典格式化为 SSE 文本（含 event: 前缀供 EventSource 分发）。"""
        event_type = event.get("event", "message")
        data_payload = json.dumps(event.get("data", {}), ensure_ascii=False)
        return f"event: {event_type}\ndata: {data_payload}\n\n"
