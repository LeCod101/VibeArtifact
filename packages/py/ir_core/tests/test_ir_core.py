"""
IR Core M2 全量集成测试。

覆盖验收标准：
- schema 节点/边类型校验
- validators 节点属性/边约束/快照完整性校验
- operations 操作应用（创建、更新、删除、级联）
- diff 差异计算与往返一致性
- graph 图查询辅助函数
- projections 投影视图过滤
- fixture 端到端集成
"""

from uuid import uuid4

import pytest
from ir_core.examples import build_todo_fixture, build_todo_operations
from ir_core.graph import get_neighbors, get_nodes_by_type, topological_sort
from ir_core.operations import ApplyError, apply_operations, compute_diff
from ir_core.projections import (
    api_doc_projection,
    architecture_projection,
    backend_projection,
    frontend_projection,
    schema_projection,
)
from ir_core.schema import (
    EDGE_CONSTRAINTS,
    NODE_PROPS_MAP,
    EdgeType,
    EntityProps,
    IREdgeData,
    IRNodeData,
    NodeType,
)
from ir_core.schema.operation_types import OperationType
from ir_core.validators import validate_edge, validate_node_props, validate_snapshot

# ============================================================
# schema 测试
# ============================================================


class TestNodeTypes:
    """节点类型相关测试。"""

    def test_valid_entity_props(self):
        """合法 entity props 通过验证"""
        props = {
            "name": "User",
            "fields": [
                {"name": "id", "type": "UUID", "primary": True, "nullable": False},
            ],
            "relationships": [],
        }
        # 直接用 Pydantic model 校验
        model = EntityProps.model_validate(props)
        assert model.name == "User"
        assert len(model.fields) == 1

    def test_invalid_entity_missing_name(self):
        """entity 缺少 name 字段被拒绝"""
        props = {
            "fields": [
                {"name": "id", "type": "UUID"},
            ],
        }
        result = validate_node_props("entity", props)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_all_node_types_in_map(self):
        """所有 NodeType 都在 NODE_PROPS_MAP 中有对应 model"""
        for nt in NodeType:
            assert nt in NODE_PROPS_MAP, f"NodeType.{nt.name} 缺少 props model"


class TestEdgeTypes:
    """边类型相关测试。"""

    def test_valid_edge_constraints(self):
        """所有 EdgeType 都在 EDGE_CONSTRAINTS 中"""
        for et in EdgeType:
            assert et in EDGE_CONSTRAINTS, (
                f"EdgeType.{et.name} 缺少约束定义"
            )


# ============================================================
# validators 测试
# ============================================================


class TestNodeValidator:
    """节点属性校验器测试。"""

    def test_valid_props_pass(self):
        """合法 props 通过"""
        props = {
            "name": "Todo MVP",
            "description": "极简待办",
            "priority": "high",
            "tags": ["mvp"],
        }
        result = validate_node_props("scope", props)
        assert result.is_valid

    def test_unknown_node_type_rejected(self):
        """未知 node_type 被拒绝"""
        result = validate_node_props("unknown_type", {"foo": "bar"})
        assert not result.is_valid
        assert any("未知" in err for err in result.errors)

    def test_invalid_props_rejected(self):
        """不符合 schema 的 props 被拒绝"""
        # scope 缺少 description、priority、tags
        props = {"name": "Test"}
        result = validate_node_props("scope", props)
        assert not result.is_valid


class TestEdgeValidator:
    """边类型校验器测试。"""

    def test_valid_edge_pass(self):
        """合法边通过"""
        result = validate_edge("defines", "scope", "entity")
        assert result.is_valid

    def test_unknown_edge_type_rejected(self):
        """未知 edge_type 被拒绝"""
        result = validate_edge("unknown_edge", "scope", "entity")
        assert not result.is_valid
        assert any("未知" in err for err in result.errors)

    def test_invalid_source_target_rejected(self):
        """不在合法组合内的源/目标被拒绝"""
        # entity -> scope 不合法（defines 只允许 scope -> entity/endpoint/page）
        result = validate_edge("defines", "entity", "scope")
        assert not result.is_valid

    def test_references_allows_any(self):
        """references 类型允许任意组合"""
        result = validate_edge("references", "page", "page")
        assert result.is_valid
        # 再试一个不常见的组合
        result2 = validate_edge("references", "entity", "decision")
        assert result2.is_valid


