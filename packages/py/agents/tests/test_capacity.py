"""
容量点数系统测试。

覆盖：
- CapacityDimension 枚举完整性
- CapacityRule 数据结构和 max_points 计算
- DEFAULT_RULES 文档一致性（含 payment 上限为 0）
- CapacityCalculator 各维度推算（基础、auth、payment、realtime、empty）
- 分档阈值判定（small / medium / large 的参数化测试）
- 超预算检测（含 large 始终超预算）
- compare() 收缩前后对比
- can_skip_contraction() 跳过收缩判定
- 超预算阻止逻辑（large 必须收缩、small 无需收缩、medium 建议收缩）
"""

import pytest
from agents.capacity.calculator import CapacityCalculator, CapacityReport, DimensionCount
from agents.capacity.rules import CapacityDimension, CapacityRule, DEFAULT_RULES
from agents.capacity.tiers import (
    TIER_BUDGETS,
    CapacityTier,
    can_skip_contraction,
    get_tier,
    is_over_budget,
)
from agents.schemas.high_level import ScopeDraft, ScopeItem
from ir_core.schema.node_types import Priority


# ============================================================
# 测试辅助函数
# ============================================================


def make_scope(name: str, tags: list[str] | None = None) -> ScopeItem:
    """构造单个 ScopeItem 测试数据。

    参数：
        name: 功能名称
        tags: 功能标签列表，默认为空

    返回：
        ScopeItem 实例
    """
    return ScopeItem(
        name=name,
        description=f"{name}功能模块",
        priority=Priority.MEDIUM,
        tags=tags or [],
    )


def make_draft(scopes: list[ScopeItem]) -> ScopeDraft:
    """构造 ScopeDraft 测试数据。

    参数：
        scopes: 功能范围列表

    返回：
        ScopeDraft 实例
    """
    return ScopeDraft(
        product_name="测试产品",
        product_description="测试描述",
        scopes=scopes,
    )


def make_scope_draft(
    n_scopes: int = 3,
    tags_map: dict[int, list[str]] | None = None,
    deferred: list[str] | None = None,
    risks: list[str] | None = None,
) -> ScopeDraft:
    """构造带 tags_map 参数的测试用 ScopeDraft。

    参数：
        n_scopes: 功能模块数量
        tags_map: 按索引指定 tags 的字典，如 {0: ["auth"], 2: ["支付"]}
        deferred: 延后功能列表
        risks: 风险列表

    返回：
        ScopeDraft 实例
    """
    scopes = []
    for i in range(n_scopes):
        tags = (tags_map or {}).get(i, [])
        if i == 0:
            priority = Priority.HIGH
        elif i < n_scopes // 2 + 1:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW
        scopes.append(
            ScopeItem(
                name=f"模块{i + 1}",
                description=f"测试模块{i + 1}的描述",
                priority=priority,
                tags=tags,
            )
        )
    return ScopeDraft(
        product_name="测试产品",
        product_description="测试产品描述",
        scopes=scopes,
        deferred_items=deferred or [],
        risks=risks or [],
    )


# ============================================================
# CapacityDimension 枚举测试
# ============================================================


class TestCapacityDimension:
    """CapacityDimension 枚举完整性测试。"""

    def test_capacity_dimensions_count(self):
        """验证 8 个维度全部定义。"""
        dims = list(CapacityDimension)
        assert len(dims) == 8

    def test_dimension_values(self):
        """验证每个维度的字符串值。"""
        expected = {
            "pages",
            "api_endpoints",
            "db_tables",
            "auth_flows",
            "integrations",
            "file_upload",
            "realtime",
            "payment",
        }
        actual = {d.value for d in CapacityDimension}
        assert actual == expected


# ============================================================
# DEFAULT_RULES 测试
# ============================================================


