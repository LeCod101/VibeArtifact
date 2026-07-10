"""
冷启动引导器模块。

当项目工作区为空时，执行最小 Agent 链路建立基础上下文：
intent -> contraction -> planner -> schema

产出：各 Agent 的高层输出（scope/task/schema 决策），
通过 upstream_outputs 逐级传递给后续 Agent。
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ColdStartResult(BaseModel):
    """
    冷启动结果。

    记录冷启动过程中产生的 Agent 输出和执行统计信息。
    - outputs: 各 Agent 的高层输出（agent_id → 输出字典）
    - files: 冷启动产生的工作区文件列表（决策型 Agent 通常为空）
    - agents_executed: 成功执行的 Agent ID 列表
    - warnings: 过程中产生的警告信息列表
    """

    outputs: dict[str, Any] = {}
    files: list[dict] = []
    agents_executed: list[str] = []
    warnings: list[str] = []


class ColdStartBootstrap:
    """
    冷启动引导器。

    当项目工作区为空时，按固定顺序执行最小 Agent 链路：
    intent -> contraction -> planner -> schema

    每步构建 AgentInput（携带前序 Agent 的输出作为上下文），
    调用 AgentRunner.run()，将高层输出累积到 upstream_outputs。

    设计要点：
    - 不做数据库持久化，只返回内存中的结果
    - 单个 Agent 失败不中断整个冷启动流程
    - 调用方负责结果的落库与展示
    """

    # 冷启动依次执行的 Agent 列表
    COLD_START_AGENTS = ["intent", "contraction", "planner", "schema"]

    def __init__(self, runner: object) -> None:
        """
        初始化冷启动引导器。

        - runner: AgentRunner 实例，用于执行各 Agent
        """
        # 延迟引用类型，避免循环导入
        self._runner = runner

    async def bootstrap(
        self,
        project_id: UUID,
        user_message: str,
        run_id: UUID | None = None,
    ) -> ColdStartResult:
        """
        执行冷启动。

        流程：
        1. 从空的 upstream_outputs 开始
        2. 按顺序执行 intent -> contraction -> planner -> schema
        3. 每步：
           a. 构建 AgentInput（累积的 upstream_outputs + user_message）
           b. 调用 AgentRunner.run(agent_id, agent_input)
           c. 将高层输出并入 upstream_outputs
        4. 返回全部输出 + 统计信息

        - project_id: 项目唯一标识
        - user_message: 用户输入的原始需求描述
        - run_id: 本次运行唯一标识（可选）
        - 返回: ColdStartResult，包含各 Agent 输出和执行统计
        """
        # 延迟导入避免循环依赖
        from agents.configs.registry import AgentRegistry
        from agents.schemas.base import AgentInput

        upstream_outputs: dict[str, Any] = {}
        all_files: list[dict] = []
        agents_executed: list[str] = []
        warnings: list[str] = []

        registry = AgentRegistry.get_instance()

        for agent_id in self.COLD_START_AGENTS:
            logger.info(
                "冷启动执行 Agent: %s (已有 %d 个上游输出)",
                agent_id,
                len(upstream_outputs),
            )

            try:
                # 构建 Agent 输入
                agent_input = AgentInput(
                    project_id=project_id,
                    run_id=run_id,
                    workspace_files=[],
                    upstream_outputs=dict(upstream_outputs),
                    conversation_context=[],
                    task_description=user_message,
                    extra={},
                )

                # 调用 AgentRunner 执行
                result = await self._runner.run(agent_id, agent_input)

                # 收集该 Agent 产生的警告
                if result.warnings:
                    warnings.extend(result.warnings)

                # 高层输出并入 upstream_outputs，供后续 Agent 参考
                config = registry.get(agent_id)
                high_level = getattr(result.output, config.high_level_key)
                upstream_outputs[agent_id] = high_level.model_dump(mode="json")

                # 累积文件产物（决策型 Agent 通常为空）
                if result.files:
                    all_files.extend(result.files)

                agents_executed.append(agent_id)

                logger.info(
                    "Agent %s 完成: %d 个文件, 当前 %d 个上游输出",
                    agent_id,
                    len(result.files),
                    len(upstream_outputs),
                )

            except Exception as exc:
                # Agent 执行本身失败（LLM 调用、解析等）
                warning_msg = f"{agent_id} 执行失败: {exc}"
                logger.warning(warning_msg, exc_info=True)
                warnings.append(warning_msg)

        logger.info(
            "冷启动完成: %d 个 Agent 成功, %d 个文件, %d 个警告",
            len(agents_executed),
            len(all_files),
            len(warnings),
        )

        return ColdStartResult(
            outputs=upstream_outputs,
            files=all_files,
            agents_executed=agents_executed,
            warnings=warnings,
        )