class TestSnapshotValidator:
    """快照完整性校验器测试。"""

    def test_valid_snapshot(self):
        """合法快照通过"""
        nodes, edges = build_todo_fixture()
        result = validate_snapshot(nodes, edges)
        assert result.is_valid, f"校验失败: {result.errors}"

    def test_dangling_edge_detected(self):
        """悬挂边被检测到"""
        # 创建一个节点和一条指向不存在节点的边
        node_id = uuid4()
        node = IRNodeData(
            id=node_id,
            node_type="entity",
            label="Test",
            props={
                "name": "Test",
                "fields": [],
                "relationships": [],
            },
        )
        # 边的 target 指向一个不存在的节点
        fake_target_id = uuid4()
        edge = IREdgeData(
            id=uuid4(),
            source_node_id=node_id,
            target_node_id=fake_target_id,
            edge_type="depends_on",
        )
        result = validate_snapshot([node], [edge])
        assert not result.is_valid
        assert any("悬挂" in err for err in result.errors)


# ============================================================
# operations 测试
# ============================================================


class TestApplyOperations:
    """操作应用测试。"""

    def test_create_node(self):
        """创建节点"""
        ops = [
            {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": "entity",
                "label": "User",
                "props": {
                    "name": "User",
                    "fields": [
                        {
                            "name": "id",
                            "type": "UUID",
                            "primary": True,
                            "nullable": False,
                        },
                    ],
                    "relationships": [],
                },
            },
        ]
        new_nodes, new_edges = apply_operations([], [], ops)
        assert len(new_nodes) == 1
        assert new_nodes[0].label == "User"
        assert new_nodes[0].node_type == "entity"

    def test_update_node_props(self):
        """部分更新节点 props"""
        node_id = uuid4()
        nodes = [
            IRNodeData(
                id=node_id,
                node_type="scope",
                label="Test",
                props={
                    "name": "Test",
                    "description": "原始描述",
                    "priority": "high",
                    "tags": ["test"],
                },
            ),
        ]
        ops = [
            {
                "operation_type": OperationType.UPDATE_NODE_PROPS,
                "node_id": str(node_id),
                "props": {"description": "更新后的描述"},
            },
        ]
        new_nodes, _ = apply_operations(nodes, [], ops)
        assert new_nodes[0].props["description"] == "更新后的描述"
        # 其他字段保持不变
        assert new_nodes[0].props["name"] == "Test"

    def test_delete_node_cascades_edges(self):
        """删除节点级联删除关联边"""
        node_a_id = uuid4()
        node_b_id = uuid4()
        nodes = [
            IRNodeData(
                id=node_a_id,
                node_type="entity",
                label="A",
                props={
                    "name": "A",
                    "fields": [],
                    "relationships": [],
                },
            ),
            IRNodeData(
                id=node_b_id,
                node_type="entity",
                label="B",
                props={
                    "name": "B",
                    "fields": [],
                    "relationships": [],
                },
            ),
        ]
        edges = [
            IREdgeData(
                id=uuid4(),
                source_node_id=node_a_id,
                target_node_id=node_b_id,
                edge_type="depends_on",
            ),
        ]
        ops = [
            {
                "operation_type": OperationType.DELETE_NODE,
                "node_id": str(node_a_id),
            },
        ]
        new_nodes, new_edges = apply_operations(nodes, edges, ops)
        # 节点 A 被删除
        assert len(new_nodes) == 1
        assert new_nodes[0].id == node_b_id
        # 关联边也被级联删除
        assert len(new_edges) == 0

    def test_create_edge(self):
        """创建边"""
        node_a_id = uuid4()
        node_b_id = uuid4()
        nodes = [
            IRNodeData(
                id=node_a_id,
                node_type="entity",
                label="A",
                props={
                    "name": "A",
                    "fields": [],
                    "relationships": [],
                },
            ),
            IRNodeData(
                id=node_b_id,
                node_type="entity",
                label="B",
                props={
                    "name": "B",
                    "fields": [],
                    "relationships": [],
                },
            ),
        ]
        ops = [
            {
                "operation_type": OperationType.CREATE_EDGE,
                "edge_type": "depends_on",
                "source_node_id": str(node_a_id),
                "target_node_id": str(node_b_id),
            },
        ]
        _, new_edges = apply_operations(nodes, [], ops)
        assert len(new_edges) == 1
        assert new_edges[0].edge_type == "depends_on"

    def test_invalid_props_raises_error(self):
        """非法 props 抛 ApplyError"""
        ops = [
            {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": "entity",
                # 缺少 name 字段
                "label": "Bad",
                "props": {"fields": []},
            },
        ]
        with pytest.raises(ApplyError):
            apply_operations([], [], ops)

    def test_missing_node_raises_error(self):
        """引用不存在的节点抛 ApplyError"""
        fake_id = str(uuid4())
        ops = [
            {
                "operation_type": OperationType.UPDATE_NODE_PROPS,
                "node_id": fake_id,
                "props": {"name": "New"},
            },
        ]
        with pytest.raises(ApplyError):
            apply_operations([], [], ops)

    def test_empty_operations(self):
        """空操作列表返回原始数据的深拷贝"""
        node_id = uuid4()
        nodes = [
            IRNodeData(
                id=node_id,
                node_type="entity",
                label="A",
                props={
                    "name": "A",
                    "fields": [],
                    "relationships": [],
                },
            ),
        ]
        edge_id = uuid4()
        node_b_id = uuid4()
        nodes.append(
            IRNodeData(
                id=node_b_id,
                node_type="entity",
                label="B",
                props={
                    "name": "B",
                    "fields": [],
                    "relationships": [],
                },
            ),
        )
        edges = [
            IREdgeData(
                id=edge_id,
                source_node_id=node_id,
                target_node_id=node_b_id,
                edge_type="depends_on",
            ),
        ]
        # 空操作列表
        new_nodes, new_edges = apply_operations(nodes, edges, [])
        # 数量一致
        assert len(new_nodes) == len(nodes)
        assert len(new_edges) == len(edges)
        # 是深拷贝，不是同一个对象
        assert new_nodes is not nodes
        assert new_edges is not edges
        assert new_nodes[0] is not nodes[0]

    def test_delete_edge(self):
        """删除边"""
        node_a_id = uuid4()
        node_b_id = uuid4()
        edge_id = uuid4()
        nodes = [
            IRNodeData(
                id=node_a_id,
                node_type="entity",
                label="A",
                props={
                    "name": "A",
                    "fields": [],
                    "relationships": [],
                },
            ),
            IRNodeData(
                id=node_b_id,
                node_type="entity",
                label="B",
                props={
                    "name": "B",
                    "fields": [],
                    "relationships": [],
                },
            ),
        ]
        edges = [
            IREdgeData(
                id=edge_id,
                source_node_id=node_a_id,
                target_node_id=node_b_id,
                edge_type="depends_on",
            ),
        ]
        ops = [
            {
                "operation_type": OperationType.DELETE_EDGE,
                "edge_id": str(edge_id),
            },
        ]
        new_nodes, new_edges = apply_operations(nodes, edges, ops)
        # 节点不受影响
        assert len(new_nodes) == 2
        # 边被删除
        assert len(new_edges) == 0

    def test_duplicate_node_id_rejected(self):
        """重复节点 ID 被拒绝"""
        node_id = uuid4()
        nodes = [
            IRNodeData(
                id=node_id,
                node_type="entity",
                label="Existing",
                props={
                    "name": "Existing",
                    "fields": [],
                    "relationships": [],
                },
            ),
        ]
        # 尝试用相同 node_id 创建节点
        ops = [
            {
                "operation_type": OperationType.CREATE_NODE,
                "node_id": str(node_id),
                "node_type": "entity",
                "label": "Duplicate",
                "props": {
                    "name": "Duplicate",
                    "fields": [],
                    "relationships": [],
                },
            },
        ]
        with pytest.raises(ApplyError, match="已存在"):
            apply_operations(nodes, [], ops)


