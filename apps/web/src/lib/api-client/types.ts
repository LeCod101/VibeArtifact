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
}
