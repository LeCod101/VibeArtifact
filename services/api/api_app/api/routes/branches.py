"""分支路由模块 - 实现分支创建、列表、切换、fork 和树形查询端点。

所有端点要求用户认证，并验证用户是项目所有者（通过 conversation -> project -> owner 链）。
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.user import User
from platform_data.repositories.branch_repo import BranchRepository
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.routes.conversations import _get_conversation_with_auth
from api_app.api.schemas.branches import (
    BranchResponse,
    BranchTreeNode,
    CreateBranchRequest,
    ForkBranchRequest,
    RollbackRequest,
    RollbackResponse,
)
from api_app.application.services.branch_service import BranchService

router = APIRouter(tags=["branches"])


# ============================================================
# 辅助函数
# ============================================================


async def _build_branch_response(
    branch, db: AsyncSession
) -> BranchResponse:
    """将 ConversationBranch 模型转换为 BranchResponse，附带消息数量。

    参数：
        branch: ConversationBranch 模型实例
        db: 异步数据库会话

    返回：
        BranchResponse 实例
    """
    repo = BranchRepository(db)
    message_count = await repo.count_messages(branch.id)
    return BranchResponse(
        id=branch.id,
        conversation_id=branch.conversation_id,
        parent_branch_id=branch.parent_branch_id,
        base_snapshot_id=branch.base_snapshot_id,
        head_snapshot_id=branch.head_snapshot_id,
        branch_name=branch.branch_name,
        created_at=branch.created_at,
        message_count=message_count,
    )


# ============================================================
# 创建分支
# ============================================================


@router.post(
    "/conversations/{conversation_id}/branches",
    response_model=BranchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_branch(
    conversation_id: UUID,
    body: CreateBranchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchResponse:
    """为指定会话创建新分支。

    参数：
        conversation_id: 会话 UUID（路径参数）
        body: 创建分支请求体
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        BranchResponse（新创建的分支信息）

    异常：
        404: 会话不存在或项目不属于当前用户
    """
    # 验证会话存在且用户有权限
    await _get_conversation_with_auth(conversation_id, current_user, db)

    service = BranchService(db)
    branch = await service.create_branch(
        conversation_id=conversation_id,
        parent_branch_id=body.parent_branch_id,
        branch_name=body.branch_name,
        base_snapshot_id=body.base_snapshot_id,
    )
    await db.commit()
    await db.refresh(branch)
    return await _build_branch_response(branch, db)


# ============================================================
# 列出分支
# ============================================================


@router.get(
    "/conversations/{conversation_id}/branches",
    response_model=list[BranchResponse],
)
async def list_branches(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BranchResponse]:
    """列出指定会话的所有分支。

    参数：
        conversation_id: 会话 UUID（路径参数）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        该会话下的所有分支列表

    异常：
        404: 会话不存在或项目不属于当前用户
    """
    # 验证会话存在且用户有权限
    await _get_conversation_with_auth(conversation_id, current_user, db)

    service = BranchService(db)
    branches = await service.list_branches(conversation_id)

    result = []
    for b in branches:
        resp = await _build_branch_response(b, db)
        result.append(resp)
    return result


# ============================================================
# 获取分支树
# ============================================================


@router.get(
    "/conversations/{conversation_id}/branches/tree",
    response_model=list[BranchTreeNode],
)
async def get_branch_tree(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BranchTreeNode]:
    """获取指定会话的分支树形结构。

    参数：
        conversation_id: 会话 UUID（路径参数）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        分支树形结构列表

    异常：
        404: 会话不存在或项目不属于当前用户
    """
    # 验证会话存在且用户有权限
    await _get_conversation_with_auth(conversation_id, current_user, db)

    service = BranchService(db)
    tree_data = await service.get_branch_tree(conversation_id)

    def to_tree_node(node_dict: dict) -> BranchTreeNode:
        """将服务层返回的字典转换为 BranchTreeNode。

        参数：
            node_dict: 包含 branch, message_count, children 的字典

        返回：
            BranchTreeNode 实例
        """
        branch = node_dict["branch"]
        branch_resp = BranchResponse(
            id=branch.id,
            conversation_id=branch.conversation_id,
            parent_branch_id=branch.parent_branch_id,
            base_snapshot_id=branch.base_snapshot_id,
            head_snapshot_id=branch.head_snapshot_id,
            branch_name=branch.branch_name,
            created_at=branch.created_at,
            message_count=node_dict.get("message_count", 0),
        )
        children = [to_tree_node(c) for c in node_dict.get("children", [])]
        return BranchTreeNode(branch=branch_resp, children=children)

    return [to_tree_node(n) for n in tree_data]


# ============================================================
# 切换活跃分支
# ============================================================


@router.post(
    "/conversations/{conversation_id}/branches/{branch_id}/switch",
    response_model=BranchResponse,
)
async def switch_branch(
    conversation_id: UUID,
    branch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchResponse:
    """切换会话的活跃分支。

    参数：
        conversation_id: 会话 UUID（路径参数）
        branch_id: 目标分支 UUID（路径参数）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        切换后的活跃分支信息

    异常：
        404: 会话或分支不存在，或项目不属于当前用户
    """
    # 验证会话存在且用户有权限
    await _get_conversation_with_auth(conversation_id, current_user, db)

    service = BranchService(db)
    try:
        await service.switch_branch(conversation_id, branch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分支不存在或不属于该会话",
        )

    # 获取切换后的分支信息
    branch = await service.get_branch(branch_id)
    await db.commit()
    return await _build_branch_response(branch, db)


# ============================================================
# Fork 分支
# ============================================================


@router.post(
    "/conversations/{conversation_id}/branches/{branch_id}/fork",
    response_model=BranchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def fork_branch(
    conversation_id: UUID,
    branch_id: UUID,
    body: ForkBranchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchResponse:
    """从指定快照点 fork 新分支。

    参数：
        conversation_id: 会话 UUID（路径参数）
        branch_id: 源分支 UUID（路径参数）
        body: Fork 分支请求体
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        BranchResponse（新 fork 的分支信息）

    异常：
        404: 会话或分支不存在，或项目不属于当前用户
    """
    # 验证会话存在且用户有权限
    await _get_conversation_with_auth(conversation_id, current_user, db)

    service = BranchService(db)
    try:
        branch = await service.fork_branch(
            conversation_id=conversation_id,
            source_branch_id=branch_id,
            fork_point_snapshot_id=body.fork_point_snapshot_id,
            branch_name=body.branch_name,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="源分支不存在或不属于该会话",
        )

    await db.commit()
    await db.refresh(branch)
    return await _build_branch_response(branch, db)


# ============================================================
# 回滚到快照
# ============================================================


@router.post(
    "/conversations/{conversation_id}/rollback",
    response_model=RollbackResponse,
)
async def rollback_to_snapshot(
    conversation_id: UUID,
    body: RollbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RollbackResponse:
    """回滚到指定快照，自动 fork 新分支或切换到已有分支。

    三种结果：
    - no_change: 目标快照就是当前分支的 head
    - forked: 目标快照在当前分支历史中，创建新分支
    - switched: 目标快照在其他分支中，切换活跃分支

    参数：
        conversation_id: 会话 UUID（路径参数）
        body: 回滚请求体，包含 snapshot_id
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        RollbackResponse（回滚操作结果）

    异常：
        404: 会话不存在、项目不属于当前用户、快照未找到
    """
    # 验证会话存在且用户有权限
    await _get_conversation_with_auth(conversation_id, current_user, db)

    service = BranchService(db)
    try:
        result = await service.rollback_to_snapshot(
            conversation_id=conversation_id,
            snapshot_id=body.snapshot_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    await db.commit()

    return RollbackResponse(
        action=result["action"],
        switched_branch_id=str(result["switched_branch_id"]),
        new_branch_id=str(result["new_branch_id"]) if result["new_branch_id"] else None,
        snapshot_id=str(result["snapshot_id"]),
    )
