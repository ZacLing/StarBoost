# 任务包格式

[English](../package_format.md) | [中文](package_format.md)

任务包根目录包含原始任务输入和 StarBoost 运行状态：

```text
task_package/
  original_task/
    task.json
    prompt.md
    rubrics.json
    human_reference.json        # 可选，永远不展示给 executor
    materials/                  # 可选，可见材料
  starboost.json                # 自动生成
  boost_runs/                   # 自动生成
  exports/                      # 自动生成
```

`task.json` 最小字段：

```json
{
  "task_id": "example_task",
  "prompt_file": "prompt.md",
  "rubrics_file": "rubrics.json",
  "materials_dir": "materials",
  "allow_web_search": false
}
```

StarBoost 当前版本要求所有 rubrics 都是 fail-fast。这样专家 review 循环会围绕硬性验收要求展开，而不是围绕可选加分项展开。

executor 可见输入会被复制到一个干净 workspace：

```text
workspace/
  inputs/
    prompt.md
    materials/
      ...
  outputs/
```

改进轮次还会额外收到：

```text
workspace/
  inputs/
    previous_deliverables/
    review_weaknesses.md
```

rubrics、隐藏 reference 和专家 reasoning 永远不会复制进 executor workspace。

