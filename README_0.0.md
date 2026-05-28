# ResearchAgent

ResearchAgent 是一个面向科研文献阅读场景的 RAG 智能体项目。项目目标是按阶段实现 PDF 文献解析、文本切分、向量检索、基于原文的问答、引用溯源、混合检索、Rerank、vLLM 本地模型接入、Agent 工具调用和评测体系。

本仓库当前只完成项目骨架初始化，不包含任何功能模块实现。

## 当前阶段

当前阶段：V0.0 项目初始化。

本阶段目标：

- 创建项目目录结构；
- 添加 Python 包目录的 `__init__.py`；
- 准备最小 `requirements.txt`；
- 记录项目目标和后续模块顺序；
- 不实现 PDF 解析、Embedding、索引、LLM 调用或 Agent 逻辑。

## 近期目标

下一阶段进入 V0.1 最小 PDF RAG 系统，按模块逐步实现：

1. `src/loaders/pdf_loader.py`：PDF 文本解析；
2. `src/chunkers/fixed_chunker.py`：固定长度文本切分；
3. `src/embeddings/embedding_model.py`：Embedding 模型封装；
4. `src/index/vector_store.py`：向量索引构建、保存、加载和检索；
5. `src/llm/vllm_client.py`：OpenAI-compatible LLM 客户端；
6. `scripts/build_index.py`：构建 PDF 索引；
7. `scripts/run_rag.py`：运行基础 RAG 问答。

## 后续模块顺序

项目按以下顺序推进：

```text
PDF RAG
↓
Hybrid Retrieval
↓
Rerank + Citation
↓
vLLM
↓
Agent Tool Calling
↓
Evaluation
↓
Engineering
↓
OCR / SFT / RL Extension
```

## 目录说明

```text
research-rag-agent/
├── README.md
├── requirements.txt
├── configs/
├── data/
│   ├── raw/
│   ├── processed/
│   └── index/
├── src/
│   ├── loaders/
│   ├── chunkers/
│   ├── embeddings/
│   ├── index/
│   ├── retrievers/
│   ├── rerank/
│   ├── llm/
│   ├── agent/
│   └── evaluation/
├── scripts/
└── docs/
```

## V0.1 目标接口预告

V0.1 的第一个正式接口将是：

```python
def load_pdf(pdf_path: str) -> list[dict]:
    ...
```

返回的每个 `dict` 将包含：

- `text`: 当前页文本；
- `source`: PDF 文件路径；
- `page`: 从 1 开始的页码；
- `metadata`: 至少包含 `type="pdf"`。

## 项目总体路线图

本快照对应 **V0.0 项目初始化**。此时项目只完成目录结构和基础文件，还没有实现任何 RAG 功能。

当前状态：

```text
V0.0 项目初始化 ✅
V0.1 最小 PDF RAG ⏳ 下一步
V0.2 BM25 + Dense Hybrid Retrieval ⏳ 计划中
V0.3 Rerank + Citation ⏳ 计划中
V0.4 Evaluation 评测体系 ⏳ 计划中
V0.5 Agent 工具调用 ⏳ 计划中
V0.6 工程化与配置化 ⏳ 计划中
V0.7 展示与项目包装 ⏳ 计划中
V0.8 扩展增强 ⏳ 计划中
```

后续版本目标：

- V0.1：跑通 `PDF → chunks → embeddings → vector search → LLM answer`。
- V0.2：加入 BM25，并实现 BM25 + Dense Hybrid Retrieval。
- V0.3：加入 Rerank，并开始做 Citation 可信度检查。
- V0.4：构建检索评测体系，计算 Recall@k、Hit Rate、MRR。
- V0.5：实现 Agent 工具调用，包括 retriever、summarizer、citation_checker 等工具。
- V0.6：加入 YAML 配置、logging、参数管理和更稳定的工程结构。
- V0.7：增加 Gradio/Streamlit 展示、架构图、实验表格和面试讲解文档。
- V0.8：探索 OCR、VLM 图表理解、多论文对比、RAGAS、工具调用 SFT、GRPO 等增强方向。

当前建议：不要一次性生成完整项目，下一步只实现 `pdf_loader.py`。
