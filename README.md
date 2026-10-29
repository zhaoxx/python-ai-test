# python-ai-test

> 基于 **FastAPI + LangChain + LangGraph** 的 AI Agent 示例项目，从 Spring AI Java 项目移植而来，演示多模型平台调度、智能客服、规划 Agent、RAG 知识库以及基于 MySQL 的对话记忆持久化。

---

## 一、项目简介

本项目是一个用于学习 / 验证 **AI Agent 编排** 的 Python 服务，主要能力包括：

| 能力 | 说明 |
|------|------|
| 多模型平台调度 | 同时支持阿里云 DashScope（通义）与 DeepSeek，按平台名动态构造模型 |
| 智能客服 Agent | LangGraph ReAct Agent + 动态工具（订单查询 / 取消） |
| 规划 Agent | Planner (结构化输出) + Bot (流式回复) 双链编排 |
| RAG 知识库 | PDF / 文本片段向量化、相似度检索、增强问答 |
| 对话记忆持久化 | 默认使用 MySQL 存储历史消息，按 `conversation_id` 隔离，基于 `message_id` 增量去重 |
| 流式输出 | 所有对话接口均使用 SSE / StreamingResponse 逐 token 返回 |

---

## 二、技术栈

- **Web 框架**：FastAPI + Uvicorn
- **AI 编排**：LangChain / LangGraph / langchain-community / langchain-openai
- **LLM**：DashScope（ChatTongyi）、DeepSeek（ChatOpenAI 兼容）
- **Embedding**：DashScope `text-embedding-v2`
- **持久化**：SQLAlchemy 2.x + PyMySQL + MySQL 8
- **配置管理**：pydantic-settings + dotenv
- **文件解析**：pypdf
- **Python 版本**：3.11+（推荐 3.13）

---

## 三、目录结构

```
python-ai-test/
├── app/
│   ├── agents/                # Agent 实现
│   │   ├── customer.py        # 智能客服 ReAct Agent
│   │   └── planner.py         # 规划 Agent + Bot 链
│   ├── api/                   # FastAPI Controller 层
│   │   ├── customer_controller.py
│   │   ├── multi_controller.py
│   │   ├── knowledge_controller.py
│   │   └── model_controller.py
│   ├── llm/
│   │   └── providers.py       # LLM 工厂（按平台名构造）
│   ├── memory/                # 对话记忆
│   │   ├── db.py              # SQLAlchemy Engine / 建表
│   │   ├── mysql_store.py     # MySQLChatMessageHistory
│   │   ├── store.py           # 全局门面 ChatMemoryStore
│   │   └── advisors.py        # 消息ID注入、ReAgain 提示增强
│   ├── rag/                   # 知识库 / 向量检索
│   │   ├── knowledge.py
│   │   ├── loaders.py
│   │   └── vectorstore.py
│   ├── tools/                 # Agent 工具
│   │   └── dynamic_tools.py   # queryOrder / cancelOrder
│   ├── models/
│   │   └── schemas.py         # 结构化输出模型 (AIJob)
│   ├── sql/
│   │   └── schema-mysql.sql   # 建表 DDL
│   ├── config.py              # pydantic-settings 配置
│   └── main.py                # FastAPI 应用入口
├── .env.example               # 环境变量模板
├── requirements.txt           # Python 依赖
└── run.py                     # 启动脚本
```

---

## 四、架构分层

```
graph TB
    Browser[浏览器/curl]
    Controller[Controller 层 /api/*]
    Agent[Agent 层<br/>customer / planner]
    LLM[LLM Provider 工厂]
    Tools[动态工具<br/>queryOrder / cancelOrder]
    RAG[RAG 知识库]
    Memory[对话记忆<br/>ChatMemoryStore]
    MySQL[(MySQL<br/>python_ai_chat_memory)]
    DS[DashScope 通义]
    DSK[DeepSeek]

    Browser --> Controller
    Controller --> Agent
    Controller --> RAG
    Agent --> LLM
    Agent --> Tools
    Agent --> Memory
    RAG --> Memory
    Memory --> MySQL
    LLM --> DS
    LLM --> DSK
    RAG --> DS
```

**调用流程示例（`/api/customer/chat`）：**