class TestDefaultRules:
    """DEFAULT_RULES 完整性和文档一致性测试。"""

    def test_default_rules_cover_all_dimensions(self):
        """所有 8 个维度都有对应的规则。"""
        all_dimensions = set(CapacityDimension)
        covered_dimensions = set(DEFAULT_RULES.keys())
        assert all_dimensions == covered_dimensions
        assert len(DEFAULT_RULES) == 8

    def test_all_dimensions_have_rules(self):
        """每个维度都有对应的规则。"""
        for dim in CapacityDimension:
            assert dim in DEFAULT_RULES, f"维度 {dim} 缺少规则定义"

    @pytest.mark.parametrize(
        "dim, expected_cost, expected_max_units",
        [
            (CapacityDimension.PAGES, 3, 8),
            (CapacityDimension.API_ENDPOINTS, 2, 15),
            (CapacityDimension.DB_TABLES, 4, 6),
            (CapacityDimension.AUTH_FLOWS, 5, 2),
            (CapacityDimension.INTEGRATIONS, 8, 2),
            (CapacityDimension.FILE_UPLOAD, 6, 1),
            (CapacityDimension.REALTIME, 10, 1),
            (CapacityDimension.PAYMENT, 12, 0),
        ],
    )
    def test_capacity_rule_max_points(self, dim, expected_cost, expected_max_units):
        """max_points = unit_cost * max_units，验证所有维度。"""
        rule = DEFAULT_RULES[dim]
        assert rule.unit_cost == expected_cost
        assert rule.max_units == expected_max_units
        assert rule.max_points == expected_cost * expected_max_units

    def test_default_rules_unit_costs(self):
        """验证每个维度的 unit_cost 和 max_units 与文档一致。"""
        # 按 M4 文档定义的规则表
        expected = {
            CapacityDimension.PAGES: (3, 8),
            CapacityDimension.API_ENDPOINTS: (2, 15),
            CapacityDimension.DB_TABLES: (4, 6),
            CapacityDimension.AUTH_FLOWS: (5, 2),
            CapacityDimension.INTEGRATIONS: (8, 2),
            CapacityDimension.FILE_UPLOAD: (6, 1),
            CapacityDimension.REALTIME: (10, 1),
            CapacityDimension.PAYMENT: (12, 0),
        }
        for dim, (unit_cost, max_units) in expected.items():
            rule = DEFAULT_RULES[dim]
            assert rule.unit_cost == unit_cost, (
                f"{dim}: unit_cost 期望 {unit_cost}，实际 {rule.unit_cost}"
            )
            assert rule.max_units == max_units, (
                f"{dim}: max_units 期望 {max_units}，实际 {rule.max_units}"
            )

    def test_rule_max_points_computed(self):
        """验证 max_points 计算字段正确（unit_cost * max_units）。"""
        for dim, rule in DEFAULT_RULES.items():
            assert rule.max_points == rule.unit_cost * rule.max_units, (
                f"{dim}: max_points 期望 {rule.unit_cost * rule.max_units}，"
                f"实际 {rule.max_points}"
            )

    def test_payment_dimension_max_units_zero(self):
        """payment 维度 Phase 1 上限为 0（不允许支付功能）。"""
        payment_rule = DEFAULT_RULES[CapacityDimension.PAYMENT]
        assert payment_rule.max_units == 0
        assert payment_rule.max_points == 0


# ============================================================
# 分档阈值测试
# ============================================================


class TestTiers:
    """容量分档判定测试。"""

    @pytest.mark.parametrize("points", [0, 15, 30])
    def test_get_tier_small(self, points):
        """0, 15, 30 分 → small。"""
        assert get_tier(points) == CapacityTier.SMALL

    @pytest.mark.parametrize("points", [31, 45, 60])
    def test_get_tier_medium(self, points):
        """31, 45, 60 分 → medium。"""
        assert get_tier(points) == CapacityTier.MEDIUM

    @pytest.mark.parametrize("points", [61, 100, 200])
    def test_get_tier_large(self, points):
        """61, 100, 200 分 → large。"""
        assert get_tier(points) == CapacityTier.LARGE

    def test_tier_boundaries(self):
        """边界值测试：30=small, 31=medium, 60=medium, 61=large。"""
        assert get_tier(30) == CapacityTier.SMALL
        assert get_tier(31) == CapacityTier.MEDIUM
        assert get_tier(60) == CapacityTier.MEDIUM
        assert get_tier(61) == CapacityTier.LARGE

    def test_tier_budgets(self):
        """验证分档预算上限。"""
        assert TIER_BUDGETS[CapacityTier.SMALL] == 30
        assert TIER_BUDGETS[CapacityTier.MEDIUM] == 60
        # large 没有预算上限
        assert CapacityTier.LARGE not in TIER_BUDGETS


# ============================================================
# 超预算检测测试
# ============================================================


