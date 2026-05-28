# ResearchAgent

ResearchAgent 是一个面向科研文献阅读场景的 RAG 智能体项目。项目目标是按阶段实现 PDF 文献解析、文本切分、向量检索、基于原文的问答、引用溯源、混合检索、Rerank、vLLM 本地模型接入、Agent 工具调用和评测体系。

本仓库当前已完成 V0.4 初步版本：在 V0.3 Hybrid Retrieval + Rerank + Citation Check 的基础上，新增 Retrieval Evaluation，用小规模人工标注问题集评估不同检索策略的 Hit、Recall 和 MRR。

## 当前阶段

当前阶段：V0.4 Retrieval Evaluation。

本阶段已完成：

- 保留 V0.1.1 的 PDF 解析、chunk 切分、embedding、向量索引、vLLM 回答链路；
- 保留 V0.2 的 Dense、BM25、Hybrid 三种检索模式；
- 保留 V0.3 的 CrossEncoder Rerank 和规则级 Citation Check；
- 新增 `data/eval/questions.jsonl`，保存页级评测问题；
- 新增 `src/evaluation/retrieval_eval.py`，实现 Hit@k、Recall@k、MRR；
- 新增 `scripts/evaluate_retrieval.py`，支持检索评测、rerank 评测、结果预览和 JSON 保存；
- 生成 `data/eval/results_bm25.json`、`data/eval/results_bm25_rerank.json`、`data/eval/results_hybrid_rerank.json`。

## 当前最佳流程

```text
PDF
↓
PDF 文本解析
↓
固定长度 chunk 切分
↓
Dense index + BM25 index
↓
Retriever / Rerank
↓
top-k chunks
↓
Hit / Recall / MRR
↓
JSON 结果文件
↓
实验报告
```

## 已实现模块

- `src/loaders/pdf_loader.py`：使用 PyMuPDF 读取 PDF，并按页输出 `Document`；
- `src/chunkers/fixed_chunker.py`：将 `Document` 切分为固定长度 `Chunk`；
- `src/embeddings/embedding_model.py`：使用 `sentence-transformers` 生成文本向量；
- `src/index/vector_store.py`：保存、加载和检索 Dense 向量索引；
- `src/index/bm25_index.py`：保存、加载和检索 BM25 索引；
- `src/retrievers/hybrid_retriever.py`：融合 Dense 和 BM25 检索结果；
- `src/rerank/reranker.py`：使用 CrossEncoder 对候选 chunks 进行精排；
- `src/evaluation/citation_eval.py`：规则级检查回答中的 citation marker；
- `src/evaluation/retrieval_eval.py`：读取评测问题并计算 Hit、Recall、MRR；
- `src/llm/vllm_client.py`：包含 `MockLLMClient` 和 `VLLMClient`；
- `scripts/build_index.py`：从 PDF 构建 Dense index 和 BM25 index；
- `scripts/run_rag.py`：运行 RAG 查询；
- `scripts/evaluate_retrieval.py`：评估检索质量。

## 评测数据

当前使用 3 条页级粗标注问题：

```jsonl
{"query": "What method does this paper propose?", "expected_pages": [1, 2]}
{"query": "What problem does this paper solve?", "expected_pages": [1, 2]}
{"query": "What experiments are used in this paper?", "expected_pages": [8, 9, 10, 11, 12, 13]}
```

说明：

- 当前是页级评测，不是严格答案级评测；
- `expected_pages` 用于判断检索结果是否命中有效证据页；
- 后续可以继续扩充问题数量，并细化到 chunk 级标注。

## 运行方式

### 1. 构建索引

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

### 2. 运行 BM25 评测

```bash
python -m scripts.evaluate_retrieval --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --retriever bm25 --top_k 3 --output_file data/eval/results_bm25.json
```

### 3. 运行 BM25 + Rerank 评测

