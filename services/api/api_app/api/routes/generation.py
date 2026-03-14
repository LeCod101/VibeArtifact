"""生成流程路由 - 实现分析、收缩、确认 scope 等端点。

M4 阶段不接入真实 LLM，所有 Agent 逻辑用 Python 规则模拟。
前端可完整跑通 analyze → contract → confirm-scope 流程。
M5 替换 _mock_analyze / _mock_contract 为真实 LLM 调用即可。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from agents.capacity.calculator import CapacityCalculator, CapacityReport
from agents.schemas.contraction import ContractionDecision, DeferredFeature
from agents.schemas.high_level import ScopeDraft, ScopeItem
from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.generation import (
    AnalyzeRequest,
    AnalyzeResponse,
    CapacityReportResponse,
    ConfirmScopeRequest,
    ConfirmScopeResponse,
    ContractRequest,
    ContractResponse,
    ContractionDecisionResponse,
    DeferredFeatureResponse,
    DimensionCountResponse,
    ScopeDraftResponse,
    ScopeItemResponse,
)
from api_app.application.services.project_service import ProjectService

router = APIRouter(
    prefix="/projects/{project_id}/generation",
    tags=["generation"],
)

# ============================================================
# 内部转换工具函数
# ============================================================


def _scope_draft_to_response(draft: ScopeDraft) -> ScopeDraftResponse:
    """将内部 ScopeDraft 转换为 API 响应模型。

    参数：
        draft: agents 层的 ScopeDraft 对象

    返回：
        ScopeDraftResponse API 响应对象
    """
    return ScopeDraftResponse(
        product_name=draft.product_name,
        product_description=draft.product_description,
        scopes=[
            ScopeItemResponse(
                name=s.name,
                description=s.description,
                priority=s.priority.value,
                tags=s.tags,
            )
            for s in draft.scopes
        ],
        deferred_items=draft.deferred_items,
        risks=draft.risks,
    )


def _capacity_report_to_response(
    report: CapacityReport,
) -> CapacityReportResponse:
    """将内部 CapacityReport 转换为 API 响应模型。

    参数：
        report: agents 层的 CapacityReport 对象

    返回：
        CapacityReportResponse API 响应对象
    """
    return CapacityReportResponse(
        dimensions=[
            DimensionCountResponse(
                dimension=d.dimension.value,
                count=d.count,
                points=d.points,
            )
            for d in report.dimensions
        ],
        total_points=report.total_points,
        tier=report.tier.value,
        budget=report.budget,
        over_budget=report.over_budget,
        needs_contraction=report.needs_contraction,
        must_contract=report.must_contract,
    )


def _response_to_scope_draft(resp: ScopeDraftResponse) -> ScopeDraft:
    """将 API 请求中的 ScopeDraftResponse 还原为内部 ScopeDraft。

    前端传回 scope_draft 时需要还原为 agents 层对象，
    以便调用 CapacityCalculator。

    参数：
        resp: 前端传来的 ScopeDraftResponse

    返回：
        agents 层的 ScopeDraft 对象
    """
    from ir_core.schema.node_types import Priority

    return ScopeDraft(
        product_name=resp.product_name,
        product_description=resp.product_description,
        scopes=[
            ScopeItem(
                name=s.name,
                description=s.description,
                priority=Priority(s.priority),
                tags=s.tags,
            )
            for s in resp.scopes
        ],
        deferred_items=resp.deferred_items,
        risks=resp.risks,
    )


# ============================================================
# Mock 函数 - M4 阶段模拟 Agent 输出
# ============================================================

# 关键词 → 功能模块映射表
_KEYWORD_MODULES: dict[str, tuple[str, str, list[str]]] = {
    # 关键词: (模块名, 描述, tags)
    "todo": ("任务管理", "创建、编辑和跟踪待办任务", ["crud"]),
    "任务": ("任务管理", "创建、编辑和跟踪待办任务", ["crud"]),
    "task": ("任务管理", "创建、编辑和跟踪待办任务", ["crud"]),
    "blog": ("博客系统", "文章发布、分类和标签管理", ["crud"]),
    "博客": ("博客系统", "文章发布、分类和标签管理", ["crud"]),
    "文章": ("博客系统", "文章发布、分类和标签管理", ["crud"]),
    "电商": ("商品管理", "商品展示、分类和搜索", ["crud"]),
    "shop": ("商品管理", "商品展示、分类和搜索", ["crud"]),
    "商品": ("商品管理", "商品展示、分类和搜索", ["crud"]),
    "订单": ("订单管理", "订单创建、支付和状态跟踪", ["crud", "payment"]),
    "order": ("订单管理", "订单创建、支付和状态跟踪", ["crud", "payment"]),
    "chat": ("即时通讯", "实时消息发送和接收", ["realtime"]),
    "聊天": ("即时通讯", "实时消息发送和接收", ["realtime"]),
    "upload": ("文件上传", "支持图片和文件上传管理", ["upload"]),
    "上传": ("文件上传", "支持图片和文件上传管理", ["upload"]),
    "文件": ("文件上传", "支持图片和文件上传管理", ["upload"]),
    "登录": ("用户认证", "注册、登录和权限管理", ["auth"]),
    "auth": ("用户认证", "注册、登录和权限管理", ["auth"]),
    "login": ("用户认证", "注册、登录和权限管理", ["auth"]),
    "支付": ("支付集成", "在线支付和账单管理", ["payment"]),
    "pay": ("支付集成", "在线支付和账单管理", ["payment"]),
    "payment": ("支付集成", "在线支付和账单管理", ["payment"]),
}

# 默认通用模块（任何项目都会包含的基础功能）
_DEFAULT_MODULES: list[tuple[str, str, str, list[str]]] = [
    ("用户管理", "用户注册、登录和个人信息管理", "high", ["auth"]),
    ("首页仪表盘", "项目概览和数据汇总展示", "medium", ["crud"]),
]


def _mock_analyze(user_idea: str) -> ScopeDraft:
    """模拟 intent_agent 的输出。

    根据 user_idea 中的关键词匹配生成合理的 ScopeDraft。
    M5 替换为真实 LLM 调用。

    参数：
        user_idea: 用户输入的产品想法文本

    返回：
        ScopeDraft 功能范围草案
    """
    from ir_core.schema.node_types import Priority

    idea_lower = user_idea.lower()
    scopes: list[ScopeItem] = []

    # 已添加的模块名称，避免重复
    added_names: set[str] = set()

    # 根据关键词匹配添加对应模块
    for keyword, (name, desc, tags) in _KEYWORD_MODULES.items():
        if keyword in idea_lower and name not in added_names:
            scopes.append(
                ScopeItem(
                    name=name,
                    description=desc,
                    priority=Priority.MEDIUM,
                    tags=tags,
                )
            )
            added_names.add(name)

    # 添加默认通用模块（如果还未被关键词匹配添加）
    for name, desc, priority_str, tags in _DEFAULT_MODULES:
        if name not in added_names:
            scopes.append(
                ScopeItem(
                    name=name,
                    description=desc,
                    priority=Priority(priority_str),
                    tags=tags,
                )
            )
            added_names.add(name)

    # 如果匹配到的模块不足 3 个，添加一个核心功能占位模块
    if len(scopes) < 3:
        scopes.append(
            ScopeItem(
                name="核心功能",
                description=f"基于「{user_idea[:20]}」的核心业务逻辑",
                priority=Priority.HIGH,
                tags=["crud"],
            )
        )

    # 从 user_idea 生成产品名称（取前 10 个字符）
    product_name = user_idea[:10].strip() or "新产品"
    if len(user_idea) > 10:
        product_name += "..."

    return ScopeDraft(
        product_name=product_name,
        product_description=f"基于用户想法自动生成的 MVP 方案：{user_idea[:50]}",
        scopes=scopes,
        deferred_items=[],
        risks=["M4 阶段为模拟数据，实际风险需 LLM 评估"],
    )


def _mock_contract(
    scope_draft: ScopeDraft,
    capacity_report: CapacityReport,
) -> tuple[ScopeDraft, ContractionDecision]:
    """模拟 contraction_agent 的收缩逻辑。

    按优先级从低到高裁剪功能模块，直到总点数降到 60 以下。
    M5 替换为真实 LLM 调用。

    参数：
        scope_draft: 原始功能范围草案
        capacity_report: 原始容量评估报告

    返回：
        (收缩后的 ScopeDraft, 收缩决策 ContractionDecision)
    """
    from ir_core.schema.node_types import Priority

    # 按优先级排序：high 排前面优先保留，low 排后面优先被裁剪
    priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    sorted_scopes = sorted(
        scope_draft.scopes,
        key=lambda s: priority_order.get(s.priority, 1),
    )

    retained: list[ScopeItem] = []
    deferred: list[DeferredFeature] = []
    calculator = CapacityCalculator()

    # 预算目标：medium 档上限 60 点
    target_budget = 60

    # 先尝试保留所有功能，再逐步裁剪 low priority 的
    for scope in sorted_scopes:
        # 试探性地加入该功能，检查是否超预算
        test_scopes = retained + [scope]
        test_draft = ScopeDraft(
            product_name=scope_draft.product_name,
            product_description=scope_draft.product_description,
            scopes=test_scopes,
        )
        test_report = calculator.calculate(test_draft)

        if test_report.total_points <= target_budget:
            retained.append(scope)
        else:
            # 高优先级功能即使超预算也保留
            if scope.priority == Priority.HIGH:
                retained.append(scope)
            else:
                deferred.append(
                    DeferredFeature(
                        name=scope.name,
                        reason=f"容量超出预算，优先级为 {scope.priority.value}，延后到后续版本",
                    )
                )

    # 构建收缩后的 ScopeDraft
    contracted_draft = ScopeDraft(
        product_name=scope_draft.product_name,
        product_description=scope_draft.product_description,
        scopes=retained,
        deferred_items=[d.name for d in deferred] + scope_draft.deferred_items,
        risks=scope_draft.risks + ["收缩可能导致部分功能缺失，需用户确认"],
    )

    decision = ContractionDecision(
        retained_features=[s.name for s in retained],
        deferred_features=deferred,
        risks=["裁剪后功能较少，用户体验可能受影响"],
        rationale=f"为控制 MVP 规模，将容量从 {capacity_report.total_points} 点收缩至预算内",
    )

    return contracted_draft, decision


# ============================================================
# 辅助函数：验证项目归属
# ============================================================


async def _get_user_project(
    project_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """验证项目属于当前用户，不属于则抛出 404。

    参数：
        project_id: 项目 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    异常：
        HTTPException 404: 项目不存在或不属于当前用户
    """
    service = ProjectService(db)
    project = await service.get_project(project_id)

    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )


# ============================================================
# API 端点
# ============================================================


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    project_id: UUID,
    body: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResponse:
    """分析用户的产品想法，生成功能范围草案和容量报告。

    流程：
    1. 验证项目属于当前用户
    2. 从 user_idea 生成 ScopeDraft（M4 用 mock）
    3. 用 CapacityCalculator 计算容量
    4. 返回 AnalyzeResponse

    参数：
        project_id: 项目 UUID（路径参数）
        body: 包含 user_idea 的请求体
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        AnalyzeResponse（scope_draft + capacity_report）
    """
    await _get_user_project(project_id, current_user, db)

    # M4 使用 mock 函数模拟 intent_agent 输出
    scope_draft = _mock_analyze(body.user_idea)

    # 计算容量
    calculator = CapacityCalculator()
    report = calculator.calculate(scope_draft)

    # 构建警告信息
    warnings: list[str] = []
    if report.must_contract:
        warnings.append("项目规模较大，必须进行收缩才能继续")
    elif report.needs_contraction:
        warnings.append("项目规模中等，建议进行收缩以优化 MVP")

    return AnalyzeResponse(
        scope_draft=_scope_draft_to_response(scope_draft),
        capacity_report=_capacity_report_to_response(report),
        warnings=warnings,
    )


@router.post("/contract", response_model=ContractResponse)
async def contract(
    project_id: UUID,
    body: ContractRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    """对功能范围进行收缩，裁剪非 MVP 功能。

    流程：
    1. 验证项目属于当前用户
    2. 如果 tier 为 small，返回 400（不需要收缩）
    3. 模拟 contraction_agent 进行收缩
    4. 重新计算收缩后的容量
    5. 返回 ContractResponse

    参数：
        project_id: 项目 UUID（路径参数）
        body: 包含 scope_draft 和 capacity_report 的请求体
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        ContractResponse（收缩后的 scope + decision + 前后容量对比）

    异常：
        400: 项目已是 small 档，无需收缩
    """
    await _get_user_project(project_id, current_user, db)

    # small 档不需要收缩
    if body.capacity_report.tier == "small":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目已在 small 分档内，无需收缩",
        )

    # 还原为内部数据结构
    original_draft = _response_to_scope_draft(body.scope_draft)

    # 计算原始容量（用内部 calculator 重新算，确保一致）
    calculator = CapacityCalculator()
    original_report = calculator.calculate(original_draft)

    # M4 使用 mock 函数模拟 contraction_agent
    contracted_draft, decision = _mock_contract(
        original_draft, original_report
    )

    # 计算收缩后的容量
    contracted_report = calculator.calculate(contracted_draft)

    # 构建警告信息
    warnings: list[str] = []
    if contracted_report.needs_contraction:
        warnings.append("收缩后仍超出 small 档预算，可能需要进一步调整")
    if len(decision.deferred_features) > 0:
        warnings.append(
            f"已延后 {len(decision.deferred_features)} 个功能到未来版本"
        )

    return ContractResponse(
        scope_draft=_scope_draft_to_response(contracted_draft),
        decision=ContractionDecisionResponse(
            retained_features=decision.retained_features,
            deferred_features=[
                DeferredFeatureResponse(
                    name=f.name,
                    reason=f.reason,
                )
                for f in decision.deferred_features
            ],
            risks=decision.risks,
            rationale=decision.rationale,
        ),
        capacity_before=_capacity_report_to_response(original_report),
        capacity_after=_capacity_report_to_response(contracted_report),
        warnings=warnings,
    )


@router.post("/confirm-scope", response_model=ConfirmScopeResponse)
async def confirm_scope(
    project_id: UUID,
    body: ConfirmScopeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConfirmScopeResponse:
    """确认功能范围，锁定 scope。

    用户可在确认时微调：恢复或延后部分功能。
    M4 阶段仅返回确认成功，不持久化到数据库。

    参数：
        project_id: 项目 UUID（路径参数）
        body: 包含 restore_features 和 defer_features 的请求体
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        ConfirmScopeResponse（确认结果）
    """
    await _get_user_project(project_id, current_user, db)

    # 如果前端传回了 scope_draft，使用 CapacityCalculator 重新计算
    if body.scope_draft is not None:
        internal_draft = _response_to_scope_draft(body.scope_draft)
        calculator = CapacityCalculator()
        report = calculator.calculate(internal_draft)

        confirmed_draft = body.scope_draft
        confirmed_report = _capacity_report_to_response(report)
    else:
        # M4 阶段：未传 scope_draft 时使用占位数据并给出警告
        confirmed_draft = ScopeDraftResponse(
            product_name="已确认",
            product_description="scope 已锁定",
            scopes=[],
            deferred_items=[],
            risks=[],
        )
        confirmed_report = CapacityReportResponse(
            dimensions=[],
            total_points=0,
            tier="small",
            budget=30,
            over_budget=False,
            needs_contraction=False,
            must_contract=False,
        )

    message = "Scope 已确认"
    if body.restore_features:
        message += f"，恢复了 {len(body.restore_features)} 个功能"
    if body.defer_features:
        message += f"，延后了 {len(body.defer_features)} 个功能"
    if body.scope_draft is None:
        message += "（警告：未传入 scope_draft，返回占位数据）"

    return ConfirmScopeResponse(
        scope_draft=confirmed_draft,
        capacity_report=confirmed_report,
        confirmed=True,
        message=message,
    )


@router.get("/capacity", response_model=CapacityReportResponse)
async def get_capacity(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CapacityReportResponse:
    """获取项目的容量报告。

    M4 阶段返回空的默认容量报告。
    后续 M5 从数据库读取已保存的 scope_draft 并计算。

    参数：
        project_id: 项目 UUID（路径参数）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        CapacityReportResponse（容量报告）
    """
    await _get_user_project(project_id, current_user, db)

    # M4 阶段返回空报告占位
    # 后续 M5 从数据库读取 scope_draft 并重新计算
    return CapacityReportResponse(
        dimensions=[],
        total_points=0,
        tier="small",
        budget=30,
        over_budget=False,
        needs_contraction=False,
        must_contract=False,
    )