class TestDiff:
    """差异计算测试。"""

    def test_diff_create_nodes(self):
        """diff 检测到新增节点"""
        new_node = IRNodeData(
            id=uuid4(),
            node_type="entity",
            label="NewEntity",
            props={
                "name": "NewEntity",
                "fields": [],
                "relationships": [],
            },
        )
        ops = compute_diff([], [], [new_node], [])
        # 应有一条 create_node 操作
        create_ops = [
            o for o in ops if o["operation_type"] == OperationType.CREATE_NODE
        ]
        assert len(create_ops) == 1

    def test_diff_delete_nodes(self):
        """diff 检测到删除节点"""
        old_node = IRNodeData(
            id=uuid4(),
            node_type="entity",
            label="OldEntity",
            props={
                "name": "OldEntity",
                "fields": [],
                "relationships": [],
            },
        )
        ops = compute_diff([old_node], [], [], [])
        # 应有一条 delete_node 操作
        delete_ops = [
            o for o in ops if o["operation_type"] == OperationType.DELETE_NODE
        ]
        assert len(delete_ops) == 1

    def test_diff_round_trip(self):
        """diff 产出的 ops 可以 apply 得到相同结果"""
        # 构建 fixture 作为目标状态
        target_nodes, target_edges = build_todo_fixture()

        # 从空状态计算 diff
        ops = compute_diff([], [], target_nodes, target_edges)

        # 用 apply_operations 从空状态应用 diff
        result_nodes, result_edges = apply_operations([], [], ops)

        # 验证结果数量一致
        assert len(result_nodes) == len(target_nodes)
        assert len(result_edges) == len(target_edges)

        # 验证结果 ID 集合一致
        result_node_ids = {n.id for n in result_nodes}
        target_node_ids = {n.id for n in target_nodes}
        assert result_node_ids == target_node_ids

    def test_diff_delete_node_with_edges(self):
        """删除节点时不会产生冗余的 DELETE_EDGE（验证 bug 修复）"""
        # 创建两个节点
        node_a_id = uuid4()
        node_b_id = uuid4()
        old_nodes = [
            IRNodeData(
                id=node_a_id,
                node_type="entity",
                label="A",
                props={
                    "name": "A",
                    "fields": [],
                    "relationships": [],
                },
            ),
            IRNodeData(
                id=node_b_id,
                node_type="entity",
                label="B",
                props={
                    "name": "B",
                    "fields": [],
                    "relationships": [],
                },
            ),
        ]
        # 创建一条边
        edge_id = uuid4()
        old_edges = [
            IREdgeData(
                id=edge_id,
                source_node_id=node_a_id,
                target_node_id=node_b_id,
                edge_type="depends_on",
            ),
        ]
        # 新快照中删除节点 A（只保留 B，无边）
        new_nodes = [old_nodes[1]]
        new_edges: list[IREdgeData] = []

        ops = compute_diff(old_nodes, old_edges, new_nodes, new_edges)

        # 应该只有 DELETE_NODE，不产生 DELETE_EDGE
        op_types = [o["operation_type"] for o in ops]
        assert OperationType.DELETE_NODE in op_types
        assert OperationType.DELETE_EDGE not in op_types

        # apply diff 不应抛出 ApplyError
        result_nodes, result_edges = apply_operations(
            old_nodes, old_edges, ops,
        )
        assert len(result_nodes) == 1
        assert result_nodes[0].id == node_b_id
        assert len(result_edges) == 0


