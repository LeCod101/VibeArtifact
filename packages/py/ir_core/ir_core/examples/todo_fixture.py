"""
Todo SaaS 的 Micro-IR fixture 模块。

提供一个完整的 Todo 待办事项应用 IR 图，包含 8 个节点和 10 条边。
用于演示和集成测试 IR Core 的全部功能：
schema 校验、操作应用、图查询、投影视图等。
"""

from uuid import uuid4

from ir_core.schema.data import IREdgeData, IRNodeData
from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import HttpMethod, NodeType, Priority
from ir_core.schema.operation_types import OperationType


def build_todo_fixture() -> tuple[list[IRNodeData], list[IREdgeData]]:
    """
    构建 Todo SaaS 的完整 Micro-IR fixture。

    返回 (nodes, edges) 元组，所有节点 id 用 uuid4() 生成。
    包含 8 个节点（1 scope + 3 entity + 2 endpoint + 2 page）
    和 10 条边（3 defines + 2 depends_on + 4 queries/mutates + 1 references）。
    """

    # --- 节点 ---

    # scope 节点：Todo MVP
    scope_id = uuid4()
    scope_node = IRNodeData(
        id=scope_id,
        node_type=NodeType.SCOPE,
        label="Todo MVP",
        props={
            "name": "Todo MVP",
            "description": "极简待办事项应用",
            "priority": Priority.HIGH,
            "tags": ["saas", "todo", "mvp"],
        },
    )

    # entity 节点：User
    user_id = uuid4()
    user_node = IRNodeData(
        id=user_id,
        node_type=NodeType.ENTITY,
        label="User",
        props={
            "name": "User",
            "fields": [
                {"name": "id", "type": "UUID", "primary": True, "nullable": False},
                {
                    "name": "email",
                    "type": "String",
                    "unique": True,
                    "nullable": False,
                },
                {"name": "password_hash", "type": "String", "nullable": False},
                {"name": "display_name", "type": "String", "nullable": True},
            ],
            "relationships": [],
        },
    )

    # entity 节点：Todo
    todo_id = uuid4()
    todo_node = IRNodeData(
        id=todo_id,
        node_type=NodeType.ENTITY,
        label="Todo",
        props={
            "name": "Todo",
            "fields": [
                {"name": "id", "type": "UUID", "primary": True, "nullable": False},
                {"name": "title", "type": "String", "nullable": False},
                {"name": "completed", "type": "Boolean", "nullable": False},
                {"name": "user_id", "type": "UUID", "nullable": False},
                {"name": "category_id", "type": "UUID", "nullable": True},
            ],
            "relationships": ["belongs_to:User", "belongs_to:Category"],
        },
    )

    # entity 节点：Category
    category_id = uuid4()
    category_node = IRNodeData(
        id=category_id,
        node_type=NodeType.ENTITY,
        label="Category",
        props={
            "name": "Category",
            "fields": [
                {"name": "id", "type": "UUID", "primary": True, "nullable": False},
                {"name": "name", "type": "String", "nullable": False},
                {"name": "color", "type": "String", "nullable": True},
                {"name": "user_id", "type": "UUID", "nullable": False},
            ],
            "relationships": ["belongs_to:User"],
        },
    )

    # endpoint 节点：Todo CRUD
    todo_crud_id = uuid4()
    todo_crud_node = IRNodeData(
        id=todo_crud_id,
        node_type=NodeType.ENDPOINT,
        label="Todo CRUD",
        props={
            "method": HttpMethod.POST,
            "path": "/api/todos",
            "description": "待办事项增删改查",
            "auth_required": True,
        },
    )

    # endpoint 节点：Category CRUD
    category_crud_id = uuid4()
    category_crud_node = IRNodeData(
        id=category_crud_id,
        node_type=NodeType.ENDPOINT,
        label="Category CRUD",
        props={
            "method": HttpMethod.POST,
            "path": "/api/categories",
            "description": "分类增删改查",
            "auth_required": True,
        },
    )

    # page 节点：Dashboard
    dashboard_id = uuid4()
    dashboard_node = IRNodeData(
        id=dashboard_id,
        node_type=NodeType.PAGE,
        label="Dashboard",
        props={
            "route": "/",
            "title": "仪表盘",
            "description": "用户主页，展示待办概览",
        },
    )

    # page 节点：Todo List
    todo_list_id = uuid4()
    todo_list_node = IRNodeData(
        id=todo_list_id,
        node_type=NodeType.PAGE,
        label="Todo List",
        props={
            "route": "/todos",
            "title": "待办列表",
            "description": "待办事项列表页，支持筛选和排序",
        },
    )

    nodes = [
        scope_node,
        user_node,
        todo_node,
        category_node,
        todo_crud_node,
        category_crud_node,
        dashboard_node,
        todo_list_node,
    ]

    # --- 边 ---

    edges = [
        # scope defines entity/endpoint/page
        IREdgeData(
            id=uuid4(),
            source_node_id=scope_id,
            target_node_id=user_id,
            edge_type=EdgeType.DEFINES,
        ),
        IREdgeData(
            id=uuid4(),
            source_node_id=scope_id,
            target_node_id=todo_id,
            edge_type=EdgeType.DEFINES,
        ),
        IREdgeData(
            id=uuid4(),
            source_node_id=scope_id,
            target_node_id=category_id,
            edge_type=EdgeType.DEFINES,
        ),
        # entity depends_on entity
        IREdgeData(
            id=uuid4(),
            source_node_id=todo_id,
            target_node_id=user_id,
            edge_type=EdgeType.DEPENDS_ON,
        ),
        IREdgeData(
            id=uuid4(),
            source_node_id=todo_id,
            target_node_id=category_id,
            edge_type=EdgeType.DEPENDS_ON,
        ),
        # endpoint queries/mutates entity
        IREdgeData(
            id=uuid4(),
            source_node_id=todo_crud_id,
            target_node_id=todo_id,
            edge_type=EdgeType.QUERIES,
        ),
        IREdgeData(
            id=uuid4(),
            source_node_id=todo_crud_id,
            target_node_id=todo_id,
            edge_type=EdgeType.MUTATES,
        ),
        IREdgeData(
            id=uuid4(),
            source_node_id=category_crud_id,
            target_node_id=category_id,
            edge_type=EdgeType.QUERIES,
        ),
        IREdgeData(
            id=uuid4(),
            source_node_id=category_crud_id,
            target_node_id=category_id,
            edge_type=EdgeType.MUTATES,
        ),
        # page references page
        IREdgeData(
            id=uuid4(),
            source_node_id=todo_list_id,
            target_node_id=dashboard_id,
            edge_type=EdgeType.REFERENCES,
        ),
    ]

    return nodes, edges


