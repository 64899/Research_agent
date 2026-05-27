# ResearchAgent 项目计划书：面向科研文献阅读的 RAG 智能体系统

> 使用说明：本文件用于输入给 Codex/AI 编程助手，指导其按阶段、按模块辅助搭建项目。  
> 开发原则：不要一次性生成完整项目；每次只实现一个小模块，运行通过后再进入下一步。  
> 项目目标：通过 AI 辅助开发，在搭建过程中学习 RAG、Agent 工具调用、vLLM 本地部署和评测体系。

---

## 0. 项目总览

### 0.1 项目名称

**ResearchAgent：面向科研文献阅读的 RAG 智能体系统**

也可命名为：

**基于本地大模型的科研文献检索、问答与综述生成智能体**

---

### 0.2 项目定位

本项目面向研究生科研文献阅读场景，构建一个结合 **RAG、混合检索、Rerank、工具调用、Agent Loop、vLLM 本地推理和评测体系** 的文献智能问答系统。

系统支持用户上传论文 PDF 或 Markdown 文档，自动完成：

1. 文档解析；
2. 文本切分；
3. Embedding 向量化；
4. 向量索引构建；
5. BM25 + Dense 混合检索；
6. Rerank 精排；
7. 引用溯源；
8. 基于本地大模型生成回答；
9. Agent 工具调用；
10. RAG 检索效果与回答效果评测。

---

### 0.3 项目核心价值

当前已有基础：

- 已学习 MiniMind：预训练、SFT、DPO；
- 已学习 LlamaFactory：微调框架使用；
- 已学习 vLLM：模型部署与推理服务。

该项目用于补齐：

- RAG：让模型使用外部知识；
- Tool Calling：让模型调用外部工具；
- Agent Loop：让模型从单轮回答升级为多步任务执行；
- vLLM：将本地模型真正接入应用系统；
- Evaluation：用指标验证系统效果，而不是只做 demo。

---

## 1. 项目总体目标

### 1.1 最低目标

完成一个可运行的科研文献 RAG 系统：

```text
PDF 文献
↓
文本解析
↓
chunk 切分
↓
embedding 向量化
↓
向量检索
↓
LLM 基于原文回答
↓
输出引用页码
```

最低可验收功能：

- 支持上传或指定一篇 PDF；
- 能解析 PDF 文本；
- 能切分 chunk；
- 能建立向量索引；
- 能基于用户问题检索相关片段；
- 能调用 LLM 生成回答；
- 能输出引用来源，例如文件名、页码、chunk_id。

---

### 1.2 标准目标

完成一个进阶 RAG 系统：

```text
PDF / Markdown
↓
文档解析
↓
chunk 切分
↓
BM25 索引 + 向量索引
↓
Hybrid Retrieval
↓
Rerank
↓
Prompt 构造
↓
vLLM 本地模型生成回答
↓
引用溯源
```

标准可验收功能：

- 支持 PDF / Markdown；
- 支持 BM25 检索；
- 支持 Dense 向量检索；
- 支持 BM25 + Dense 混合检索；
- 支持 Rerank 精排；
- 支持 vLLM 本地模型接口；
- 支持引用溯源；
- 有基础检索评测脚本。

---

### 1.3 优秀目标

完成 RAG Agent 系统：

```text
用户问题
↓
Agent 判断任务
↓
选择工具
├── pdf_reader
├── retriever
├── summarizer
├── table_generator
├── citation_checker
└── calculator
↓
执行工具
↓
返回 observation
↓
LLM 继续推理
↓
最终回答
```

优秀可验收功能：

- 有最小 Agent Loop；
- LLM 能输出 tool_call JSON；
- 程序能解析 tool_call；
- 能执行工具；
- 能把工具结果 observation 回填给 LLM；
- 支持多步工具调用；
- 支持复杂任务，如“总结创新点”“对比三篇论文方法”“生成论文汇报提纲”；
- 有工具调用日志；
- 有评测报告；
- 有 README、架构图和实验记录。

---

## 2. 不做什么

为了避免项目失控，第一阶段不做以下内容：

