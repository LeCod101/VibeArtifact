"""批量生成任务。

毕设全流程一键生成，由 API 层触发。
逐步调用 Agent 完成需求分析、架构设计、数据库、代码、文档等。
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from worker_app.celery_app import celery_app

logger = logging.getLogger(__name__)

_sync_engine = None

# 每个步骤对应的 Agent 提示模板
_STEP_PROMPTS: dict[str, str] = {
    "requirement": (
        "请根据以下项目信息生成完整的需求分析文档。"
        "使用 create_document 工具，doc_type 设为 requirement。"
        "\n\n项目名称：{project_name}\n技术要求：{tech_requirements}"
    ),
    "architecture": (
        "根据项目需求，请完成以下两项：\n"
        "1. 使用 create_diagram 工具生成系统架构图（architecture 类型）\n"
        "2. 使用 create_document 工具生成系统设计文档（design 类型）"
    ),
    "database": (
        "根据项目需求和系统设计，请完成以下两项：\n"
        "1. 使用 create_diagram 工具生成数据库 ER 图（er 类型）\n"
        "2. 使用 create_sql 工具生成完整的建表 SQL 脚本"
    ),
    "code": (
        "根据系统设计和数据库设计，逐模块生成项目核心代码。"
        "每个模块使用一次 create_file 工具创建。"
        "请按照以下顺序生成：实体类/模型 → 数据访问层 → 业务逻辑层 → 控制器/路由 → 配置文件。"
    ),
    "api_doc": (
        "根据已生成的代码，使用 create_document 工具生成完整的 API 文档（api_doc 类型）。"
        "包含每个接口的请求方法、URL、参数、返回值和示例。"
    ),
}


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        raw_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://vibe:vibe@localhost:5432/vibeartifact",
        )
        sync_url = raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        _sync_engine = create_engine(sync_url, pool_pre_ping=True)
    return _sync_engine


async def _run_agent_for_step(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    step_prompt: str,
    conversation_history: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """异步调用 Agent 处理单个步骤，返回内容和工具结果。"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    from agents.agent import VibeArtifactAgent
    from agents.tools.context import ToolContext
    from runtime_tools.llm.config import LLMConfig
    from runtime_tools.llm.provider import LiteLLMProvider

    async_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://vibe:vibe@localhost:5432/vibeartifact",
    )
    engine = create_async_engine(async_url, pool_pre_ping=True)

    async with AsyncSession(engine) as db:
        config = LLMConfig.from_env()
        provider = LiteLLMProvider(config=config)
        tool_context = ToolContext(db=db, project_id=project_id, user_id=user_id)

        agent = VibeArtifactAgent(
            llm_provider=provider,
            tool_context=tool_context,
        )

        full_content = ""
        tool_results: list[dict[str, Any]] = []

        async for event in agent.chat(
            user_message=step_prompt,
            conversation_history=conversation_history,
            project_context={"project_id": str(project_id)},
            mode="auto",
        ):
            event_type = event.get("event", "")
            event_data = event.get("data", {})

            if event_type == "content":
                full_content += event_data.get("content", "")
            elif event_type == "tool_result":
                tool_results.append(event_data)

        await db.commit()

    await engine.dispose()
    return full_content, tool_results


@celery_app.task(bind=True, name="tasks.batch_generate", max_retries=1, time_limit=600)
def batch_generate(
    self,
    project_id: str,
    user_id: str,
    steps: list[str] | None = None,
) -> dict[str, Any]:
    """毕设全流程批量生成。

    Args:
        project_id: 项目 UUID
        user_id: 用户 UUID
        steps: 生成步骤列表
    """
    from platform_data.models.project import Project

    all_steps = steps or ["requirement", "architecture", "database", "code", "api_doc"]
    project_uuid = uuid.UUID(project_id)
    user_uuid = uuid.UUID(user_id)

    engine = _get_sync_engine()
    with Session(engine) as db:
        project = db.execute(
            select(Project).where(Project.id == project_uuid)
        ).scalar_one_or_none()
        if project is None:
            return {"status": "failed", "error": "项目不存在"}

        project_name = project.name
        tech_requirements = project.tech_requirements or ""

    completed_steps: list[str] = []
    conversation_history: list[dict[str, Any]] = []

    for step in all_steps:
        prompt_template = _STEP_PROMPTS.get(step)
        if not prompt_template:
            logger.warning("未知的批量生成步骤: %s", step)
            continue

        step_prompt = prompt_template.format(
            project_name=project_name,
            tech_requirements=tech_requirements,
        )

        logger.info("批量生成 - 步骤 %s 开始 (project=%s)", step, project_id)

        try:
            content, tool_results = asyncio.run(
                _run_agent_for_step(
                    project_id=project_uuid,
                    user_id=user_uuid,
                    step_prompt=step_prompt,
                    conversation_history=conversation_history,
                )
            )

            # 将本步骤的对话添加到历史中，供下一步参考
            conversation_history.append({"role": "user", "content": step_prompt})
            if content:
                conversation_history.append({"role": "assistant", "content": content})

            completed_steps.append(step)
            logger.info(
                "批量生成 - 步骤 %s 完成 (project=%s, tools=%d)",
                step, project_id, len(tool_results),
            )

        except Exception:
            logger.exception("批量生成 - 步骤 %s 失败 (project=%s)", step, project_id)
            return {
                "status": "partial",
                "project_id": project_id,
                "completed_steps": completed_steps,
                "failed_step": step,
            }

    return {
        "status": "completed",
        "project_id": project_id,
        "completed_steps": completed_steps,
    }
