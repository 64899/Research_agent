# ResearchAgent

ResearchAgent 是一个面向科研文献阅读场景的 RAG 智能体项目。项目目标是按阶段实现 PDF 文献解析、文本切分、向量检索、基于原文的问答、引用溯源、混合检索、Rerank、vLLM 本地模型接入、Agent 工具调用和评测体系。

本仓库当前已完成 V0.5 初步版本：在 V0.4 Retrieval Evaluation 的基础上，新增工具层和规则级 Agent 调度层。系统已经可以通过统一入口调用检索、问答和检索评测能力。

## 当前阶段

当前阶段：V0.5 Agent Tool Calling。

本阶段已完成：

- 保留 V0.1.1 的 PDF RAG 和 vLLM 调用能力；
- 保留 V0.2 的 BM25 + Dense Hybrid Retrieval；
- 保留 V0.3 的 Rerank 和 Citation Check；
- 保留 V0.4 的 Retrieval Evaluation；
- 新增 `src/tools/retrieval_tool.py`，封装 chunk 检索；
- 新增 `src/tools/rag_tool.py`，封装 RAG 问答；
- 新增 `src/tools/evaluation_tool.py`，封装检索评测；
- 新增 `src/agent/research_agent.py`，实现规则级 Agent 调度；
- 新增 `scripts/run_agent.py`，作为 Agent 命令行入口。

## 当前 Agent 架构

```text
scripts/run_agent.py
↓
ResearchAgent
↓
detect_intent()
↓
retrieval_tool / rag_tool / evaluation_tool
↓
已有 RAG、检索、评测模块
```

## 工具层

### Retrieval Tool

```text
src/tools/retrieval_tool.py
```

核心接口：

```python
retrieve_chunks(...)
```

作用：只检索 chunks，不生成回答。

### RAG Tool

```text
src/tools/rag_tool.py
```

核心接口：

```python
answer_question(...)
```

作用：完成一次检索、context 构造、prompt 构造和 LLM 生成。

返回字段包括：

```text
question
answer
sources
context
prompt
```

### Evaluation Tool

```text
src/tools/evaluation_tool.py
```

核心接口：

```python
evaluate_retrieval_tool(...)
```

作用：复用 V0.4 的检索评测逻辑，返回整体指标和逐问题结果。

## Agent 路由规则

当前 Agent 是规则级 Agent，不是语言级 Agent。

```text
包含 evaluate / evaluation / metric / mrr / recall / hit
→ evaluate

包含 retrieve / search / find chunks / show chunks
→ retrieve

其他输入
→ answer
```

这种方式简单、稳定、可解释，适合当前学习阶段。后续如果要升级为语言级 Agent，可以在扩展阶段实现 LLM Router。

## 运行方式

### 1. Retrieval Tool

```bash
python -m src.tools.retrieval_tool --index_dir data/index/test_index --query "What method does this paper propose?" --retriever bm25 --top_k 2
```

### 2. RAG Tool

```bash
python -m src.tools.rag_tool --index_dir data/index/test_index --query "What method does this paper propose?" --retriever bm25 --top_k 2 --llm mock
```

### 3. Evaluation Tool

```bash
python -m src.tools.evaluation_tool --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --retriever bm25 --top_k 3
```

预期结果：

```text
Mean Hit: 1.0000
Mean Recall: 0.6111
Mean MRR: 0.8333
```

### 4. Agent Answer

```bash
python -m scripts.run_agent --index_dir data/index/test_index --query "What method does this paper propose?" --retriever bm25 --top_k 2 --llm mock
```

预期路由：

```text
Type: answer
```

### 5. Agent Retrieve

```bash
python -m scripts.run_agent --index_dir data/index/test_index --query "search relevant chunks about experiments" --retriever bm25 --top_k 2
```

预期路由：

```text
Type: retrieve
```

### 6. Agent Evaluate

```bash
python -m scripts.run_agent --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --query "evaluate retrieval quality" --retriever bm25 --top_k 3
```

预期路由：

```text
Type: evaluate
```

## 当前实验结论

V0.5 已经把系统从脚本式调用推进到工具层和 Agent 调度层：

```text
脚本
→ 工具函数
→ 规则级 Agent
→ 统一命令行入口
```

当前主要收益：

- RAG 问答、chunk 检索和检索评测都可以作为工具函数复用；
- Agent 可以根据用户输入调度不同工具；
- 路由规则稳定、透明、便于调试；
- `scripts/run_agent.py` 统一了 Agent 调用入口；
- 为后续工程化和配置化打下基础。

## 当前限制

- Agent 依赖关键词规则，不理解复杂自然语言意图；
- 不支持多步规划；
- 不支持多轮记忆；
- 不支持语言级 tool calling；
- 暂未引入 LangChain 等 Agent 框架；
- 工具之间仍存在部分重复加载逻辑，后续工程化时需要整理。

## 下一步

建议进入工程化与配置化方向：

```text
Configuration
↓
Logging
↓
Cleaner module boundaries
↓
Project packaging
```

优先任务：

- 新增 YAML 配置文件，统一管理 index、retriever、rerank、LLM 参数；
- 给 `run_rag.py`、`evaluate_retrieval.py`、`run_agent.py` 引入配置读取；
- 增加 logging，记录检索、rerank、LLM 和 Agent 调用过程；
- 抽取公共加载逻辑，减少 `scripts/` 和 `src/tools/` 之间的重复。

## 项目总体路线图

本快照对应 **V0.5 Agent Tool Calling**。此时系统已经具备最小 RAG 链路、Hybrid Retrieval、Rerank、Citation Check、Retrieval Evaluation 和规则级 Agent 调度能力。

当前状态：

```text
V0.0 项目初始化 ✅
V0.1 最小 PDF RAG ✅
V0.1.1 vLLM 本地模型接入 ✅
V0.2 BM25 + Dense Hybrid Retrieval ✅
V0.3 Rerank + Citation Check ✅
V0.4 Retrieval Evaluation ✅
V0.5 Agent 工具调用 ✅ 当前快照
V0.6 工程化与配置化 ⏳ 下一步
V0.7 展示与项目包装 ⏳ 计划中
V0.8 扩展增强 ⏳ 计划中
```

已完成能力：

- `retrieve_chunks` 工具；
- `answer_question` 工具；
- `evaluate_retrieval_tool` 工具；
- `ResearchAgent` 规则路由；
- `scripts/run_agent.py`；
- answer / retrieve / evaluate 三类路由；
- V0.5 验收测试。

后续版本目标：

- V0.6：加入 YAML 配置、logging、参数管理和更稳定的工程结构。
- V0.7：增加 Gradio/Streamlit 展示、架构图、实验表格和面试讲解文档。
- V0.8：探索 OCR、VLM 图表理解、多论文对比、RAGAS、SFT、GRPO 等增强方向。
