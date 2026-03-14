"""
Prompt 分层拼装器模块。

实现 6 层 Prompt 拼装策略（技术架构 5.1），按优先级顺序组装最终 system prompt：
platform_policy → role → task → output_contract → tool_rules → context_slice

每一层对应一种关注点，互不干扰，便于独立修改和测试。
"""

from enum import StrEnum


class PromptLayer(StrEnum):
    """
    Prompt 分层枚举。

    定义 6 个标准层，按优先级从高到低排列。
    系统在拼装 prompt 时按此顺序拼接各层内容。
    """

    PLATFORM_POLICY = "platform_policy"
    ROLE = "role"
    TASK = "task"
    OUTPUT_CONTRACT = "output_contract"
    TOOL_RULES = "tool_rules"
    CONTEXT_SLICE = "context_slice"


# 各层的中文标题，用于在最终 prompt 中作为分隔标记
_LAYER_TITLES: dict[PromptLayer, str] = {
    PromptLayer.PLATFORM_POLICY: "平台策略",
    PromptLayer.ROLE: "角色设定",
    PromptLayer.TASK: "任务描述",
    PromptLayer.OUTPUT_CONTRACT: "输出格式约束",
    PromptLayer.TOOL_RULES: "工具使用规则",
    PromptLayer.CONTEXT_SLICE: "上下文信息",
}

# 默认平台策略模板
DEFAULT_PLATFORM_POLICY = """你是 VibeArtifact AI 产品工程系统的一个专业 Agent。
你必须严格按照指定的 JSON schema 输出结构化结果。
禁止在 JSON 之外输出任何内容。
所有文本内容使用中文。"""

# 层与层之间的分隔线
_LAYER_SEPARATOR = "\n" + "=" * 60 + "\n"


class PromptBuilder:
    """
    6 层 Prompt 拼装器。

    按照技术架构 5.1 的分层规范组装最终 system prompt：
    platform_policy → role → task → output_contract → tool_rules → context_slice

    使用链式调用风格设置各层内容，最终通过 build_system_prompt() 拼装完整 prompt。
    """

    def __init__(self) -> None:
        """初始化拼装器，创建空的层内容字典。"""
        self._layers: dict[PromptLayer, str] = {}

    def set_platform_policy(self, policy: str) -> "PromptBuilder":
        """
        设置平台级约束层。

        包含 JSON 输出规则、安全规则、通用行为约束等。
        - policy: 平台策略文本
        - 返回: self，支持链式调用
        """
        self._layers[PromptLayer.PLATFORM_POLICY] = policy
        return self

    def set_role(self, role_prompt: str) -> "PromptBuilder":
        """
        设置角色身份层。

        定义 Agent 的角色身份和核心职责，通常从 templates/ 加载。
        - role_prompt: 角色身份 prompt 文本
        - 返回: self，支持链式调用
        """
        self._layers[PromptLayer.ROLE] = role_prompt
        return self

    def set_task(self, task_prompt: str) -> "PromptBuilder":
        """
        设置当前任务描述层。

        描述本次调用需要完成的具体任务。
        - task_prompt: 任务描述文本
        - 返回: self，支持链式调用
        """
        self._layers[PromptLayer.TASK] = task_prompt
        return self

    def set_output_contract(self, schema_description: str) -> "PromptBuilder":
        """
        设置输出格式约束层。

        明确规定 Agent 输出的 JSON schema 描述，确保输出可被解析。
        - schema_description: 输出 JSON schema 的文本描述
        - 返回: self，支持链式调用
        """
        self._layers[PromptLayer.OUTPUT_CONTRACT] = schema_description
        return self

    def set_tool_rules(self, rules: str) -> "PromptBuilder":
        """
        设置工具使用规则层。

        Phase 1 通常为空，后续 Phase 可添加 function calling 规则。
        - rules: 工具规则文本
        - 返回: self，支持链式调用
        """
        self._layers[PromptLayer.TOOL_RULES] = rules
        return self

    def set_context_slice(self, context: str) -> "PromptBuilder":
        """
        设置上下文切片层。

        注入 IR 快照数据和对话历史摘要，使 Agent 了解当前项目状态。
        - context: 上下文切片文本（通常由 ContextSlice.to_prompt_text() 生成）
        - 返回: self，支持链式调用
        """
        self._layers[PromptLayer.CONTEXT_SLICE] = context
        return self

    def set_layer(self, layer: PromptLayer, content: str) -> "PromptBuilder":
        """
        通用层设置方法。

        可用于程序化设置任意层的内容。
        - layer: 要设置的层枚举值
        - content: 该层的文本内容
        - 返回: self，支持链式调用
        """
        self._layers[layer] = content
        return self

    def build_system_prompt(self) -> str:
        """
        按优先级顺序拼装完整 system prompt。

        遍历 PromptLayer 枚举定义的顺序，将已设置的层内容用分隔线隔开拼接。
        跳过未设置或空内容的层。

        - 返回: 拼装后的完整 system prompt 字符串
        """
        sections: list[str] = []

        for layer in PromptLayer:
            content = self._layers.get(layer)
            if not content:
                continue
            title = _LAYER_TITLES.get(layer, layer.value)
            section = f"## {title}\n\n{content}"
            sections.append(section)

        return _LAYER_SEPARATOR.join(sections)

    def build_messages(self, user_message: str) -> list[dict[str, str]]:
        """
        构建完整的 messages 列表。

        包含 system prompt 和 user message，格式兼容 OpenAI / Anthropic API。
        - user_message: 用户消息文本
        - 返回: [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
        """
        system_prompt = self.build_system_prompt()

        messages: list[dict[str, str]] = []

        # system prompt 可能为空（所有层都未设置的情况）
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_message})

        return messages
