# ResearchAgent

ResearchAgent 是一个面向科研文献阅读场景的 RAG 智能体项目。项目目标是按阶段实现 PDF 文献解析、文本切分、向量检索、基于原文的问答、引用溯源、混合检索、Rerank、vLLM 本地模型接入、Agent 工具调用和评测体系。

本仓库当前已完成 V0.2 初步版本：在 V0.1.1 最小 RAG 链路基础上，新增 BM25 检索和 BM25 + Dense Hybrid Retrieval，并支持对 Dense-only、BM25-only、Hybrid 三种检索模式进行对比。

## 当前阶段

当前阶段：V0.2 BM25 + Dense Hybrid Retrieval。

本阶段已完成：

- 保留 V0.1.1 的 PDF 解析、chunk 切分、embedding、向量索引、vLLM 回答链路；
- 新增 `src/index/bm25_index.py`，支持 BM25 索引构建、保存、加载和检索；
- 新增 `src/retrievers/hybrid_retriever.py`，支持 Dense 分数和 BM25 分数融合；
- `scripts/build_index.py` 同时保存 Dense index 和 BM25 index；
- `scripts/run_rag.py` 支持 `--retriever dense|bm25|hybrid`；
- Hybrid Retrieval 支持 `--alpha` 参数控制 Dense 和 BM25 权重；
- 实验报告中记录了 Dense-only、BM25-only、Hybrid 的初步对比。

当前主要问题：

- Hybrid 融合分数仍然较粗糙；
- 关键方法定义 chunk 能被 Hybrid 召回，但排序不一定最靠前；
- 需要 V0.3 引入 Rerank，对 Hybrid 候选结果进行更精细排序。

## 当前 RAG 流程

```text
PDF
↓
PDF 文本解析
↓
固定长度 chunk 切分
↓
Dense index + BM25 index
↓
Dense / BM25 / Hybrid Retrieval
↓
构造 context 和 prompt
↓
Mock LLM 或 vLLM 本地模型生成回答
↓
输出引用来源
```

## 已实现模块

- `src/loaders/pdf_loader.py`：使用 PyMuPDF 读取 PDF，并按页输出 `Document`；
- `src/chunkers/fixed_chunker.py`：将 `Document` 切分为固定长度 `Chunk`；
- `src/embeddings/embedding_model.py`：使用 `sentence-transformers` 生成文本向量；
- `src/index/vector_store.py`：保存、加载和检索 Dense 向量索引；
- `src/index/bm25_index.py`：保存、加载和检索 BM25 索引；
- `src/retrievers/hybrid_retriever.py`：融合 Dense 和 BM25 检索结果；
- `src/llm/vllm_client.py`：包含 `MockLLMClient` 和 `VLLMClient`；
- `scripts/build_index.py`：从 PDF 构建 Dense index 和 BM25 index；
- `scripts/run_rag.py`：加载索引，按指定 retriever 检索 chunks，并输出回答和引用来源；
- `docs/experiment_report.md`：记录 V0.1 和 V0.2 实验结果。

## 运行方式

### 1. 安装依赖

```bash
pip install -r requirements.txt
pip install rank-bm25
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
├── vectors.npy
└── bm25_chunks.json
```

### 4. Dense-only 检索

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 2 --retriever dense --llm mock
```

观察：Dense 检索能召回语义相关片段，但可能混入出版信息、页眉页脚等噪声。

### 5. BM25-only 检索

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 2 --retriever bm25 --llm mock
```

观察：BM25 对 `method`、`propose` 等关键词更敏感，能够召回更直接的方法定义片段。

### 6. Hybrid Retrieval

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 3 --retriever hybrid --alpha 0.3 --llm mock
```

`alpha` 含义：

```text
final_score = alpha * dense_score + (1 - alpha) * bm25_score
```

- `alpha` 越大，越偏向 Dense；
- `alpha` 越小，越偏向 BM25。

当前实验中，`alpha=0.3` 能把 BM25 找到的 page 2 方法定义 chunk 召回到前 3。

### 7. Hybrid + vLLM

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 3 --retriever hybrid --alpha 0.3 --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 192
```

当前输出包括：

- 用户问题；
- vLLM 生成回答；
- 引用来源；
- 检索到的 top-k 原文片段；
- Hybrid 模式下的 `score`、`dense_score`、`bm25_score`。

## 当前实验结论

V0.2 初步实验说明：

```text
Dense-only: 召回语义相关片段，但容易混入出版信息噪声
BM25-only: 更容易召回包含 propose/method 等关键词的片段
Hybrid: 能结合两者，减少部分噪声，并召回更直接的方法定义证据
```

详细实验记录见：

```text
docs/experiment_report.md
```

## 下一步

进入 V0.3：Rerank 与引用质量优化。

目标：

- 使用 Hybrid Retrieval 召回更多候选，例如 top-20；
- 使用 Reranker 对候选结果重新排序；
- 选择排序后的 top-k 交给 LLM；
- 提升关键证据 chunk 的排序位置；
- 为后续 Citation 检查和 RAG 评测做准备。

## 后续模块顺序

```text
PDF RAG
↓
BM25 + Dense Hybrid Retrieval
↓
Rerank + Citation
↓
Agent Tool Calling
↓
Evaluation
↓
Engineering
↓
OCR / SFT / RL Extension
```
