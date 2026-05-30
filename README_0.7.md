# ResearchAgent

ResearchAgent 是一个面向科研文献阅读场景的 RAG 智能体项目。项目目标是按阶段实现 PDF 文献解析、文本切分、向量检索、基于原文的问答、引用溯源、混合检索、Rerank、vLLM 本地模型接入、Agent 工具调用、检索评测、配置化、日志化和 Web UI 演示。

本仓库当前已完成 V0.7：在 V0.6 Configuration + Logging 的基础上，新增项目架构说明、Demo 演示指南和 Minimal Gradio Web UI。系统不仅可以通过 CLI 运行，也可以通过网页指定 PDF 路径、构建临时索引并进行问答。

## 当前阶段

当前阶段：V0.7 Documentation + Minimal Web UI。

本阶段已完成：

- 保留 V0.1.1 的 PDF RAG 和 vLLM 调用能力；
- 保留 V0.2 的 BM25 + Dense Hybrid Retrieval；
- 保留 V0.3 的 Rerank 和 Citation Check；
- 保留 V0.4 的 Retrieval Evaluation；
- 保留 V0.5 的工具层和规则级 Agent；
- 保留 V0.6 的 YAML 配置和 logging；
- 新增 `docs/architecture.md`，说明系统架构和模块职责；
- 新增 `docs/demo_guide.md`，说明项目如何演示和运行；
- 新增 `scripts/web_demo.py`，提供 Minimal Gradio Web UI；
- Web UI 支持指定 config、指定 index_dir、输入 query；
- Web UI 支持指定本机 PDF 路径并覆盖构建 `data/index/webui_demo`；
- Web UI 分区显示 Answer、Sources、Chunks、Metrics。

## 当前推荐入口

CLI 主入口：

```text
scripts/run_agent.py
```

Web UI 入口：

```text
scripts/web_demo.py
```

调试入口：

```text
scripts/run_rag.py
scripts/evaluate_retrieval.py
```

## 当前架构

```text
configs/*.yaml
↓
scripts/run_agent.py / scripts/web_demo.py
↓
ResearchAgent
↓
intent routing
↓
retrieval_tool / rag_tool / evaluation_tool
↓
BM25 / Dense / Hybrid / Rerank / LLM / Evaluation
↓
Answer + Sources / Chunks / Metrics
↓
logs/research_agent.log
```

Web UI 中指定 PDF 路径后的建索引链路：

```text
PDF path
↓
load_pdf
↓
chunk_documents
↓
EmbeddingModel
↓
VectorStore + BM25Index
↓
覆盖保存到 data/index/webui_demo
↓
Run Agent 读取 data/index/webui_demo
```

详细说明见：

```text
docs/architecture.md
```

## 文档结构

当前重点文档：

```text
docs/architecture.md
docs/demo_guide.md
docs/experiment_report.md
README_0.0.md
README_0.1.md
README_0.1.1.md
README_0.2.md
README_0.3.md
README_0.4.md
README_0.5.md
README_0.6.md
README_0.7.md
```

说明：

- `docs/architecture.md`：说明模块职责、数据结构流转和系统边界；
- `docs/demo_guide.md`：说明 CLI 和 Web UI 演示方式；
- `docs/experiment_report.md`：记录各阶段实验过程和结果；
- `README_0.x.md`：按版本保留项目快照。

## Demo 快速运行

### 1. CLI Agent Answer

```bash
python -m scripts.run_agent --config configs/default.yaml --query "What method does this paper propose?"
```

### 2. CLI Agent Retrieve

```bash
python -m scripts.run_agent --config configs/default.yaml --query "search relevant chunks about experiments"
```

### 3. CLI Agent Evaluate

```bash
python -m scripts.run_agent --config configs/default.yaml --query "evaluate retrieval quality"
```

预期：

```text
Mean Hit: 1.0000
Mean Recall: 0.6111
Mean MRR: 0.8333
```

### 4. 本地 vLLM Answer

```bash
python -m scripts.run_agent --config configs/local_vllm.yaml --query "What method does this paper propose?"
```

### 5. Web UI

启动：

```bash
python -m scripts.web_demo
```

打开终端输出的本地地址，例如：

```text
http://127.0.0.1:7860
```

Web UI 支持：

- `Config path`：例如 `configs/default.yaml` 或 `configs/local_vllm.yaml`；
- `Index dir override`：当前问答读取的索引目录；
- `PDF path`：本机 PDF 路径，例如 `data/raw/test.pdf`；
- `Build Web UI Index`：覆盖构建 `data/index/webui_demo`；
- `Query`：用户问题；
- `Run Agent`：调用 `ResearchAgent`；
- `Answer / Sources / Chunks / Metrics` 分区输出。

