"""
Author↔Reviewer 多轮协作循环（LangGraph 实现）。

用 LangGraph StateGraph 驱动"author 写 → reviewer 评 → author 改"的
有界循环：reviewer 给出 approve 或达到轮次上限时结束。

设计边界：本图完全在触发它的那个 Celery task 内部同步跑完再返回，
不使用 LangGraph checkpointer / 跨进程持久化——图状态就是普通
Python 对象，生命周期等于一次 Celery task 执行。跨 worker 的分布式
调度、超时、重试仍由 Celery 负责（分层架构：LangGraph 管单次对话
怎么循环，Celery 管这些循环怎么分布式跑）。
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, TypedDict

from pydantic import BaseModel

from agents.schemas.base import AgentInput
from agents.schemas.review import ReviewFeedback, ReviewInput, ReviewVerdict
from agents.schemas.workspace import WorkspaceFileData

logger = logging.getLogger(__name__)

# 默认最大轮次（与 RepairLoop 的单次重试哲学对齐，评审给到 3 轮）
DEFAULT_MAX_ROUNDS = 3

# 轮次事件回调类型：(event, payload) -> None
# event 取值 "review_round_start" / "review_verdict"
TurnEventCallback = Callable[[str, dict], Awaitable[None]]


class ReviewTurnRecord(BaseModel):
    """
    单轮评审记录（落库 conversation_turns 表的内存态）。

    - agent_id: author Agent 标识
    - role: "author" 或 "reviewer"
    - round_number: 轮次（从 1 开始）
    - verdict: reviewer 轮的评审结论（author 轮为空）
    - content_summary: 本轮产出摘要
    """

    agent_id: str
    role: str
    round_number: int
    verdict: str = ""
    content_summary: str = ""


class PairRunResult(BaseModel):
    """
    author↔reviewer 配对执行结果。

    - files: 最终版本的产物文件列表（path/content/kind）
    - approved: reviewer 是否最终批准
    - rounds: 实际执行的轮次数
    - turns: 全部轮次记录（含 author 和 reviewer）
    - warnings: 过程中累积的警告
    """

    files: list[dict] = []
    approved: bool = False
    rounds: int = 0
    turns: list[ReviewTurnRecord] = []
    warnings: list[str] = []


class _PairState(TypedDict):
    """LangGraph 图状态。"""

    round_number: int
    files: list[dict]
    review: ReviewFeedback | None
    turns: list[ReviewTurnRecord]
    warnings: list[str]


class ConversationGraph:
    """
    author↔reviewer 多轮协作循环执行器。

    以 LangGraph StateGraph 组织两个节点：
    - author: 调用 AgentRunner 执行 author（首轮生成 / 后续按意见修订）
    - reviewer: 调用 AgentRunner 执行配对 reviewer，产出 verdict

    条件边：revise 且轮次未达上限 → 回到 author；否则 END。
    """

    def __init__(
        self,
        runner,
        max_rounds: int = DEFAULT_MAX_ROUNDS,
        on_event: TurnEventCallback | None = None,
    ) -> None:
        """
        初始化协作循环执行器。

        - runner: AgentRunner 实例（单轮执行原语）
        - max_rounds: 最大轮次上限，默认 3
        - on_event: 轮次事件回调（可选，用于 SSE 发布）
        """
        self._runner = runner
        self._max_rounds = max_rounds
        self._on_event = on_event

    async def run_pair(
        self,
        author_id: str,
        reviewer_id: str,
        agent_input: AgentInput,
    ) -> PairRunResult:
        """
        执行一次完整的 author↔reviewer 多轮循环。

        - author_id: author Agent 标识（如 "backend"）
        - reviewer_id: 配对 reviewer Agent 标识（如 "backend_reviewer"）
        - agent_input: author 的初始输入（上游输出、任务描述等）
        - 返回: PairRunResult，files 为最终通过（或达上限时最后一版）的文件
        """
        graph = self._build_graph(author_id, reviewer_id, agent_input)

        initial_state: _PairState = {
            "round_number": 0,
            "files": [],
            "review": None,
            "turns": [],
            "warnings": [],
        }

        final_state = await graph.ainvoke(initial_state)

        review = final_state["review"]
        approved = (
            review is not None and review.verdict == ReviewVerdict.APPROVE
        )
        warnings = list(final_state["warnings"])

        if not approved:
            warnings.append(
                f"'{author_id}' 经 {final_state['round_number']} 轮评审仍未通过"
                f"（needs_review），保留最后一版产物继续流程"
            )

        return PairRunResult(
            files=final_state["files"],
            approved=approved,
            rounds=final_state["round_number"],
            turns=final_state["turns"],
            warnings=warnings,
        )

    def _build_graph(
        self,
        author_id: str,
        reviewer_id: str,
        base_input: AgentInput,
    ):
        """
        构建 author↔reviewer 的 LangGraph 状态图。

        - author_id: author Agent 标识
        - reviewer_id: reviewer Agent 标识
        - base_input: author 的初始输入
        - 返回: 编译后的 LangGraph 图
        """
        from langgraph.graph import END, StateGraph

        async def author_node(state: _PairState) -> dict:
            """author 节点：首轮生成 / 按 reviewer 意见修订。"""
            round_number = state["round_number"] + 1
            await self._emit(
                "review_round_start",
                {
                    "agent_id": author_id,
                    "reviewer_id": reviewer_id,
                    "round_number": round_number,
                    "max_rounds": self._max_rounds,
                },
            )

            # 后续轮次把 reviewer 意见注入 extra.fix_context
            extra = dict(base_input.extra)
            review = state["review"]
            if review is not None:
                extra["fix_context"] = {
                    "review_summary": review.summary,
                    "review_comments": [
                        c.model_dump(mode="json") for c in review.comments
                    ],
                }
                extra["is_revision"] = True

            author_input = base_input.model_copy(
                update={"extra": extra},
            )

            result = await self._runner.run(author_id, author_input)

            turn = ReviewTurnRecord(
                agent_id=author_id,
                role="author",
                round_number=round_number,
                content_summary=(
                    f"产出 {len(result.files)} 个文件"
                    + ("（按评审意见修订）" if review is not None else "")
                ),
            )

            return {
                "round_number": round_number,
                "files": result.files,
                "turns": state["turns"] + [turn],
                "warnings": state["warnings"] + list(result.warnings),
            }

        async def reviewer_node(state: _PairState) -> dict:
            """reviewer 节点：评审 author 本轮产出。"""
            review_input = ReviewInput(
                project_id=base_input.project_id,
                run_id=base_input.run_id,
                workspace_files=[
                    WorkspaceFileData(
                        path=f["path"],
                        content=f["content"],
                        kind=f.get("kind", "code"),
                    )
                    for f in state["files"]
                ],
                upstream_outputs=base_input.upstream_outputs,
                conversation_context=[],
                task_description=(
                    f"评审 {author_id} agent 第 {state['round_number']} 轮的产出文件"
                ),
                author_agent_id=author_id,
                round_number=state["round_number"],
            )

            result = await self._runner.run(reviewer_id, review_input)
            review: ReviewFeedback = getattr(result.output, "review")

            await self._emit(
                "review_verdict",
                {
                    "agent_id": author_id,
                    "reviewer_id": reviewer_id,
                    "round_number": state["round_number"],
                    "verdict": str(review.verdict),
                    "summary": review.summary,
                },
            )

            turn = ReviewTurnRecord(
                agent_id=author_id,
                role="reviewer",
                round_number=state["round_number"],
                verdict=str(review.verdict),
                content_summary=review.summary
                or f"{len(review.comments)} 条意见",
            )

            return {
                "review": review,
                "turns": state["turns"] + [turn],
                "warnings": state["warnings"] + list(result.warnings),
            }

        def should_continue(state: _PairState) -> str:
            """条件边：revise 且未达上限 → author；否则 END。"""
            review = state["review"]
            if (
                review is not None
                and review.verdict == ReviewVerdict.REVISE
                and state["round_number"] < self._max_rounds
            ):
                return "author"
            return END

        builder = StateGraph(_PairState)
        builder.add_node("author", author_node)
        builder.add_node("reviewer", reviewer_node)
        builder.set_entry_point("author")
        builder.add_edge("author", "reviewer")
        builder.add_conditional_edges("reviewer", should_continue)

        return builder.compile()

    async def _emit(self, event: str, payload: dict[str, Any]) -> None:
        """
        发布轮次事件（回调存在时）。

        回调异常不中断主流程，仅记录日志。
        """
        if self._on_event is None:
            return
        try:
            await self._on_event(event, payload)
        except Exception:
            logger.warning("轮次事件回调失败: %s", event, exc_info=True)
