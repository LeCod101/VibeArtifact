"""
Agent 上下文切片模块。

定义 ContextSlice 数据结构，用于封装 Agent 运行所需的工作区文件、
上游 Agent 输出和对话摘要。提供 to_prompt_text() 方法将切片序列化为
可嵌入 prompt 的可读文本。
"""

import json
from typing import Any

from pydantic import BaseModel

from agents.schemas.base import MessageSlice
from agents.schemas.workspace import WorkspaceFileData


class ContextSlice(BaseModel):
    """
    Agent 上下文切片。

    包含 Agent 运行所需的工作区文件、上游输出和对话摘要。
    是 ContextAssembler 的输出、PromptBuilder 的 context_slice 层输入。

    - workspace_files: 当前工作区的文件列表
    - upstream_outputs: 上游 Agent 的高层输出（agent_id → 输出字典）
    - conversation_summary: 对话历史的文本摘要
    - recent_messages: 最近几轮对话消息
    """

    workspace_files: list[WorkspaceFileData] = []
    upstream_outputs: dict[str, Any] = {}
    conversation_summary: str = ""
    recent_messages: list[MessageSlice] = []

    def to_prompt_text(self) -> str:
        """
        将上下文切片序列化为可嵌入 prompt 的文本。

        输出格式包含以下部分（按顺序）：
        1. 上游输出 — 前序 Agent 的结构化产出
        2. 工作区文件 — 已生成文件的路径清单与内容
        3. 对话摘要 — 历史对话的总结
        4. 最近对话 — 最近几轮的原始消息

        空的部分会被跳过，不输出。
        - 返回: 格式化的上下文文本
        """
        sections: list[str] = []

        upstream_section = self._format_upstream_outputs()
        if upstream_section:
            sections.append(upstream_section)

        files_section = self._format_workspace_files()
        if files_section:
            sections.append(files_section)

        if self.conversation_summary:
            sections.append(
                f"## 对话摘要\n\n{self.conversation_summary}"
            )

        messages_section = self._format_recent_messages()
        if messages_section:
            sections.append(messages_section)

        if not sections:
            return "（暂无上下文信息）"

        return "\n\n".join(sections)

    def _format_upstream_outputs(self) -> str:
        """
        格式化上游 Agent 输出部分。

        每个上游 Agent 的输出以 JSON 形式嵌入，供下游 Agent 参考。
        - 返回: 格式化文本，无数据时返回空字符串
        """
        if not self.upstream_outputs:
            return ""

        parts: list[str] = ["## 上游 Agent 输出"]
        for agent_id, output in self.upstream_outputs.items():
            parts.append(f"\n### {agent_id}")
            parts.append("```json")
            parts.append(
                json.dumps(output, ensure_ascii=False, indent=2, default=str)
            )
            parts.append("```")

        return "\n".join(parts)

    def _format_workspace_files(self) -> str:
        """
        格式化工作区文件部分。

        列出文件路径与类别，并附上文件内容，供 Agent 参考已有产物。
        - 返回: 格式化文本，无文件时返回空字符串
        """
        if not self.workspace_files:
            return ""

        parts: list[str] = ["## 工作区文件"]
        for f in self.workspace_files:
            parts.append(f"\n### [{f.kind}] {f.path}")
            parts.append("```")
            parts.append(f.content)
            parts.append("```")

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
