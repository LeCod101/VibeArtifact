"""模板路由模块 - 实现模板列表、详情和从模板创建项目的端点。"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.templates import (
    CreateFromTemplateRequest,
    CreateFromTemplateResponse,
    TemplateDetailResponse,
    TemplateResponse,
)
from api_app.application.services.template_service import TemplateService

router = APIRouter(tags=["templates"])


@router.get(
    "/templates",
    response_model=list[TemplateResponse],
)
async def list_templates(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[TemplateResponse]:
    """列出公开模板。

    不需要认证，所有用户均可查看公开模板列表。
    支持通过 category 查询参数过滤模板类别。

    参数：
        category: 模板类别过滤（可选，如 saas / api / landing）
        db: 异步数据库会话

    返回：
        公开模板列表（不含 snapshot_data）
    """
    service = TemplateService(db)
    templates = await service.list_templates(category=category)
    await db.commit()
    return [
        TemplateResponse(
            id=str(tpl.id),
            name=tpl.name,
            description=tpl.description,
            category=tpl.category.value if hasattr(tpl.category, "value") else str(tpl.category),
            icon=tpl.icon,
            is_public=tpl.is_public,
            created_at=tpl.created_at,
        )
        for tpl in templates
    ]


@router.get(
    "/templates/{template_id}",
    response_model=TemplateDetailResponse,
)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TemplateDetailResponse:
    """获取模板详情（含 snapshot_data）。

    不需要认证。

    参数：
        template_id: 模板 UUID（路径参数）
        db: 异步数据库会话

    返回：
        TemplateDetailResponse（含完整快照数据）

    异常：
        404: 模板不存在
    """
    service = TemplateService(db)
    template = await service.get_template(template_id)
    await db.commit()

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    return TemplateDetailResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        category=template.category.value if hasattr(template.category, "value") else str(template.category),
        icon=template.icon,
        is_public=template.is_public,
        created_at=template.created_at,
        snapshot_data=template.snapshot_data,
    )


@router.post(
    "/projects/from-template",
    response_model=CreateFromTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_from_template(
    body: CreateFromTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreateFromTemplateResponse:
    """从模板创建项目。

    需要认证。创建项目并基于模板的 snapshot_data 初始化 IR 节点和边。

    参数：
        body: 创建请求（包含 template_id 和 project_name）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        CreateFromTemplateResponse（含新项目 ID 和快照 ID）

    异常：
        404: 模板不存在
    """
    service = TemplateService(db)

    try:
        project, snapshot = await service.create_project_from_template(
            user_id=current_user.id,
            project_name=body.project_name,
            template_id=UUID(body.template_id),
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    await db.commit()

    return CreateFromTemplateResponse(
        project_id=str(project.id),
        snapshot_id=str(snapshot.id),
        message="项目创建成功",
    )
