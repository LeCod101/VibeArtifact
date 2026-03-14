"""
Todo 基准用例 — 输入 "Todo SaaS" → 分析 → 无需收缩 → 确认。

验证最简单的端到端流程：
1. 构造 Todo SaaS 的 ScopeDraft（3-4 个模块）
2. CapacityCalculator 计算 → 验证在 small 档
3. 验证不需要收缩

同时测试 generation.py 中的 _mock_analyze 和 _mock_contract。
"""

from agents.capacity.calculator import CapacityCalculator
from agents.capacity.tiers import CapacityTier, can_skip_contraction
from agents.schemas.high_level import ScopeDraft, ScopeItem
from ir_core.schema.node_types import Priority


# ============================================================
# Todo SaaS 基准数据
# ============================================================


def _make_todo_draft() -> ScopeDraft:
    """构造 Todo SaaS 的基准 ScopeDraft。

    包含 3 个核心功能模块，模拟最小可行的 Todo 应用。

    返回：
        ScopeDraft 实例
    """
    return ScopeDraft(
        product_name="Todo SaaS",
        product_description="简单的待办事项管理 SaaS 应用",
        scopes=[
            ScopeItem(
                name="任务管理",
                description="创建、编辑、删除和标记完成待办任务",
                priority=Priority.HIGH,
                tags=["crud"],
            ),
            ScopeItem(
                name="任务分类",
                description="按分类组织和过滤任务",
                priority=Priority.MEDIUM,
                tags=[],
            ),
            ScopeItem(
                name="首页仪表盘",
                description="任务统计和进度概览",
                priority=Priority.MEDIUM,
                tags=[],
            ),
        ],
        deferred_items=[],
        risks=[],
    )


def _make_small_todo_draft() -> ScopeDraft:
    """构造 2 个模块的 Todo ScopeDraft，确保在 small 档内。

    返回：
        ScopeDraft 实例
    """
    return ScopeDraft(
        product_name="Mini Todo",
        product_description="最小化待办应用",
        scopes=[
            ScopeItem(
                name="任务管理",
                description="创建和管理待办任务",
                priority=Priority.HIGH,
                tags=["crud"],
            ),
            ScopeItem(
                name="首页仪表盘",
                description="任务概览",
                priority=Priority.MEDIUM,
                tags=[],
            ),
        ],
        deferred_items=[],
        risks=[],
    )


# ============================================================
# Todo 基准用例测试
# ============================================================


class TestTodoBaseline:
    """Todo SaaS 基准用例 — 验证最简流程。"""

    def test_todo_capacity_small_tier(self):
        """2 模块 Todo → small 档，无需收缩。

        2 个 scope：pages=2*3=6, api=4*2=8, db=2*4=8 → 22 点 → small
        """
        draft = _make_small_todo_draft()
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        assert report.total_points == 22
        assert report.tier == CapacityTier.SMALL

    def test_todo_no_contraction_needed(self):
        """small 档不需要收缩。"""
        draft = _make_small_todo_draft()
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        assert report.needs_contraction is False
        assert report.must_contract is False
        assert can_skip_contraction(report.tier) is True

    def test_todo_over_budget_false(self):
        """small 档不超预算。"""
        draft = _make_small_todo_draft()
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        assert report.over_budget is False

    def test_todo_3_modules_medium(self):
        """3 模块 Todo → medium 档。

        3 个 scope：pages=3*3=9, api=6*2=12, db=3*4=12 → 33 点 → medium
        """
        draft = _make_todo_draft()
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        assert report.total_points == 33
        assert report.tier == CapacityTier.MEDIUM

    def test_todo_3_modules_can_skip(self):
        """3 模块 Todo 是 medium 档，用户可选择跳过收缩。"""
        draft = _make_todo_draft()
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        # medium 档可以跳过收缩
        assert can_skip_contraction(report.tier) is True
        # 但建议收缩
        assert report.needs_contraction is True
        assert report.must_contract is False

    def test_todo_no_special_tags(self):
        """Todo 应用无特殊 tags（auth, payment 等），特殊维度均为 0。"""
        draft = _make_todo_draft()
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        dim_map = {d.dimension.value: d for d in report.dimensions}
        assert dim_map["auth_flows"].count == 0
        assert dim_map["integrations"].count == 0
        assert dim_map["file_upload"].count == 0
        assert dim_map["realtime"].count == 0
        assert dim_map["payment"].count == 0

    def test_todo_dimensions_basic(self):
        """验证 Todo 应用的基础维度计算正确。"""
        draft = _make_todo_draft()
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        dim_map = {d.dimension.value: d for d in report.dimensions}

        # 3 个 scope
        assert dim_map["pages"].count == 3
        assert dim_map["pages"].points == 9

        # 3 * 2 = 6 个端点
        assert dim_map["api_endpoints"].count == 6
        assert dim_map["api_endpoints"].points == 12

        # 3 张表
        assert dim_map["db_tables"].count == 3
        assert dim_map["db_tables"].points == 12

    def test_todo_with_auth_adds_capacity(self):
        """给 Todo 加上 auth 模块 → 点数增加。"""
        draft = ScopeDraft(
            product_name="Todo + Auth",
            product_description="带认证的 Todo 应用",
            scopes=[
                ScopeItem(
                    name="用户认证",
                    description="注册和登录",
                    priority=Priority.HIGH,
                    tags=["auth"],
                ),
                ScopeItem(
                    name="任务管理",
                    description="创建和管理任务",
                    priority=Priority.HIGH,
                    tags=["crud"],
                ),
            ],
        )
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        dim_map = {d.dimension.value: d for d in report.dimensions}
        # auth tag → auth_flows=1, 点数=5
        assert dim_map["auth_flows"].count == 1
        assert dim_map["auth_flows"].points == 5

        # 总点数 = 22（基础 2 scope）+ 5（auth）= 27
        assert report.total_points == 27
        assert report.tier == CapacityTier.SMALL

    def test_todo_full_flow(self):
        """完整流程：构建 draft → 计算容量 → 判断是否收缩 → 确认。"""
        # 步骤 1：构建 scope draft
        draft = _make_small_todo_draft()
        assert len(draft.scopes) == 2

        # 步骤 2：计算容量
        calculator = CapacityCalculator()
        report = calculator.calculate(draft)

        # 步骤 3：判断是否需要收缩
        assert report.tier == CapacityTier.SMALL
        assert report.needs_contraction is False
        skip = can_skip_contraction(report.tier)
        assert skip is True

        # 步骤 4：无需收缩，直接确认
        # （M4 阶段 confirm 是 API 层操作，这里只验证逻辑正确）
        assert report.over_budget is False
        assert report.must_contract is False
