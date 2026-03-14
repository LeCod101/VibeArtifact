"""
上下文组装器模块。

从 AgentInput 中提取和组装 ContextSlice，
将原始的输入数据转换为结构化的上下文切片。
"""

from agents.context.slice import ContextSlice
from agents.schemas.base import AgentInput

# Decision 节点的类型标识
_DECISION_NODE_TYPE = "decision"

# 默认保留的最近消息数量
_DEFAULT_RECENT_MESSAGE_COUNT = 10


class ContextAssembler:
    """
    上下文组装器。

    从 AgentInput 中提取和组装 ContextSlice。
    负责 IR 数据分类（普通节点 vs 决策节点）和对话消息截取。

    - recent_message_count: 保留最近几轮对话消息，默认 10 条
    """

    def __init__(
        self,
        recent_message_count: int = _DEFAULT_RECENT_MESSAGE_COUNT,
    ) -> None:
        """
        初始化组装器。

        - recent_message_count: 保留最近几轮对话消息的数量
        """
        self._recent_message_count = recent_message_count

    def assemble(self, agent_input: AgentInput) -> ContextSlice:
        """
        从 AgentInput 组装上下文切片。

        执行以下步骤：
        1. 从 ir_nodes 中分离出 decision 类型的节点
        2. 截取最近的对话消息
        3. 组装为 ContextSlice

        - agent_input: Agent 统一输入对象
        - 返回: 组装好的 ContextSlice
        """
        # 分离 decision 节点和普通节点
        decision_nodes = [
            node for node in agent_input.ir_nodes
            if node.node_type == _DECISION_NODE_TYPE
        ]

        # 截取最近的对话消息
        recent_messages = agent_input.conversation_context[
            -self._recent_message_count:
        ]

        return ContextSlice(
            ir_nodes=agent_input.ir_nodes,
            ir_edges=agent_input.ir_edges,
            recent_messages=recent_messages,
            decision_nodes=decision_nodes,
        )
