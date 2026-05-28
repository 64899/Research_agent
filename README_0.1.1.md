# ResearchAgent

ResearchAgent 是一个面向科研文献阅读场景的 RAG 智能体项目。项目目标是按阶段实现 PDF 文献解析、文本切分、向量检索、基于原文的问答、引用溯源、混合检索、Rerank、vLLM 本地模型接入、Agent 工具调用和评测体系。

本仓库当前已完成 V0.1.1 最小 RAG 链路：支持 PDF 解析、chunk 切分、embedding、向量检索、索引保存/加载、Mock LLM 占位回答，以及通过 vLLM OpenAI-compatible API 调用本地 Qwen2.5-3B-Instruct 生成回答。

## 当前阶段

当前阶段：V0.1.1 最小 PDF RAG 系统，vLLM 本地模型接入版本。

本阶段已完成：

- 使用 PyMuPDF 解析文本型 PDF；
- 将 PDF 页面切分为固定长度 chunks；
- 使用 `sentence-transformers/all-MiniLM-L6-v2` 生成 chunk embedding；
- 构建、保存和加载向量索引；
- 根据 query 检索 top-k chunks；
- 支持 `MockLLMClient` 进行链路占位测试；
- 支持 `VLLMClient` 调用本地 vLLM OpenAI-compatible API；
- 使用 Qwen2.5-3B-Instruct 生成基于检索上下文的回答；
- 输出引用来源，包括 source、page 和 chunk_id；
- 在 `docs/experiment_report.md` 中记录 V0.1 实验结果。

当前主要问题：Dense 向量检索会召回页眉、页脚、出版信息或不够精确的片段，下一步需要进入 V0.2 的 BM25 + Dense Hybrid Retrieval。

## 当前 RAG 流程

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
- `src/index/vector_store.py`：保存、加载和检索向量索引；
- `src/llm/vllm_client.py`：包含 `MockLLMClient` 和 `VLLMClient`；
- `scripts/build_index.py`：从 PDF 构建向量索引；
- `scripts/run_rag.py`：加载索引，检索相关 chunks，并输出回答和引用来源；
- `docs/experiment_report.md`：记录 V0.1 实验结果和当前问题。

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

### 4. 运行 Mock RAG

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 2 --llm mock
```

Mock LLM 只用于验证：

```text
retrieval → context → prompt → llm.generate() → answer
```

不代表真实论文回答质量。

### 5. 启动 vLLM 服务

示例启动命令：

```bash
vllm serve /mnt/c/Users/LLL/Desktop/minimind \
  --host 0.0.0.0 \
  --api-key abc123 \
  --served-model-name X \
  --max-model-len 1024 \
  --port 7890 \
  --gpu-memory-utilization 0.7
```

当前实验中已将模型替换为 Qwen2.5-3B-Instruct，并通过相同的 OpenAI-compatible API 调用。

Windows 侧测试服务：

```powershell
Invoke-RestMethod `
  -Uri http://localhost:7890/v1/models `
  -Headers @{ Authorization = "Bearer abc123" }
```

### 6. 运行 vLLM RAG

```bash
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 2 --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 128
```

当前输出包括：

- 用户问题；
- vLLM 生成回答；
- 引用来源；
- 检索到的 top-k 原文片段。

## 单模块验证

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

VLLM client：

```bash
python -c "from src.llm.vllm_client import VLLMClient; c = VLLMClient('http://localhost:7890/v1', 'abc123', 'X'); print(c.generate('Answer in one sentence: what is retrieval augmented generation?', temperature=0.1, max_tokens=128))"
```

## 当前实验结论

V0.1.1 已经跑通：

```text
PDF → chunks → embeddings → vector index → retrieval → prompt → vLLM answer → sources
```

实验观察：

- Qwen2.5-3B-Instruct 能正常生成回答，不再出现小模型的长时间复读问题；
- 当前 Dense 检索可以召回部分相关内容；
- 检索结果仍会混入页眉、页脚、出版信息和不完整表格片段；
- 当前主要瓶颈是 retrieval quality，而不是 LLM connectivity。

详细实验记录见：

```text
docs/experiment_report.md
```

## 下一步

进入 V0.2：BM25 + Dense Hybrid Retrieval。

目标：

- 实现 BM25 索引；
- 支持 BM25-only 检索；
- 保留当前 Dense 向量检索；
- 实现 Hybrid Retrieval；
- 对比 Dense-only、BM25-only 和 Hybrid Retrieval 的结果；
- 为后续 Rerank 和 Citation 质量检查做准备。

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

## 项目总体路线图

本快照对应 **V0.1.1 vLLM 本地模型接入版本**。此时最小 RAG 链路已经从 mock answer 升级为本地 vLLM 真实生成。

当前状态：

```text
V0.0 项目初始化 ✅
V0.1 最小 PDF RAG ✅
V0.1.1 vLLM 本地模型接入 ✅ 当前快照
V0.2 BM25 + Dense Hybrid Retrieval ⏳ 下一步
V0.3 Rerank + Citation ⏳ 计划中
V0.4 Evaluation 评测体系 ⏳ 计划中
V0.5 Agent 工具调用 ⏳ 计划中
V0.6 工程化与配置化 ⏳ 计划中
V0.7 展示与项目包装 ⏳ 计划中
V0.8 扩展增强 ⏳ 计划中
```

已完成能力：

- 最小 PDF RAG 主链路；
- `MockLLMClient` 和 `VLLMClient`；
- 本地 vLLM OpenAI-compatible API 调用；
- Qwen2.5-3B-Instruct 生成回答；
- V0.1 实验记录。

后续版本目标：

- V0.2：加入 BM25，并实现 BM25 + Dense Hybrid Retrieval，解决 Dense-only 检索噪声问题。
- V0.3：加入 Rerank，让最能回答 query 的证据 chunk 排到前面。
- V0.4：构建检索评测体系，计算 Recall@k、Hit Rate、MRR。
- V0.5：实现 Agent 工具调用。
- V0.6-V0.8：配置化、展示包装和 OCR/VLM/SFT/RL 等增强方向。

当前建议：先提升 retrieval quality，再继续做 Agent。
