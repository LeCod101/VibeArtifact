"""
冷启动引导器模块。

当项目 IR 为空时，执行最小 Agent 链路建立基础 IR：
intent -> contraction -> planner -> schema

产出：scope 节点 + risk 节点 + task 节点 + entity 节点 + endpoint 节点
"""

from __future__ import annotations

import logging
from uuid import UUID

from pydantic import BaseModel

from ir_core.operations.apply import ApplyError, apply_operations
from ir_core.schema.data import IREdgeData, IRNodeData

logger = logging.getLogger(__name__)


class ColdStartResult(BaseModel):
    """
    冷启动结果。

    记录冷启动过程中产生的 IR 数据和执行统计信息。
    - new_snapshot_id: 新快照 ID（由调用方设置，此处预留）
    - ir_nodes: 冷启动后的所有节点列表
    - ir_edges: 冷启动后的所有边列表
    - operations_applied: 成功应用的操作总数
    - agents_executed: 成功执行的 Agent ID 列表
    - warnings: 过程中产生的警告信息列表
    """

    new_snapshot_id: UUID | None = None
    ir_nodes: list[IRNodeData] = []
    ir_edges: list[IREdgeData] = []
    operations_applied: int = 0
    agents_executed: list[str] = []
    warnings: list[str] = []


class ColdStartBootstrap:
    """
    冷启动引导器。

    当项目 IR 为空时，按固定顺序执行最小 Agent 链路：
    intent -> contraction -> planner -> schema

    每步构建 AgentInput，调用 AgentRunner.run()，
    将产出的 operations 应用到累积的 IR 上。

    设计要点：
    - 不做数据库持久化，只返回内存中的结果
    - 单个 Agent 失败不中断整个冷启动流程
    - 调用方负责快照创建和 DB 写入
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
        snapshot_id: UUID,
        user_message: str,
    ) -> ColdStartResult:
        """
        执行冷启动。

        流程：
        1. 从空 nodes/edges 开始
        2. 按顺序执行 intent -> contraction -> planner -> schema
        3. 每步：
           a. 构建 AgentInput（当前 nodes/edges + user_message）
           b. 调用 AgentRunner.run(agent_id, agent_input)
           c. 拿到 AgentRunResult.operations
           d. 调用 apply_operations(nodes, edges, operations) 更新 IR
        4. 返回最终 nodes/edges + 统计信息

        - project_id: 项目唯一标识
        - snapshot_id: 当前快照唯一标识
        - user_message: 用户输入的原始需求描述
        - 返回: ColdStartResult，包含最终 IR 和执行统计
        """
        # 延迟导入避免循环依赖
        from agents.schemas.base import AgentInput

        # 初始化空 IR
        current_nodes: list[IRNodeData] = []
        current_edges: list[IREdgeData] = []

        total_operations = 0
        agents_executed: list[str] = []
        warnings: list[str] = []

        for agent_id in self.COLD_START_AGENTS:
            logger.info(
                "冷启动执行 Agent: %s (已有 %d 节点, %d 边)",
                agent_id,
                len(current_nodes),
                len(current_edges),
            )

            try:
                # 构建 Agent 输入
                agent_input = AgentInput(
                    project_id=project_id,
                    snapshot_id=snapshot_id,
                    ir_nodes=current_nodes,
                    ir_edges=current_edges,
                    conversation_context=[],
                    task_description=user_message,
                    extra={},
                )

                # 调用 AgentRunner 执行
                result = await self._runner.run(agent_id, agent_input)

                # 收集该 Agent 产生的警告
                if result.warnings:
                    warnings.extend(result.warnings)

                # 如果没有操作，跳过 apply
                if not result.operations:
                    logger.info(
                        "Agent %s 未产生任何操作，跳过 apply",
                        agent_id,
                    )
                    agents_executed.append(agent_id)
                    continue

                # 应用操作到当前 IR
                new_nodes, new_edges = apply_operations(
                    current_nodes,
                    current_edges,
                    result.operations,
                )
                current_nodes = new_nodes
                current_edges = new_edges
                total_operations += len(result.operations)
                agents_executed.append(agent_id)

                logger.info(
                    "Agent %s 完成: 应用 %d 个操作, 当前 %d 节点 %d 边",
                    agent_id,
                    len(result.operations),
                    len(current_nodes),
                    len(current_edges),
                )

            except ApplyError as exc:
                # apply_operations 校验失败
                warning_msg = (
                    f"{agent_id} 操作应用失败: {exc}"
                )
                logger.warning(warning_msg)
                warnings.append(warning_msg)

            except Exception as exc:
                # Agent 执行本身失败（LLM 调用、解析等）
                warning_msg = f"{agent_id} 执行失败: {exc}"
                logger.warning(warning_msg, exc_info=True)
                warnings.append(warning_msg)

        logger.info(
            "冷启动完成: %d 个 Agent 成功, %d 个操作, %d 节点 %d 边, %d 个警告",
            len(agents_executed),
            total_operations,
            len(current_nodes),
            len(current_edges),
            len(warnings),
        )

        return ColdStartResult(
            ir_nodes=current_nodes,
            ir_edges=current_edges,
            operations_applied=total_operations,
            agents_executed=agents_executed,
            warnings=warnings,
        )
