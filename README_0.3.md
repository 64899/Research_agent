# ResearchAgent

ResearchAgent 是一个面向科研文献阅读场景的 RAG 智能体项目。项目目标是按阶段实现 PDF 文献解析、文本切分、向量检索、基于原文的问答、引用溯源、混合检索、Rerank、vLLM 本地模型接入、Agent 工具调用和评测体系。

本仓库当前已完成 V0.3 版本：在 V0.2 BM25 + Dense Hybrid Retrieval 基础上，新增 CrossEncoder Rerank 和规则级 Citation Check。系统能够先宽召回候选 chunks，再对候选进行精排，交给 vLLM 生成回答，并检查回答中是否包含有效 citation marker。

## 当前阶段

当前阶段：V0.3 Hybrid Retrieval + Rerank + Citation Check。

本阶段已完成：

- 保留 V0.1.1 的 PDF 解析、chunk 切分、embedding、向量索引、vLLM 回答链路；
- 保留 V0.2 的 Dense、BM25、Hybrid 三种检索模式；
- 新增 `src/rerank/reranker.py`，使用 CrossEncoder 对候选 chunks 重新排序；
- 新增 `src/evaluation/citation_eval.py`，检查回答中的 `[1]`、`[2]` 引用编号是否合法；
- `scripts/run_rag.py` 支持 `--rerank`、`--candidate_k`、`--reranker_model` 和 `--check_citations`；
- 当前最佳链路为 `Hybrid Retrieval top-10 → CrossEncoder Rerank → top-3 → vLLM answer → Citation Check`；
- 实验报告中记录了 V0.3 的 Hybrid + Rerank 效果和 Citation Check 结果。

当前主要收益：

- Rerank 将方法定义 chunk 排到第一；
- LLM 输入 context 的证据质量明显提升；
- 最终回答能更完整地总结论文提出的方法组成；
- Citation Check 能发现当前本地模型没有稳定输出 citation marker 的问题；
- 当前系统已经具备一个可演示的科研论文 RAG 问答链路。

## 当前最佳 RAG 流程

```text
PDF
↓
PDF 文本解析
↓
固定长度 chunk 切分
↓
Dense index + BM25 index
↓
Hybrid Retrieval top-N
↓
CrossEncoder Rerank
↓
top-k chunks
↓
构造 context 和 prompt
↓
vLLM 本地模型生成回答
↓
输出引用来源
↓
Citation Check
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
- `src/llm/vllm_client.py`：包含 `MockLLMClient` 和 `VLLMClient`；
- `scripts/build_index.py`：从 PDF 构建 Dense index 和 BM25 index；
- `scripts/run_rag.py`：加载索引，按指定 retriever 检索 chunks，可选 rerank，并输出回答、引用来源和 Citation Check；
- `docs/experiment_report.md`：记录 V0.1、V0.2 和 V0.3 实验结果。

## 运行方式

### 1. 安装依赖

```bash
pip install -r requirements.txt
pip install rank-bm25
```

Rerank 依赖 `sentence-transformers` 中的 `CrossEncoder`，当前使用：

```text
cross-encoder/ms-marco-MiniLM-L-6-v2
```

### 2. 构建索引

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

### 3. Hybrid + Rerank + Mock LLM 验收

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --retriever hybrid --alpha 0.3 --candidate_k 10 --top_k 3 --rerank --llm mock
```

当前期望结果：

```text
[1] page 1, chunk_id=test_p1_c2
[2] page 12, chunk_id=test_p12_c73
[3] page 12, chunk_id=test_p12_c75
```

其中 `test_p1_c2` 是方法定义 chunk，包含论文提出的三个组成部分。

### 4. Hybrid + Rerank + vLLM 验收

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --retriever hybrid --alpha 0.3 --candidate_k 10 --top_k 3 --rerank --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 192
```

当前模型回答能总结出：

```text
1. architecture-agnostic variational attention
2. Monte Carlo shaping layer
3. model uncertainty estimation scheme
```

说明 Rerank 后提供给 LLM 的上下文质量明显提升。

### 5. Citation Check 验收

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --retriever hybrid --alpha 0.3 --candidate_k 10 --top_k 3 --rerank --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 192 --check_citations
```