- 不做完整工业级知识库平台；
- 不做多用户权限系统；
- 不做复杂数据库后端；
- 不做复杂前端；
- 不一开始做 LangGraph；
- 不一开始做 MCP；
- 不一开始做 OCR/VLM；
- 不一开始做强化学习；
- 不一次性生成完整项目。

这些作为后续增强：

- OCR；
- VLM 图表理解；
- LangGraph 重构；
- MCP 工具服务；
- 工具调用轨迹 SFT；
- GRPO / Agentic RL。

---

## 3. 技术栈建议

| 模块 | 技术选型 |
|---|---|
| 开发语言 | Python |
| LLM 推理 | vLLM |
| 模型接口 | OpenAI-compatible API |
| 文档解析 | PyMuPDF / pdfplumber |
| Markdown 解析 | markdown / mistune |
| Embedding | bge-small-zh / bge-m3 / text2vec |
| 向量库 | Chroma 或 FAISS |
| BM25 | rank-bm25 |
| Rerank | bge-reranker |
| Agent | 先手写 Agent Loop |
| 评测 | 自定义 Recall@k / Hit Rate / MRR，后续接 RAGAS |
| 前端 | Gradio 或 Streamlit，后期再做 |
| 配置管理 | YAML |
| 日志 | logging |
| 版本管理 | Git + GitHub |

---

## 4. 推荐仓库结构

请按以下结构创建项目：

```text
research-rag-agent/
├── README.md
├── requirements.txt
├── configs/
│   ├── model.yaml
│   ├── rag.yaml
│   └── agent.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── index/
├── src/
│   ├── loaders/
│   │   ├── pdf_loader.py
│   │   ├── markdown_loader.py
│   │   └── image_ocr.py
│   ├── chunkers/
│   │   ├── fixed_chunker.py
│   │   └── semantic_chunker.py
│   ├── embeddings/
│   │   └── embedding_model.py
│   ├── index/
│   │   ├── vector_store.py
│   │   ├── bm25_index.py
│   │   └── index_manager.py
│   ├── retrievers/
│   │   ├── dense_retriever.py
│   │   ├── bm25_retriever.py
│   │   └── hybrid_retriever.py
│   ├── rerank/
│   │   └── reranker.py
│   ├── llm/
│   │   └── vllm_client.py
│   ├── agent/
│   │   ├── tools.py
│   │   ├── tool_parser.py
│   │   ├── tool_executor.py
│   │   └── agent_loop.py
│   ├── evaluation/
│   │   ├── retrieval_eval.py
│   │   ├── ragas_eval.py
│   │   └── citation_eval.py
│   └── app.py
├── scripts/
│   ├── build_index.py
│   ├── run_rag.py
│   ├── run_agent.py
│   └── eval.py
└── docs/
    ├── architecture.md
    ├── experiment_report.md
    └── interview_notes.md
```

---

## 5. 数据结构约定

### 5.1 Document 数据结构

PDF 或 Markdown 解析后，统一转为：

```python
Document = {
    "text": str,
    "source": str,
    "page": int | None,
    "metadata": dict
}
```

字段说明：

- `text`：当前页或当前段落文本；
- `source`：文件路径或文件名；
- `page`：页码，Markdown 可为 None；
- `metadata`：额外信息，如标题、作者、章节名等。

---

### 5.2 Chunk 数据结构

文本切分后，统一转为：

```python
Chunk = {
    "chunk_id": str,
    "text": str,
    "source": str,
    "page": int | None,
    "metadata": dict
}
```

字段说明：

- `chunk_id`：唯一 ID；
- `text`：chunk 文本；
- `source`：来源文件；
- `page`：来源页码；
- `metadata`：额外信息。

---

### 5.3 Retrieval Result 数据结构

检索模块返回：

```python
RetrievalResult = {
    "chunk_id": str,
    "text": str,
    "source": str,
    "page": int | None,
    "score": float,
    "metadata": dict
}
```

---

### 5.4 Tool Call 数据结构

Agent 中 LLM 输出工具调用时，统一使用 JSON：

```json
{
  "type": "tool_call",
  "tool_name": "retriever",
  "arguments": {
    "query": "论文的创新点是什么？",
    "top_k": 5
  }
}
```

最终回答格式：

```json
{
  "type": "final_answer",
  "answer": "本文的主要创新点包括……"
}
```

