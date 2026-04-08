/**
 * API 类型定义 - 镜像后端 Pydantic schema
 *
 * 包含后端 API 的请求和响应类型定义（含 v2 单 Agent + 工具集模型）。
 */

/* ============ 认证相关 ============ */

/** 注册请求 */
export interface RegisterRequest {
  email: string;
  password: string;
  display_name?: string;
}

/** 登录请求 */
export interface LoginRequest {
  email: string;
  password: string;
}

/** 刷新令牌请求 */
export interface RefreshRequest {
  refresh_token: string;
}

/** 令牌响应 - 登录/刷新成功后返回 */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** 用户信息响应 */
export interface UserResponse {
  id: string;
  email: string;
  display_name: string | null;
  status: string;
  created_at: string;
}

/* ============ 项目相关 ============ */

/** 创建项目请求 */
export interface CreateProjectRequest {
  name: string;
  description?: string;
  /** 项目类型（如 homework / thesis / personal） */
  project_type?: string;
}

/** 项目信息响应 */
export interface ProjectResponse {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  project_type?: string;
  course_name?: string | null;
  tech_requirements?: string | null;
}

/* ============ 对话相关 ============ */

/** 创建对话请求 */
export interface CreateConversationRequest {
  title?: string;
}

/** 对话信息响应 */
export interface ConversationResponse {
  id: string;
  project_id: string;
  title: string | null;
  mode: string;
  status: string;
  created_at: string;
  updated_at: string;
}

/* ============ 消息相关 ============ */

/** 保存消息请求 */
export interface SaveMessageRequest {
  role: "user" | "assistant" | "system";
  content: string;
}

/** 工具调用信息（消息中嵌入，与 SSE tool_call 对齐） */
export interface ToolCallInfo {
  tool_name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
}

/** 消息信息响应 */
export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  content_type: string;
  created_at: string;
  tool_calls?: ToolCallInfo[];
  artifacts_created?: string[];
}

/* ============ 对话模式 / 兼容非流式发送（若后端仍提供） ============ */

/** 发送消息请求 */
export interface SendMessageRequest {
  content: string;
}

/** 发送消息响应（助手回复，无变更摘要） */
export interface SendMessageResponse {
  user_message: MessageResponse;
  assistant_message: MessageResponse;
}

/** 对话 SSE 事件数据（旧字段名保留，供非 Agent 流复用） */
export interface ChatSSEEvent {
  event: string;
  data: Record<string, unknown>;
}

/* ============ Agent v2：模式、SSE、Chat、产物 ============ */

/** Agent 运行模式 */
export type AgentMode = "auto" | "discussion" | "thinking";

/** Agent SSE 事件类型 */
export type SSEEventType =
  | "thinking"
  | "tool_call"
  | "tool_result"
  | "content"
  | "error"
  | "done";

/** Agent SSE 单条事件 */
export interface AgentSSEEvent {
  event: SSEEventType;
  data: Record<string, unknown>;
}

/** 产物类型 */
export type ArtifactType =
  | "code"
  | "document"
  | "diagram"
  | "sql"
  | "config"
  | "other";

/** 产物详情响应（对齐后端 ArtifactResponse） */
export interface ArtifactResponseV2 {
  id: string;
  project_id: string;
  artifact_type: ArtifactType;
  title: string;
  content: string;
  file_path: string | null;
  language: string | null;
  version_num: number;
  parent_id: string | null;
  created_at: string;
  updated_at: string;
}

/** 产物列表项（对齐后端 ArtifactListItem，不含 content） */
export interface ArtifactListItem {
  id: string;
  project_id: string;
  artifact_type: ArtifactType;
  title: string;
  file_path: string | null;
  language: string | null;
  version_num: number;
  parent_id: string | null;
  created_at: string;
  updated_at: string;
}

/** 产物版本历史项（对齐后端 ArtifactVersionResponse） */
export interface ArtifactVersionItem {
  id: string;
  version_num: number;
  title: string;
  created_at: string;
}

/** 更新产物请求（对齐后端 ArtifactUpdateRequest） */
export interface UpdateArtifactRequest {
  title?: string;
  content?: string;
  file_path?: string;
  language?: string;
}

/** 导出项目请求（与后端 ExportRequest 对齐） */
export interface ExportProjectRequest {
  export_type?: string;
}

/** 导出任务响应（与后端 ExportResponse 对齐） */
export interface ExportResponse {
  id: string;
  project_id: string;
  export_type: string;
  file_url: string | null;
  file_size_bytes: number | null;
  created_at: string;
}

/** Chat 请求（SSE 流式入口） */
export interface ChatRequest {
  message: string;
  mode?: AgentMode;
  conversation_id?: string;
}

/* ============ 更新项目 ============ */

/** 更新项目请求 */
export interface UpdateProjectRequest {
  name?: string;
  description?: string;
}

/* ============ 设置相关 ============ */

/** API 密钥创建/更新请求 */
export interface ApiKeyCreateRequest {
  provider: string;
  api_key: string;
  display_label?: string;
}

/** API 密钥响应（掩码显示） */
export interface ApiKeyResponse {
  id: string;
  provider: string;
  masked_key: string;
  display_label: string | null;
  is_active: boolean;
  is_valid: boolean | null;
  last_validated_at: string | null;
  created_at: string;
}

/** 密钥验证结果 */
export interface ApiKeyValidateResponse {
  key_id: string;
  provider: string;
  is_valid: boolean;
  message: string;
}

/** 模型偏好请求 */
export interface ModelPreferenceRequest {
  reasoning_model?: string | null;
  generation_model?: string | null;
}

/** 模型偏好响应 */
export interface ModelPreferenceResponse {
  reasoning_model: string | null;
  generation_model: string | null;
}

/** 按提供商汇总的用量 */
export interface ProviderUsageSummary {
  provider: string;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_cost: number;
  call_count: number;
}

/** 用量汇总响应 */
export interface UsageSummaryResponse {
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_cost: number;
  call_count: number;
  by_provider: ProviderUsageSummary[];
}

/** 可用模型 */
export interface AvailableModel {
  id: string;
  name: string;
  provider: string;
  tier: string;
}
