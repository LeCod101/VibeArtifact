"""
Agent 上下文切片模块。

定义 ContextSlice 数据结构，用于封装 Agent 运行所需的 IR 快照数据、
对话摘要和决策节点。提供 to_prompt_text() 方法将切片序列化为
可嵌入 prompt 的可读文本。
"""

from ir_core.schema.data import IREdgeData, IRNodeData
from pydantic import BaseModel

from agents.schemas.base import MessageSlice


class ContextSlice(BaseModel):
    """
    Agent 上下文切片。

    包含 Agent 运行所需的 IR 快照数据、对话摘要和决策节点。
    是 ContextAssembler 的输出、PromptBuilder 的 context_slice 层输入。

    - ir_nodes: 当前快照的 IR 节点列表
    - ir_edges: 当前快照的 IR 边列表
    - conversation_summary: 对话历史的文本摘要
    - recent_messages: 最近几轮对话消息
    - decision_nodes: node_type == "decision" 的决策节点列表
    """

    ir_nodes: list[IRNodeData] = []
    ir_edges: list[IREdgeData] = []
    conversation_summary: str = ""
    recent_messages: list[MessageSlice] = []
    decision_nodes: list[IRNodeData] = []

    def to_prompt_text(self) -> str:
        """
        将上下文切片序列化为可嵌入 prompt 的文本。

        输出格式包含以下部分（按顺序）：
        1. IR 快照 — 节点和边的简明摘要
        2. 对话摘要 — 历史对话的总结
        3. 最近对话 — 最近几轮的原始消息
        4. 决策记录 — 已做出的架构决策

        空的部分会被跳过，不输出。
        - 返回: 格式化的上下文文本
        """
        sections: list[str] = []

        # IR 快照部分
        ir_section = self._format_ir_snapshot()
        if ir_section:
            sections.append(ir_section)

        # 对话摘要部分
        if self.conversation_summary:
            sections.append(
                f"## 对话摘要\n\n{self.conversation_summary}"
            )

        # 最近对话部分
        messages_section = self._format_recent_messages()
        if messages_section:
            sections.append(messages_section)

        # 决策记录部分
        decisions_section = self._format_decisions()
        if decisions_section:
            sections.append(decisions_section)

        if not sections:
            return "（暂无上下文信息）"

        return "\n\n".join(sections)

    def _format_ir_snapshot(self) -> str:
        """
        格式化 IR 快照部分。

        将节点和边转为简明的文本列表。
        - 返回: IR 快照的格式化文本，无数据时返回空字符串
        """
        if not self.ir_nodes and not self.ir_edges:
            return ""

        parts: list[str] = ["## IR 快照"]

        # 格式化节点
        if self.ir_nodes:
            parts.append("\n### 节点")
            for node in self.ir_nodes:
                # 提取 label，优先使用 props 中的 name
                name = node.props.get("name", node.label)
                parts.append(
                    f"- [{node.node_type}] {name} (id: {node.id})"
                )

        # 格式化边
        if self.ir_edges:
            parts.append("\n### 边")
            for edge in self.ir_edges:
                parts.append(
                    f"- {edge.source_node_id} --[{edge.edge_type}]--> "
                    f"{edge.target_node_id}"
                )

        return "\n".join(parts)

    def _format_recent_messages(self) -> str:
        """
        格式化最近对话消息部分。

        将消息列表格式化为可读的对话记录。
        - 返回: 对话消息的格式化文本，无消息时返回空字符串
        """
        if not self.recent_messages:
            return ""

        parts: list[str] = ["## 最近对话"]

        # 角色名称映射
        role_names = {
            "user": "用户",
            "assistant": "助手",
            "system": "系统",
        }

        for msg in self.recent_messages:
            role_label = role_names.get(msg.role, msg.role)
            parts.append(f"\n**{role_label}**: {msg.content}")

        return "\n".join(parts)

    def _format_decisions(self) -> str:
        """
        格式化决策记录部分。

        将 decision 类型的节点格式化为决策列表。
        - 返回: 决策记录的格式化文本，无决策时返回空字符串
        """
        if not self.decision_nodes:
            return ""

        parts: list[str] = ["## 决策记录"]

        for node in self.decision_nodes:
            title = node.props.get("title", node.label)
            status = node.props.get("status", "unknown")
            description = node.props.get("description", "")
            parts.append(f"\n### {title}")
            parts.append(f"- 状态: {status}")
            if description:
                parts.append(f"- 描述: {description}")

        return "\n".join(parts)
