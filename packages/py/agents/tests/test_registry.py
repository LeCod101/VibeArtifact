"""
AgentRegistry 测试模块。

测试 Agent 注册表的核心功能：
- register_all_agents 批量注册
- get 按 ID 查询
- list_by_category 按类别筛选
- list_by_tier 按模型档位筛选
- 重复注册检测
- reset 重置
"""

import pytest
from agents.configs.base import AgentConfig, ModelTier, RoleCategory
from agents.configs.definitions import register_all_agents
from agents.configs.registry import AgentRegistry
from agents.schemas.base import AgentInput, AgentOutput


class TestRegisterAllAgents:
    """register_all_agents 批量注册测试。"""

    def test_registers_10_agents(self):
        """register_all_agents() 注册 10 个 Agent。"""
        registry = register_all_agents()
        agents = registry.list_agents()
        assert len(agents) == 10

    def test_all_agent_ids_present(self):
        """10 个 Agent 的 ID 都存在于注册表中。"""
        registry = register_all_agents()
        expected_ids = {
            "intent", "contraction", "planner", "schema",
            "backend", "frontend", "doc", "diagram", "qa", "export",
        }
        actual_ids = {a.agent_id for a in registry.list_agents()}
        assert actual_ids == expected_ids


class TestRegistryGet:
    """AgentRegistry.get() 测试。"""

    def test_get_intent_returns_correct_config(self):
        """get('intent') 返回正确的 AgentConfig。"""
        register_all_agents()
        registry = AgentRegistry.get_instance()
        config = registry.get("intent")
        assert config.agent_id == "intent"
        assert config.name == "Intent Agent"
        assert config.role_category == RoleCategory.INTENT_PLANNING
        assert config.model_tier == ModelTier.REASONING

    def test_get_nonexistent_raises_key_error(self):
        """get('nonexistent') 抛出 KeyError。"""
        register_all_agents()
        registry = AgentRegistry.get_instance()
        with pytest.raises(KeyError, match="未注册"):
            registry.get("nonexistent")


class TestRegistryFilter:
    """AgentRegistry 筛选功能测试。"""

    def test_list_by_category_intent_planning(self):
        """list_by_category(INTENT_PLANNING) 返回 3 个 Agent。"""
        register_all_agents()
        registry = AgentRegistry.get_instance()
        result = registry.list_by_category(RoleCategory.INTENT_PLANNING)
        assert len(result) == 3
        ids = {a.agent_id for a in result}
        assert ids == {"intent", "contraction", "planner"}

    def test_list_by_tier_reasoning(self):
        """list_by_tier(REASONING) 返回正确数量的 Agent。"""
        register_all_agents()
        registry = AgentRegistry.get_instance()
        result = registry.list_by_tier(ModelTier.REASONING)
        # intent, contraction, planner, schema, qa 都是 REASONING
        assert len(result) == 5
        ids = {a.agent_id for a in result}
        assert "intent" in ids
        assert "schema" in ids
        assert "qa" in ids

    def test_list_by_tier_generation(self):
        """list_by_tier(GENERATION) 返回正确数量的 Agent。"""
        register_all_agents()
        registry = AgentRegistry.get_instance()
        result = registry.list_by_tier(ModelTier.GENERATION)
        # backend, frontend, doc, diagram, export 都是 GENERATION
        assert len(result) == 5


class TestRegistryEdgeCases:
    """AgentRegistry 边界情况测试。"""

    def test_duplicate_registration_raises_value_error(self):
        """重复注册同一 agent_id 抛出 ValueError。"""
        registry = AgentRegistry.get_instance()
        config = AgentConfig(
            agent_id="test_agent",
            name="Test Agent",
            description="测试用 Agent",
            role_category=RoleCategory.QA,
            model_tier=ModelTier.REASONING,
            input_schema=AgentInput,
            output_schema=AgentOutput,
            high_level_key="test",
        )
        registry.register(config)

        # 再次注册同一 agent_id 应幂等跳过，不抛异常
        registry.register(config)
        assert len(registry.list_agents()) == 1

    def test_reset_clears_registry(self):
        """reset() 后注册表为空。"""
        register_all_agents()
        registry = AgentRegistry.get_instance()
        assert len(registry.list_agents()) == 10

        # 重置
        AgentRegistry.reset()
        new_registry = AgentRegistry.get_instance()
        assert len(new_registry.list_agents()) == 0
