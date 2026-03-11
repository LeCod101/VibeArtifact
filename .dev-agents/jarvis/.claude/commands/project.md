# /project - 生成项目AI说明

为项目生成AI友好的说明文件

## 使用方式

/project init [项目路径]     # 扫描项目，生成说明
/project update [项目路径]   # 更新项目说明

## /project init

1. 扫描项目目录
2. 识别技术栈（package.json, pyproject.toml 等）
3. 分析目录结构
4. 读取README（如有）
5. 生成项目说明文档
6. 询问用户补充业务概念和开发规范

## /project update

1. 读取现有项目说明
2. 询问本次变更内容
3. 更新"当前状态"、"进行中的任务"、"变更记录"