---

## 6. 开发阶段规划

---

# V0.1：最小 PDF RAG 系统

## 目标

先跑通最基础链路：

```text
PDF → chunk → embedding → vector search → LLM answer
```

## 需要实现的文件

```text
src/loaders/pdf_loader.py
src/chunkers/fixed_chunker.py
src/embeddings/embedding_model.py
src/index/vector_store.py
src/llm/vllm_client.py
scripts/build_index.py
scripts/run_rag.py
```

## 模块要求

### 6.1 `pdf_loader.py`

功能：

- 使用 PyMuPDF 读取 PDF；
- 输入 PDF 路径；
- 输出 `list[Document]`；
- 每一页作为一个 Document；
- 保留 source、page、metadata；
- 加异常处理。

接口建议：

```python
def load_pdf(pdf_path: str) -> list[dict]:
    ...
```

输出示例：

```python
[
    {
        "text": "paper content...",
        "source": "data/raw/paper.pdf",
        "page": 1,
        "metadata": {"type": "pdf"}
    }
]
```

---

### 6.2 `fixed_chunker.py`

功能：

- 输入 `list[Document]`；
- 按固定字符长度切分；
- 支持 overlap；
- 输出 `list[Chunk]`；
- 保留 source 和 page。

接口建议：

```python
def chunk_documents(
    documents: list[dict],
    chunk_size: int = 800,
    overlap: int = 100
) -> list[dict]:
    ...
```

---

### 6.3 `embedding_model.py`

功能：

- 封装 embedding 模型；
- 输入字符串列表；
- 输出向量列表；
- 后续可替换 embedding 模型。

接口建议：

```python
class EmbeddingModel:
    def __init__(self, model_name: str):
        ...

    def encode(self, texts: list[str]) -> list[list[float]]:
        ...
```

---

### 6.4 `vector_store.py`

功能：

- 支持建立向量索引；
- 支持保存索引；
- 支持加载索引；
- 支持根据 query 搜索 top_k chunks。

接口建议：

```python
class VectorStore:
    def build(self, chunks: list[dict]) -> None:
        ...

    def save(self, path: str) -> None:
        ...

    def load(self, path: str) -> None:
        ...

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        ...
```

---

### 6.5 `vllm_client.py`

功能：

- 封装 vLLM OpenAI-compatible API；
- 输入 prompt；
- 输出模型回答；
- 支持 temperature、max_tokens。

接口建议：

```python
class VLLMClient:
    def __init__(self, base_url: str, api_key: str, model_name: str):
        ...

    def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> str:
        ...
```

如果暂时没有 vLLM 环境，可以先实现一个 mock LLM 或调用兼容 OpenAI 格式的其他模型，后续替换。

---

### 6.6 `build_index.py`

功能：

- 读取 PDF；
- 切分 chunk；
- 建立向量索引；
- 保存索引。

命令示例：

```bash
python scripts/build_index.py --input data/raw/paper.pdf --index_dir data/index/paper_index
```

---

### 6.7 `run_rag.py`

功能：

- 加载索引；
- 输入问题；
- 检索 top_k；
- 拼接 context；
- 调用 LLM；
- 输出回答和引用来源。

命令示例：

```bash
python scripts/run_rag.py --index_dir data/index/paper_index --query "这篇论文的创新点是什么？"
```

---

## V0.1 验收标准

- 能读取 PDF；
- 能构建索引；
- 能输入问题并返回回答；
- 回答中能显示引用来源；
- 代码可运行，无明显报错；
- README 记录启动步骤。

---

# V0.2：BM25 + Dense 混合检索

## 目标

提升检索质量，解决单纯向量检索对专有名词不稳定的问题。

## 新增文件

```text
src/index/bm25_index.py
src/retrievers/dense_retriever.py
src/retrievers/bm25_retriever.py
src/retrievers/hybrid_retriever.py
```

---

## 模块要求

### 6.8 `bm25_index.py`

功能：

- 使用 rank-bm25；
- 基于 chunk 文本建立 BM25 索引；
- 支持 query 检索 top_k。

接口建议：

```python
class BM25Index:
    def build(self, chunks: list[dict]) -> None:
        ...

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        ...
```

