# /notify-jarvis - 通知贾维斯

向贾维斯发送通知（需用户确认）

## 使用方式
/notify-jarvis [消息内容]

## 执行步骤

1. 先询问用户确认："确定要通知贾维斯吗？"

2. 用户确认后，向 `../shared/notifications.json` 添加通知：
   - from: kyle
   - to: jarvis
   - type: review_result / bug_report / message
   - 包含任务名称、审查报告路径、消息内容

3. 告知用户："已通知贾维斯，请让他查看 /status"