class TestOverBudget:
    """超预算检测测试。"""

    def test_is_over_budget(self):
        """综合验证 is_over_budget 在各种情况下的结果。"""
        # small 预算 30：30 不超，31 超
        assert is_over_budget(30, CapacityTier.SMALL) is False
        assert is_over_budget(31, CapacityTier.SMALL) is True
        # medium 预算 60：60 不超，61 超
        assert is_over_budget(60, CapacityTier.MEDIUM) is False
        assert is_over_budget(61, CapacityTier.MEDIUM) is True
        # large 始终超
        assert is_over_budget(61, CapacityTier.LARGE) is True
        assert is_over_budget(1000, CapacityTier.LARGE) is True

    def test_small_within_budget(self):
        """small 档 30 点不超预算。"""
        assert is_over_budget(30, CapacityTier.SMALL) is False

    def test_small_over_budget(self):
        """small 档 31 点超预算。"""
        assert is_over_budget(31, CapacityTier.SMALL) is True

    def test_medium_within_budget(self):
        """medium 档 60 点不超预算。"""
        assert is_over_budget(60, CapacityTier.MEDIUM) is False

    def test_medium_over_budget(self):
        """medium 档 61 点超预算。"""
        assert is_over_budget(61, CapacityTier.MEDIUM) is True

    def test_large_always_over_budget(self):
        """large 档始终视为超预算。"""
        assert is_over_budget(61, CapacityTier.LARGE) is True
        assert is_over_budget(100, CapacityTier.LARGE) is True


# ============================================================
# can_skip_contraction 测试
# ============================================================


class TestCanSkipContraction:
    """can_skip_contraction() 跳过收缩判定测试。"""

    def test_can_skip_contraction(self):
        """综合验证：small 可跳, medium 可跳, large 不可跳。"""
        assert can_skip_contraction(CapacityTier.SMALL) is True
        assert can_skip_contraction(CapacityTier.MEDIUM) is True
        assert can_skip_contraction(CapacityTier.LARGE) is False

    def test_small_can_skip(self):
        """small 档可以跳过收缩。"""
        assert can_skip_contraction(CapacityTier.SMALL) is True

    def test_medium_can_skip(self):
        """medium 档可以跳过收缩（用户自行决定）。"""
        assert can_skip_contraction(CapacityTier.MEDIUM) is True

    def test_large_cannot_skip(self):
        """large 档不能跳过收缩。"""
        assert can_skip_contraction(CapacityTier.LARGE) is False


# ============================================================
# CapacityCalculator 测试
# ============================================================