完整演示说明见：

```text
docs/demo_guide.md
```

## 配置文件

### Mock 配置

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

## Web UI 评估边界

Web UI 可以对任意文字版 PDF 做临时索引和问答，但评测指标只有在当前索引和 `eval_file` 对应同一篇 PDF 时才有意义。

例如：

```text
data/index/test_index
data/eval/questions.jsonl
```

这两者是配套的，因此可以运行可靠的 Retrieval Evaluation。

如果 Web UI 刚刚用另一个 PDF 覆盖构建了：

```text
data/index/webui_demo
```

但仍然使用旧的：

```text
data/eval/questions.jsonl
```

则 Metrics 结果不可靠。此时应主要查看：

```text
Answer
Sources
Chunks
```

并人工判断检索证据是否支持回答。

## 日志

日志文件：

```text
logs/research_agent.log
```

查看日志：

```bash
Get-Content logs/research_agent.log -Tail 60
```

当前日志会记录：

- Agent started / finished；
- query；
- config；
- detected_intent；
- calling_tool；
- retrieval_config；
- retrieval_finished；
- prompt_built；
- llm；
- answer_generated；
- evaluation_finished。

## 当前实验结论

V0.7 的重点是把项目整理成可展示、可复盘、可讲解的形式，并提供一个最小 Web UI。

当前主要收益：

- 架构文档说明了模块职责和数据流；
- Demo 文档给出了 CLI 和 Web UI 的运行方式；
- Web UI 可以指定 PDF 路径并覆盖构建临时索引；
- Web UI 可以分区展示回答、来源、原始 chunks 和评测指标；
- 主入口、调试入口和演示入口的边界更清晰；
- 项目已经具备基础展示能力。

## 当前限制

- Web UI 只支持本机 PDF 路径，不是真正的浏览器文件上传；
- Web UI 只维护一个临时索引 `data/index/webui_demo`；
- 每次构建 Web UI 索引都会覆盖上一次结果；
- 临时 PDF 没有配套 eval_file 时，Metrics 不可靠；
- 仍不支持多论文管理；
- 仍不支持 OCR；
- 仍不支持图表理解；
- 仍不支持多轮对话记忆；
- 暂未进行 Python packaging；
- 暂不补最终版根目录 `README.md`，因为后续还会继续进入 V0.8/V0.9/V1.0。

## Agent 后续演进

当前 V0.7 的 Agent 仍然是规则级工具调用：

```text
关键词匹配
↓
answer / retrieve / evaluate
↓
调用对应工具
```

后续 Agent 能力按三步升级：

```text
V0.8 LLM Router
→ 让 LLM 判断应该调用 answer / retrieve / evaluate 哪类工具

V0.9 LLM Structured Tool Calling
→ 让 LLM 输出规范 tool call JSON，包括 tool 和 arguments

V1.0 Multi-step Agent
→ 支持 tool call → observation → next tool/final answer 的多步调用
```

设计顺序是：先保证工具链路稳定，再升级工具选择方式，再升级结构化调用格式，最后再做多步 Agent。

## 项目总体路线图

本快照对应 **V0.7 Documentation + Minimal Web UI**。此时系统已经具备最小 RAG 链路、Hybrid Retrieval、Rerank、Citation Check、Retrieval Evaluation、规则级 Agent 调度、YAML 配置、日志系统、架构文档、演示指南和 Web UI。

当前状态：

```text
V0.0 项目初始化 ✅
V0.1 最小 PDF RAG ✅
V0.1.1 vLLM 本地模型接入 ✅
V0.2 BM25 + Dense Hybrid Retrieval ✅
V0.3 Rerank + Citation Check ✅
V0.4 Retrieval Evaluation ✅
V0.5 Agent 工具调用 ✅
V0.6 工程化与配置化 ✅
V0.7 展示与 Web UI 包装 ✅ 当前快照
V0.8 LLM Router ⏳ 下一步
V0.9 LLM Structured Tool Calling ⏳ 计划中
V1.0 Multi-step Agent ⏳ 计划中
```

后续版本目标：

- V0.8：实现 LLM Router，让大模型判断用户意图并选择 `answer / retrieve / evaluate`。
- V0.9：实现 LLM Structured Tool Calling，让大模型输出规范 `tool + arguments` JSON。
- V1.0：实现 Multi-step Agent，支持有限步数的 `tool call → observation → next tool/final answer`。
- 后续增强：多论文管理、批量建索引、浏览器上传 PDF、OCR、VLM 图表理解、更强 reranker、RAGAS、多轮对话记忆等。
