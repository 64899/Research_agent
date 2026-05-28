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
