"""
设置路由模块。

提供用户 API 密钥管理、模型偏好设置和用量统计查询的 API 端点。
所有端点需要 JWT 认证。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.settings import (
    ApiKeyCreateRequest,
    ApiKeyResponse,
    ApiKeyValidateResponse,
    AvailableModel,
    ModelPreferenceRequest,
    ModelPreferenceResponse,
    UsageSummaryResponse,
)
from api_app.application.services.settings_service import SettingsService

router = APIRouter(tags=["settings"])


# ──────────────────────────────────────
# API 密钥管理
# ──────────────────────────────────────


@router.get("/settings/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyResponse]:
    """
    获取用户所有 API 密钥（掩码显示）。

    返回用户已配置的所有 LLM Provider 密钥，
    密钥内容以掩码形式展示，不返回明文。
    """
    service = SettingsService(db)
    return await service.list_api_keys(current_user.id)


@router.post("/settings/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_api_key(
    body: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    """
    添加或更新 API 密钥。

    如果用户已有该 provider 的密钥，则更新；否则创建新记录。
    密钥使用 Fernet 加密存储。

    参数:
        body: 密钥创建请求（provider + 明文密钥）
    """
    service = SettingsService(db)
    return await service.upsert_api_key(
        user_id=current_user.id,
        provider=body.provider,
        api_key=body.api_key,
        display_label=body.display_label,
    )


@router.delete("/settings/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    删除 API 密钥。

    参数:
        key_id: 密钥记录 ID
    """
    service = SettingsService(db)
    deleted = await service.delete_api_key(current_user.id, key_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="密钥记录不存在",
        )


@router.post("/settings/api-keys/{key_id}/validate", response_model=ApiKeyValidateResponse)
async def validate_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyValidateResponse:
    """
    验证 API 密钥有效性。

    通过向对应 LLM Provider 发起轻量级调用来测试密钥是否有效。

    参数:
        key_id: 密钥记录 ID
    """
    service = SettingsService(db)
    return await service.validate_api_key(current_user.id, key_id)


# ──────────────────────────────────────
# 模型偏好
# ──────────────────────────────────────


@router.get("/settings/model-preference", response_model=ModelPreferenceResponse)
async def get_model_preference(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelPreferenceResponse:
    """
    获取用户的模型偏好设置。

    返回用户选择的推理模型和生成模型。
    """
    service = SettingsService(db)
    return await service.get_model_preference(current_user.id)


@router.put("/settings/model-preference", response_model=ModelPreferenceResponse)
async def update_model_preference(
    body: ModelPreferenceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelPreferenceResponse:
    """
    更新用户的模型偏好设置。

    参数:
        body: 模型偏好更新请求
    """
    service = SettingsService(db)
    return await service.update_model_preference(
        user_id=current_user.id,
        reasoning_model=body.reasoning_model,
        generation_model=body.generation_model,
        fields_set=body.model_fields_set,
    )


# ──────────────────────────────────────
# 用量统计
# ──────────────────────────────────────


@router.get("/settings/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageSummaryResponse:
    """
    获取用户最近 30 天的 LLM 用量汇总。

    按 Provider 分组展示 token 用量和费用。
    """
    service = SettingsService(db)
    return await service.get_usage_summary(current_user.id)


# ──────────────────────────────────────
# 可用模型
# ──────────────────────────────────────


@router.get("/settings/available-models", response_model=list[AvailableModel])
async def get_available_models(
    current_user: User = Depends(get_current_user),
) -> list[AvailableModel]:
    """
    获取可用模型列表。

    返回平台支持的所有 LLM 模型及其档位信息。
    """
    return SettingsService.get_available_models()
