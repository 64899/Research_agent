# 实验报告

## V0.1 最小 PDF RAG

### 实验环境

- 日期：2026-05-28
- LLM 后端：vLLM
- LLM 模型：Qwen2.5-3B-Instruct
- vLLM 暴露的模型名：`X`
- API 地址：`http://localhost:7890/v1`
- Embedding 模型：`sentence-transformers/all-MiniLM-L6-v2`
- 测试 PDF：`data/raw/test.pdf`
- 索引目录：`data/index/test_index`
- 检索方式：Dense 向量检索
- `top_k`：2
- `temperature`：0.1
- `max_tokens`：128

### 当前流程

```text
PDF
↓
PDF 文本解析
↓
固定长度 chunk 切分
↓
Embedding 向量化
↓
向量索引构建与加载
↓
Dense 向量检索
↓
Prompt 构造
↓
vLLM 生成回答
↓
输出引用来源
```

### 模型连通性测试

测试命令：

```powershell
python -c "from src.llm.vllm_client import VLLMClient; c = VLLMClient('http://localhost:7890/v1', 'abc123', 'X'); print(c.generate('Answer in one sentence: what is retrieval augmented generation?', temperature=0.1, max_tokens=128))"
```

模型输出：

```text
Retrieval-Augmented Generation refers to the process of using pre-existing knowledge or information from external sources (retrieval) as a basis for generating new content or text.
```

观察：

- `VLLMClient` 可以正常连接本地 vLLM OpenAI-compatible API。
- Qwen2.5-3B-Instruct 能正常遵循简单英文指令并生成回答。
- 之前使用更小模型时出现的复读问题，更可能是模型能力或模型格式问题，不是 RAG 管道本身的问题。

### Query 1：论文提出了什么方法

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 2 --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 128
```

问题：

```text
What method does this paper propose?
```

模型回答：

```text
The paper proposes Deep Variational Class Balancing Attention Model (D-VCBAM). This can be inferred from the following sentence in the given context:

"However, D- VCBAM holds an absolute advantage in the number of misjudged ID samples, which can further reduce unnecessary manual intervention."
```

检索到的引用来源：

```text
[1] data/raw/test.pdf, page 12, chunk_id=test_p12_c75
[2] data/raw/test.pdf, page 1, chunk_id=test_p1_c7
```

观察：

- 模型能根据检索片段生成通顺回答，并识别出 `D-VCBAM`。
- 来源 [1] 与方法实验表现相关，但不是最直接的方法定义段落。
- 来源 [2] 是 page 1 的出版信息和版权信息，属于明显噪声。
- 当前 Dense 检索可以召回部分相关内容，但证据定位还不够精确。

### Query 2：论文解决什么问题

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What problem does this paper solve?" --top_k 2 --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 128
```

问题：

```text
What problem does this paper solve?
```

模型回答：

```text
The paper does not explicitly state what specific problem it solves. The text provides information about a case study involving eight different bearing health states, but does not mention any particular problem or challenge that the authors aim to address. Therefore, based solely on the given context, I cannot determine the main problem solved by the paper.
```

检索到的引用来源：

```text
[1] data/raw/test.pdf, page 12, chunk_id=test_p12_c77
[2] data/raw/test.pdf, page 6, chunk_id=test_p6_c40
```

观察：

- 模型能够遵守 prompt，在证据不足时说明无法确定，而不是强行编造。
- 来源 [1] 主要是实验设置中的 bearing health states，不是论文问题定义。
- 来源 [2] 是方法优化目标推导内容，也不是问题定义。
- 该 query 暴露出 Dense 检索对“论文解决什么问题”这类高层问题召回不稳定。

