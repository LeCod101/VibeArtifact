"""
容量规则模块。

定义容量维度枚举和每个维度的计分规则。
规则表决定了每个维度的单位点数和 Phase 1 上限，
用于将 ScopeDraft 映射为具体的容量点数。
"""

from enum import StrEnum

from pydantic import BaseModel, computed_field


class CapacityDimension(StrEnum):
    """
    容量维度枚举。

    每个枚举值对应一个可量化的产品复杂度维度。
    """

    PAGES = "pages"
    API_ENDPOINTS = "api_endpoints"
    DB_TABLES = "db_tables"
    AUTH_FLOWS = "auth_flows"
    INTEGRATIONS = "integrations"
    FILE_UPLOAD = "file_upload"
    REALTIME = "realtime"
    PAYMENT = "payment"


class CapacityRule(BaseModel):
    """
    单个维度的容量规则。

    - dimension: 对应的容量维度
    - unit_cost: 每单位占用的点数
    - max_units: Phase 1 允许的最大单位数
    - max_points: 该维度的最大点数（自动计算 = unit_cost * max_units）
    """

    dimension: CapacityDimension
    unit_cost: int
    max_units: int

    @computed_field
    @property
    def max_points(self) -> int:
        """计算该维度的最大点数上限。"""
        return self.unit_cost * self.max_units


# 默认规则表，按 M4 文档定义
DEFAULT_RULES: dict[CapacityDimension, CapacityRule] = {
    CapacityDimension.PAGES: CapacityRule(
        dimension=CapacityDimension.PAGES,
        unit_cost=3,
        max_units=8,
    ),
    CapacityDimension.API_ENDPOINTS: CapacityRule(
        dimension=CapacityDimension.API_ENDPOINTS,
        unit_cost=2,
        max_units=15,
    ),
    CapacityDimension.DB_TABLES: CapacityRule(
        dimension=CapacityDimension.DB_TABLES,
        unit_cost=4,
        max_units=6,
    ),
    CapacityDimension.AUTH_FLOWS: CapacityRule(
        dimension=CapacityDimension.AUTH_FLOWS,
        unit_cost=5,
        max_units=2,
    ),
    CapacityDimension.INTEGRATIONS: CapacityRule(
        dimension=CapacityDimension.INTEGRATIONS,
        unit_cost=8,
        max_units=2,
    ),
    CapacityDimension.FILE_UPLOAD: CapacityRule(
        dimension=CapacityDimension.FILE_UPLOAD,
        unit_cost=6,
        max_units=1,
    ),
    CapacityDimension.REALTIME: CapacityRule(
        dimension=CapacityDimension.REALTIME,
        unit_cost=10,
        max_units=1,
    ),
    CapacityDimension.PAYMENT: CapacityRule(
        dimension=CapacityDimension.PAYMENT,
        unit_cost=12,
        max_units=0,
    ),
}
