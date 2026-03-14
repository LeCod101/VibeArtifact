"""
容量计算器模块。

从 ScopeDraft 推算各维度的数量，计算容量总点数，
生成包含分档、预算、是否需要收缩等信息的报告。
"""

from pydantic import BaseModel

from agents.capacity.rules import CapacityDimension, CapacityRule, DEFAULT_RULES
from agents.capacity.tiers import (
    CapacityTier,
    TIER_BUDGETS,
    can_skip_contraction,
    get_tier,
    is_over_budget,
)
from agents.schemas.high_level import ScopeDraft


class DimensionCount(BaseModel):
    """
    单个维度的计数结果。

    - dimension: 容量维度
    - count: 该维度的单位数量
    - points: 该维度的点数（= count * unit_cost）
    """

    dimension: CapacityDimension
    count: int
    points: int


class CapacityReport(BaseModel):
    """
    容量评估报告。

    - dimensions: 各维度的计数和点数明细
    - total_points: 容量总点数
    - tier: 分档结果
    - budget: 当前分档的点数预算上限（large 无上限则为 -1）
    - over_budget: 是否超出当前分档预算
    - needs_contraction: 是否需要收缩（medium 建议，large 强制）
    - must_contract: 是否必须收缩（仅 large 为 True）
    """

    dimensions: list[DimensionCount]
    total_points: int
    tier: CapacityTier
    budget: int
    over_budget: bool
    needs_contraction: bool
    must_contract: bool
    warnings: list[str] = []


# 用于从 scope tags 中检测特殊维度的关键词集合
_AUTH_TAGS = {"auth", "login", "register", "认证", "登录", "注册"}
_INTEGRATION_TAGS = {"integration", "third-party", "外部", "集成", "第三方"}
_UPLOAD_TAGS = {"upload", "file", "上传", "文件"}
_REALTIME_TAGS = {"realtime", "websocket", "实时"}
_PAYMENT_TAGS = {"payment", "pay", "支付"}