### Query 3：论文使用了哪些数据集或实验

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What datasets or experiments are used in this paper?" --top_k 2 --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 128
```

问题：

```text
What datasets or experiments are used in this paper?
```

模型回答：

```text
Based on the information provided in the context, there is no explicit mention of specific datasets or experiments used in this paper. The reference [1] provides details about a dataset called "T3" with dimensions 5x200 and 6x50, but it does not specify if these were used in any particular experiment or study. Similarly, reference [2] mentions an article titled "Engineering Applications of Artificial Intelligence" published in 2025, which discusses the use of OOD (Out-of-Distribution) samples but does not indicate what datasets or experiments were employed. Therefore, the document does not provide enough
```

检索到的引用来源：

```text
[1] data/raw/test.pdf, page 9, chunk_id=test_p9_c66
[2] data/raw/test.pdf, page 1, chunk_id=test_p1_c7
```

观察：

- 来源 [1] 和实验/数据设置有一定关系，但 chunk 起点不完整，导致上下文不够清晰。
- 来源 [2] 仍然是 page 1 的出版信息噪声。
- 模型回答末尾被 `max_tokens=128` 截断，说明真实生成时需要根据任务调整 `max_tokens`。
- 当前系统对表格型实验信息的抽取效果有限，后续需要更好的 chunk 策略、Hybrid Retrieval 或 Rerank。

### 当前问题

- Dense 向量检索有时会召回页眉、页脚、出版信息等噪声内容。
- 对于比较泛的问题，例如 `What is this paper about?`，系统不一定能稳定召回 abstract 或 introduction。
- 当前 chunk 清洗逻辑还比较简单，没有专门去除重复页眉页脚。
- 当前系统还没有 BM25、Hybrid Retrieval、Rerank 或检索评测指标。
- 表格型信息容易被切成不完整 chunk，影响模型理解。
- `max_tokens=128` 对部分回答偏短，可能导致回答被截断。

### 阶段结论

V0.1 已经跑通最小 RAG 链路：

```text
PDF → chunks → embeddings → vector index → retrieval → prompt → vLLM answer → sources
```

当前主要瓶颈是检索质量，而不是 LLM 连通性。

### 下一步

进入 V0.2：

```text
BM25 + Dense Hybrid Retrieval
```

预期改进：

- 减少页眉、页脚和出版信息等噪声召回。
- 提升对关键词敏感问题的检索效果。
- 对比 Dense-only、BM25-only 和 Hybrid Retrieval 的检索结果。
- 为后续 Rerank 和 Citation 质量检查做准备。

## V0.2 初步实验：Dense / BM25 / Hybrid 对比

### 实验设置

- Query: `What method does this paper propose?`
- LLM backend: vLLM
- LLM model: Qwen2.5-3B-Instruct
- Served model name: `X`
- Dense embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- BM25 tokenizer: simple English/number regex tokenizer
- Hybrid alpha: 0.3
- `top_k`: 3
- `temperature`: 0.1
- `max_tokens`: 192

### Dense-only 结果

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 2 --retriever dense --llm mock
```

检索结果摘要：

```text
[1] data/raw/test.pdf, page 12, chunk_id=test_p12_c75
[2] data/raw/test.pdf, page 1, chunk_id=test_p1_c7
```

观察：

- Dense 检索召回了 page 12 的方法评估相关片段。
- 第二条结果是 page 1 的出版信息和版权信息，属于噪声。
- Dense-only 对该 query 的证据定位不够精确。

### BM25-only 结果

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 2 --retriever bm25 --llm mock
```

检索结果摘要：

```text
[1] data/raw/test.pdf, page 12, chunk_id=test_p12_c73
[2] data/raw/test.pdf, page 2, chunk_id=test_p2_c10
```

观察：

- BM25 召回了 page 2 的方法定义片段，其中包含 `we propose an alternative approach...`。
- BM25 对 `method`、`propose` 等关键词更敏感。
- 相比 Dense-only，BM25 更容易找到和方法描述直接相关的证据。

### Hybrid Retrieval 结果

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 3 --retriever hybrid --alpha 0.3 --llm mock
```

检索结果摘要：

```text
[1] score=0.7000 dense=0.0000 bm25=1.0000, page 12, chunk_id=test_p12_c73
[2] score=0.4691 dense=0.0000 bm25=0.6702, page 2, chunk_id=test_p2_c10
[3] score=0.3000 dense=1.0000 bm25=0.0000, page 12, chunk_id=test_p12_c75
```

