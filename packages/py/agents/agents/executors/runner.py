"""
统一 Agent 执行器模块。

封装 Agent 调用的完整流程：
1. 从 AgentRegistry 获取 AgentConfig
2. ContextAssembler 组装上下文
3. PromptBuilder 拼装 prompt
4. LLMProvider 调用模型
5. 解析响应为 AgentOutput
6. file_extractor 提取工作区文件
7. 返回结果
"""

from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError
from runtime_tools.cost.tracker import CostTracker
from runtime_tools.llm.config import LLMConfig, get_model_for_tier
from runtime_tools.llm.provider import BaseLLMProvider
from runtime_tools.llm.schemas import LLMMessage, LLMRequest

from agents.configs.base import AgentConfig
from agents.configs.registry import AgentRegistry
from agents.context.assembler import ContextAssembler
from agents.context.budget import ContextBudget
from agents.prompts.builder import PromptBuilder
from agents.schemas.base import AgentInput, AgentRunMeta


def _strip_json_fences(content: str) -> str:
    """
    去除 LLM 输出中可能包裹 JSON 的 Markdown 代码围栏。

    部分模型会无视"禁止在 JSON 之外输出任何内容"的约束，
    以 ```json ... ``` 形式返回，此处做容错剥离。

    - content: LLM 原始输出文本
    - 返回: 剥离围栏后的文本（无围栏时原样返回）
    """
    text = content.strip()
    if text.startswith("```"):
        # 去掉第一行的 ```json 或 ```
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        # 去掉结尾的 ```
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


class AgentOutputParseError(Exception):
    """
    Agent 输出解析错误。

    当 LLM 返回的内容无法解析为合法 JSON，
    或 JSON 不符合 Agent 的 output_schema 时抛出。
    - agent_id: 出错的 Agent 标识
    - raw_content: LLM 返回的原始内容
    - cause: 原始异常
    """

    def __init__(
        self, agent_id: str, raw_content: str, cause: Exception
    ) -> None:
        self.agent_id = agent_id
        self.raw_content = raw_content
        self.cause = cause
        super().__init__(
            f"Agent '{agent_id}' 输出解析失败: {cause}"
        )


class AgentRunResult(BaseModel):
    """
    Agent 单次运行结果。

    包含 Agent 的输出、提取的工作区文件列表、警告信息和运行元信息。
    - agent_id: 执行的 Agent 唯一标识
    - output: Agent 的具体输出（BaseModel 子类实例）
    - files: 提取的工作区文件字典列表（path/content/kind）
    - warnings: 汇总的警告信息列表
    - meta: Agent 运行元信息（可选）
    """

    # 允许 BaseModel 子类作为字段值
    model_config = {"arbitrary_types_allowed": True}

    agent_id: str
    output: BaseModel
    files: list[dict] = []
    warnings: list[str] = []
    meta: AgentRunMeta | None = None