当前观察结果：

```text
has_citations: False
used_citations: []
invalid_citations: []
source_count: 3
is_valid: False
warnings:
- answer does not contain citation markers like [1]
```

这不是 Citation Check 的错误，而是说明当前本地模型虽然能生成较好的回答，但没有稳定遵守 citation marker 格式。V0.3 的目标是“能检查”，不是强制模型一定生成合规引用。

## 当前实验结论

V0.3 初步实验说明：

```text
Dense-only: 能召回语义相关片段，但容易混入噪声
BM25-only: 更容易召回关键词匹配片段
Hybrid: 能结合 Dense 和 BM25，改善候选召回
Hybrid + Rerank: 能把最能回答问题的证据 chunk 排到第一
Citation Check: 能检测回答中是否缺少有效引用编号
```

详细实验记录见：

```text
docs/experiment_report.md
```

## 当前限制

- Reranker 使用的是英文 MS MARCO 模型，未必最适合所有中英文科研论文；
- 当前只在一篇 PDF 上做了初步验证；
- Citation Check 当前是规则级检查，只能判断是否包含有效编号，不能判断语义是否真正被 sources 支持；
- 当前 Qwen2.5-3B-Instruct 没有稳定输出 `[1]`、`[2]` 这类 citation marker；
- 尚未实现 Recall@k、Hit Rate、MRR 等检索评测指标；
- chunk 策略仍然简单，对表格和页眉页脚的处理还不够好。

## 下一步

建议进入结构化回答与评测方向：

```text
Structured JSON Answer
↓
Retrieval Evaluation
↓
更系统的实验报告
```

优先任务：

- 让模型输出 JSON，例如 `{"answer": "...", "citations": [1]}`；
- 对 JSON 解析失败、citation 无效等情况增加重试策略；
- 构建小规模 eval questions；
- 计算 Recall@k、Hit Rate、MRR；
- 对比 Dense-only、BM25-only、Hybrid、Hybrid + Rerank 的检索效果。

## 后续模块顺序

```text
PDF RAG
↓
BM25 + Dense Hybrid Retrieval
↓
Rerank + Citation
↓
Evaluation
↓
Agent Tool Calling
↓
Engineering
↓
OCR / SFT / RL Extension
```

## 项目总体路线图

本快照对应 **V0.3 Hybrid Retrieval + Rerank + Citation Check**。此时系统已经能通过 Hybrid 进行宽召回，再用 CrossEncoder 对候选 chunks 精排，并用规则级检查发现模型回答是否缺少 citation marker。

当前状态：

```text
V0.0 项目初始化 ✅
V0.1 最小 PDF RAG ✅
V0.1.1 vLLM 本地模型接入 ✅
V0.2 BM25 + Dense Hybrid Retrieval ✅
V0.3 Rerank + Citation Check ✅ 当前快照
V0.4 Structured Answer / Evaluation ⏳ 下一步
V0.5 Agent 工具调用 ⏳ 计划中
V0.6 工程化与配置化 ⏳ 计划中
V0.7 展示与项目包装 ⏳ 计划中
V0.8 扩展增强 ⏳ 计划中
```

已完成能力：

- Hybrid Retrieval top-N 候选召回；
- CrossEncoder Rerank；
- `--rerank`、`--candidate_k`、`--reranker_model`；
- Hybrid + Rerank + vLLM 真实回答；
- Rerank 成功将方法定义 chunk 排到第一；
- `--check_citations`；
- 规则级 Citation Check；
- V0.3 实验记录。

后续版本目标：

- V0.4：结构化 JSON 回答、citation 失败重试、检索评测体系，计算 Recall@k、Hit Rate、MRR。
- V0.5：实现 Agent 工具调用。
- V0.6：加入 YAML 配置、logging、参数管理和更稳定的工程结构。
- V0.7：增加 Gradio/Streamlit 展示、架构图、实验表格和面试讲解文档。
- V0.8：探索 OCR、VLM 图表理解、多论文对比、RAGAS、工具调用 SFT、GRPO 等增强方向。

当前建议：先做结构化回答和基础评测，再进入 Agent。
