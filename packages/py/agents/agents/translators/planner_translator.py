"""
PlannerTranslator 模块 — 任务计划翻译器。

将 planner agent 输出的 TaskPlan 翻译为 IROperation 列表。

翻译规则：
1. 每个 TaskStep → create_node（类型 task）
2. 每个 TaskStep 的 depends_on → create_edge（类型 depends_on）
3. 边的方向：被依赖的步骤 → 依赖它的步骤（source 是前置，target 是后续）
"""

from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import TaskPlan

from .base import BaseTranslator, TranslatorResult

# planner 生成的步骤中，合法的 agent_id 集合
_VALID_AGENT_IDS = frozenset(
    {"schema", "backend", "frontend", "doc", "diagram", "qa", "export"}
)


class PlannerTranslator(BaseTranslator):
    """
    任务计划翻译器。

    将 TaskPlan（任务执行计划）翻译为 IR 操作列表。
    产生 task 节点和步骤间的 depends_on 边。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 TaskPlan 翻译为 IROperation 列表。

        翻译逻辑：
        1. 为每个 TaskStep 创建 task 类型节点
        2. 根据每个步骤的 depends_on 列表，创建 depends_on 类型的边
        3. 执行完整性校验，产生警告信息

        - high_level_output: TaskPlan 实例
        - 返回: TranslatorResult，包含创建节点和边的操作列表
        """
        if not isinstance(high_level_output, TaskPlan):
            return TranslatorResult(
                operations=[],
                warnings=[
                    "PlannerTranslator 期望 TaskPlan 类型，实际收到 "
                    f"{type(high_level_output).__name__}"
                ],
            )

        plan: TaskPlan = high_level_output
        operations: list[dict] = []
        warnings: list[str] = []

        # 边界检查：steps 为空
        if not plan.steps:
            return TranslatorResult(
                operations=[],
                warnings=["steps 列表为空，至少需要一个任务步骤才能继续"],
            )

        # 构建 step_id → 操作列表索引的映射，用于后续创建边时引用
        step_id_to_op_index: dict[str, int] = {}

        # 收集所有 step_id，用于校验 depends_on 引用的合法性
        all_step_ids = {step.step_id for step in plan.steps}

        # 翻译每个 TaskStep 为 create_node 操作
        for step in plan.steps:
            # 校验 agent_id 合法性
            if step.agent_id not in _VALID_AGENT_IDS:
                warnings.append(
                    f"步骤 {step.step_id} 的 agent_id '{step.agent_id}' "
                    f"不在合法值列表中，合法值: "
                    f"{', '.join(sorted(_VALID_AGENT_IDS))}"
                )

            # 校验 step_id 格式
            if not step.step_id.startswith("step_"):
                warnings.append(
                    f"步骤 {step.step_id} 的 step_id 格式不规范，"
                    "建议使用 'step_<序号>' 格式"
                )

            # 校验 depends_on 引用的 step_id 是否存在
            for dep_id in step.depends_on:
                if dep_id not in all_step_ids:
                    warnings.append(
                        f"步骤 {step.step_id} 依赖的 {dep_id} "
                        "不存在于 steps 列表中"
                    )

            op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.TASK,
                "label": f"{step.agent_id}: {step.description[:50]}",
                "props": {
                    "step_id": step.step_id,
                    "agent_id": step.agent_id,
                    "description": step.description,
                    "depends_on": step.depends_on,
                },
            }
            step_id_to_op_index[step.step_id] = len(operations)
            operations.append(op)

        # 创建步骤间的依赖边
        # 边方向：被依赖的步骤（source）→ 依赖它的步骤（target）
        for step in plan.steps:
            for dep_id in step.depends_on:
                # 只有 dep_id 存在于映射中时才创建边
                if dep_id in step_id_to_op_index:
                    edge_op = {
                        "operation_type": OperationType.CREATE_EDGE,
                        "edge_type": EdgeType.DEPENDS_ON,
                        # 通过操作索引引用（_ref:op_index 格式）
                        "source_node_id": (
                            f"_ref:{step_id_to_op_index[dep_id]}"
                        ),
                        "target_node_id": (
                            f"_ref:{step_id_to_op_index[step.step_id]}"
                        ),
                    }
                    operations.append(edge_op)

        # 检测循环依赖
        cycle_warning = self._detect_cycles(plan)
        if cycle_warning:
            warnings.append(cycle_warning)

        # 校验标准 DAG 结构完整性
        structure_warnings = self._check_dag_structure(plan)
        warnings.extend(structure_warnings)

        return TranslatorResult(operations=operations, warnings=warnings)

    def _detect_cycles(self, plan: TaskPlan) -> str | None:
        """
        检测任务步骤之间是否存在循环依赖。

        使用 DFS 染色法（白灰黑三色标记）检测有向图中的环。
        - plan: TaskPlan 实例
        - 返回: 若检测到循环则返回警告字符串，否则返回 None
        """
        # 构建邻接表
        adj: dict[str, list[str]] = {}
        for step in plan.steps:
            adj[step.step_id] = list(step.depends_on)

        # 0=白色（未访问），1=灰色（正在访问），2=黑色（已完成）
        color: dict[str, int] = {s.step_id: 0 for s in plan.steps}

        def dfs(node: str) -> bool:
            """
            深度优先搜索，检测从 node 出发是否存在环。
            - 返回: True 表示检测到环
            """
            color[node] = 1
            for neighbor in adj.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == 1:
                    return True
                if color[neighbor] == 0 and dfs(neighbor):
                    return True
            color[node] = 2
            return False

        for step_id in color:
            if color[step_id] == 0:
                if dfs(step_id):
                    return "检测到循环依赖，请检查 steps 的 depends_on 配置"

        return None

    def _check_dag_structure(self, plan: TaskPlan) -> list[str]:
        """
        校验任务计划是否符合标准 DAG 结构。

        检查点：
        - 是否包含 7 个标准步骤
        - agent_id 是否覆盖所有必需的 Agent
        - schema 步骤是否无依赖
        - qa 步骤是否依赖所有第 2 层步骤

        - plan: TaskPlan 实例
        - 返回: 警告信息列表
        """
        warnings: list[str] = []

        # 收集所有 agent_id
        agent_ids = [step.agent_id for step in plan.steps]

        # 检查标准步骤数量
        if len(plan.steps) != 7:
            warnings.append(
                f"标准 DAG 应包含 7 个步骤，当前有 {len(plan.steps)} 个"
            )

        # 检查必需的 agent 是否全部覆盖
        required_agents = {
            "schema", "backend", "frontend", "doc", "diagram", "qa", "export"
        }
        missing_agents = required_agents - set(agent_ids)
        if missing_agents:
            warnings.append(
                f"缺少以下必需 Agent 的步骤: "
                f"{', '.join(sorted(missing_agents))}"
            )

        # 检查 schema 步骤是否无依赖
        for step in plan.steps:
            if step.agent_id == "schema" and step.depends_on:
                warnings.append(
                    f"schema 步骤 ({step.step_id}) 不应有依赖，"
                    f"当前依赖: {step.depends_on}"
                )

        return warnings
