# ResearchAgent

ResearchAgent 是一个面向科研文献阅读场景的 RAG 智能体项目。项目目标是按阶段实现 PDF 文献解析、文本切分、向量检索、基于原文的问答、引用溯源、混合检索、Rerank、vLLM 本地模型接入、Agent 工具调用和评测体系。

本仓库当前已完成 V0.1 最小 RAG 链路的 mock 版本：支持 PDF 解析、chunk 切分、embedding、向量检索、索引保存/加载，以及 mock LLM 占位回答。

## 当前阶段

当前阶段：V0.1 最小 PDF RAG 系统，Mock LLM 版本。

本阶段目标：

- 使用 PyMuPDF 解析文本型 PDF；
- 将 PDF 页面切分为固定长度 chunks；
- 使用 `sentence-transformers` 生成 chunk embedding；
- 构建、保存和加载向量索引；
- 根据 query 检索 top-k chunks；
- 使用 `MockLLMClient` 输出占位回答；
- 输出引用来源，包括 source、page 和 chunk_id。

注意：当前 LLM 仍是 mock，占位回答不代表真实论文问答结果。

## 近期目标

下一阶段继续完善 V0.1，将 mock LLM 替换为 OpenAI-compatible LLM 客户端，并逐步接入本地 vLLM 服务。当前模块顺序为：

1. `src/loaders/pdf_loader.py`：PDF 文本解析；
2. `src/chunkers/fixed_chunker.py`：固定长度文本切分；
3. `src/embeddings/embedding_model.py`：Embedding 模型封装；
4. `src/index/vector_store.py`：向量索引构建、保存、加载和检索；
5. `src/llm/vllm_client.py`：OpenAI-compatible LLM 客户端；
6. `scripts/build_index.py`：构建 PDF 索引；
7. `scripts/run_rag.py`：运行基础 RAG 问答。

## V0.1 当前进展

当前已经完成最小 PDF RAG 链路的前半部分：

```text
PDF
↓
PDF 文本解析
↓
固定长度 chunk 切分
↓
Embedding 向量化
↓
向量索引构建与保存
↓
加载索引并检索 top-k chunks
↓
Mock LLM 输出占位回答
↓
输出引用来源
```

已实现模块：

- `src/loaders/pdf_loader.py`：使用 PyMuPDF 读取 PDF，并按页输出 `Document`；
- `src/chunkers/fixed_chunker.py`：将 `Document` 切分为固定长度 `Chunk`；
- `src/embeddings/embedding_model.py`：使用 `sentence-transformers` 生成文本向量；
- `src/index/vector_store.py`：保存、加载和检索向量索引；
- `src/llm/vllm_client.py`：当前包含 `MockLLMClient`，用于占位测试；
- `scripts/build_index.py`：从 PDF 构建索引；
- `scripts/run_rag.py`：加载索引，检索相关 chunks，并输出 mock 回答和引用来源。

## 运行方式

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备 PDF

将文本型 PDF 放入：

```text
data/raw/
```

例如：

```text
data/raw/test.pdf
```

当前版本不支持扫描版 PDF OCR。

### 3. 构建索引

```bash
python -m scripts.build_index --input data/raw/test.pdf --index_dir data/index/test_index
```

成功后会生成：

```text
data/index/test_index/
├── chunks.json
└── vectors.npy
```

### 4. 运行 Mock RAG 检索问答

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 3
```

当前输出包括：

- 用户问题；
- mock answer；
- 引用来源；
- 检索到的 top-k 原文片段。

### 5. 单模块验证

PDF loader：

```bash
python src/loaders/pdf_loader.py data/raw/test.pdf
```

Fixed chunker：

```bash
python src/chunkers/fixed_chunker.py
```

Embedding model：

```bash
python src/embeddings/embedding_model.py
```

Vector store：

```bash
python -m src.index.vector_store
```

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
