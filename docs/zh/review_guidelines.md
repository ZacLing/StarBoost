# 审阅指南

[English](../review_guidelines.md) | [中文](review_guidelines.md)

每次 review 都应该足够具体，让下一轮 AI 能根据专家反馈改进产出，但又不暴露专家隐藏 reasoning 或标准答案。

review 有两个作用对象：

- StarBoost 会读取结构化 strengths 和 weaknesses，用于校验和组织下一轮 prompt。
- 下一轮 executor 只会收到 weaknesses，不会收到 strengths、scores、rubrics 或 human reference。

默认规则：

- 至少三个 strengths。
- 第一轮 review 至少五个 weaknesses。
- 每次 review 被接受后，最低 weakness 数量减少一。
- 最低 weakness 数量只是下限；如果专家觉得结果仍然不满意，可以写更多 weaknesses。
- 当最低 weakness 数量降到 0 时，提交零个 weakness 会结束流程；提交一个或多个 weaknesses 会继续进入下一轮。
- review 必须填写 StarBoost 设计中的两个 score：
  - `Latest Deliverables Satisfaction`：1-5 的整数，5 表示对当前版本非常满意，1 表示非常不满意。
  - `Latest Deliverables Aligns User Scores`：1-10 的整数，5 表示大致等于专家自己完成这个 task 的水平。
- 重复复制的 strengths 或 weaknesses 会在提交时被拒绝。

好的 weakness：

```text
- API behavior 部分描述了 search endpoints，但没有说明 invalid query parameters 的错误响应 JSON。
```

弱的 weakness：

```text
- Make it better.
```
