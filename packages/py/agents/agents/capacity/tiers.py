"""
容量分档模块。

根据总点数将项目分为 small / medium / large 三档，
决定是否需要触发收缩流程。
- small (0-30)：直接通过，无需收缩
- medium (31-60)：建议收缩，用户可跳过
- large (61+)：必须收缩，不可跳过
"""

from enum import StrEnum


class CapacityTier(StrEnum):
    """
    容量分档枚举。

    - SMALL: 小型项目，0-30 点
    - MEDIUM: 中型项目，31-60 点
    - LARGE: 大型项目，61 点以上
    """

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


# 每个分档的点数预算上限
TIER_BUDGETS: dict[CapacityTier, int] = {
    CapacityTier.SMALL: 30,
    CapacityTier.MEDIUM: 60,
}


def get_tier(points: int) -> CapacityTier:
    """
    根据总点数返回对应的容量分档。

    - points: 容量总点数
    - 返回: 对应的 CapacityTier 枚举值
    """
    if points <= TIER_BUDGETS[CapacityTier.SMALL]:
        return CapacityTier.SMALL
    if points <= TIER_BUDGETS[CapacityTier.MEDIUM]:
        return CapacityTier.MEDIUM
    return CapacityTier.LARGE


def is_over_budget(points: int, tier: CapacityTier) -> bool:
    """
    判断给定点数是否超出指定分档的预算。

    - points: 容量总点数
    - tier: 目标分档
    - 返回: 超出预算则为 True

    注意：large 分档没有预算上限概念，始终视为超出。
    """
    budget = TIER_BUDGETS.get(tier)
    if budget is None:
        # large 分档没有预算上限，始终超出
        return True
    return points > budget


def can_skip_contraction(tier: CapacityTier) -> bool:
    """
    判断指定分档是否可以跳过收缩流程。

    - tier: 容量分档
    - 返回: 可跳过收缩则为 True

    规则：
    - small: 直接通过，无需收缩
    - medium: 用户可选择跳过
    - large: 必须收缩，不可跳过
    """
    if tier == CapacityTier.SMALL:
        return True
    if tier == CapacityTier.MEDIUM:
        return True
    return False
