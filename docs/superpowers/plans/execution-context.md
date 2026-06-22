# 执行约定 — 给每个子 agent 看的偏差表

本文件记录**实际执行时与原计划的偏差**。每个执行任务的 subagent 都必须读这份文件,并优先遵守这些约定(原计划被覆盖的部分以本文件为准)。

---

## 1. Python 环境:用 `sd_lora`,不新建 `durian`

预检发现本机已有 conda 环境 `sd_lora`,内含:
- PyTorch 2.12.0.dev (cu128) — RTX 5070 完美支持
- diffusers / peft / transformers / accelerate(版本不查,直接用)

**所有计划中提到 `conda activate durian` 或 `conda run -n durian` 的地方,改为 `conda activate sd_lora` / `conda run -n sd_lora`。**

**Task 4(原 setup_train_env.ps1)简化为**:
- 不创建新环境
- 在 `sd_lora` 中补装缺失的库:`fastapi uvicorn[standard] aiofiles pydantic loguru pyyaml pytest pytest-asyncio imagehash icrawler optimum[openvino] openvino`
- 写一个 `scripts/setup_train_env.ps1` 脚本是"补包脚本",不创建环境

## 2. Docker 本地不验证

设计要求生成 `Dockerfile` 与 `docker-compose.yml`,**仍要生成**(给服务器用)。
**Task 32**(本地构建 Docker 镜像验证)**完全跳过**,但 Task 23/24(写 Dockerfile 与 docker-compose.yml)正常进行。

## 3. 训练跳过,用现有 LoRA

`D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/durian-aigc-code/models/lora/musang_king/` 已有训完的 LoRA(26 个 checkpoint)。

**Task 13(M3 实际训练)替换为**:
1. 把 `durian-aigc-code/models/lora/musang_king/checkpoint-final/` 复制到 `D:/durian-data/models/lora/musang_king/`(注意:从 checkpoint-final 目录的内容复制到目标目录,不要嵌套一层 checkpoint-final/)
2. 在 `docs/training-log.md` 记一句"复用旧版训练产物 (checkpoint-final),未重训"

**Task 12 仍要完成**(`lora_trainer.py` 适配新配置,只是不真的跑训练)。

## 4. 数据爬虫不实际执行(M2 Task 6 smoke 跳过)

外网受限,用户手动准备数据。
**Task 6 仍要写完整代码 + 单元测试**,但 "Step 5: Smoke 测试 — 实际爬一个品种" 这一步**跳过**,Step 6 提交时正常 commit。
**Task 9 BLIP smoke 测试(Step 5)同样跳过**,代码 + 单测照做。
**Task 10 一键脚本仍要写**,smoke 不跑。

## 5. 旧代码归档位置确认

预检发现:
- `durian-aigc-code/` — **较新的代码副本,保留并搬到 backend/**
- `durian-aigc/` — 较旧,**搬到 archive/durian-aigc-old/**
- `durian-aigc-code/models/lora/musang_king/` — **不要丢**,要用 checkpoint-final

按 Task 2 步骤搬:
- `durian-aigc-code/__pycache__/` 直接删
- `durian-aigc-code/models/` **先复制 checkpoint-final 到 D:/durian-data/**,然后再连带 durian-aigc-code 一起删
- 旧 `durian-aigc/` → `archive/durian-aigc-old/`

## 6. 路径含中文的兜底

`D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/` 路径含中文,某些工具(尤其前端 `npm install` 偶尔)会出问题。
- 所有数据/模型已外置到 `D:/durian-data/`(英文路径) ✅
- 如某个 npm/pip 命令报中文路径错误,在执行时把命令改成绝对路径形式重试
- 不要尝试整体迁移项目目录(用户在那里)

## 7. PowerShell 语法注意

本环境是 Windows PowerShell 5.1(不是 PowerShell Core / pwsh 7),**没有** `&&` 和 `||`:
- 用 `;` 串接命令
- 条件依赖用 `if ($LASTEXITCODE -eq 0) { ... }`

Bash 工具调用走的是 Git Bash,POSIX 语法 OK;但**所有面向用户最终运行的脚本**(`scripts/*.ps1`)仍写 PowerShell 5.1 兼容语法。

## 8. Git 提交时一律含本文件指出的偏差注释

每个 Task 的 git commit message 末尾若涉及偏差,加一行 `(scope adjusted per execution-context.md)`。

## 9. 报错策略

只在以下情况下停下来报告主 agent:
- 命令报错且无法在 Task 内自行解决
- 测试无法通过且改了 3 次仍失败
- 用户需要确认的安全/不可逆操作

其他情况(包括缺包、路径、commit 失败可重试)自行解决,不打扰。

---

**END OF EXECUTION CONTEXT.**
