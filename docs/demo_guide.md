# ResearchAgent Demo Guide

本文档记录 ResearchAgent 当前 V0.7 阶段的演示方式。目标是让项目可以被快速运行、展示和复现实验结果。

当前推荐 CLI 演示入口是：

```text
scripts/run_agent.py
```

当前推荐 Web UI 演示入口是：

```text
scripts/web_demo.py
```

`scripts/run_rag.py` 和 `scripts/evaluate_retrieval.py` 保留为调试和实验入口。

## 1. 演示前准备

### 1.1 进入项目目录

```powershell
cd E:\LDW\Code\LLM\agent\research-rag-agent
```

### 1.2 激活环境

```powershell
conda activate research_agent
```

### 1.3 确认已有测试索引

当前演示默认使用：

```text
data/index/test_index
```

可以检查目录是否存在：

```powershell
Get-ChildItem data/index/test_index
```

如果该目录存在，说明可以直接运行问答和检索评测。

### 1.4 确认配置文件

当前有两个推荐配置：

```text
configs/default.yaml
configs/local_vllm.yaml
```

用途：

```text
default.yaml    使用 mock LLM，适合不启动本地模型时演示链路
local_vllm.yaml 使用本地 vLLM，适合展示真实回答效果
```

## 2. 最小演示路线

建议演示顺序：

```text
1. Agent Answer
2. Agent Retrieve
3. Agent Evaluate
4. vLLM Answer
5. Web UI
6. 日志文件
```

这条路线能展示系统的主要能力：

- 文献问答；
- chunk 检索；
- 检索质量评测；
- 本地大模型接入；
- Web UI 演示；
- 运行日志追踪。

## 3. Demo 1：Agent Answer

使用 mock LLM 演示完整 Agent 调用链路：

```powershell
python -m scripts.run_agent --config configs/default.yaml --query "What method does this paper propose?"
```

预期输出结构：

```text
Type: answer
Input: What method does this paper propose?

Answer:
This is a mock answer. LLM generation is not connected yet, but retrieval and prompt construction are working.

Sources:
[1] data/raw/test.pdf, page ..., chunk_id=...
[2] data/raw/test.pdf, page ..., chunk_id=...
[3] data/raw/test.pdf, page ..., chunk_id=...
```

演示重点：

- Agent 将普通问题路由到 `answer`；
- 系统完成检索、prompt 构造和回答生成；
- 即使使用 mock LLM，也能展示 sources 是否正确返回。

## 4. Demo 2：Agent Retrieve

只检索相关 chunks，不生成回答：

```powershell
python -m scripts.run_agent --config configs/default.yaml --query "search relevant chunks about experiments"
```

预期输出结构：

```text
Type: retrieve
Input: search relevant chunks about experiments

Chunks:
[1] data/raw/test.pdf, page ..., chunk_id=...
...
```

演示重点：

- Agent 根据 `search` 关键词路由到 `retrieve`；
- 该模式适合调试检索质量；
- 可以直接看到返回的 chunk 文本片段。

## 5. Demo 3：Agent Evaluate

运行检索评测：

```powershell
python -m scripts.run_agent --config configs/default.yaml --query "evaluate retrieval quality"
```

预期输出：

```text
Type: evaluate
Input: evaluate retrieval quality

Overall:
Mean Hit: 1.0000
Mean Recall: 0.6111
Mean MRR: 0.8333
```

演示重点：

- Agent 根据 `evaluate` 关键词路由到 `evaluate`；
- 系统读取 `data/eval/questions.jsonl`；
- 使用 Hit、Recall、MRR 量化当前检索质量。

当前默认配置下使用 BM25，因此结果应与 V0.4/V0.6 记录一致：

```text
Mean Hit    = 1.0000
Mean Recall = 0.6111
Mean MRR    = 0.8333
```

## 6. Demo 4：本地 vLLM 问答

如果已经启动本地 vLLM 服务，可以使用：

```powershell
python -m scripts.run_agent --config configs/local_vllm.yaml --query "What method does this paper propose?"
```

预期输出示例：