---

### 6.9 `hybrid_retriever.py`

功能：

- 同时调用 BM25 和 Dense 检索；
- 对检索分数做归一化；
- 融合分数；
- 去重；
- 返回 top_k。

接口建议：

```python
class HybridRetriever:
    def __init__(self, dense_retriever, bm25_retriever, alpha: float = 0.5):
        ...

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        ...
```

分数融合建议：

```text
final_score = alpha * dense_score + (1 - alpha) * bm25_score
```

其中：

- `alpha` 越大，越偏向语义检索；
- `alpha` 越小，越偏向关键词检索。

---

## V0.2 验收标准

- 能单独使用 BM25 检索；
- 能单独使用向量检索；
- 能使用 Hybrid 检索；
- 能输出三种检索结果对比；
- 能解释 BM25 和 Dense Retrieval 的区别。

---

# V0.3：Rerank 与引用溯源

## 目标

让检索结果更精确，让回答可追溯。

## 新增文件

```text
src/rerank/reranker.py
src/evaluation/citation_eval.py
```

---

## 模块要求

### 6.10 `reranker.py`

功能：

- 输入 query 和候选 chunks；
- 使用 reranker 模型重新打分；
- 返回重排后的 top_k。

接口建议：

```python
class Reranker:
    def __init__(self, model_name: str):
        ...

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5
    ) -> list[dict]:
        ...
```

流程：

```text
Hybrid Retrieval top-20
↓
Rerank
↓
Top-5
↓
LLM
```

---

### 6.11 引用格式要求

回答后必须附带引用信息：

```text
引用来源：
[1] paper.pdf, page 3, chunk_id=xxx
[2] paper.pdf, page 5, chunk_id=yyy
```

如果没有检索到可靠上下文，要求模型回答：

```text
文档中未找到足够依据，无法确定。
```

---

## V0.3 验收标准

- 支持 Hybrid top-20 + Rerank top-5；
- 回答中能输出引用来源；
- 检索结果中包含 source、page、chunk_id；
- 能对比是否使用 Rerank 的回答差异。

---

# V0.4：接入 vLLM 本地推理

## 目标

把本地模型部署成服务，并作为 RAG / Agent 的统一推理后端。

## 任务

1. 使用 vLLM 启动本地模型；
2. 实现 OpenAI-compatible API 调用；
3. 替换原来的临时 LLM 接口；
4. 记录响应时间；
5. 支持配置文件设置模型名、base_url、temperature、max_tokens。

---

## 配置文件示例：`configs/model.yaml`

```yaml
llm:
  provider: "vllm"
  base_url: "http://localhost:8000/v1"
  api_key: "EMPTY"
  model_name: "Qwen/Qwen2.5-1.5B-Instruct"
  temperature: 0.2
  max_tokens: 1024
```

---

## V0.4 验收标准

- vLLM 服务能启动；
- `vllm_client.py` 能正常调用本地模型；
- `run_rag.py` 能通过本地模型生成回答；
- 记录单次问答耗时；
- README 中写清楚启动命令。

---

# V0.5：Agent 工具调用

## 目标

从普通 RAG 问答升级为 RAG Agent，使模型能根据任务选择工具。

## 新增文件

```text
src/agent/tools.py
src/agent/tool_parser.py
src/agent/tool_executor.py
src/agent/agent_loop.py
scripts/run_agent.py
```

---

## 工具设计

### 6.12 工具列表

| 工具名 | 作用 |
|---|---|
| `retriever` | 检索相关原文片段 |
| `summarizer` | 总结给定文本 |
| `table_generator` | 生成论文对比表 |
| `citation_checker` | 检查回答是否有原文依据 |
| `calculator` | 执行简单数学计算 |

---

### 6.13 `tools.py`

定义工具 schema 和工具函数。

示例 schema：

```python
TOOLS = [
    {
        "name": "retriever",
        "description": "从论文知识库中检索与问题相关的原文片段",
        "parameters": {
            "query": "检索问题",
            "top_k": "返回片段数量"
        }
    },
    {
        "name": "citation_checker",
        "description": "检查回答是否能被检索到的上下文支持",
        "parameters": {
            "answer": "模型生成的回答",
            "contexts": "检索到的上下文"
        }
    }
]
```