1. Controller 解析参数 → 调用 `customer.stream_chat(message, session_id)`
2. Agent 写入用户消息到 MySQL，构造 LangGraph 输入
3. ReAct Agent 调用 DeepSeek（带工具），流式生成回复
4. 流结束后，将 assistant 完整回复写回 MySQL

---

## 五、核心模块说明

### 5.1 LLM Provider（`app/llm/providers.py`）
- 通过 `build_chat_model(platform, model, temperature)` 工厂构造 ChatModel
- 平台名：`deepseek` / `dashscope`，默认 `deepseek`
- Embedding 仅支持 DashScope（DeepSeek 不提供向量化模型）

### 5.2 对话记忆（`app/memory/`）
- `MySQLChatMessageHistory`：实现 `BaseChatMessageHistory`，按 `conversation_id` 隔离
- `ChatMemoryStore`：门面，提供 `get_history / get / clear`，自动截断到 `last_n`
- 增量去重：写入前注入 `message_id` UUID，已存在则跳过（等价 Java `IncrementalJdbcChatMemoryRepository`）

### 5.3 Agent 层
- **customer**：基于 `create_react_agent`，挂 `queryOrder` / `cancelOrder` 工具，进程内 `MemorySaver` + MySQL 双写
- **planner**：低温度结构化输出 `AIJob`，根据 `JobType` 分流（CANCEL / QUERY / OTHER）

### 5.4 RAG（`app/rag/`）
- 文本/PDF 切片 → DashScope Embedding → 内存向量库 → topK 相似度 → 增强 prompt

### 5.5 配置（`app/config.py`）
- 基于 `pydantic-settings`，启动时读取 `.env`，包含 LLM Key、温度、MySQL URL

---

## 六、API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/customer/chat` | 智能客服（流式，带工具） |
| GET | `/api/multi/chat` | 规划 + Bot 多链（流式） |
| GET | `/api/v1/knowledge-base/insert-text` | 文本入知识库 |
| POST | `/api/v1/knowledge-base/upload-file` | PDF/文件上传 |
| GET | `/api/v1/knowledge-base/search` | 相似性搜索 |
| GET | `/api/v1/knowledge-base/chat` | RAG 问答 |
| GET | `/api/v1/knowledge-base/chat-stream` | RAG 流式问答 |
| GET | `/chat` | 多平台模型直接对话 |

---

## 七、快速开始

### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

### 2. 配置环境变量

```powershell
Copy-Item .env.example .env
```

编辑 `.env`：

```env
DASHSCOPE_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx

MYSQL_URL=mysql+pymysql://root:123456@localhost:3306/spring_ai?charset=utf8mb4
```

### 3. 准备 MySQL

确保 `spring_ai` 库已创建；服务启动时会自动建表 `python_ai_chat_memory`。

### 4. 启动服务

```powershell
python run.py
```

服务监听 `http://0.0.0.0:8080`，浏览器请使用 **http://localhost:8080** 访问。

### 5. 调用示例

```
http://localhost:8080/api/customer/chat?message=你好&sessionId=1
http://localhost:8080/api/v1/knowledge-base/chat?query=refund%20policy&topK=3
```

---

## 八、数据表

```sql
CREATE TABLE python_ai_chat_memory (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  conversation_id VARCHAR(36) NOT NULL,
  content LONGTEXT NOT NULL,
  type VARCHAR(20) NOT NULL,           -- human / ai / system
  timestamp TIMESTAMP NOT NULL,
  message_id VARCHAR(36) NOT NULL,
  KEY idx_conversation_id_timestamp (conversation_id, timestamp),
  KEY uk_message_id (message_id)
);
```

---

## 九、设计要点

- **流式优先**：所有对话接口返回 `StreamingResponse`，避免长文本阻塞
- **会话隔离**：通过 `conversation_id` 隔离，跨进程也能从 MySQL 恢复
- **平台无关**：业务层只调用 `build_chat_model(platform)`，新增平台只改 Provider
- **Java 对齐**：包结构 / 接口路径与同名 Java 项目一一对应，便于阅读对比

---

## 十、后续可扩展

- [ ] 向量库换成 Milvus / Chroma 等持久化方案
- [ ] 引入 LangSmith / OpenTelemetry 链路追踪
- [ ] 工具支持从数据库 / 配置文件热加载
- [ ] 鉴权与多租户隔离