```text
Type: answer
Input: What method does this paper propose?

Answer:
The paper proposes an uncertainty-aware deep variational attention network (DVAN).

Sources:
[1] data/raw/test.pdf, page ..., chunk_id=...
[2] data/raw/test.pdf, page ..., chunk_id=...
[3] data/raw/test.pdf, page ..., chunk_id=...
```

演示重点：

- `local_vllm.yaml` 会把 LLM backend 从 mock 切换到 vLLM；
- 系统通过 OpenAI-compatible API 调用本地模型；
- 回答会基于检索到的文献片段生成。

## 7. vLLM 服务启动参考

如果需要在 WSL/Ubuntu 中启动 vLLM，可以参考：

```bash
vllm serve /mnt/c/Users/LLL/Desktop/minimind \
  --host 0.0.0.0 \
  --api-key abc123 \
  --served-model-name X \
  --max-model-len 1024 \
  --port 7890 \
  --gpu-memory-utilization 0.7
```

如果使用其他本地模型，只需要保持：

```text
api_key
served-model-name
port
```

和 `configs/local_vllm.yaml` 中的配置一致。

### 7.1 检查 vLLM 服务

PowerShell 中运行：

```powershell
Invoke-RestMethod `
  -Uri http://localhost:7890/v1/models `
  -Headers @{ Authorization = "Bearer abc123" }
```

如果返回模型列表，说明 vLLM 服务已经可访问。

### 7.2 测试 VLLMClient

```powershell
python -c "from src.llm.vllm_client import VLLMClient; c = VLLMClient('http://localhost:7890/v1', 'abc123', 'X'); print(c.generate('Answer in one sentence: what is retrieval augmented generation?', temperature=0.1, max_tokens=128))"
```

如果能输出一句回答，说明本地模型调用正常。

## 8. Demo 5：Web UI

启动 Web UI：

```powershell
python -m scripts.web_demo
```

终端会显示本地访问地址，例如：

```text
Running on local URL: http://127.0.0.1:7860
```

打开该地址即可进入 Web UI。

### 8.1 使用已有索引问答

如果已经有测试索引：

```text
data/index/test_index
```

可以在页面中填写：

```text
Config path: configs/default.yaml
Index dir override: data/index/test_index
Query: What method does this paper propose?
```

然后点击：

```text
Run Agent
```

页面会在不同 tab 中展示：

```text
Answer
Sources
Chunks
Metrics
```

### 8.2 指定 PDF 路径并构建 Web UI 索引

Web UI 支持输入本机 PDF 路径，例如：

```text
PDF path: data/raw/test.pdf
```

然后点击：

```text
Build Web UI Index
```

系统会执行：

```text
load_pdf
↓
chunk_documents
↓
EmbeddingModel
↓
VectorStore
↓
BM25Index
↓
保存到 data/index/webui_demo
```

注意：

```text
data/index/webui_demo
```

是 Web UI 的临时 demo 索引目录。每次点击 `Build Web UI Index` 都会覆盖之前的 `webui_demo` 索引。

构建成功后，页面中的 `Index dir override` 会指向：

```text
data/index/webui_demo
```

之后点击 `Run Agent`，问答会读取这个新构建的索引。

### 8.3 Web UI 的评估边界

Web UI 可以对任意文字版 PDF 做临时索引和问答，但 `Metrics` 只有在当前索引和 eval 文件匹配时才有意义。

例如：

```text
data/index/test_index
data/eval/questions.jsonl
```

这两者是配套的，因此可以做可靠评测。

如果你用 Web UI 临时构建了另一个 PDF 的索引：

```text
data/index/webui_demo
```

但配置文件仍然指向旧的：

```text
data/eval/questions.jsonl
```

那么 `Metrics` 不可靠。此时应主要查看：

```text
Answer
Sources
Chunks
```

并人工判断检索证据是否支持回答。

## 9. 调试入口

### 9.1 直接运行 RAG

```powershell
python -m scripts.run_rag --config configs/default.yaml --query "What method does this paper propose?"
```

用途：

- 绕过 Agent；
- 直接检查检索、prompt 和回答生成；
- 适合调试 RAG 链路。

### 9.2 覆盖配置参数

```powershell
python -m scripts.run_rag --config configs/default.yaml --query "What method does this paper propose?" --top_k 2
```

说明：

- YAML 提供默认值；
- 命令行参数可以临时覆盖默认值；
- 适合做 top_k、retriever、rerank 等实验。

### 9.3 直接运行检索评测

```powershell
python -m scripts.evaluate_retrieval --config configs/default.yaml
```

显示详细检索结果：

```powershell
python -m scripts.evaluate_retrieval --config configs/default.yaml --show_results
```

保存评测结果：

```powershell
python -m scripts.evaluate_retrieval --config configs/default.yaml --output_file data/eval/results_demo.json
```

## 10. 查看日志

日志文件：

```text
logs/research_agent.log
```

查看日志：

```powershell
Get-Content logs/research_agent.log
```

只看最后一段：

```powershell
Get-Content logs/research_agent.log -Tail 40
```

日志中应包含：

```text
Agent started
query=...
config: ...
detected_intent=...
calling_tool=...
retrieval_tool_started
retrieval_finished results=...
intent=...
Agent finished
```

演示重点：

- 日志能说明 Agent 选择了哪个工具；
- 能看到检索配置；
- 能看到检索结果数量；
- 能看到评测指标；
- 出问题时可以用日志定位环节。

## 11. 推荐演示脚本

如果只想快速完整展示，可以按顺序运行：

```powershell
python -m scripts.run_agent --config configs/default.yaml --query "What method does this paper propose?"
python -m scripts.run_agent --config configs/default.yaml --query "search relevant chunks about experiments"
python -m scripts.run_agent --config configs/default.yaml --query "evaluate retrieval quality"
Get-Content logs/research_agent.log -Tail 60
```

如果本地 vLLM 已启动，再运行：

```powershell
python -m scripts.run_agent --config configs/local_vllm.yaml --query "What method does this paper propose?"
```

Web UI 演示：

```powershell
python -m scripts.web_demo
```

## 12. 常见问题

### 12.1 ModuleNotFoundError: No module named 'src'

原因通常是没有在项目根目录运行命令。

应先进入：

```powershell
cd E:\LDW\Code\LLM\agent\research-rag-agent
```

然后使用：

```powershell
python -m scripts.run_agent ...
```

### 12.2 vLLM 返回 Unauthorized

原因通常是 API key 不一致。

检查 vLLM 启动参数：

```text
--api-key abc123
```

以及配置文件：

```yaml
llm:
  api_key: abc123