观察：

- `alpha=0.3` 时，Hybrid 更偏向 BM25，因此 page 2 的方法定义 chunk 被召回到前 3。
- Hybrid 去掉了 Dense-only 中 page 1 的出版信息噪声。
- 当前融合方式仍然会把 BM25 第一名 page 12 排在 page 2 前面，排序仍不够理想。

### Hybrid + vLLM 生成结果

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --top_k 3 --retriever hybrid --alpha 0.3 --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 192
```

模型回答：

```text
This paper proposes an alternative approach to constructing variational attention called "uncertainty-aware deep variational attention network" (DVAN). The DVAN uses the posterior distribution of the network parameters of the attention module to generate random attention weights, eliminating the need for custom-designed structures and making variational attention more easily applicable across different architectures.
```

引用来源：

```text
[1] data/raw/test.pdf, page 12, chunk_id=test_p12_c73
[2] data/raw/test.pdf, page 2, chunk_id=test_p2_c10
[3] data/raw/test.pdf, page 12, chunk_id=test_p12_c75
```

观察：

- Hybrid 召回了 page 2 的方法定义片段后，模型回答明显更具体。
- 回答中提到了 `variational attention`、`posterior distribution of the network parameters`、`random attention weights` 和 `architecture-agnostic` 等关键信息。
- 相比 Dense-only，Hybrid 提供了更有用的上下文。
- 但引用排序仍不够理想：最关键的方法定义来源是 [2]，而不是 [1]。

### V0.2 当前结论

BM25 + Dense Hybrid Retrieval 已经初步改善检索质量：

```text
Dense-only: 召回语义相关片段，但容易混入出版信息噪声
BM25-only: 更容易召回包含 propose/method 等关键词的片段
Hybrid: 能结合两者，减少部分噪声，并召回更直接的方法定义证据
```

当前主要问题：

- Hybrid 融合分数仍然较粗糙；
- page 12 的方法评估片段仍排在 page 2 的方法定义片段之前；
- 需要后续 Rerank 对候选结果进行更精细排序。

下一步建议：

```text
V0.3: Hybrid top-N → Rerank → top-k → LLM answer
```

## V0.3 初步实验：Hybrid + Rerank

### 实验设置

- Query: `What method does this paper propose?`
- Retriever: Hybrid Retrieval
- Hybrid alpha: 0.3
- Candidate count before rerank: 10
- Final `top_k`: 3
- Reranker model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- LLM backend: vLLM
- LLM model: Qwen2.5-3B-Instruct
- `temperature`: 0.1
- `max_tokens`: 192

### Rerank 检索结果

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --retriever hybrid --alpha 0.3 --candidate_k 10 --top_k 3 --rerank --llm mock
```

Rerank 后的检索结果摘要：

```text
[1] page 1, chunk_id=test_p1_c2, rerank_score=6.0820
[2] page 12, chunk_id=test_p12_c73, rerank_score=1.4177
[3] page 12, chunk_id=test_p12_c75, rerank_score=0.3065
```

第一名 chunk 内容包含：

```text
this paper proposes:
(1) an architecture-agnostic variational attention;
(2) a Monte Carlo shaping layer;
(3) a model uncertainty estimation scheme.
```

观察：

- Rerank 将最能直接回答问题的 page 1 方法定义 chunk 排到第一。
- 未 rerank 时，Hybrid 排名前两位主要是 page 12 的实验表现片段和 page 2 的方法相关片段。
- Rerank 后，候选排序更符合 query 的真实意图。

### Hybrid + Rerank + vLLM 生成结果

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --retriever hybrid --alpha 0.3 --candidate_k 10 --top_k 3 --rerank --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 192
```

模型回答：

```text
This paper proposes an uncertainty-aware deep variational attention network for Out-of-Distribution (OOD) detection-assisted trustworthy mechanical fault diagnosis. Specifically, it includes three main components:

