"""
DAG 解析器模块。

从 AgentRegistry 读取所有 agent 的 depends_on 依赖关系，
构建执行图（邻接表），提供拓扑排序和并行分组功能。

输出执行计划：List[List[str]]，每个内层列表是可并行执行的一组 agent_id。
"""

from __future__ import annotations

from collections import defaultdict, deque

from agents.configs.registry import AgentRegistry


class DAGParseError(Exception):
    """
    DAG 解析错误。

    当依赖图中存在环、缺失节点等结构性问题时抛出。
    """


class DAGParser:
    """
    DAG 解析器。

    从 AgentRegistry 中读取所有 agent 及其依赖关系，
    构建邻接表，执行拓扑排序，并输出分层执行计划。
    """

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        """
        初始化 DAG 解析器。

        - registry: Agent 注册表实例，为 None 时使用全局单例
        """
        self._registry = registry or AgentRegistry.get_instance()

        # 邻接表：key 依赖被完成后，可以解锁 value 列表中的 agent
        # forward[A] = [B, C] 表示 A 完成后 B、C 可以推进
        self._forward: dict[str, list[str]] = defaultdict(list)

        # 入度表：每个 agent 还有几个前置依赖没完成
        self._in_degree: dict[str, int] = {}

        # 所有 agent_id 集合
        self._all_agents: set[str] = set()

    def build_graph(self) -> None:
        """
        从 AgentRegistry 构建执行图。

        遍历所有已注册 agent，根据 dependencies 字段建立邻接表和入度表。
        如果依赖的 agent 不存在于注册表中，抛出 DAGParseError。
        """
        agents = self._registry.list_agents()
        self._forward = defaultdict(list)
        self._in_degree = {}
        self._all_agents = set()

        # 收集所有 agent_id
        for agent_cfg in agents:
            self._all_agents.add(agent_cfg.agent_id)
            self._in_degree[agent_cfg.agent_id] = 0

        # 构建邻接表和入度
        for agent_cfg in agents:
            for dep in agent_cfg.dependencies:
                # 校验依赖是否存在
                if dep not in self._all_agents:
                    raise DAGParseError(
                        f"Agent '{agent_cfg.agent_id}' 依赖的 "
                        f"'{dep}' 未在注册表中找到"
                    )
                # dep 完成后可以解锁当前 agent
                self._forward[dep].append(agent_cfg.agent_id)
                self._in_degree[agent_cfg.agent_id] += 1

    def topological_sort(self) -> list[str]:
        """
        对执行图进行拓扑排序。

        使用 Kahn 算法（BFS），返回一个合法的拓扑序列。
        如果图中存在环，抛出 DAGParseError。
        返回按拓扑序排列的 agent_id 列表。
        """
        in_degree = dict(self._in_degree)
        queue: deque[str] = deque()

        # 将所有入度为 0 的节点入队
        for agent_id, degree in in_degree.items():
            if degree == 0:
                queue.append(agent_id)

        result: list[str] = []

        while queue:
            # 按字母序取出，保证确定性
            current = min(queue)
            queue.remove(current)
            result.append(current)

            # 将后继节点入度减 1
            for successor in self._forward.get(current, []):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        # 检测环
        if len(result) != len(self._all_agents):
            visited = set(result)
            cycle_nodes = [
                aid for aid in self._all_agents if aid not in visited
            ]
            raise DAGParseError(
                f"DAG 中检测到环，涉及 agent: {cycle_nodes}"
            )

        return result

    def get_execution_layers(self) -> list[list[str]]:
        """
        获取分层执行计划。

        将 agent 按依赖层级分组，同一层级内的 agent 无互相依赖，
        可以并行执行。层级间必须串行。

        返回 List[List[str]]，例如：
        [
            ["intent"],
            ["contraction"],
            ["planner"],
            ["schema"],
            ["backend", "frontend", "doc", "diagram"],
            ["qa"],
            ["export"],
        ]
        """
        in_degree = dict(self._in_degree)
        queue: deque[str] = deque()

        # 将所有入度为 0 的节点入队
        for agent_id, degree in in_degree.items():
            if degree == 0:
                queue.append(agent_id)

        layers: list[list[str]] = []

        while queue:
            # 当前层级：所有入度为 0 的节点
            # 排序保证确定性
            current_layer = sorted(queue)
            layers.append(current_layer)
            queue.clear()

            # 将当前层所有节点的后继入度减 1
            for agent_id in current_layer:
                for successor in self._forward.get(agent_id, []):
                    in_degree[successor] -= 1
                    if in_degree[successor] == 0:
                        queue.append(successor)

        # 检测环
        total_scheduled = sum(len(layer) for layer in layers)
        if total_scheduled != len(self._all_agents):
            raise DAGParseError("DAG 中检测到环，无法生成完整执行计划")

        return layers

    def get_agent_dependencies(self, agent_id: str) -> list[str]:
        """
        获取某个 agent 的直接前置依赖列表。

        - agent_id: 目标 agent 标识
        返回该 agent 的 dependencies 列表。
        """
        config = self._registry.get(agent_id)
        return list(config.dependencies)

    def get_agent_successors(self, agent_id: str) -> list[str]:
        """
        获取某个 agent 的直接后继列表。

        - agent_id: 目标 agent 标识
        返回依赖该 agent 的所有后续 agent_id 列表。
        """
        return list(self._forward.get(agent_id, []))


def build_execution_plan(
    registry: AgentRegistry | None = None,
) -> list[list[str]]:
    """
    便捷函数：一步构建执行计划。

    从 AgentRegistry 读取依赖关系，构建图，返回分层执行计划。
    - registry: Agent 注册表，为 None 时使用全局单例
    返回 List[List[str]]，每层可并行执行的 agent_id 列表。
    """
    parser = DAGParser(registry)
    parser.build_graph()
    return parser.get_execution_layers()
