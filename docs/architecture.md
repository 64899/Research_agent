# ResearchAgent 架构说明

本文档记录 ResearchAgent 当前 V0.7 阶段的系统架构。

ResearchAgent 是一个面向科研文献阅读的 RAG 智能体系统。当前系统已经完成 PDF 解析、文本切分、Embedding、Dense 检索、BM25 检索、Hybrid Retrieval、Rerank、vLLM 接入、检索评测、规则级 Agent、配置文件和日志系统。

本文档的目标不是解释每一行代码，而是说明各模块之间如何协作。

## 总体架构

当前系统可以分成四条主要链路：

```text
离线建索引链路
在线问答链路
检索评测链路
Web UI 演示链路
```

### 离线建索引链路

离线建索引链路负责把 PDF 文献转成可检索的索引。

```text
PDF 文件
↓
PDF Loader
↓
Document 列表
↓
Fixed Chunker
↓
Chunk 列表
↓
Embedding Model
↓
VectorStore
↓
BM25Index
↓
保存到 data/index/
```

主要入口：

```text
scripts/build_index.py
```

主要输出：

```text
data/index/<index_name>/
```

### 在线问答链路

在线问答链路负责接收用户问题，检索相关 chunk，构造 prompt，并调用 LLM 生成回答。

```text
用户问题
↓
ResearchAgent
↓
意图识别
↓
RAG Tool
↓
Retriever
↓
Reranker 可选
↓
Prompt Builder
↓
LLM Client
↓
Answer + Sources
```

主要入口：

```text
scripts/run_agent.py
scripts/run_rag.py
```

推荐主入口：

```text
scripts/run_agent.py
```

### 检索评测链路

检索评测链路负责用人工标注的 expected pages 检查检索质量。

```text
Eval Questions
↓
Retriever
↓
Retrieved Results
↓
Hit / Recall / MRR
↓
Evaluation Report
```

主要入口：

```text
scripts/evaluate_retrieval.py
```

主要评测文件：

```text
data/eval/questions.jsonl
data/eval/results_*.json
```

### Web UI 演示链路

Web UI 演示链路负责把已有 Agent 能力包装成可交互页面。

```text
用户输入 PDF path
↓
Build Web UI Index
↓
覆盖构建 data/index/webui_demo
↓
用户输入 Query
↓
Run Agent
↓
ResearchAgent
↓
Answer / Sources / Chunks / Metrics
```

主要入口：

```text
scripts/web_demo.py
```

Web UI 不重新实现 RAG 逻辑，它只调用已有的 loader、chunker、embedding、index 和 Agent 模块。

## 模块职责

### Loader

位置：

```text
src/loaders/pdf_loader.py
```

职责：

- 读取 PDF；
- 按页抽取文本；
- 跳过空文本页；
- 输出统一 Document 结构；
- 对文件不存在、PDF 打不开、无可提取文本等情况给出明确异常。

输出结构：

```python
{
    "text": "...",
    "source": "data/raw/test.pdf",
    "page": 1,
    "metadata": {"type": "pdf"},
}
```

### Chunker

位置：

```text
src/chunkers/fixed_chunker.py
```

职责：

- 将长文本切分成较短 chunk；
- 支持固定长度和 overlap；
- 保留 source、page、metadata；
- 生成稳定的 chunk_id；
- 为后续 Embedding、BM25 和检索提供基本单位。

输出结构：

```python
{
    "chunk_id": "test_p1_c2",
    "text": "...",
    "source": "data/raw/test.pdf",
    "page": 1,
    "metadata": {"type": "pdf"},
}
```

### Embedding

位置：

```text
src/embeddings/embedding_model.py
```

职责：

- 加载 sentence-transformers 模型；
- 将 chunk 文本转换成向量；
- 将 query 文本转换成向量；
- 为 Dense 检索提供输入。

当前默认模型：

```text
sentence-transformers/all-MiniLM-L6-v2
```

### Index

位置：

```text
src/index/vector_store.py
src/index/bm25_index.py
```

职责：

- `VectorStore` 负责 Dense 向量索引；
- `BM25Index` 负责关键词检索索引；
- 二者都支持保存和加载；
- 二者都返回统一的 result 结构，方便上层 retriever、reranker 和 RAG tool 使用。

典型检索结果：

```python
{
    "chunk_id": "test_p1_c2",
    "text": "...",
    "source": "data/raw/test.pdf",
    "page": 1,
    "metadata": {"type": "pdf"},
    "score": 6.0820,
}
```