1. An architecture-agnostic variational attention applicable to various popular deterministic attention.
2. A Monte Carlo shaping layer ensuring attention weights' diversity for reliable uncertainty quantification.
3. A model uncertainty estimation scheme detecting distribution shifts.

These components work together to form the proposed method, which aims to improve the OOD detection performance of models while maintaining their ability to make accurate predictions for in-distribution samples.
```

引用来源：

```text
[1] data/raw/test.pdf, page 1, chunk_id=test_p1_c2
[2] data/raw/test.pdf, page 12, chunk_id=test_p12_c73
[3] data/raw/test.pdf, page 12, chunk_id=test_p12_c75
```

观察：

- 模型回答直接总结出了论文提出方法的三个组成部分。
- 回答主要依据 [1]，即方法定义 chunk，而不是仅依赖 page 12 的实验表现片段。
- 相比 Dense-only 和 Hybrid-only，Hybrid + Rerank 的证据排序和最终回答质量明显更好。

### Citation Check 规则级检查

运行命令：

```powershell
python -m scripts.run_rag --index_dir data/index/test_index --query "What method does this paper propose?" --retriever hybrid --alpha 0.3 --candidate_k 10 --top_k 3 --rerank --llm vllm --base_url http://localhost:7890/v1 --api_key abc123 --model_name X --temperature 0.1 --max_tokens 192 --check_citations
```

模型回答：

```text
This paper proposes an uncertainty-aware deep variational attention network for OOD detection-assisted trustworthy mechanical fault diagnosis.
```

引用来源：

```text
[1] data/raw/test.pdf, page 1, chunk_id=test_p1_c2
[2] data/raw/test.pdf, page 12, chunk_id=test_p12_c73
[3] data/raw/test.pdf, page 12, chunk_id=test_p12_c75
```

Citation Check 输出：

```text
has_citations: False
used_citations: []
invalid_citations: []
source_count: 3
is_valid: False
warnings:
- answer does not contain citation markers like [1]
```

观察：

- `citation_eval.py` 可以正确检测回答中是否包含 `[1]`、`[2]` 这类 citation marker。
- 当前 Qwen2.5-3B-Instruct 能生成内容质量较好的回答，但没有稳定遵守“每句话带 citation marker”的格式要求。
- Prompt 已经确认输入模型，因此问题不在 RAG 调用链，而在模型对引用格式的遵循不稳定。
- 当前阶段不强制回答正文必须带 `[1]`、`[2]`，但必须在回答后展示 `Sources`，让用户能够回到原文检查证据。
- Citation Check 在 V0.3 中更适合作为质量提示：它能指出“正文没有引用标记”，但这不等于该回答完全不可用。
- 不采用自动补 `[1]` 的 fallback，因为这会制造“模型实际没有生成引用但系统伪造引用”的假可信感。
- 下一阶段优先评估检索质量。

### V0.3 当前结论

Rerank 初步解决了 Hybrid Retrieval 中“召回到了相关 chunk，但排序不够理想”的问题。Citation Check 已经可以发现模型回答中是否缺少有效引用标记，但当前阶段不把正文 citation marker 作为强制要求。

当前最佳链路为：

```text
Hybrid Retrieval top-10 → CrossEncoder Rerank → top-3 → vLLM answer + Sources → Citation Check
```

当前主要收益：

- 将方法定义 chunk 排到第一；
- 提升 LLM 输入 context 的证据质量；
- 让最终回答更完整、更贴近原文；
- 能检测模型是否输出有效 citation marker，并将其作为质量提示；
- 明确当前最低引用要求：回答后必须展示 `Sources`；
- 为后续检索评测打基础。

后续改进方向：

- 尝试更适合中英文论文检索的 reranker；
- 比较不同 `candidate_k` 和 `top_k` 对回答质量的影响；
- 构建小规模 eval set，计算 Recall@k、Hit Rate 和 MRR；
- 对比 Dense-only、BM25-only、Hybrid、Hybrid + Rerank 的检索质量；
- 后续进入 Agent 工具调用和工程化完善。

## V0.4 初步实验：Retrieval Evaluation

### 实验目标

V0.4 的目标是从“凭观察判断检索效果”转向“用小规模评测集量化比较检索器”。本阶段不改变 RAG 生成链路，也不要求模型回答正文必须带 citation marker，而是优先评估检索结果是否命中预期证据页。

### 新增文件

```text
data/eval/questions.jsonl
data/eval/results_bm25.json
data/eval/results_bm25_rerank.json
data/eval/results_hybrid_rerank.json
src/evaluation/retrieval_eval.py
scripts/evaluate_retrieval.py
```

### 评测集

当前使用 3 条页级粗标注问题：

```jsonl
{"query": "What method does this paper propose?", "expected_pages": [1, 2]}
{"query": "What problem does this paper solve?", "expected_pages": [1, 2]}
{"query": "What experiments are used in this paper?", "expected_pages": [8, 9, 10, 11, 12, 13]}
```

说明：

- `expected_pages` 是人工标注的证据页范围，不是严格答案级标注。
- 当前评测是页级检索评测，用来比较不同 retriever 的趋势。
- 后续可以继续细化到 chunk 级标注或答案级评测。

### 指标定义

本阶段实现了三个基础指标：

```text
Hit@k: top-k 中只要命中任意 expected page，就记为 1。
Recall@k: expected pages 中有多少比例被 top-k 覆盖。
MRR: 第一个命中结果的 reciprocal rank。
```

### 运行命令

BM25：

```powershell
python -m scripts.evaluate_retrieval --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --retriever bm25 --top_k 3 --output_file data/eval/results_bm25.json
```

BM25 + Rerank：

```powershell
python -m scripts.evaluate_retrieval --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --retriever bm25 --top_k 3 --rerank --candidate_k 10 --output_file data/eval/results_bm25_rerank.json
```

Hybrid + Rerank：

```powershell
python -m scripts.evaluate_retrieval --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --retriever hybrid --alpha 0.3 --top_k 3 --rerank --candidate_k 10 --output_file data/eval/results_hybrid_rerank.json
```

如果需要人工检查检索结果，可以加：

```powershell
--show_results
```

### Overall 结果

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

### 观察

- BM25 在当前 3 条英文问题上覆盖率最高，`Mean Recall` 达到 0.6111。
- BM25 + Rerank 的 `Mean MRR` 达到 1.0000，说明每个问题的第一个有效证据都排到了第一位。
- Hybrid + Rerank 的 `Mean MRR` 同样达到 1.0000，但 `Mean Recall` 低于 BM25，说明排序靠前但覆盖面较窄。
- Rerank 更擅长改善排序位置，不一定提升 Recall；在 top-k 较小的情况下，它还可能把部分相关页挤出 top-k。
- 当前问题主要是英文关键词型问题，因此 BM25 表现强是合理现象。

### V0.4 当前结论

当前最稳 baseline 是 BM25。若目标是覆盖更多证据页，优先使用 BM25；若目标是让第一个输入给 LLM 的证据更可能有效，BM25 + Rerank 更合适。

V0.4 已经建立了一个最小检索评测闭环：

```text
eval questions → retriever search → Hit / Recall / MRR → JSON result files → experiment report
```

后续改进方向：

- 扩充 `questions.jsonl`，增加更多论文阅读问题；
- 校准 `expected_pages`，减少粗标注带来的误差；
- 对比不同 `top_k`、`candidate_k` 和 `alpha`；
- 后续进入 Agent 工具调用和工程化完善。

## V0.5 初步实验：Agent Tool Calling

### 实验目标

V0.5 的目标是把前面已经完成的 RAG 能力从“脚本调用”整理成“工具函数 + Agent 调度”。本阶段使用规则级 Agent，不使用 LangChain，也不让 LLM 负责选择工具。

当前 Agent 的职责是：

```text
用户输入
→ 规则判断意图
→ 调用对应工具
→ 返回结构化结果
```

### 新增文件

```text
src/tools/__init__.py
src/tools/retrieval_tool.py
src/tools/rag_tool.py
src/tools/evaluation_tool.py
src/agent/research_agent.py
scripts/run_agent.py
```

### 工具接口

Retrieval Tool：

```text
retrieve_chunks(...)
```

作用：只检索 chunks，不生成回答。

RAG Tool：

```text
answer_question(...)
```

作用：完成一次检索、context 构造、prompt 构造和 LLM 生成，返回 `question`、`answer`、`sources`、`context`、`prompt`。

Evaluation Tool：

```text
evaluate_retrieval_tool(...)
```

作用：复用 V0.4 的检索评测逻辑，返回 `config`、`overall` 和逐问题结果。

ResearchAgent：

```text
ResearchAgent.run(user_input)
```

作用：根据用户输入进行规则路由，然后调用对应工具。

### 路由规则

当前是规则级 Agent，意图判断方式如下：

```text
包含 evaluate / evaluation / metric / mrr / recall / hit
→ evaluate