# ============================================================
# graph 测试
# ============================================================


class TestGraphHelpers:
    """图查询辅助函数测试。"""

    def test_get_nodes_by_type(self):
        """按类型过滤"""
        nodes, _ = build_todo_fixture()
        entities = get_nodes_by_type("entity", nodes)
        # fixture 中有 3 个 entity: User, Todo, Category
        assert len(entities) == 3
        for n in entities:
            assert n.node_type == "entity"

    def test_get_neighbors(self):
        """获取邻居"""
        nodes, edges = build_todo_fixture()
        # 找 Todo 节点
        todo_node = None
        for n in nodes:
            if n.label == "Todo":
                todo_node = n
                break
        assert todo_node is not None

        # Todo 的邻居应包含 User（depends_on）、Category（depends_on）、
        # Todo CRUD（queries/mutates）、scope（defines）
        neighbors = get_neighbors(todo_node.id, nodes, edges)
        neighbor_labels = {n.label for n in neighbors}
        assert "User" in neighbor_labels
        assert "Category" in neighbor_labels

    def test_topological_sort(self):
        """拓扑排序"""
        nodes, edges = build_todo_fixture()
        # 只对 entity 节点做拓扑排序
        entity_nodes = get_nodes_by_type("entity", nodes)
        sorted_nodes = topological_sort(entity_nodes, edges)

        # 排序后长度不变
        assert len(sorted_nodes) == len(entity_nodes)

        # Todo 依赖 User 和 Category，所以 User 和 Category 应排在 Todo 前面
        sorted_labels = [n.label for n in sorted_nodes]
        todo_idx = sorted_labels.index("Todo")
        user_idx = sorted_labels.index("User")
        category_idx = sorted_labels.index("Category")
        assert user_idx < todo_idx
        assert category_idx < todo_idx