---

### 6.14 `tool_parser.py`

功能：

- 从 LLM 输出中解析 JSON；
- 判断是 tool_call 还是 final_answer；
- 对 JSON 格式错误做容错；
- 如果解析失败，返回错误信息。

接口建议：

```python
def parse_tool_call(response: str) -> dict:
    ...
```

---

### 6.15 `tool_executor.py`

功能：

- 根据 tool_name 调用对应工具；
- 校验参数；
- 捕获异常；
- 返回 observation。

接口建议：

```python
class ToolExecutor:
    def __init__(self, tools: dict):
        ...

    def execute(self, tool_name: str, arguments: dict) -> dict:
        ...
```

---

### 6.16 `agent_loop.py`

功能：

- 维护对话历史；
- 每一步调用 LLM；
- 解析 tool_call；
- 执行工具；
- 将 observation 回填；
- 达到 final_answer 或 max_steps 停止；
- 打印工具调用日志。

核心伪代码：

```python
history = [system_prompt, user_question]

for step in range(max_steps):
    response = llm.generate(history)

    parsed = parse_tool_call(response)

    if parsed["type"] == "tool_call":
        observation = tool_executor.execute(
            parsed["tool_name"],
            parsed["arguments"]
        )
        history.append({
            "role": "tool",
            "name": parsed["tool_name"],
            "content": observation
        })

    elif parsed["type"] == "final_answer":
        return parsed["answer"]

    else:
        history.append({
            "role": "system",
            "content": "工具调用格式错误，请重新输出合法 JSON。"
        })
```

---

## Agent System Prompt 要求

系统提示词需要明确告诉模型：

1. 可以使用哪些工具；
2. 什么时候应该调用工具；
3. 必须输出 JSON；
4. 不允许编造引用；
5. 如果文档中没有依据，应说明找不到依据；
6. 如果已经有足够信息，输出 final_answer。

示例：

```text
你是一个科研文献阅读 Agent。你可以调用工具完成任务。

可用工具：
1. retriever：从论文库中检索相关原文片段；
2. summarizer：总结给定文本；
3. table_generator：生成多篇论文对比表；
4. citation_checker：检查回答是否有原文依据；
5. calculator：执行简单数学计算。

规则：
- 如果问题需要论文原文依据，必须优先调用 retriever；
- 如果需要比较多篇论文，可以多次调用 retriever；
- 回答必须基于工具返回的 observation；
- 不允许编造文档中没有的内容；
- 如果没有足够依据，回答“文档中未找到足够依据”；
- 每次输出必须是合法 JSON；
- 如果需要调用工具，输出 type=tool_call；
- 如果可以最终回答，输出 type=final_answer。
```

---

## V0.5 验收标准

- 能运行 `scripts/run_agent.py`；
- LLM 能输出 tool_call；
- 程序能解析 tool_call；
- 工具能被执行；
- observation 能回填给 LLM；
- Agent 能完成至少 3 类任务：
  - 论文创新点总结；
  - 实验结果总结；
  - 多篇论文对比表生成；
- 有工具调用日志；
- 设置 max_steps 防止死循环。

---

# V0.6：评测体系

## 目标

让项目有实验结果和可量化指标。

## 新增文件

```text
src/evaluation/retrieval_eval.py
src/evaluation/ragas_eval.py
src/evaluation/citation_eval.py
scripts/eval.py
docs/experiment_report.md
```

---

## 评测数据格式

构造 `data/eval/eval_questions.jsonl`：

```json
{"question": "这篇论文的核心创新点是什么？", "answer": "标准答案", "gold_chunk_ids": ["chunk_001", "chunk_005"]}
{"question": "本文使用了哪些数据集？", "answer": "标准答案", "gold_chunk_ids": ["chunk_010"]}
```

---

## 检索指标

实现以下指标：

### Recall@k

含义：正确 chunk 是否出现在 top-k 检索结果中。

### Hit Rate

含义：top-k 中是否至少命中一个正确 chunk。

### MRR

含义：第一个正确 chunk 排名越靠前，分数越高。

---

## 对比实验

至少完成以下对比：

