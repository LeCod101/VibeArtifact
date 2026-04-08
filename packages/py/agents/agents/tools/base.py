"""工具基类与注册机制。

定义 @tool 装饰器和 ToolDefinition，
使每个工具函数自动生成 LLM function calling 的 JSON Schema。
"""

from __future__ import annotations

import inspect
import types
import typing
from dataclasses import dataclass
from typing import Any, Callable, get_args, get_origin, get_type_hints

# Python 基础类型 → JSON Schema 类型名映射
_BASIC_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


@dataclass
class ToolDefinition:
    """工具定义，描述一个工具的名称、用途、参数格式和执行函数。

    Attributes:
        name: 工具名，与函数名一致
        description: 工具用途描述，来源于 docstring 首行
        parameters: JSON Schema 格式的参数定义
        handler: 异步执行函数
    """

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]


def _python_type_to_json_schema(python_type: Any) -> dict[str, Any]:
    """将 Python 类型注解转换为 JSON Schema 片段。

    支持 str / int / float / bool / list / list[X] / Optional[X] / X | None。
    """
    origin = get_origin(python_type)
    args = get_args(python_type)

    # 处理 Union / Optional（X | None）
    if origin is types.UnionType or origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _python_type_to_json_schema(non_none[0])
        return {"type": "string"}

    # list 或 list[X]
    if origin is list:
        if args:
            return {"type": "array", "items": _python_type_to_json_schema(args[0])}
        return {"type": "array"}

    # 基础类型
    type_name = _BASIC_TYPE_MAP.get(python_type)
    if type_name:
        return {"type": type_name}

    return {"type": "string"}


def _is_optional_type(python_type: Any) -> bool:
    """判断类型是否包含 None（即 Optional 语义）。"""
    origin = get_origin(python_type)
    args = get_args(python_type)
    if origin is types.UnionType or origin is typing.Union:
        return type(None) in args
    return False


def _parse_docstring(docstring: str) -> tuple[str, dict[str, str]]:
    """解析 Google 风格 docstring，提取工具描述和各参数说明。

    Returns:
        (description, {param_name: param_description})
    """
    if not docstring:
        return ("", {})

    lines = docstring.strip().split("\n")
    description = lines[0].strip()

    param_descs: dict[str, str] = {}
    in_args_section = False

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.lower() in ("args:", "参数:"):
            in_args_section = True
            continue
        if stripped.lower() in ("returns:", "返回:", "raises:", "异常:"):
            in_args_section = False
            continue
        if in_args_section and ":" in stripped:
            param_name, _, param_desc = stripped.partition(":")
            param_name = param_name.strip()
            param_desc = param_desc.strip()
            if param_name:
                param_descs[param_name] = param_desc

    return (description, param_descs)


def tool(func: Callable[..., Any]) -> Callable[..., Any]:
    """工具装饰器，从函数签名和 docstring 自动生成 LLM function calling 元数据。

    被装饰的函数必须是 async 的，返回 dict。
    装饰器会在函数上附加 ``_tool_definition`` 属性。
    """
    if not inspect.iscoroutinefunction(func):
        raise TypeError(f"工具函数 {func.__name__} 必须是 async 函数")

    sig = inspect.signature(func)
    hints = get_type_hints(func)
    description, param_descs = _parse_docstring(func.__doc__ or "")

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        python_type = hints.get(param_name, str)
        schema = _python_type_to_json_schema(python_type)

        if param_name in param_descs:
            schema["description"] = param_descs[param_name]

        properties[param_name] = schema

        has_default = param.default is not inspect.Parameter.empty
        is_optional = _is_optional_type(python_type)
        if not has_default and not is_optional:
            required.append(param_name)

    parameters: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": required,
    }

    tool_def = ToolDefinition(
        name=func.__name__,
        description=description,
        parameters=parameters,
        handler=func,
    )

    func._tool_definition = tool_def  # type: ignore[attr-defined]
    return func