def build_todo_operations() -> list[dict]:
    """
    返回从空快照构建 Todo fixture 的操作列表。

    生成一组 create_node + create_edge 操作，
    可传入 apply_operations([], [], ops) 从空状态构建完整的 Todo fixture。
    每次调用会生成新的 uuid，保证幂等性。
    """
    operations: list[dict] = []

    # 预生成所有节点 ID，后续创建边时引用
    scope_id = str(uuid4())
    user_id = str(uuid4())
    todo_id = str(uuid4())
    category_id = str(uuid4())
    todo_crud_id = str(uuid4())
    category_crud_id = str(uuid4())
    dashboard_id = str(uuid4())
    todo_list_id = str(uuid4())

    # --- 创建节点操作 ---

    # scope: Todo MVP
    operations.append({
        "operation_type": OperationType.CREATE_NODE,
        "node_id": scope_id,
        "node_type": NodeType.SCOPE,
        "label": "Todo MVP",
        "props": {
            "name": "Todo MVP",
            "description": "极简待办事项应用",
            "priority": Priority.HIGH,
            "tags": ["saas", "todo", "mvp"],
        },
    })

    # entity: User
    operations.append({
        "operation_type": OperationType.CREATE_NODE,
        "node_id": user_id,
        "node_type": NodeType.ENTITY,
        "label": "User",
        "props": {
            "name": "User",
            "fields": [
                {"name": "id", "type": "UUID", "primary": True, "nullable": False},
                {
                    "name": "email",
                    "type": "String",
                    "unique": True,
                    "nullable": False,
                },
                {"name": "password_hash", "type": "String", "nullable": False},
                {"name": "display_name", "type": "String", "nullable": True},
            ],
            "relationships": [],
        },
    })

    # entity: Todo
    operations.append({
        "operation_type": OperationType.CREATE_NODE,
        "node_id": todo_id,
        "node_type": NodeType.ENTITY,
        "label": "Todo",
        "props": {
            "name": "Todo",
            "fields": [
                {"name": "id", "type": "UUID", "primary": True, "nullable": False},
                {"name": "title", "type": "String", "nullable": False},
                {"name": "completed", "type": "Boolean", "nullable": False},
                {"name": "user_id", "type": "UUID", "nullable": False},
                {"name": "category_id", "type": "UUID", "nullable": True},
            ],
            "relationships": ["belongs_to:User", "belongs_to:Category"],
        },
    })

    # entity: Category
    operations.append({
        "operation_type": OperationType.CREATE_NODE,
        "node_id": category_id,
        "node_type": NodeType.ENTITY,
        "label": "Category",
        "props": {
            "name": "Category",
            "fields": [
                {"name": "id", "type": "UUID", "primary": True, "nullable": False},
                {"name": "name", "type": "String", "nullable": False},
                {"name": "color", "type": "String", "nullable": True},
                {"name": "user_id", "type": "UUID", "nullable": False},
            ],
            "relationships": ["belongs_to:User"],
        },
    })

    # endpoint: Todo CRUD
    operations.append({
        "operation_type": OperationType.CREATE_NODE,
        "node_id": todo_crud_id,
        "node_type": NodeType.ENDPOINT,
        "label": "Todo CRUD",
        "props": {
            "method": HttpMethod.POST,
            "path": "/api/todos",
            "description": "待办事项增删改查",
            "auth_required": True,
        },
    })

    # endpoint: Category CRUD
    operations.append({
        "operation_type": OperationType.CREATE_NODE,
        "node_id": category_crud_id,
        "node_type": NodeType.ENDPOINT,
        "label": "Category CRUD",
        "props": {
            "method": HttpMethod.POST,
            "path": "/api/categories",
            "description": "分类增删改查",
            "auth_required": True,
        },
    })

    # page: Dashboard
    operations.append({
        "operation_type": OperationType.CREATE_NODE,
        "node_id": dashboard_id,
        "node_type": NodeType.PAGE,
        "label": "Dashboard",
        "props": {
            "route": "/",
            "title": "仪表盘",
            "description": "用户主页，展示待办概览",
        },
    })

    # page: Todo List
    operations.append({
        "operation_type": OperationType.CREATE_NODE,
        "node_id": todo_list_id,
        "node_type": NodeType.PAGE,
        "label": "Todo List",
        "props": {
            "route": "/todos",
            "title": "待办列表",
            "description": "待办事项列表页，支持筛选和排序",
        },
    })

    # --- 创建边操作 ---

    # scope defines entity (3 条)
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.DEFINES,
        "source_node_id": scope_id,
        "target_node_id": user_id,
    })
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.DEFINES,
        "source_node_id": scope_id,
        "target_node_id": todo_id,
    })
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.DEFINES,
        "source_node_id": scope_id,
        "target_node_id": category_id,
    })

    # entity depends_on entity (2 条)
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.DEPENDS_ON,
        "source_node_id": todo_id,
        "target_node_id": user_id,
    })
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.DEPENDS_ON,
        "source_node_id": todo_id,
        "target_node_id": category_id,
    })

    # endpoint queries/mutates entity (4 条)
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.QUERIES,
        "source_node_id": todo_crud_id,
        "target_node_id": todo_id,
    })
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.MUTATES,
        "source_node_id": todo_crud_id,
        "target_node_id": todo_id,
    })
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.QUERIES,
        "source_node_id": category_crud_id,
        "target_node_id": category_id,
    })
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.MUTATES,
        "source_node_id": category_crud_id,
        "target_node_id": category_id,
    })

    # page references page (1 条)
    operations.append({
        "operation_type": OperationType.CREATE_EDGE,
        "edge_type": EdgeType.REFERENCES,
        "source_node_id": todo_list_id,
        "target_node_id": dashboard_id,
    })

    return operations