| 实验编号 | 配置 |
|---|---|
| E1 | Dense Retrieval only |
| E2 | BM25 only |
| E3 | Hybrid Retrieval |
| E4 | Hybrid + Rerank |
| E5 | 不同 chunk_size 对比 |
| E6 | 不同 top_k 对比 |

---

## V0.6 验收标准

- 有 20–50 条测试问题；
- 能运行 `scripts/eval.py`；
- 能输出 Recall@k、Hit Rate、MRR；
- 有实验结果表格；
- 有 `docs/experiment_report.md`；
- 能说明不同配置对效果的影响。

---

# V0.7：工程化与展示

## 目标

让项目更像完整工程，而不是零散脚本。

## 任务

1. 加入 Gradio 或 Streamlit 页面；
2. 加入 YAML 配置；
3. 加入 logging；
4. 加入简单缓存；
5. 完善 README；
6. 增加架构图；
7. 增加 demo 截图；
8. 整理面试问题。

---

## README 必须包含

1. 项目简介；
2. 项目架构；
3. 功能列表；
4. 环境安装；
5. vLLM 启动方式；
6. 索引构建方式；
7. RAG 问答运行方式；
8. Agent 运行方式；
9. 评测方式；
10. 实验结果；
11. 项目亮点；
12. 后续计划。

---

# V0.8：后续增强项

以下内容不是第一阶段必须完成。

---

## 方向 A：OCR / VLM 多模态文档解析

目标：

- 处理扫描版 PDF；
- 识别论文图片中的文字；
- 提取图表标题、图注；
- 使用 VLM 理解关键图表；
- 将图表信息加入 RAG 索引。

新增模块：

```text
src/loaders/image_ocr.py
src/loaders/vlm_image_parser.py
```

---

## 方向 B：工具调用轨迹 SFT

前提：

- Agent 已经能运行；
- 能保存工具调用日志。

保存轨迹格式：

```json
{
  "user": "这篇论文的创新点是什么？",
  "trajectory": [
    {
      "type": "tool_call",
      "tool_name": "retriever",
      "arguments": {
        "query": "创新点",
        "top_k": 5
      }
    },
    {
      "type": "observation",
      "content": "检索结果..."
    },
    {
      "type": "final_answer",
      "answer": "本文的创新点包括..."
    }
  ]
}
```

用途：

- 构造 SFT 数据；
- 训练模型学习工具调用格式；
- 提高工具调用稳定性。

---

## 方向 C：GRPO / Agentic RL

前提：

- 有稳定 Agent 环境；
- 有可执行工具；
- 有任务数据；
- 有奖励函数；
- 有轨迹日志。

奖励设计示例：

| 行为 | 奖励 |
|---|---:|
| 检索命中正确 chunk | +1 |
| 工具选择正确 | +1 |
| 引用准确 | +2 |
| 回答忠实原文 | +3 |
| 不必要工具调用 | -0.5 |
| JSON 格式错误 | -1 |
| 无依据编造 | -3 |

注意：这属于高级扩展，不建议第一阶段做。

---

## 7. 每周开发计划

如果每天投入 4–5 小时，推荐 6 周基础版 + 2 周增强版。

| 周次 | 目标 | 主要任务 | 交付物 |
|---|---|---|---|
| 第 1 周 | 最小 RAG | PDF 解析、chunk、embedding、向量检索、基础问答 | `run_rag.py` |
| 第 2 周 | 检索增强 | BM25、Hybrid Retrieval、元数据绑定 | `hybrid_retriever.py` |
| 第 3 周 | 精排与引用 | Rerank、引用溯源、prompt 优化 | 可追溯问答结果 |
| 第 4 周 | vLLM 接入 | 本地模型部署、API 调用、响应时间记录 | `vllm_client.py` |
| 第 5 周 | Agent 工具调用 | tool schema、parser、executor、agent loop | `run_agent.py` |
| 第 6 周 | 评测与报告 | Recall@k、MRR、RAGAS、实验对比 | 实验报告 |
| 第 7 周 | 工程化优化 | Gradio UI、日志、配置文件、缓存 | 可展示 demo |
| 第 8 周 | 扩展增强 | OCR/VLM 或工具调用 SFT 初版 | 简历增强点 |