### Retriever

位置：

```text
src/retrievers/hybrid_retriever.py
```

职责：

- 组合 Dense 检索和 BM25 检索；
- 对两类分数进行归一化；
- 使用 `alpha` 融合分数；
- 返回排序后的候选 chunks。

融合公式：

```text
final_score = alpha * dense_score + (1 - alpha) * bm25_score
```

说明：

- `alpha` 越大，越偏向 Dense 语义检索；
- `alpha` 越小，越偏向 BM25 关键词检索；
- 当前实验中 `alpha=0.3` 对英文论文问题较稳定。

### Reranker

位置：

```text
src/rerank/reranker.py
```

职责：

- 接收 query 和候选 chunks；
- 使用 CrossEncoder 对 `(query, chunk_text)` 成对打分；
- 对候选结果重新排序；
- 返回最终 top-k chunks。

当前默认模型：

```text
cross-encoder/ms-marco-MiniLM-L-6-v2
```

Rerank 的作用不是扩大召回范围，而是改善候选结果的排序。它通常能提升 MRR，但不一定提升 Recall。

### LLM Client

位置：

```text
src/llm/vllm_client.py
```

职责：

- 提供 mock LLM，方便不启动本地模型时调试链路；
- 提供 vLLM client，连接 OpenAI-compatible API；
- 对上层暴露统一的 `generate(...)` 接口。

当前支持：

```text
mock
vllm
```

本地 vLLM 默认配置：

```text
base_url: http://localhost:7890/v1
api_key: abc123
model_name: X
```

### Evaluation

位置：

```text
src/evaluation/retrieval_eval.py
src/evaluation/citation_eval.py
```

职责：

- `retrieval_eval.py` 计算 Hit、Recall、MRR；
- `citation_eval.py` 检查回答中是否包含有效 citation marker；
- 当前 citation check 只做规则检查，不做语义级事实核验。

当前检索评测指标：

```text
Hit@k
Recall@k
MRR
```

### Tools

位置：

```text
src/tools/retrieval_tool.py
src/tools/rag_tool.py
src/tools/evaluation_tool.py
```

职责：

- 将底层模块封装成 Agent 可调用的工具函数；
- 避免 Agent 直接操作 VectorStore、BM25Index、LLM Client 等底层对象；
- 让 answer、retrieve、evaluate 三类能力变成清晰接口。

当前工具：

```text
retrieve_chunks(...)
answer_question(...)
evaluate_retrieval_tool(...)
```

### Agent

位置：

```text
src/agent/research_agent.py
```

职责：

- 接收用户输入；
- 判断用户意图；
- 调用对应工具；
- 返回结构化结果。

当前是规则级 Agent，不是语言级 Agent。

路由规则：

```text
包含 evaluate / evaluation / metric / mrr / recall / hit
→ evaluate

包含 retrieve / search / find chunks / show chunks
→ retrieve

其他输入
→ answer
```

当前设计选择：

- 先使用规则路由，保证稳定和可解释；
- 不引入 LangChain；
- 不让 LLM 负责工具选择；
- 后续按 LLM Router、Structured Tool Calling、Multi-step Agent 逐步增强。

Agent 演进路线：

```text
V0.5 Rule-based Tool Calling
→ 工具函数已经封装完成，ResearchAgent 使用关键词规则选择工具

V0.8 LLM Router
→ LLM 只判断 intent，输出 answer / retrieve / evaluate

V0.9 LLM Structured Tool Calling
→ LLM 输出结构化 tool call JSON，包括 tool 和 arguments

V1.0 Multi-step Agent
→ 支持 tool call → observation → next tool/final answer 的多步调用
```

这条路线的核心原则是先保持工具执行链路稳定，再逐步增强工具选择和多步执行能力。

### Config

位置：

```text
configs/default.yaml
configs/local_vllm.yaml
src/config/config_loader.py
```

职责：

- 集中管理 index、retrieval、rerank、LLM、logging 参数；
- 减少重复命令行参数；
- 支持 mock 和本地 vLLM 两种运行配置；
- 保留命令行覆盖配置文件的能力。

配置结构：

```text
index
retrieval
rerank
llm
agent
logging
```

### Logging

位置：

```text
src/utils/logger.py
logs/research_agent.log
```

职责：