class TestCapacityCalculator:
    """CapacityCalculator 各维度计算测试。"""

    def test_calculate_simple_scope(self):
        """3 个 scope，无特殊 tags → pages=3(9pts) + api=6(12pts) + db=3(12pts) = 33pts → medium。"""
        draft = make_scope_draft(n_scopes=3)
        calc = CapacityCalculator()
        report = calc.calculate(draft)

        assert report.total_points == 33
        assert report.tier == CapacityTier.MEDIUM

        # 验证各基础维度的明细
        dim_map = {d.dimension: d for d in report.dimensions}
        assert dim_map[CapacityDimension.PAGES].count == 3
        assert dim_map[CapacityDimension.PAGES].points == 9
        assert dim_map[CapacityDimension.API_ENDPOINTS].count == 6
        assert dim_map[CapacityDimension.API_ENDPOINTS].points == 12
        assert dim_map[CapacityDimension.DB_TABLES].count == 3
        assert dim_map[CapacityDimension.DB_TABLES].points == 12

    def test_calculate_with_auth_tag(self):
        """scope 包含 auth tag → auth_flows=1(5pts)。"""
        draft = make_scope_draft(n_scopes=2, tags_map={0: ["auth"]})
        calc = CapacityCalculator()
        report = calc.calculate(draft)

        dim_map = {d.dimension: d for d in report.dimensions}
        assert dim_map[CapacityDimension.AUTH_FLOWS].count == 1
        assert dim_map[CapacityDimension.AUTH_FLOWS].points == 5

    def test_calculate_with_payment_tag(self):
        """scope 包含 "支付" tag → payment 维度检测到，但 max_units=0 被 clamp。"""
        draft = make_scope_draft(n_scopes=2, tags_map={1: ["支付"]})
        calc = CapacityCalculator()
        report = calc.calculate(draft)

        dim_map = {d.dimension: d for d in report.dimensions}
        # payment max_units=0，即使检测到也会被 clamp 为 0
        assert dim_map[CapacityDimension.PAYMENT].count == 0
        assert dim_map[CapacityDimension.PAYMENT].points == 0

    def test_calculate_with_realtime_tag(self):
        """scope 包含 "realtime" tag → realtime=1(10pts)。"""
        draft = make_scope_draft(n_scopes=2, tags_map={0: ["realtime"]})
        calc = CapacityCalculator()
        report = calc.calculate(draft)

        dim_map = {d.dimension: d for d in report.dimensions}
        assert dim_map[CapacityDimension.REALTIME].count == 1
        assert dim_map[CapacityDimension.REALTIME].points == 10

    def test_calculate_empty_scope(self):
        """空 scopes → total_points=0 → small。"""
        draft = make_scope_draft(n_scopes=0)
        calc = CapacityCalculator()
        report = calc.calculate(draft)

        assert report.total_points == 0
        assert report.tier == CapacityTier.SMALL
        assert report.needs_contraction is False
        assert report.must_contract is False

    def test_calculator_simple_todo(self):
        """3 个 scope（无特殊 tags）的基本计算。

        预期：pages=3, api_endpoints=6, db_tables=3
        点数：3*3 + 6*2 + 3*4 = 9+12+12 = 33 → medium
        """
        scopes = [
            make_scope("任务管理"),
            make_scope("列表展示"),
            make_scope("统计面板"),
        ]
        draft = make_draft(scopes)
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        # 验证基础维度推算
        dim_map = {d.dimension: d for d in report.dimensions}
        assert dim_map[CapacityDimension.PAGES].count == 3
        assert dim_map[CapacityDimension.API_ENDPOINTS].count == 6
        assert dim_map[CapacityDimension.DB_TABLES].count == 3

        # 特殊维度均为 0
        assert dim_map[CapacityDimension.AUTH_FLOWS].count == 0
        assert dim_map[CapacityDimension.INTEGRATIONS].count == 0
        assert dim_map[CapacityDimension.FILE_UPLOAD].count == 0
        assert dim_map[CapacityDimension.REALTIME].count == 0
        assert dim_map[CapacityDimension.PAYMENT].count == 0

        # 总点数 = 3*3 + 6*2 + 3*4 = 33
        assert report.total_points == 33
        assert report.tier == CapacityTier.MEDIUM

    def test_calculator_with_auth(self):
        """包含 auth tag 的 scope → auth_flows 计数。"""
        scopes = [
            make_scope("用户认证", tags=["auth"]),
            make_scope("任务管理"),
        ]
        draft = make_draft(scopes)
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        dim_map = {d.dimension: d for d in report.dimensions}
        assert dim_map[CapacityDimension.AUTH_FLOWS].count == 1

    def test_calculator_with_payment(self):
        """包含 payment tag 的 scope → payment 计数。

        注意：payment 的 max_units=0，所以 clamped 后 count=0。
        """
        scopes = [
            make_scope("支付模块", tags=["payment"]),
            make_scope("任务管理"),
        ]
        draft = make_draft(scopes)
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        dim_map = {d.dimension: d for d in report.dimensions}
        # payment 的 max_units=0，clamped 后为 0
        assert dim_map[CapacityDimension.PAYMENT].count == 0
        assert dim_map[CapacityDimension.PAYMENT].points == 0

    def test_calculator_with_realtime(self):
        """包含 realtime tag 的 scope → realtime 计数。"""
        scopes = [
            make_scope("即时通讯", tags=["realtime"]),
            make_scope("任务管理"),
        ]
        draft = make_draft(scopes)
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        dim_map = {d.dimension: d for d in report.dimensions}
        assert dim_map[CapacityDimension.REALTIME].count == 1
        assert dim_map[CapacityDimension.REALTIME].points == 10

    def test_calculator_over_budget(self):
        """构造超 60 点的 scope → over_budget=True, must_contract=True。

        8 个 scope + auth + realtime + upload + integration：
        pages=8*3=24, api=15*2=30（clamped 到 15），
        db=6*4=24（clamped 到 6），auth=5, realtime=10, upload=6, integration=8
        总计 = 24+30+24+5+8+6+10 = 107 → large
        """
        scopes = [
            make_scope("模块1", tags=["auth"]),
            make_scope("模块2", tags=["realtime"]),
            make_scope("模块3", tags=["upload"]),
            make_scope("模块4", tags=["integration"]),
            make_scope("模块5"),
            make_scope("模块6"),
            make_scope("模块7"),
            make_scope("模块8"),
        ]
        draft = make_draft(scopes)
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        assert report.total_points > 60
        assert report.tier == CapacityTier.LARGE
        assert report.over_budget is True
        assert report.must_contract is True
        assert report.needs_contraction is True

    def test_calculator_empty_scopes(self):
        """空 scopes → 总点数=0, small。"""
        draft = make_draft([])
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        assert report.total_points == 0
        assert report.tier == CapacityTier.SMALL
        assert report.over_budget is False
        assert report.must_contract is False

    def test_calculator_medium_needs_contraction(self):
        """medium 档 needs_contraction=True 但 must_contract=False。"""
        scopes = [
            make_scope("模块1"),
            make_scope("模块2"),
            make_scope("模块3"),
        ]
        draft = make_draft(scopes)
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        # 3 个 scope → 33 点 → medium
        assert report.tier == CapacityTier.MEDIUM
        assert report.needs_contraction is True
        assert report.must_contract is False

    def test_calculator_small_no_contraction(self):
        """small 档 needs_contraction=False。"""
        scopes = [
            make_scope("模块1"),
            make_scope("模块2"),
        ]
        draft = make_draft(scopes)
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        # 2 个 scope → pages=2*3=6, api=4*2=8, db=2*4=8 → 22 点 → small
        assert report.total_points == 22
        assert report.tier == CapacityTier.SMALL
        assert report.needs_contraction is False
        assert report.must_contract is False