---

## 8. Codex 使用规范

### 8.1 正确提问方式

不要让 Codex 一次性生成完整项目。

正确方式：

```text
我正在搭建 ResearchAgent 项目。
现在只实现 PDF 解析模块。
请你写 src/loaders/pdf_loader.py，要求：
1. 使用 PyMuPDF；
2. 输入 PDF 路径；
3. 输出 list[dict]；
4. 每个 dict 包含 text、source、page、metadata；
5. 加异常处理；
6. 给出最小测试代码；
7. 不要改动其他文件。
```

---

### 8.2 每次只做一个模块

推荐顺序：

```text
pdf_loader
↓
fixed_chunker
↓
embedding_model
↓
vector_store
↓
run_rag
↓
bm25_index
↓
hybrid_retriever
↓
reranker
↓
vllm_client
↓
tools
↓
tool_parser
↓
tool_executor
↓
agent_loop
↓
evaluation
```

---

### 8.3 每完成一个模块，需要让 Codex 解释

提问模板：

```text
请逐行解释刚才生成的代码，重点说明：
1. 这个模块解决什么问题；
2. 输入是什么；
3. 输出是什么；
4. 和上下游模块如何连接；
5. 关键参数有哪些；
6. 如果报错应该从哪里排查。
```

---

### 8.4 每完成一个模块，需要写学习记录

在 `docs/interview_notes.md` 中记录：

```text
模块名称：
解决问题：
输入：
输出：
关键参数：
常见问题：
面试可能追问：
```

---

## 9. 面试可讲的项目亮点

完成基础版后，项目可以强调以下亮点：

1. **不是普通 RAG Demo**：加入 BM25 + Dense 混合检索；
2. **不是只调用在线 API**：接入 vLLM 本地推理服务；
3. **不是只返回答案**：支持引用溯源；
4. **不是只凭主观判断效果**：有 Recall@k、Hit Rate、MRR 评测；
5. **不是被动问答**：加入 Agent 工具调用；
6. **能扩展后训练**：后续可基于工具调用轨迹做 SFT / GRPO。

---

## 10. 简历表述建议

### 项目名称

**ResearchAgent：面向科研文献阅读的 RAG 智能体系统**

### 项目介绍

构建面向科研文献阅读场景的本地大模型 RAG Agent 系统，支持 PDF/Markdown 文献解析、混合检索、Rerank 精排、引用溯源和多工具调用，基于 vLLM 部署本地模型服务，实现论文问答、创新点提取、实验结果总结和多论文对比等功能。

### 项目工作

1. 构建文档解析与索引模块，实现 PDF 文本提取、chunk 切分、Embedding 表示、元数据绑定和向量索引构建；
2. 设计 BM25 + Dense 的混合检索流程，引入 Rerank 精排机制，提升复杂科研问题下的检索命中率与上下文相关性；
3. 基于 vLLM 部署本地大模型服务，封装 OpenAI-compatible API，实现 RAG 系统对本地模型的统一调用；
4. 设计 Agent 工具调用协议，实现 retriever、summarizer、table_generator、citation_checker 等工具协同，使模型能够根据任务自主选择检索、总结和引用检查流程；
5. 构建 Recall@k、MRR、Hit Rate 和 RAGAS 评测流程，对比不同 chunk 策略、召回方式和 Rerank 配置对问答效果的影响。

---

## 11. 最终验收清单

### 必须完成

- [ ] PDF 解析；
- [ ] chunk 切分；
- [ ] embedding；
- [ ] 向量索引；
- [ ] 基础 RAG 问答；
- [ ] 引用来源输出；
- [ ] BM25 检索；
- [ ] Hybrid Retrieval；
- [ ] Rerank；
- [ ] vLLM Client；
- [ ] 最小 Agent Loop；
- [ ] 工具调用日志；
- [ ] 检索评测；
- [ ] README。

---

### 尽量完成

- [ ] Gradio / Streamlit UI；
- [ ] RAGAS；
- [ ] 多论文对比；
- [ ] citation_checker；
- [ ] 配置文件；
- [ ] 日志系统；
- [ ] 实验报告；
- [ ] 架构图。

---