```

二者必须一致。

### 12.3 模型回答质量不好

可能原因：

- 检索结果不够相关；
- `top_k` 太小；
- rerank 未开启；
- 本地模型能力不足；
- prompt 约束不够清晰。

建议先用：

```powershell
python -m scripts.run_agent --config configs/default.yaml --query "search relevant chunks about experiments"
```

检查检索结果，再考虑切换 retriever、调整 top_k 或开启 rerank。

### 12.4 Citation Check 提示没有引用标记

当前系统不强制模型回答正文必须带 `[1]`、`[2]`。最低要求是回答后展示 `Sources`，用户可以根据来源回到原文检查。

Citation Check 当前只是规则级质量提示，不等于语义级事实核验。

### 12.5 Web UI 中 Answer 很好但 Chunks 看起来不相关

这说明需要检查检索证据，而不是只看最终回答。

可能原因：

- 模型根据不完整 context 或自身知识猜对了；
- 相关内容在 chunk 后半部分；
- 当前 retriever 对问题不敏感；
- 当前 index_dir 不是你以为的索引；
- 临时 PDF 没有配套 eval_file，无法自动判断检索质量。

建议优先检查：

```text
Sources
Chunks
Index dir override
logs/research_agent.log
```

## 13. 当前演示边界

当前 Demo 不包含：

- 真正浏览器文件上传；
- 多论文选择；
- OCR；
- 图表理解；
- 多轮对话记忆；
- LLM 自动选择工具。

后续 Agent 路线：

```text
V0.8 LLM Router
V0.9 LLM Structured Tool Calling
V1.0 Multi-step Agent
```

这些能力适合后续版本继续扩展。
