/**
 * API 错误类 - 统一处理后端返回的错误信息
 */
export class ApiError extends Error {
  /** HTTP 状态码 */
  status: number;
  /** 后端返回的错误详情 */
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}
