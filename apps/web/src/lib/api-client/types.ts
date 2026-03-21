/**
 * API 类型定义 - 镜像后端 Pydantic schema
 *
 * 包含所有 M1 后端 API 的请求和响应类型定义。
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
  active_branch_id: string | null;
  created_at: string;
  updated_at: string;
}

/* ============ 消息相关 ============ */

/** 保存消息请求 */
export interface SaveMessageRequest {
  role: "user" | "assistant" | "system";
  content: string;
}

/** 消息信息响应 */
export interface MessageResponse {
  id: string;
  conversation_id: string;
  branch_id: string;
  role: string;
  content: string;
  content_type: string;
  created_at: string;
  /** 消息执行前的快照 ID */
  snapshot_before_id?: string | null;
  /** 消息执行后的快照 ID */
  snapshot_after_id?: string | null;
  /** 变更摘要（仅 assistant 消息可能携带） */
  change_summary?: ChangeSummaryResponse;
}

/* ============ 对话模式相关 ============ */

/** 发送消息请求 */
export interface SendMessageRequest {
  content: string;
}

/** 变更摘要 */
export interface ChangeSummaryResponse {
  summary: string;
  affected_areas: string[];
  operations_count: number;
  agents_executed: string[];
  new_snapshot_id: string | null;
  warnings: string[];
}

/** 发送消息响应（含助手回复 + 变更摘要） */
export interface SendMessageResponse {
  user_message: MessageResponse;
  assistant_message: MessageResponse;
  change_summary: ChangeSummaryResponse;
}

/** 对话 SSE 事件数据 */
export interface ChatSSEEvent {
  event: string;
  data: Record<string, unknown>;
}

/* ============ 更新项目 ============ */

/** 更新项目请求 */
export interface UpdateProjectRequest {
  name?: string;
  description?: string;
}

/* ============ 快照相关 ============ */

/** 快照信息响应 */
export interface SnapshotResponse {
  id: string;
  project_id: string;
  version: number;
  parent_id: string | null;
  status: string;
  created_at: string;
}

/* ============ 产物相关 ============ */

/** 产物信息响应 */
export interface ArtifactResponse {
  id: string;
  project_id: string;
  snapshot_id: string;
  name: string;
  kind: string;
  content_hash: string | null;
  created_at: string;
}

/* ============ 全权委托运行列表 ============ */

/** 全权委托运行列表项 */
export interface DelegatedRunListItem {
  run_id: string;
  status: string;
  created_at: string | null;
  completed_at: string | null;
}

/* ============ 分支相关 ============ */

/** 创建分支请求 */
export interface CreateBranchRequest {
  parent_branch_id: string;
  branch_name?: string;
  base_snapshot_id?: string;
}

/** Fork 分支请求 */
export interface ForkBranchRequest {
  fork_point_snapshot_id: string;
  branch_name?: string;
}

/** 分支信息响应 */
export interface BranchResponse {
  id: string;
  conversation_id: string;
  parent_branch_id: string | null;
  base_snapshot_id: string | null;
  head_snapshot_id: string | null;
  branch_name: string | null;
  created_at: string;
  message_count: number;
}

/** 分支树节点 */
export interface BranchTreeNode {
  branch: BranchResponse;
  children: BranchTreeNode[];
}

/** 回滚请求 */
export interface RollbackRequest {
  snapshot_id: string;
}

/** 回滚响应 */
export interface RollbackResponse {
  action: "forked" | "switched" | "no_change";
  switched_branch_id: string;
  new_branch_id: string | null;
  snapshot_id: string;
}

/* ============ 审批相关 ============ */

/** 风险条目 */
export interface RiskItem {
  id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  mitigation: string | null;
}

/** 待决策条目 */
export interface DecisionItem {
  id: string;
  title: string;
  description: string;
  status: string;
  alternatives: string[] | null;
}

/** 审批历史条目 */
export interface ApprovalHistoryItem {
  id: string;
  action: string;
  reason: string | null;
  created_at: string;
}

/** 审批项响应 — 包含风险、决策和审批历史 */
export interface ApprovalItemsResponse {
  run_id: string;
  status: string;
  high_risks: RiskItem[];
  pending_decisions: DecisionItem[];
  requires_approval: boolean;
  approval_history: ApprovalHistoryItem[];
}

/** 审批操作响应 */
export interface ApprovalActionResponse {
  success: boolean;
  action: string;
  run_id: string;
  new_status: string;
  message: string;
}

/** 批准请求 */
export interface ApproveRequest {
  reason?: string;
}

/** 拒绝请求 */
export interface RejectRequest {
  reason?: string;
}

/** 调整请求 */
export interface AdjustRequest {
  feedback: string;
  reason?: string;
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
