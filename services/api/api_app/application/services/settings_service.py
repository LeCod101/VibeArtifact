"""
Settings 业务逻辑服务。

处理用户 API 密钥的 CRUD、模型偏好管理和用量统计查询。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.schemas.settings import (
    ApiKeyResponse,
    ApiKeyValidateResponse,
    AvailableModel,
    ModelPreferenceResponse,
    ProviderUsageSummary,
    UsageSummaryResponse,
)
from api_app.core.encryption import decrypt_api_key, encrypt_api_key, mask_api_key

logger = logging.getLogger(__name__)

# 可用模型列表（静态配置，后续可改为动态获取）
AVAILABLE_MODELS: list[AvailableModel] = [
    AvailableModel(
        id="anthropic/claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        provider="anthropic",
        tier="both",
    ),
    AvailableModel(
        id="anthropic/claude-haiku-4-5-20251001",
        name="Claude Haiku 4.5",
        provider="anthropic",
        tier="generation",
    ),
    AvailableModel(
        id="openai/gpt-4o",
        name="GPT-4o",
        provider="openai",
        tier="both",
    ),
    AvailableModel(
        id="openai/gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        tier="generation",
    ),
    AvailableModel(
        id="google/gemini-2.0-flash",
        name="Gemini 2.0 Flash",
        provider="google",
        tier="both",
    ),
    AvailableModel(
        id="google/gemini-2.5-pro-preview-06-05",
        name="Gemini 2.5 Pro",
        provider="google",
        tier="reasoning",
    ),
]


class SettingsService:
    """
    设置业务逻辑服务。

    封装 API 密钥管理、模型偏好和用量统计的数据库操作。
    """

    def __init__(self, db: AsyncSession):
        """
        初始化设置服务。

        参数:
            db: 异步数据库会话
        """
        self._db = db

    # ──────────────────────────────────────
    # API 密钥管理
    # ──────────────────────────────────────

    async def list_api_keys(self, user_id: UUID) -> list[ApiKeyResponse]:
        """
        获取用户所有 API 密钥（掩码显示）。

        参数:
            user_id: 用户 ID

        返回:
            API 密钥列表（掩码）
        """
        from platform_data.models.user_api_key import UserApiKey

        result = await self._db.execute(
            select(UserApiKey)
            .where(UserApiKey.user_id == user_id)
            .order_by(UserApiKey.created_at.desc())
        )
        keys = result.scalars().all()

        responses = []
        for key in keys:
            responses.append(
                ApiKeyResponse(
                    id=key.id,
                    provider=key.provider,
                    masked_key=key.masked_key,
                    display_label=key.display_label,
                    is_active=key.is_active,
                    is_valid=key.is_valid,
                    last_validated_at=key.last_validated_at,
                    created_at=key.created_at,
                )
            )

        return responses

    async def upsert_api_key(
        self,
        user_id: UUID,
        provider: str,
        api_key: str,
        display_label: str | None = None,
    ) -> ApiKeyResponse:
        """
        添加或更新 API 密钥。

        如果用户已有该 provider 的密钥则更新，否则创建新记录。

        参数:
            user_id: 用户 ID
            provider: 提供商标识
            api_key: 明文 API 密钥
            display_label: 自定义标签

        返回:
            密钥响应（掩码）
        """
        from platform_data.models.user_api_key import UserApiKey

        # 查找是否已存在
        result = await self._db.execute(
            select(UserApiKey).where(
                UserApiKey.user_id == user_id,
                UserApiKey.provider == provider,
            )
        )
        existing = result.scalar_one_or_none()

        encrypted = encrypt_api_key(api_key)
        masked = mask_api_key(api_key)

        if existing is not None:
            # 更新已有记录
            existing.encrypted_key = encrypted
            existing.masked_key = masked
            existing.display_label = display_label
            existing.is_valid = None
            existing.last_validated_at = None
            existing.is_active = True
            await self._db.commit()
            await self._db.refresh(existing)

            return ApiKeyResponse(
                id=existing.id,
                provider=existing.provider,
                masked_key=masked,
                display_label=existing.display_label,
                is_active=existing.is_active,
                is_valid=existing.is_valid,
                last_validated_at=existing.last_validated_at,
                created_at=existing.created_at,
            )

        # 创建新记录
        new_key = UserApiKey(
            user_id=user_id,
            provider=provider,
            encrypted_key=encrypted,
            masked_key=masked,
            display_label=display_label,
        )
        self._db.add(new_key)
        await self._db.commit()
        await self._db.refresh(new_key)

        return ApiKeyResponse(
            id=new_key.id,
            provider=new_key.provider,
            masked_key=masked,
            display_label=new_key.display_label,
            is_active=new_key.is_active,
            is_valid=new_key.is_valid,
            last_validated_at=new_key.last_validated_at,
            created_at=new_key.created_at,
        )

    async def delete_api_key(self, user_id: UUID, key_id: UUID) -> bool:
        """
        删除 API 密钥。

        参数:
            user_id: 用户 ID
            key_id: 密钥记录 ID

        返回:
            是否成功删除
        """
        from platform_data.models.user_api_key import UserApiKey

        result = await self._db.execute(
            delete(UserApiKey).where(
                UserApiKey.id == key_id,
                UserApiKey.user_id == user_id,
            )
        )
        await self._db.commit()
        return result.rowcount > 0

    async def validate_api_key(
        self, user_id: UUID, key_id: UUID
    ) -> ApiKeyValidateResponse:
        """
        验证 API 密钥有效性。

        通过 LiteLLM 发起一个轻量级调用来测试密钥是否有效。

        参数:
            user_id: 用户 ID
            key_id: 密钥记录 ID

        返回:
            验证结果
        """
        from platform_data.models.user_api_key import UserApiKey

        result = await self._db.execute(
            select(UserApiKey).where(
                UserApiKey.id == key_id,
                UserApiKey.user_id == user_id,
            )
        )
        key_record = result.scalar_one_or_none()
        if key_record is None:
            return ApiKeyValidateResponse(
                key_id=key_id,
                provider="unknown",
                is_valid=False,
                message="密钥记录不存在",
            )

        # 验证冷却期：距上次验证不足 60 秒则拒绝
        if key_record.last_validated_at is not None:
            elapsed = (datetime.now(timezone.utc) - key_record.last_validated_at).total_seconds()
            if elapsed < 60:
                return ApiKeyValidateResponse(
                    key_id=key_id,
                    provider=key_record.provider,
                    is_valid=key_record.is_valid or False,
                    message="验证过于频繁，请稍后再试",
                )

        # 解密密钥
        try:
            plain_key = decrypt_api_key(key_record.encrypted_key)
        except Exception:
            key_record.is_valid = False
            key_record.last_validated_at = datetime.now(timezone.utc)
            await self._db.commit()
            return ApiKeyValidateResponse(
                key_id=key_id,
                provider=key_record.provider,
                is_valid=False,
                message="密钥解密失败",
            )

        # 尝试轻量级 LLM 调用验证
        is_valid = False
        message = "验证失败"
        try:
            import litellm

            # 构建默认测试模型
            test_model_map = {
                "anthropic": "anthropic/claude-haiku-4-5-20251001",
                "openai": "openai/gpt-4o-mini",
                "google": "google/gemini-2.0-flash",
                "azure": "azure/gpt-4o-mini",
            }

            test_model = test_model_map.get(
                key_record.provider, "openai/gpt-4o-mini"
            )

            # 使用 litellm 的 api_key 参数直接传入
            await litellm.acompletion(
                model=test_model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
                api_key=plain_key,
            )
            is_valid = True
            message = "密钥验证成功"
        except Exception as exc:
            message = "密钥验证失败，请检查密钥是否正确"
            logger.warning("API Key 验证失败: provider=%s, error=%s", key_record.provider, exc)

        # 更新验证状态
        key_record.is_valid = is_valid
        key_record.last_validated_at = datetime.now(timezone.utc)
        await self._db.commit()

        return ApiKeyValidateResponse(
            key_id=key_id,
            provider=key_record.provider,
            is_valid=is_valid,
            message=message,
        )

    # ──────────────────────────────────────
    # 模型偏好
    # ──────────────────────────────────────

    async def get_model_preference(self, user_id: UUID) -> ModelPreferenceResponse:
        """
        获取用户模型偏好。

        参数:
            user_id: 用户 ID

        返回:
            模型偏好响应
        """
        from platform_data.models.user_api_key import UserModelPreference

        result = await self._db.execute(
            select(UserModelPreference).where(
                UserModelPreference.user_id == user_id
            )
        )
        pref = result.scalar_one_or_none()

        if pref is None:
            return ModelPreferenceResponse(
                reasoning_model=None,
                generation_model=None,
            )

        return ModelPreferenceResponse(
            reasoning_model=pref.reasoning_model,
            generation_model=pref.generation_model,
        )

    async def update_model_preference(
        self,
        user_id: UUID,
        reasoning_model: str | None = None,
        generation_model: str | None = None,
        fields_set: set[str] | None = None,
    ) -> ModelPreferenceResponse:
        """
        更新用户模型偏好。

        使用 fields_set 区分"未发送"和"显式发送 None"，
        允许用户将已设置的模型清空。

        参数:
            user_id: 用户 ID
            reasoning_model: 推理模型标识
            generation_model: 生成模型标识
            fields_set: 请求中实际出现的字段集合

        返回:
            更新后的模型偏好
        """
        from platform_data.models.user_api_key import UserModelPreference

        result = await self._db.execute(
            select(UserModelPreference).where(
                UserModelPreference.user_id == user_id
            )
        )
        pref = result.scalar_one_or_none()

        if pref is None:
            pref = UserModelPreference(
                user_id=user_id,
                reasoning_model=reasoning_model,
                generation_model=generation_model,
            )
            self._db.add(pref)
        else:
            # 仅更新请求中实际出现的字段
            _set = fields_set or set()
            if "reasoning_model" in _set:
                pref.reasoning_model = reasoning_model or None
            if "generation_model" in _set:
                pref.generation_model = generation_model or None

        await self._db.commit()
        await self._db.refresh(pref)

        return ModelPreferenceResponse(
            reasoning_model=pref.reasoning_model,
            generation_model=pref.generation_model,
        )

    # ──────────────────────────────────────
    # 用量统计
    # ──────────────────────────────────────

    async def get_usage_summary(self, user_id: UUID) -> UsageSummaryResponse:
        """
        获取用户最近 30 天的用量汇总。

        参数:
            user_id: 用户 ID

        返回:
            用量汇总响应
        """
        from platform_data.models.usage_record import UsageRecord

        # 30 天前
        since = datetime.now(timezone.utc) - timedelta(days=30)

        # 按 provider 分组统计
        result = await self._db.execute(
            select(
                UsageRecord.provider,
                func.sum(UsageRecord.prompt_tokens).label("total_prompt"),
                func.sum(UsageRecord.completion_tokens).label("total_completion"),
                func.sum(UsageRecord.total_cost).label("total_cost"),
                func.count(UsageRecord.id).label("call_count"),
            )
            .where(
                UsageRecord.user_id == user_id,
                UsageRecord.created_at >= since,
            )
            .group_by(UsageRecord.provider)
        )
        rows = result.all()

        by_provider: list[ProviderUsageSummary] = []
        grand_prompt = 0
        grand_completion = 0
        grand_cost = 0.0
        grand_count = 0

        for row in rows:
            prompt = int(row.total_prompt or 0)
            completion = int(row.total_completion or 0)
            cost = float(row.total_cost or 0.0)
            count = int(row.call_count or 0)

            by_provider.append(
                ProviderUsageSummary(
                    provider=row.provider,
                    total_prompt_tokens=prompt,
                    total_completion_tokens=completion,
                    total_cost=cost,
                    call_count=count,
                )
            )
            grand_prompt += prompt
            grand_completion += completion
            grand_cost += cost
            grand_count += count

        return UsageSummaryResponse(
            total_prompt_tokens=grand_prompt,
            total_completion_tokens=grand_completion,
            total_cost=grand_cost,
            call_count=grand_count,
            by_provider=by_provider,
        )

    # ──────────────────────────────────────
    # 可用模型
    # ──────────────────────────────────────

    @staticmethod
    def get_available_models() -> list[AvailableModel]:
        """
        获取可用模型列表。

        返回:
            可用模型列表
        """
        return AVAILABLE_MODELS

    # ──────────────────────────────────────
    # 用户密钥解析（供 LLM 调用时使用）
    # ──────────────────────────────────────

    async def get_user_api_keys_decrypted(
        self, user_id: UUID
    ) -> dict[str, str]:
        """
        获取用户所有有效的 API 密钥（解密后）。

        仅返回 is_active=True 的密钥，供 LLM 调用时使用。

        参数:
            user_id: 用户 ID

        返回:
            provider 到 API Key 环境变量名的映射
        """
        from platform_data.models.user_api_key import UserApiKey

        result = await self._db.execute(
            select(UserApiKey).where(
                UserApiKey.user_id == user_id,
                UserApiKey.is_active.is_(True),
            )
        )
        keys = result.scalars().all()

        # 映射 provider 到对应的环境变量名
        env_var_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "azure": "AZURE_API_KEY",
        }

        api_keys: dict[str, str] = {}
        for key in keys:
            try:
                plain = decrypt_api_key(key.encrypted_key)
                var_name = env_var_map.get(key.provider)
                if var_name:
                    api_keys[var_name] = plain
            except Exception:
                logger.warning("解密用户密钥失败: key_id=%s", key.id)

        return api_keys
