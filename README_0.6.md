# ResearchAgent

ResearchAgent 是一个面向科研文献阅读场景的 RAG 智能体项目。项目目标是按阶段实现 PDF 文献解析、文本切分、向量检索、基于原文的问答、引用溯源、混合检索、Rerank、vLLM 本地模型接入、Agent 工具调用、检索评测、配置化和日志化。

本仓库当前已完成 V0.6 初步版本：在 V0.5 Agent Tool Calling 的基础上，新增 YAML 配置文件和 logging 支持。系统已经可以通过配置文件统一管理检索、rerank、LLM、评测和日志参数，并记录 Agent 的运行链路。

## 当前阶段

当前阶段：V0.6 Configuration + Logging。

本阶段已完成：

- 保留 V0.1.1 的 PDF RAG 和 vLLM 调用能力；
- 保留 V0.2 的 BM25 + Dense Hybrid Retrieval；
- 保留 V0.3 的 Rerank 和 Citation Check；
- 保留 V0.4 的 Retrieval Evaluation；
- 保留 V0.5 的工具层和规则级 Agent；
- 新增 `configs/default.yaml`，作为 mock LLM 默认配置；
- 新增 `configs/local_vllm.yaml`，作为本地 vLLM 配置；
- 新增 `src/config/config_loader.py`，读取 YAML 配置；
- 新增 `src/utils/logger.py`，统一创建 logger；
- `scripts/run_agent.py` 支持 `--config`；
- `scripts/run_rag.py` 支持 `--config`；
- `scripts/evaluate_retrieval.py` 支持 `--config`；
- Agent、RAG Tool、Retrieval Tool、Evaluation Tool 接入日志。

## 当前架构

```text
configs/*.yaml
↓
scripts/run_agent.py
↓
ResearchAgent
↓
retrieval_tool / rag_tool / evaluation_tool
↓
BM25 / Dense / Hybrid / Rerank / LLM / Evaluation
↓
logs/research_agent.log
```

## 配置文件

### 默认配置

```text
configs/default.yaml
```

默认使用：

```text
retriever: bm25
top_k: 3
rerank: false
llm: mock
log_file: logs/research_agent.log
```

适合不启动本地模型时调试 Agent、检索和评测链路。

### 本地 vLLM 配置

```text
configs/local_vllm.yaml
```

默认使用：

```text
llm: vllm
base_url: http://localhost:7890/v1
api_key: abc123
model_name: X
```

适合本地 vLLM 服务已经启动时做真实问答实验。

## 运行方式

### 1. Agent Answer

使用 mock LLM：

```bash
python -m scripts.run_agent --config configs/default.yaml --query "What method does this paper propose?"
```

使用本地 vLLM：

```bash
python -m scripts.run_agent --config configs/local_vllm.yaml --query "What method does this paper propose?"
```

### 2. Agent Retrieve

```bash
python -m scripts.run_agent --config configs/default.yaml --query "search relevant chunks about experiments"
```

预期路由：

```text
Type: retrieve
```

### 3. Agent Evaluate

```bash
python -m scripts.run_agent --config configs/default.yaml --query "evaluate retrieval quality"
```

预期结果：

```text
Mean Hit: 1.0000
Mean Recall: 0.6111
Mean MRR: 0.8333
```

### 4. RAG Script

```bash
python -m scripts.run_rag --config configs/default.yaml --query "What method does this paper propose?"
```

临时覆盖配置：

```bash
python -m scripts.run_rag --config configs/default.yaml --query "What method does this paper propose?" --top_k 2
```

### 5. Retrieval Evaluation Script

```bash
python -m scripts.evaluate_retrieval --config configs/default.yaml
```

## 日志

日志文件位置：

```text
logs/research_agent.log
```

当前记录内容包括：

- Agent 启动和结束；
- 用户输入；
- 当前配置；
- 检测到的 intent；
- 调用的 tool；
- retrieval 配置；
- retrieval 结果数量；
- prompt 构造完成；
- LLM backend；
- answer 生成完成；
- evaluation 指标。

示例日志：

```text
Agent started
query=What method does this paper propose?
detected_intent=answer
calling_tool=answer_question
rag_tool_started
retrieval_tool_started
retrieval_finished results=3
prompt_built
llm=mock
answer_generated
intent=answer
Agent finished
```

## 当前实验结论

V0.6 已经把项目从“脚本能跑”推进到“配置可复现、过程可观察”：

```text
命令行参数
→ YAML 配置
→ Agent / Tool 调用
→ 日志记录
```

当前主要收益：

- 常用参数集中管理，减少重复命令；
- mock 和本地 vLLM 可以通过配置文件切换；
- Agent 的 answer、retrieve、evaluate 三类路径都有日志；
- 检索评测可以直接复用默认配置；
- 后续调试检索、rerank、LLM 回答质量时有日志依据。

## 当前限制

- 配置读取逻辑在多个脚本中仍有重复；
- logger 当前主要记录 INFO 级流程事件；
- 异常路径的日志还不完整；
- 还没有统一的应用入口类；
- 还没有 Web UI；
- 还没有 Python packaging。

## 项目总体路线图

本快照对应 **V0.6 Configuration + Logging**。此时系统已经具备最小 RAG 链路、Hybrid Retrieval、Rerank、Citation Check、Retrieval Evaluation、规则级 Agent 调度、YAML 配置和日志能力。

当前状态：

```text
V0.0 项目初始化 ✅
V0.1 最小 PDF RAG ✅
V0.1.1 vLLM 本地模型接入 ✅
V0.2 BM25 + Dense Hybrid Retrieval ✅
V0.3 Rerank + Citation Check ✅
V0.4 Retrieval Evaluation ✅
V0.5 Agent 工具调用 ✅
V0.6 工程化与配置化 ✅ 当前快照
V0.7 展示与项目包装 ⏳ 下一步
V0.8 扩展增强 ⏳ 计划中
```

已完成能力：

- YAML 配置文件；
- `default.yaml` mock 配置；
- `local_vllm.yaml` 本地 vLLM 配置；
- `run_agent.py --config`；
- `run_rag.py --config`；
- `evaluate_retrieval.py --config`；
- `logs/research_agent.log`；
- answer / retrieve / evaluate 三类路径日志。

后续版本目标：

- V0.7：增加 Gradio/Streamlit 展示、架构图、实验表格和项目讲解文档。
- V0.8：探索 OCR、VLM 图表理解、多论文对比、RAGAS、SFT、GRPO 等增强方向。
