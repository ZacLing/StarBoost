# StarBoost

**面向专家标注与 AI 产出迭代改进的工作台。**

[English](README.md) | [中文](README.zh.md)

StarBoost 帮助领域专家把自己的判断沉淀为结构化、可复用、可审计的标注数据。你提供一个任务包，让 AI 先产出初稿，然后专家像正常审阅工作成果一样进行反馈：指出做得好的地方、写下具体弱点，也可以给出评分。

每次 review 之后，AI 会基于反馈给出一个新的版本，专家可以继续审阅更新后的结果。经过多轮迭代，StarBoost 会记录专家反馈、改进后的产出、运行时间、执行 trace 和最终导出包，让整个标注过程可以回看、比较和复用。

实际使用时，你可以把 StarBoost 当成一个专家参与的 AI 标注工作台：加载任务，查看 AI 输出，填写结构化 review，提交反馈，然后重复这个过程，直到没有值得继续推动下一轮改进的弱点。

## 它能帮你做什么

| 专家工作 | StarBoost 如何辅助 |
| --- | --- |
| 审阅 AI 产出 | 生成包含 strengths、weaknesses、notes、scores 的结构化 review 模板。 |
| 把反馈变成数据 | 将每轮 review 保存为机器可读的元数据。 |
| 逐轮改进答案 | 把专家确认的 weaknesses 送入下一轮 AI 产出。 |
| 保留完整过程 | 保存输出文件、trace、耗时、review 文件和最终导出包。 |
| 隐藏标准答案和评分标准 | executor 只看到可见输入；rubrics 和 reference 不进入工作区。 |

## 工作流

```text
任务包
  -> AI 生成初始产出
  -> 专家审阅 strengths 和 weaknesses
  -> AI 生成更新版本
  -> 专家继续审阅
  -> 导出完整标注记录
```

## 快速开始

```bash
cd StarBoost
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

# 启动 StarBoost 工作台。
starboost

# 在工作台中加载任务包。
starboost [no task]> load_task /path/to/package --executor-model gpt-5.5

# 加载后的任务会成为当前任务，常用命令不再需要重复写 path。
starboost [my_task]> review
starboost [my_task]> submit
starboost [my_task]> status
```

也可以使用直接命令。`load_task` 之后，StarBoost 会记住当前任务：

```bash
starboost load_task /path/to/package --executor-model gpt-5.5
starboost review
starboost submit
starboost status
```

校验内置示例任务：

```bash
starboost validate examples/simple_memo_task
```

StarBoost 默认使用 Docker 隔离执行 AI 产出流程。镜像和认证配置见 [Docker 与认证](docs/zh/docker_and_auth.md)。

## 任务包结构

一个 StarBoost 任务包通常包含：

```text
my_task_package/
  original_task/
    task.json
    prompt.md
    rubrics.json
    materials/
      ...
```

StarBoost 会在 `original_task/` 同级生成运行文件：

```text
my_task_package/
  starboost.json
  boost_runs/
  exports/
```

executor 不会看到 `rubrics.json` 或 `human_reference.json`；它只会收到 prompt 和被复制进干净 workspace 的可见材料。

## 文档

| 主题 | 英文 | 中文 |
| --- | --- | --- |
| Overview | [Overview](docs/overview.md) | [概览](docs/zh/overview.md) |
| Quickstart | [Quickstart](docs/quickstart.md) | [快速开始](docs/zh/quickstart.md) |
| Package Format | [Package Format](docs/package_format.md) | [任务包格式](docs/zh/package_format.md) |
| CLI Workflow | [CLI Workflow](docs/cli_workflow.md) | [命令行流程](docs/zh/cli_workflow.md) |
| Review Guidelines | [Review Guidelines](docs/review_guidelines.md) | [审阅指南](docs/zh/review_guidelines.md) |
| Docker And Auth | [Docker And Auth](docs/docker_and_auth.md) | [Docker 与认证](docs/zh/docker_and_auth.md) |