# ============================================================
# projections 测试
# ============================================================


class TestProjections:
    """投影视图测试。"""

    def test_schema_projection(self):
        """schema 投影只含 entity 节点"""
        nodes, edges = build_todo_fixture()
        result = schema_projection(nodes, edges)
        assert result.name == "schema"
        # 所有节点都是 entity
        for n in result.nodes:
            assert n.node_type == "entity"
        # 有 3 个 entity 节点
        assert len(result.nodes) == 3

    def test_backend_projection(self):
        """backend 投影含 entity + endpoint"""
        nodes, edges = build_todo_fixture()
        result = backend_projection(nodes, edges)
        assert result.name == "backend"
        node_types = {n.node_type for n in result.nodes}
        assert "entity" in node_types
        assert "endpoint" in node_types
        # 不应包含 page、scope 等
        assert "page" not in node_types
        assert "scope" not in node_types
        # 3 entity + 2 endpoint = 5
        assert len(result.nodes) == 5

    def test_frontend_projection(self):
        """frontend 投影含 page + component"""
        nodes, edges = build_todo_fixture()
        result = frontend_projection(nodes, edges)
        assert result.name == "frontend"
        node_types = {n.node_type for n in result.nodes}
        # fixture 中有 page 但没有 component
        assert "page" in node_types
        assert "entity" not in node_types
        # 2 page 节点
        assert len(result.nodes) == 2

    def test_api_doc_projection(self):
        """api_doc 投影含 endpoint + 关联 entity"""
        nodes, edges = build_todo_fixture()
        result = api_doc_projection(nodes, edges)
        assert result.name == "api_doc"
        node_types = {n.node_type for n in result.nodes}
        assert "endpoint" in node_types
        # 通过 queries/mutates 边关联的 entity 也应该包含
        assert "entity" in node_types
        # 不应包含 page、scope
        assert "page" not in node_types
        assert "scope" not in node_types

    def test_architecture_projection(self):
        """architecture 投影含全部节点"""
        nodes, edges = build_todo_fixture()
        result = architecture_projection(nodes, edges)
        assert result.name == "architecture"
        # 节点数和边数应与原始数据一致
        assert len(result.nodes) == len(nodes)
        assert len(result.edges) == len(edges)


# ============================================================
# fixture 集成测试
# ============================================================


class TestTodoFixture:
    """Todo fixture 端到端集成测试。"""

    def test_fixture_node_count(self):
        """fixture 包含 >= 8 个节点"""
        nodes, _ = build_todo_fixture()
        assert len(nodes) >= 8

    def test_fixture_edge_count(self):
        """fixture 包含 >= 10 条边"""
        _, edges = build_todo_fixture()
        assert len(edges) >= 10

    def test_fixture_passes_validation(self):
        """fixture 通过全量 snapshot validator"""
        nodes, edges = build_todo_fixture()
        result = validate_snapshot(nodes, edges)
        assert result.is_valid, f"校验失败: {result.errors}"

    def test_fixture_from_operations(self):
        """用 apply_operations 从空状态构建 fixture"""
        ops = build_todo_operations()
        nodes, edges = apply_operations([], [], ops)
        # 验证数量
        assert len(nodes) >= 8
        assert len(edges) >= 10
        # 验证通过快照校验
        result = validate_snapshot(nodes, edges)
        assert result.is_valid, f"校验失败: {result.errors}"

    def test_fixture_schema_projection(self):
        """fixture 的 schema 投影只含 entity"""
        nodes, edges = build_todo_fixture()
        result = schema_projection(nodes, edges)
        # 所有节点类型都是 entity
        for n in result.nodes:
            assert n.node_type == "entity"
        # 3 个 entity
        assert len(result.nodes) == 3

    def test_fixture_backend_projection(self):
        """fixture 的 backend 投影含 entity + endpoint"""
        nodes, edges = build_todo_fixture()
        result = backend_projection(nodes, edges)
        node_types = {n.node_type for n in result.nodes}
        assert "entity" in node_types
        assert "endpoint" in node_types
        # 3 entity + 2 endpoint = 5
        assert len(result.nodes) == 5
        # 应有 queries/mutates/depends_on 边
        edge_types = {e.edge_type for e in result.edges}
        assert "queries" in edge_types
        assert "mutates" in edge_types
        assert "depends_on" in edge_types
