# API 结构化模板

## META
模块: [模块名称]
版本: v1.0
基础路径: /api/v1
认证: Bearer Token | Cookie | 无

## 接口清单
| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /path | 说明 | yes/no |

## 接口详情

### METHOD /path
> 说明

请求:
{field: "type, 必填/可选, 说明"}

响应:
{code: "number, 0=成功", data: {}, msg: "string"}

错误码:
| code | 说明 |
|------|------|

## 通用说明
认证方式: Authorization: Bearer {token}
响应格式: {code, data, msg}
分页参数: page(从1开始), size(默认20)
