"""
校验结果数据结构模块。

定义 ValidationResult，用于统一表示所有校验器的返回结果，
包含校验是否通过、致命错误列表和非致命警告列表。
"""

from __future__ import annotations

from pydantic import BaseModel


class ValidationResult(BaseModel):
    """
    校验结果。

    - is_valid: 校验是否通过（无致命错误时为 True）
    - errors: 致命错误列表，必须修复
    - warnings: 非致命警告列表，建议处理但不阻塞
    """

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    @staticmethod
    def ok() -> ValidationResult:
        """
        创建一个校验通过的结果。

        返回 is_valid=True、无错误、无警告的结果对象。
        """
        return ValidationResult(is_valid=True, errors=[], warnings=[])

    @staticmethod
    def fail(
        errors: list[str],
        warnings: list[str] | None = None,
    ) -> ValidationResult:
        """
        创建一个校验失败的结果。

        - errors: 致命错误列表（至少需要包含一条）
        - warnings: 可选的非致命警告列表
        """
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings or [],
        )

    def merge(self, other: ValidationResult) -> ValidationResult:
        """
        合并两个校验结果。

        将 other 的 errors 和 warnings 追加到当前结果中，
        只要任意一方有致命错误，合并后 is_valid 即为 False。
        """
        merged_errors = self.errors + other.errors
        merged_warnings = self.warnings + other.warnings
        return ValidationResult(
            is_valid=(len(merged_errors) == 0),
            errors=merged_errors,
            warnings=merged_warnings,
        )
