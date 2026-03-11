# /notify-kyle - 通知凯尔

向凯尔发送通知（需用户确认）

## 使用方式
/notify-kyle [消息内容]

## 执行步骤

1. 先询问用户确认："确定要通知凯尔吗？"

2. 用户确认后，向 `../shared/notifications.json` 添加通知：
   - from: jarvis
   - to: kyle
   - type: review_request / bug_report / message
   - 包含任务名称、相关文件、消息内容

3. 告知用户："已通知凯尔，请让他查看 /status"
