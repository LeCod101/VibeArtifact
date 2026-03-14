"""生成流程相关的请求和响应模型。

定义分析、收缩、确认 scope 等端点使用的
请求体和响应体 Schema。
"""

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """分析请求 - 用户输入产品想法。

    字段：
        user_idea: 用户输入的原始产品想法文本（1-2000 字符）
    """

    user_idea: str = Field(min_length=1, max_length=2000)


class ScopeItemResponse(BaseModel):
    """功能模块信息。

    字段：
        name: 功能名称
        description: 功能描述
        priority: 优先级（high / medium / low）
        tags: 功能标签列表
    """

    name: str
    description: str
    priority: str
    tags: list[str] = []


class ScopeDraftResponse(BaseModel):
    """功能范围草案。

    字段：
        product_name: 产品名称
        product_description: 产品总体描述
        scopes: 保留的功能模块列表
        deferred_items: 延后到未来版本的功能项
        risks: 识别到的风险清单
    """

    product_name: str
    product_description: str
    scopes: list[ScopeItemResponse]
    deferred_items: list[str] = []
    risks: list[str] = []


class DimensionCountResponse(BaseModel):
    """维度点数详情。

    字段：
        dimension: 容量维度名称
        count: 该维度的单位数量
        points: 该维度的点数
    """

    dimension: str
    count: int
    points: int


class CapacityReportResponse(BaseModel):
    """容量报告。

    字段：
        dimensions: 各维度的计数和点数明细
        total_points: 容量总点数
        tier: 分档结果（small / medium / large）
        budget: 当前分档的点数预算上限
        over_budget: 是否超出当前分档预算
        needs_contraction: 是否需要收缩
        must_contract: 是否必须收缩
    """

    dimensions: list[DimensionCountResponse]
    total_points: int
    tier: str
    budget: int
    over_budget: bool
    needs_contraction: bool
    must_contract: bool


class AnalyzeResponse(BaseModel):
    """分析结果 - ScopeDraft + CapacityReport。

    字段：
        scope_draft: 功能范围草案
        capacity_report: 容量评估报告
        warnings: 警告信息列表
    """

    scope_draft: ScopeDraftResponse
    capacity_report: CapacityReportResponse
    warnings: list[str] = []


class DeferredFeatureResponse(BaseModel):
    """延后功能。

    字段：
        name: 被延后的功能名称
        reason: 延后理由
    """

    name: str
    reason: str


class ContractionDecisionResponse(BaseModel):
    """收缩决策。

    字段：
        retained_features: 保留的功能名称列表
        deferred_features: 延后的功能列表
        risks: 收缩带来的风险描述列表
        rationale: 整体收缩理由
    """

    retained_features: list[str]
    deferred_features: list[DeferredFeatureResponse]
    risks: list[str]
    rationale: str


class ContractRequest(BaseModel):
    """收缩请求 - 从前端传回 scope_draft 和 capacity_report。

    字段：
        scope_draft: 功能范围草案
        capacity_report: 容量评估报告
    """

    scope_draft: ScopeDraftResponse
    capacity_report: CapacityReportResponse


class ContractResponse(BaseModel):
    """收缩结果。

    字段：
        scope_draft: 收缩后的功能范围草案
        decision: 收缩决策详情
        capacity_before: 收缩前的容量报告
        capacity_after: 收缩后的容量报告
        warnings: 警告信息列表
    """

    scope_draft: ScopeDraftResponse
    decision: ContractionDecisionResponse
    capacity_before: CapacityReportResponse
    capacity_after: CapacityReportResponse
    warnings: list[str] = []


class ConfirmScopeRequest(BaseModel):
    """确认 scope 请求。

    用户可微调：手动恢复或延后功能。
    可选传回当前 scope_draft，用于重新计算容量。

    字段：
        restore_features: 要恢复的功能名称列表
        defer_features: 要延后的功能名称列表
        scope_draft: 当前功能范围草案（可选，传入时将重新计算容量）
    """

    restore_features: list[str] = []
    defer_features: list[str] = []
    scope_draft: ScopeDraftResponse | None = None


class ConfirmScopeResponse(BaseModel):
    """确认 scope 结果。

    字段：
        scope_draft: 最终确认的功能范围草案
        capacity_report: 对应的容量报告
        confirmed: 是否已确认
        message: 确认结果提示信息
    """

    scope_draft: ScopeDraftResponse
    capacity_report: CapacityReportResponse
    confirmed: bool
    message: str