### 后续扩展

- [ ] OCR；
- [ ] VLM 图表理解；
- [ ] LangGraph；
- [ ] MCP；
- [ ] 工具调用轨迹 SFT；
- [ ] GRPO / Agentic RL。

---

## 12. 项目开发原则

1. **先跑通，再优化**；
2. **先 RAG，再 Agent**；
3. **先手写 Agent Loop，再考虑 LangGraph**；
4. **先文本 PDF，再考虑多模态**；
5. **先 SFT 轨迹数据，再考虑 RL**；
6. **每个模块都要能解释输入、输出和作用**；
7. **不追求代码一开始完美，追求逐步可运行**；
8. **所有结果必须有实验记录**；
9. **不要把项目变成简单换皮开源项目**；
10. **AI 可以写代码，但架构和验收标准由你控制**。

---

## 13. 给 Codex 的总任务说明

你可以将下面这段作为第一次输入给 Codex：

```text
我正在开发一个名为 ResearchAgent 的项目，目标是构建一个面向科研文献阅读的 RAG 智能体系统。请你协助我按阶段完成开发，但不要一次性生成完整项目。

开发原则：
1. 每次只实现一个模块；
2. 所有模块必须有清晰的输入输出；
3. 代码要可运行、可测试；
4. 不要生成过度复杂的工程；
5. 优先保证最小链路跑通；
6. 每个模块完成后，请解释它在整个系统中的作用。

项目阶段：
V0.1：PDF 解析、chunk、embedding、向量检索、基础 RAG；
V0.2：BM25 + Dense 混合检索；
V0.3：Rerank 与引用溯源；
V0.4：vLLM 本地模型接入；
V0.5：Agent 工具调用；
V0.6：检索和生成评测；
V0.7：工程化与展示；
V0.8：OCR/VLM、工具调用 SFT、GRPO 等增强项。

请先帮我创建项目目录结构和最小 requirements.txt，然后等待我下一步指令。
```

---

## 14. 第一条具体 Codex 指令

建议第一步不要让 Codex 写太多代码，只让它创建目录结构。

```text
请根据 ResearchAgent 项目计划，创建如下项目目录结构：

research-rag-agent/
├── README.md
├── requirements.txt
├── configs/
├── data/raw/
├── data/processed/
├── data/index/
├── src/loaders/
├── src/chunkers/
├── src/embeddings/
├── src/index/
├── src/retrievers/
├── src/rerank/
├── src/llm/
├── src/agent/
├── src/evaluation/
├── scripts/
└── docs/

要求：
1. 只创建目录和空文件；
2. 在每个 Python 包目录下添加 __init__.py；
3. requirements.txt 先写入基础依赖；
4. README.md 写入项目简介、当前阶段、运行目标；
5. 不要实现具体功能代码。
```

---

## 15. 第二条具体 Codex 指令

目录建立后，再做 PDF 解析模块：

```text
现在请实现 V0.1 的第一个模块：src/loaders/pdf_loader.py。

要求：
1. 使用 PyMuPDF；
2. 提供 load_pdf(pdf_path: str) -> list[dict]；
3. 每页输出一个 dict；
4. dict 包含 text、source、page、metadata；
5. page 从 1 开始；
6. metadata 至少包含 type="pdf"；
7. 对文件不存在、PDF 解析失败、空文本页做异常处理；
8. 在文件底部提供简单测试代码；
9. 不要修改其他模块。
```

---

## 16. 当前阶段最重要的判断标准

如果你能完成以下流程，项目就已经进入正轨：

```text
给定一篇 PDF
↓
运行 build_index.py
↓
生成索引
↓
运行 run_rag.py
↓
输入“这篇论文的创新点是什么？”
↓
系统返回基于原文的回答
↓
回答后附带引用页码
```

完成这个后，再考虑 Hybrid Retrieval、Rerank、Agent、评测。

---

## 17. 总结

本项目不追求一开始做成完整工业级系统，而是按照以下主线递进：

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

核心目标是：

> 通过 AI 辅助一步步搭建项目，在过程中真正理解 RAG、Agent、工具调用和本地模型部署，最终形成一个能写进简历、能被面试追问、能展示工程能力的第二项目。