# ============================================================
# compare() 测试
# ============================================================


class TestCapacityCompare:
    """compare() 收缩前后对比测试。"""

    def test_compare(self):
        """验证 compare() 返回正确的前后差异。"""
        calculator = CapacityCalculator()

        # 收缩前：3 个 scope（33 点 medium）
        before_draft = make_draft([
            make_scope("模块1"),
            make_scope("模块2"),
            make_scope("模块3"),
        ])
        before_report = calculator.calculate(before_draft)

        # 收缩后：2 个 scope（22 点 small）
        after_draft = make_draft([
            make_scope("模块1"),
            make_scope("模块2"),
        ])
        after_report = calculator.calculate(after_draft)

        diff = calculator.compare(before_report, after_report)

        # 验证总点数变化
        assert diff["total_before"] == before_report.total_points
        assert diff["total_after"] == after_report.total_points
        assert diff["total_delta"] == after_report.total_points - before_report.total_points
        assert diff["total_delta"] < 0

        # 验证分档变化
        assert diff["tier_before"] == "medium"
        assert diff["tier_after"] == "small"
        assert diff["tier_changed"] is True

        # 验证维度明细存在
        assert len(diff["dimensions"]) == 8

    def test_compare_same_report(self):
        """相同报告对比，delta 为 0。"""
        calculator = CapacityCalculator()
        draft = make_draft([make_scope("模块1")])
        report = calculator.calculate(draft)

        diff = calculator.compare(report, report)

        assert diff["total_delta"] == 0
        assert diff["tier_changed"] is False
        for dim_diff in diff["dimensions"]:
            assert dim_diff["count_delta"] == 0
            assert dim_diff["points_delta"] == 0

    def test_compare_reports(self):
        """两个 CapacityReport 对比，验证 saved_points 和 tier 变化。"""
        calc = CapacityCalculator()

        # 收缩前：5 个 scope → medium
        before_draft = make_scope_draft(n_scopes=5)
        before_report = calc.calculate(before_draft)

        # 收缩后：2 个 scope → small
        after_draft = make_scope_draft(n_scopes=2)
        after_report = calc.calculate(after_draft)

        comparison = calc.compare(before_report, after_report)

        # 收缩后点数应该减少
        assert comparison["total_delta"] < 0
        assert comparison["total_before"] > comparison["total_after"]

        # tier 发生变化
        assert comparison["tier_changed"] is True


# ============================================================
# 超预算阻止逻辑测试
# ============================================================


class TestBudgetEnforcement:
    """超预算阻止逻辑测试。"""

    def test_large_project_must_contract(self):
        """10 个 scope → total > 60 → must_contract=True。"""
        draft = make_scope_draft(n_scopes=10)
        calc = CapacityCalculator()
        report = calc.calculate(draft)

        # 10 scopes: pages=8(clamped)*3=24, api=15(clamped)*2=30, db=6(clamped)*4=24 = 78
        assert report.total_points > 60
        assert report.tier == CapacityTier.LARGE
        assert report.must_contract is True
        assert report.needs_contraction is True

    def test_small_project_no_contraction(self):
        """2 个 scope → total < 30 → needs_contraction=False。"""
        draft = make_scope_draft(n_scopes=2)
        calc = CapacityCalculator()
        report = calc.calculate(draft)

        # 2 scopes: pages=2*3=6, api=4*2=8, db=2*4=8 = 22
        assert report.total_points == 22
        assert report.tier == CapacityTier.SMALL
        assert report.needs_contraction is False
        assert report.must_contract is False

    def test_medium_project_needs_contraction_but_not_must(self):
        """medium 项目建议收缩但不强制。"""
        draft = make_scope_draft(n_scopes=3)
        calc = CapacityCalculator()
        report = calc.calculate(draft)

        # 3 scopes: 33 pts → medium
        assert report.tier == CapacityTier.MEDIUM
        assert report.needs_contraction is True
        assert report.must_contract is False