```bash
python -m scripts.evaluate_retrieval --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --retriever bm25 --top_k 3 --rerank --candidate_k 10 --output_file data/eval/results_bm25_rerank.json
```

### 4. 运行 Hybrid + Rerank 评测

```bash
python -m scripts.evaluate_retrieval --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --retriever hybrid --alpha 0.3 --top_k 3 --rerank --candidate_k 10 --output_file data/eval/results_hybrid_rerank.json
```

### 5. 查看检索结果细节

可以添加：

```bash
--show_results
```

该参数会打印每个 query 的 retrieved pages、chunk_id、score、rerank_score 和文本预览，用于人工校准 `expected_pages`。

## 当前实验结果

```text
BM25:
Mean Hit    = 1.0000
Mean Recall = 0.6111
Mean MRR    = 0.8333

BM25 + Rerank:
Mean Hit    = 1.0000
Mean Recall = 0.5556
Mean MRR    = 1.0000

Hybrid + Rerank:
Mean Hit    = 1.0000
Mean Recall = 0.3889
Mean MRR    = 1.0000
```

## 当前实验结论

- BM25 是当前最稳 baseline，Recall 最高；
- BM25 + Rerank 的 MRR 最好，说明第一个有效证据总能排到第一位；
- Hybrid + Rerank 的排序也好，但当前小评测集上 Recall 低于 BM25；
- Rerank 主要改善排序，不保证提升 Recall；
- 当前 3 条 query 更偏英文关键词匹配，因此 BM25 表现强是合理现象。

详细实验记录见：

```text
docs/experiment_report.md
```

## 当前限制

- 当前评测集只有 3 条问题，样本量很小；
- `expected_pages` 是页级粗标注，不是 chunk 级精确标注；
- 当前只在一篇 PDF 上做了评测；
- Reranker 使用英文 MS MARCO 模型，未必最适合所有科研论文；
- Citation Check 仍是规则级质量提示，不做语义级事实核验。

## 下一步

建议进入 Agent 工具调用方向：

```text
Agent Tool Calling
↓
Engineering
↓
Project Packaging
```

优先任务：

- 将现有能力包装成工具函数，例如 `retrieve_chunks`、`answer_question`、`evaluate_retrieval`；
- 明确 Agent 可以调用哪些工具、输入输出是什么；
- 先做一个最小 Agent，不引入复杂框架；
- 保留当前可复现的 RAG 和评测脚本作为底层能力。

## 项目总体路线图

本快照对应 **V0.4 Retrieval Evaluation**。此时系统已经具备最小 RAG 链路、Hybrid Retrieval、Rerank、Citation Check 和基础检索评测能力。

当前状态：

```text
V0.0 项目初始化 ✅
V0.1 最小 PDF RAG ✅
V0.1.1 vLLM 本地模型接入 ✅
V0.2 BM25 + Dense Hybrid Retrieval ✅
V0.3 Rerank + Citation Check ✅
V0.4 Retrieval Evaluation ✅ 当前快照
V0.5 Agent 工具调用 ⏳ 下一步
V0.6 工程化与配置化 ⏳ 计划中
V0.7 展示与项目包装 ⏳ 计划中
V0.8 扩展增强 ⏳ 计划中
```

已完成能力：

- 页级 eval questions；
- Hit@k、Recall@k、MRR；
- Dense、BM25、Hybrid 检索评测；
- Rerank 后检索评测；
- `--show_results` 人工检查检索结果；
- `--output_file` 保存 JSON 评测结果；
- V0.4 实验记录。

后续版本目标：

- V0.5：实现 Agent 工具调用。
- V0.6：加入 YAML 配置、logging、参数管理和更稳定的工程结构。
- V0.7：增加 Gradio/Streamlit 展示、架构图、实验表格和面试讲解文档。
- V0.8：探索 OCR、VLM 图表理解、多论文对比、RAGAS、SFT、GRPO 等增强方向。