包含 retrieve / search / find chunks / show chunks
→ retrieve

其他输入
→ answer
```

说明：

- 这是最小可控 Agent，不是语言级 Agent。
- 优点是稳定、可解释、便于调试。
- 后续如果需要更灵活的工具选择，可以在扩展阶段升级为 LLM Router。

### 验收命令

Retrieval Tool：

```powershell
python -m src.tools.retrieval_tool --index_dir data/index/test_index --query "What method does this paper propose?" --retriever bm25 --top_k 2
```

RAG Tool：

```powershell
python -m src.tools.rag_tool --index_dir data/index/test_index --query "What method does this paper propose?" --retriever bm25 --top_k 2 --llm mock
```

Evaluation Tool：

```powershell
python -m src.tools.evaluation_tool --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --retriever bm25 --top_k 3
```

Agent Answer：

```powershell
python -m scripts.run_agent --index_dir data/index/test_index --query "What method does this paper propose?" --retriever bm25 --top_k 2 --llm mock
```

Agent Evaluate：

```powershell
python -m scripts.run_agent --index_dir data/index/test_index --eval_file data/eval/questions.jsonl --query "evaluate retrieval quality" --retriever bm25 --top_k 3
```

### 验收结果

5 条最小验收命令均能正常运行：

```text
retrieval_tool → OK
rag_tool mock → OK
evaluation_tool → OK
run_agent answer → OK
run_agent evaluate → OK
```

其中 `run_agent evaluate` 的 BM25 指标与 V0.4 结果一致：

```text
Mean Hit    = 1.0000
Mean Recall = 0.6111
Mean MRR    = 0.8333
```

### V0.5 当前结论

V0.5 已经完成最小 Agent Tool Calling：

```text
scripts/run_agent.py
→ ResearchAgent
→ retrieval_tool / rag_tool / evaluation_tool
→ existing RAG and evaluation modules
```

当前 Agent 不依赖 LLM 做工具选择，而是使用关键词规则路由。这符合当前阶段目标：先把系统从脚本式调用推进到工具层和 Agent 调度层。

当前主要收益：

- RAG、检索和评测能力已经变成可复用工具函数；
- `ResearchAgent` 可以统一调度 answer、retrieve、evaluate 三类任务；
- 命令行入口统一为 `scripts/run_agent.py`；
- 工具调用链路稳定、可解释，适合作为后续工程化基础。

当前限制：

- 路由依赖关键词，不理解复杂意图；
- 没有多步规划；
- 没有多轮记忆；
- 没有语言级 tool calling；
- 暂不引入 LangChain 等框架。

后续改进方向：

- 进入 V0.6 工程化与配置化；
- 增加 YAML 配置，减少命令行参数重复；
- 增加 logging，记录检索、rerank、LLM 和 Agent 调用过程；
- 进一步整理公共加载逻辑，减少脚本和工具之间的重复。
