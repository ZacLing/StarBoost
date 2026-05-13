# StarBoost 概览

[English](../overview.md) | [中文](overview.md)

StarBoost 围绕 AI 产出和专家反馈组织一套可迭代的标注流程：

1. 加载一个任务包。
2. AI 在隔离 workspace 中生成初始产出。
3. 专家查看最新产出并填写 review。
4. StarBoost 校验 review 中 strengths 和 weaknesses 的数量要求。
5. AI 根据专家确认的 weaknesses 生成新的完整产出。
6. 专家继续审阅，直到当前轮次允许提交零个 weakness 并结束流程；如果专家仍不满意，也可以继续写 weaknesses 进入下一轮。
7. 导出完整运行记录，包括产出、review、trace、耗时和状态文件。