class AgentRunner:
    """
    统一 Agent 执行器。

    封装 Agent 调用的完整流程，包括上下文组装、prompt 拼装、
    LLM 调用、响应解析、Translator 翻译和成本记账。
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        registry: AgentRegistry | None = None,
        llm_config: LLMConfig | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        """
        初始化 Agent 执行器。

        - llm_provider: LLM 调用提供者实例
        - registry: Agent 注册表，为 None 时使用全局单例
        - llm_config: LLM 配置，为 None 时从环境变量读取
        - cost_tracker: 成本追踪器，为 None 时不记账
        """
        self._llm = llm_provider
        self._registry = registry or AgentRegistry.get_instance()
        self._llm_config = llm_config or LLMConfig.from_env()
        self._cost_tracker = cost_tracker

    async def run(
        self, agent_id: str, agent_input: AgentInput
    ) -> AgentRunResult:
        """
        执行单个 Agent。

        完整流程：
        1. 获取 Agent 配置
        2. 组装上下文 + 预算截断
        3. 拼装 prompt
        4. 确定模型 + 调用 LLM
        5. 解析输出
        6. 填充运行元信息
        7. file_extractor 提取工作区文件
        8. 成本记账
        9. 返回 AgentRunResult

        - agent_id: Agent 唯一标识
        - agent_input: Agent 统一输入
        - 返回: AgentRunResult，包含 output、files、warnings
        """
        # 步骤 1：获取 Agent 配置
        config = self._registry.get(agent_id)

        # 步骤 2：组装上下文
        assembler = ContextAssembler()
        context_slice = assembler.assemble(agent_input)

        # 步骤 2.1：预算截断
        budget = ContextBudget()
        context_slice = budget.truncate(context_slice)

        # 步骤 3：拼装 prompt
        # 延迟导入避免循环依赖
        from agents.prompts.templates.role_prompts import get_role_prompt

        builder = PromptBuilder()
        builder.set_role(get_role_prompt(agent_id))
        builder.set_task(agent_input.task_description)
        builder.set_output_contract(self._build_output_contract(config))
        builder.set_context_slice(context_slice.to_prompt_text())

        # 步骤 3.1：构建 messages
        # task_description 已在 set_task 中注入 system prompt，
        # user message 只需发送简短触发指令，避免内容重复
        messages = builder.build_messages(
            "请根据上述上下文和任务要求生成输出。"
        )

        # 步骤 4：确定模型（provider/model 二元组）
        provider, model_name = get_model_for_tier(
            self._llm_config, config.model_tier
        )

        # 步骤 5：调用 LLM
        llm_request = LLMRequest(
            messages=[LLMMessage(**m) for m in messages],
            model=f"{provider}/{model_name}",
            metadata={
                "agent_id": agent_id,
                "project_id": str(agent_input.project_id),
            },
        )
        llm_response = await self._llm.complete(llm_request)

        # 步骤 6：解析输出
        try:
            raw_output = json.loads(_strip_json_fences(llm_response.content))
            output = config.output_schema.model_validate(raw_output)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise AgentOutputParseError(
                agent_id=agent_id,
                raw_content=llm_response.content,
                cause=exc,
            ) from exc

        # 步骤 7：填充运行元信息
        meta = AgentRunMeta(
            model=llm_response.model,
            provider=llm_response.provider,
            prompt_tokens=llm_response.usage.prompt_tokens,
            completion_tokens=llm_response.usage.completion_tokens,
            total_cost=llm_response.cost,
            latency_ms=llm_response.latency_ms,
        )
        output.meta = meta

        # 步骤 8：file_extractor 提取工作区文件
        from agents.executors.file_extractor import extract_files

        high_level = getattr(output, config.high_level_key)
        files = extract_files(agent_id, high_level)

        # 步骤 9：成本记账（如果有 tracker）
        if self._cost_tracker:
            await self._cost_tracker.record(
                agent_id=agent_id,
                project_id=agent_input.project_id,
                model=llm_response.model,
                provider=llm_response.provider,
                prompt_tokens=llm_response.usage.prompt_tokens,
                completion_tokens=llm_response.usage.completion_tokens,
                total_cost=llm_response.cost,
                latency_ms=llm_response.latency_ms,
            )

        # 步骤 10：组装并返回结果
        return AgentRunResult(
            agent_id=agent_id,
            output=output,
            files=files,
            warnings=output.warnings,
            meta=meta,
        )

    @staticmethod
    def _build_output_contract(config: AgentConfig) -> str:
        """
        根据 output schema 生成输出格式约束文本。

        从 AgentConfig 的 output_schema 提取 JSON Schema，
        格式化为 prompt 中使用的约束描述。

        - config: Agent 配置
        - 返回: 输出格式约束文本
        """
        schema = config.output_schema.model_json_schema()
        return (
            "你必须输出符合以下 JSON Schema 的 JSON:\n"
            f"{json.dumps(schema, ensure_ascii=False, indent=2)}"
        )