- 创建统一 logger；
- 同时输出到控制台和日志文件；
- 记录 Agent 路由、工具调用、检索配置、检索结果数量、LLM 调用和评测结果；
- 帮助定位问题发生在哪个环节。

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

### Web UI

位置：

```text
scripts/web_demo.py
```

职责：

- 提供 Gradio 页面；
- 支持指定 `Config path`；
- 支持指定 `Index dir override`；
- 支持输入本机 `PDF path` 并构建临时索引；
- 将临时索引覆盖保存到 `data/index/webui_demo`；
- 调用 `ResearchAgent` 进行 answer / retrieve / evaluate；
- 分区展示 Answer、Sources、Chunks、Metrics。

Web UI 建索引流程：

```text
PDF path
↓
load_pdf
↓
chunk_documents
↓
EmbeddingModel
↓
VectorStore.save
↓
BM25Index.save
↓
data/index/webui_demo
```

设计边界：

- 当前 Web UI 只维护一个临时索引；
- 每次构建都会覆盖 `data/index/webui_demo`；
- 它不是多论文管理系统；
- Metrics 只有在当前索引和 eval_file 匹配时才可靠。

## 数据结构流转

### Document

PDF Loader 输出 Document：

```python
{
    "text": "...",
    "source": "data/raw/test.pdf",
    "page": 1,
    "metadata": {"type": "pdf"},
}
```

### Chunk

Chunker 输出 Chunk：

```python
{
    "chunk_id": "test_p1_c2",
    "text": "...",
    "source": "data/raw/test.pdf",
    "page": 1,
    "metadata": {"type": "pdf"},
}
```

### Search Result

Retriever 输出 Search Result：

```python
{
    "chunk_id": "test_p1_c2",
    "text": "...",
    "source": "data/raw/test.pdf",
    "page": 1,
    "metadata": {"type": "pdf"},
    "score": 0.7000,
    "dense_score": 0.0000,
    "bm25_score": 1.0000,
    "rerank_score": 6.0820,
}
```

其中 `dense_score`、`bm25_score`、`rerank_score` 不是所有 retriever 都会返回，取决于当前检索方式。

### RAG Result

RAG Tool 输出结果：

```python
{
    "question": "...",
    "answer": "...",
    "sources": [...],
    "context": "...",
    "prompt": "...",
}
```

### Agent Result

ResearchAgent 输出结果：

```python
{
    "type": "answer",
    "input": "...",
    "result": {...},
}
```

或打印时展示为：

```text
Type: answer
Input: What method does this paper propose?

Answer:
...

Sources:
...
```

## 当前推荐运行入口

### 主入口

推荐使用：

```powershell
python -m scripts.run_agent --config configs/default.yaml --query "What method does this paper propose?"
```

使用本地 vLLM：

```powershell
python -m scripts.run_agent --config configs/local_vllm.yaml --query "What method does this paper propose?"
```

### 调试入口

仅运行 RAG：

```powershell
python -m scripts.run_rag --config configs/default.yaml --query "What method does this paper propose?"
```

仅运行检索评测：

```powershell
python -m scripts.evaluate_retrieval --config configs/default.yaml
```

### Web UI 入口

启动 Web UI：

```powershell
python -m scripts.web_demo
```

Web UI 默认使用：

```text
data/index/webui_demo
```

作为临时索引目录。

## 当前边界

当前系统已经具备一个最小但完整的科研文献 RAG Agent 结构，但仍有明确边界：

- CLI 主要支持已经建好的索引；
- Web UI 支持本机 PDF 路径建临时索引，但不支持真正浏览器文件上传；
- Web UI 只维护一个 `data/index/webui_demo` 临时索引；
- 暂不支持多论文集合管理；
- 暂不支持 OCR；
- 暂不支持图表理解；
- 暂不支持多轮记忆；
- 暂不支持 LLM 自动选择工具；
- 暂未进行 Python packaging。

## 后续方向

V0.7 已完成项目展示和 Minimal Web UI 包装：

```text
docs/demo_guide.md
README_0.7.md
项目架构图
实验结果表格
Minimal Web UI
```

下一阶段 Agent 路线：

```text
V0.8 LLM Router
V0.9 LLM Structured Tool Calling
V1.0 Multi-step Agent
```

更后面的增强方向：

```text
多论文管理
批量建索引
OCR
VLM 图表理解
更强 reranker
RAGAS 或 LLM-as-judge
多轮对话记忆
```
