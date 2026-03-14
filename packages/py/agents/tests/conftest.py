"""
共享测试 fixture 模块。

为所有测试文件提供通用的 fixture：
- sample_ir_nodes: 样本 IR 节点列表
- sample_agent_input: 标准 AgentInput 实例
- mock_intent_output_json: IntentOutput 的 JSON 字符串
- reset_registry: 自动重置 AgentRegistry 单例
"""

import json
from uuid import uuid4

import pytest
from agents.configs.registry import AgentRegistry
from agents.schemas.base import AgentInput
from ir_core.schema.data import IRNodeData


@pytest.fixture
def sample_ir_nodes():
    """创建样本 IR 节点列表，包含两个 scope 节点。"""
    return [
        IRNodeData(
            id=uuid4(),
            node_type="scope",
            label="用户管理",
            props={
                "name": "用户管理",
                "description": "注册登录",
                "priority": "high",
                "tags": ["core"],
            },
        ),
        IRNodeData(
            id=uuid4(),
            node_type="scope",
            label="任务管理",
            props={
                "name": "任务管理",
                "description": "创建和管理任务",
                "priority": "high",
                "tags": ["core"],
            },
        ),
    ]


@pytest.fixture
def sample_agent_input():
    """创建标准 AgentInput fixture，提供基本的项目信息。"""
    return AgentInput(
        project_id=uuid4(),
        snapshot_id=uuid4(),
        ir_nodes=[],
        ir_edges=[],
        task_description="创建一个 Todo SaaS 应用",
    )


@pytest.fixture
def mock_intent_output_json():
    """IntentOutput 的 JSON 字符串，供 MockLLMProvider 返回。"""
    return json.dumps(
        {
            "reasoning": "分析用户需求后确定核心功能",
            "confidence": 0.85,
            "warnings": [],
            "scope_draft": {
                "product_name": "TodoApp",
                "product_description": "简单的待办事项管理应用",
                "scopes": [
                    {
                        "name": "任务管理",
                        "description": "创建、编辑、删除任务",
                        "priority": "high",
                        "tags": ["core"],
                    },
                    {
                        "name": "用户认证",
                        "description": "注册和登录",
                        "priority": "high",
                        "tags": ["auth"],
                    },
                ],
                "deferred_items": ["团队协作", "日历集成"],
                "risks": ["需求范围可能扩大"],
            },
        },
        ensure_ascii=False,
    )


@pytest.fixture(autouse=True)
def reset_registry():
    """每个测试前重置 AgentRegistry 单例，避免测试间状态泄露。"""
    AgentRegistry.reset()
    yield
    AgentRegistry.reset()