class CapacityCalculator:
    """
    容量计算器。

    根据规则表将 ScopeDraft 转换为容量报告。
    支持自定义规则，默认使用 DEFAULT_RULES。
    """

    def __init__(
        self,
        rules: dict[CapacityDimension, CapacityRule] | None = None,
    ) -> None:
        """
        初始化计算器。

        - rules: 自定义规则字典，为 None 时使用默认规则表
        """
        self._rules = rules if rules is not None else DEFAULT_RULES

    def calculate(self, scope_draft: ScopeDraft) -> CapacityReport:
        """
        从 ScopeDraft 计算容量报告。

        简化推算逻辑：
        - pages: scopes 数量（每个功能模块约 1 页面）
        - api_endpoints: scopes 数量 * 2（每个模块平均 2 个端点）
        - db_tables: scopes 数量（每个功能约 1 张表）
        - auth_flows: tags 中包含认证相关关键词的 scope 数量
        - integrations: tags 中包含集成相关关键词的 scope 数量
        - file_upload: 任意 scope 含上传标签则为 1，否则 0
        - realtime: 任意 scope 含实时标签则为 1，否则 0
        - payment: 任意 scope 含支付标签则为 1，否则 0

        - scope_draft: 功能范围草案
        - 返回: 容量评估报告
        """
        scopes = scope_draft.scopes
        num_scopes = len(scopes)

        # 收集所有 scope 的 tags（统一小写）
        all_tags_per_scope: list[set[str]] = []
        for scope in scopes:
            all_tags_per_scope.append({t.lower() for t in scope.tags})

        # 按维度统计数量
        raw_counts: dict[CapacityDimension, int] = {}

        # 基础维度：基于 scope 数量推算
        raw_counts[CapacityDimension.PAGES] = num_scopes
        raw_counts[CapacityDimension.API_ENDPOINTS] = num_scopes * 2
        raw_counts[CapacityDimension.DB_TABLES] = num_scopes

        # auth_flows：统计包含认证标签的 scope 数量
        auth_count = 0
        for tags in all_tags_per_scope:
            if tags & _AUTH_TAGS:
                auth_count += 1
        raw_counts[CapacityDimension.AUTH_FLOWS] = auth_count

        # integrations：统计包含集成标签的 scope 数量
        integration_count = 0
        for tags in all_tags_per_scope:
            if tags & _INTEGRATION_TAGS:
                integration_count += 1
        raw_counts[CapacityDimension.INTEGRATIONS] = integration_count

        # file_upload / realtime / payment：布尔型维度（0 或 1）
        raw_counts[CapacityDimension.FILE_UPLOAD] = self._has_any_tag(
            all_tags_per_scope, _UPLOAD_TAGS
        )
        raw_counts[CapacityDimension.REALTIME] = self._has_any_tag(
            all_tags_per_scope, _REALTIME_TAGS
        )
        raw_counts[CapacityDimension.PAYMENT] = self._has_any_tag(
            all_tags_per_scope, _PAYMENT_TAGS
        )

        # 根据规则表计算每个维度的点数（受 max_units 上限约束）
        dimension_counts: list[DimensionCount] = []
        total = 0

        for dim in CapacityDimension:
            rule = self._rules[dim]
            # 实际数量不超过规则的 max_units
            clamped = min(raw_counts.get(dim, 0), rule.max_units)
            points = clamped * rule.unit_cost
            dimension_counts.append(
                DimensionCount(dimension=dim, count=clamped, points=points)
            )
            total += points

        tier = get_tier(total)
        budget = TIER_BUDGETS.get(tier, -1)
        over = is_over_budget(total, tier)

        # medium 建议收缩，large 强制收缩
        needs = tier in (CapacityTier.MEDIUM, CapacityTier.LARGE)
        must = tier == CapacityTier.LARGE

        # 检测 payment 维度，Phase 1 不支持支付，生成警告
        warnings: list[str] = []
        if raw_counts.get(CapacityDimension.PAYMENT, 0) > 0:
            warnings.append(
                "检测到支付相关功能，Phase 1 不支持支付集成，建议延后到后续版本"
            )

        return CapacityReport(
            dimensions=dimension_counts,
            total_points=total,
            tier=tier,
            budget=budget,
            over_budget=over,
            needs_contraction=needs,
            must_contract=must,
            warnings=warnings,
        )

    def compare(
        self,
        before: CapacityReport,
        after: CapacityReport,
    ) -> dict:
        """
        对比收缩前后的容量报告。

        - before: 收缩前的报告
        - after: 收缩后的报告
        - 返回: 包含各维度变化和总点数变化的对比字典
        """
        # 构建 before 维度映射
        before_map: dict[CapacityDimension, DimensionCount] = {
            d.dimension: d for d in before.dimensions
        }
        after_map: dict[CapacityDimension, DimensionCount] = {
            d.dimension: d for d in after.dimensions
        }

        dimension_diffs: list[dict] = []
        for dim in CapacityDimension:
            b = before_map.get(dim)
            a = after_map.get(dim)
            b_count = b.count if b else 0
            a_count = a.count if a else 0
            b_points = b.points if b else 0
            a_points = a.points if a else 0
            dimension_diffs.append(
                {
                    "dimension": dim.value,
                    "count_before": b_count,
                    "count_after": a_count,
                    "count_delta": a_count - b_count,
                    "points_before": b_points,
                    "points_after": a_points,
                    "points_delta": a_points - b_points,
                }
            )

        return {
            "dimensions": dimension_diffs,
            "total_before": before.total_points,
            "total_after": after.total_points,
            "total_delta": after.total_points - before.total_points,
            "tier_before": before.tier.value,
            "tier_after": after.tier.value,
            "tier_changed": before.tier != after.tier,
        }

    @staticmethod
    def _has_any_tag(
        tags_per_scope: list[set[str]],
        keywords: set[str],
    ) -> int:
        """
        检查是否有任意 scope 的 tags 包含指定关键词。

        - tags_per_scope: 每个 scope 的标签集合列表
        - keywords: 需要匹配的关键词集合
        - 返回: 1（存在匹配）或 0（无匹配）
        """
        for tags in tags_per_scope:
            if tags & keywords:
                return 1
        return 0
