"""
上下文 Token 预算控制器模块。

按优先级截断上下文，确保不超过模型的 token 限制。
优先级规则（技术架构 5.2）：
1. 当前任务目标（不截断）
2. 当前快照 IR slice
3. decision nodes
4. 最近若干轮对话
5. 历史摘要
"""

import math

from agents.context.slice import ContextSlice

# 中文文本的 token 估算系数：1 token 约 3.5 个字符
_CHARS_PER_TOKEN = 3.5

# 默认最大 token 数
_DEFAULT_MAX_TOKENS = 8000


class ContextBudget:
    """
    上下文 token 预算控制器。

    按优先级截断上下文，确保不超过模型的 token 限制。
    高优先级的内容优先保留，低优先级的内容在预算不足时被截断或丢弃。

    优先级从高到低：
    1. IR 节点（核心数据，优先保留）
    2. IR 边（结构关系，其次保留）
    3. 决策节点（架构记录，第三保留）
    4. 最近对话（上下文参考，第四保留）
    5. 对话摘要（历史概要，最后保留）
    """

    def __init__(self, max_tokens: int = _DEFAULT_MAX_TOKENS) -> None:
        """
        初始化预算控制器。

        - max_tokens: 上下文最大 token 数，默认 8000
        """
        self.max_tokens = max_tokens

    def truncate(self, context_slice: ContextSlice) -> ContextSlice:
        """
        按优先级截断上下文切片。

        从高优先级到低优先级逐步添加内容，当累计 token 数接近上限时
        停止添加后续内容。已部分添加的列表会被截断到当前位置。

        - context_slice: 原始的上下文切片
        - 返回: 截断后的新 ContextSlice（不修改原对象）
        """
        remaining_tokens = self.max_tokens

        # 优先级 1：IR 节点
        truncated_nodes, used = self._truncate_list_by_budget(
            context_slice.ir_nodes,
            remaining_tokens,
        )
        remaining_tokens -= used

        # 优先级 2：IR 边
        truncated_edges, used = self._truncate_list_by_budget(
            context_slice.ir_edges,
            remaining_tokens,
        )
        remaining_tokens -= used

        # 优先级 3：决策节点
        truncated_decisions, used = self._truncate_list_by_budget(
            context_slice.decision_nodes,
            remaining_tokens,
        )
        remaining_tokens -= used

        # 优先级 4：最近对话消息
        truncated_messages, used = self._truncate_list_by_budget(
            context_slice.recent_messages,
            remaining_tokens,
        )
        remaining_tokens -= used

        # 优先级 5：对话摘要（按字符截断）
        truncated_summary = self._truncate_text_by_budget(
            context_slice.conversation_summary,
            remaining_tokens,
        )

        return ContextSlice(
            ir_nodes=truncated_nodes,
            ir_edges=truncated_edges,
            conversation_summary=truncated_summary,
            recent_messages=truncated_messages,
            decision_nodes=truncated_decisions,
        )

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        估算文本的 token 数。

        使用简单的字符数除以系数来估算，适用于中英文混合文本。
        中文约 1 token/1.5-2 字符，英文约 1 token/4 字符，
        取折中值 3.5 字符/token。

        - text: 待估算的文本
        - 返回: 估算的 token 数（向上取整）
        """
        if not text:
            return 0
        return math.ceil(len(text) / _CHARS_PER_TOKEN)

    def _truncate_list_by_budget(
        self,
        items: list,
        budget_tokens: int,
    ) -> tuple[list, int]:
        """
        按 token 预算截断列表。

        逐项序列化并估算 token 数，直到预算耗尽。
        - items: 待截断的 Pydantic model 列表
        - budget_tokens: 可用的 token 预算
        - 返回: (截断后的列表, 实际消耗的 token 数)
        """
        if budget_tokens <= 0 or not items:
            return [], 0

        result = []
        total_used = 0

        for item in items:
            # 将 Pydantic model 序列化为 JSON 字符串来估算
            item_text = item.model_dump_json()
            item_tokens = self.estimate_tokens(item_text)

            # 检查是否超出预算
            if total_used + item_tokens > budget_tokens:
                break

            result.append(item)
            total_used += item_tokens

        return result, total_used

    def _truncate_text_by_budget(
        self,
        text: str,
        budget_tokens: int,
    ) -> str:
        """
        按 token 预算截断文本。

        如果文本超出预算，按字符数截断并添加省略标记。
        - text: 待截断的文本
        - budget_tokens: 可用的 token 预算
        - 返回: 截断后的文本
        """
        if not text or budget_tokens <= 0:
            return ""

        text_tokens = self.estimate_tokens(text)
        if text_tokens <= budget_tokens:
            return text

        # 按预算比例截断字符数
        max_chars = int(budget_tokens * _CHARS_PER_TOKEN)
        if max_chars <= 0:
            return ""

        # 预留省略标记的空间
        ellipsis_marker = "…（已截断）"
        available_chars = max_chars - len(ellipsis_marker)
        if available_chars <= 0:
            return ""

        return text[:available_chars] + ellipsis_marker
