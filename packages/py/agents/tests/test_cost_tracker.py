"""
CostTracker 测试模块。

测试成本追踪器的记录、查询和统计功能。
"""

from uuid import uuid4

import pytest
from runtime_tools.cost.tracker import CostTracker


class TestCostTrackerRecord:
    """CostTracker 记录功能测试。"""

    @pytest.mark.asyncio
    async def test_record_and_get_records(self):
        """记录后 get_records() 返回正确数量。"""
        tracker = CostTracker()
        project_id = uuid4()

        await tracker.record(
            agent_id="intent",
            project_id=project_id,
            model="test-model",
            provider="mock",
            prompt_tokens=100,
            completion_tokens=50,
            total_cost=0.01,
            latency_ms=500.0,
        )

        records = tracker.get_records()
        assert len(records) == 1
        assert records[0].agent_id == "intent"

    @pytest.mark.asyncio
    async def test_multiple_records(self):
        """多次记录后 get_records() 返回正确数量。"""
        tracker = CostTracker()
        project_id = uuid4()

        for i in range(3):
            await tracker.record(
                agent_id=f"agent_{i}",
                project_id=project_id,
                model="test-model",
                provider="mock",
                prompt_tokens=100,
                completion_tokens=50,
                total_cost=0.01,
                latency_ms=500.0,
            )

        records = tracker.get_records()
        assert len(records) == 3


class TestCostTrackerAggregation:
    """CostTracker 统计功能测试。"""

    @pytest.mark.asyncio
    async def test_get_total_cost(self):
        """get_total_cost() 计算总成本。"""
        tracker = CostTracker()
        project_id = uuid4()

        await tracker.record(
            agent_id="intent",
            project_id=project_id,
            model="m1",
            provider="mock",
            prompt_tokens=100,
            completion_tokens=50,
            total_cost=0.01,
            latency_ms=500.0,
        )
        await tracker.record(
            agent_id="schema",
            project_id=project_id,
            model="m1",
            provider="mock",
            prompt_tokens=200,
            completion_tokens=100,
            total_cost=0.02,
            latency_ms=600.0,
        )

        total = tracker.get_total_cost()
        assert abs(total - 0.03) < 1e-9

    @pytest.mark.asyncio
    async def test_get_total_tokens(self):
        """get_total_tokens() 计算总 token 数。"""
        tracker = CostTracker()
        project_id = uuid4()

        await tracker.record(
            agent_id="intent",
            project_id=project_id,
            model="m1",
            provider="mock",
            prompt_tokens=100,
            completion_tokens=50,
            total_cost=0.01,
            latency_ms=500.0,
        )
        await tracker.record(
            agent_id="schema",
            project_id=project_id,
            model="m1",
            provider="mock",
            prompt_tokens=200,
            completion_tokens=100,
            total_cost=0.02,
            latency_ms=600.0,
        )

        # 总 token = (100+50) + (200+100) = 450
        total = tracker.get_total_tokens()
        assert total == 450

    @pytest.mark.asyncio
    async def test_filter_by_project_id(self):
        """按 project_id 筛选记录。"""
        tracker = CostTracker()
        project_a = uuid4()
        project_b = uuid4()

        await tracker.record(
            agent_id="intent",
            project_id=project_a,
            model="m1",
            provider="mock",
            prompt_tokens=100,
            completion_tokens=50,
            total_cost=0.01,
            latency_ms=500.0,
        )
        await tracker.record(
            agent_id="schema",
            project_id=project_b,
            model="m1",
            provider="mock",
            prompt_tokens=200,
            completion_tokens=100,
            total_cost=0.02,
            latency_ms=600.0,
        )

        # 按 project_a 筛选
        records_a = tracker.get_records(project_id=str(project_a))
        assert len(records_a) == 1
        assert records_a[0].agent_id == "intent"

        # 按 project_b 筛选成本
        cost_b = tracker.get_total_cost(project_id=str(project_b))
        assert abs(cost_b - 0.02) < 1e-9


class TestCostTrackerEmpty:
    """CostTracker 空状态测试。"""

    def test_empty_tracker_returns_zero_cost(self):
        """空 tracker 返回 0 成本。"""
        tracker = CostTracker()
        assert tracker.get_total_cost() == 0

    def test_empty_tracker_returns_zero_tokens(self):
        """空 tracker 返回 0 token。"""
        tracker = CostTracker()
        assert tracker.get_total_tokens() == 0

    def test_empty_tracker_returns_empty_records(self):
        """空 tracker 返回空记录列表。"""
        tracker = CostTracker()
        assert tracker.get_records() == []
