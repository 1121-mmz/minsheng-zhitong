# 民声直通 · 政务热线智能分诊 Agent

基于 **LangGraph 多 Agent 编排 + RAG 向量检索**的政务诉求智能分诊系统。市民描述诉求后，由「受理 → 检索 → 决策」三个 Agent 协作完成结构化分诊，输出推荐主办/协办单位与派单依据，并贯穿工单流转全流程。

## ✨ 核心特性

- **多 Agent 编排**：基于 LangGraph `StateGraph` 拆分为受理 Agent（诉求理解 + 多轮澄清）、检索 Agent（Function Calling 工具调用）、决策 Agent（结构化结论），职责分离、状态流转清晰；
- **Function Calling**：模型自主决定调用检索工具（部门权责清单检索 `search_regulation` / 历史工单检索 `lookup_history`），多步推理；
- **多轮澄清**：诉求信息不足时，受理 Agent 反问市民补充地点、事项等要素，形成对话闭环；
- **RAG 向量检索**：`FastEmbed(bge-small-zh)` 向量化 + `Qdrant` 余弦相似度 TopK 召回 + `DeepSeek` 生成，输出附带法律依据溯源、降低幻觉；
- **容错降级**：Function Calling 失败降级单次生成、向量库不可用回退关键词匹配、超时与人工兜底，保证链路不中断；
- **完整业务闭环**：RBAC 三级权限（超级管理员/管理员/市民）、HMAC 无状态 Token + BCrypt 鉴权、工单全生命周期（待派单 → 已派单）、满意度评价、数据大盘。

## 🏗️ 架构

```
市民诉求
   ↓
① 受理 Agent（理解诉求、抽取要素；信息不足 → 反问澄清，多轮对话）
   ↓ 信息足够
② 检索 Agent（Function Calling 调工具：查权责清单 + 查历史工单）
   ↓
③ 决策 Agent（综合输出结构化分诊结论 + 置信度）
   ↓
工单流转（待派单 → 已派单 → 满意度评价）
```

**服务架构**：Vue3 前端(Nginx) → Spring Boot 业务后端 → Python FastAPI AI 服务 ↔ Qdrant 向量库，由 Docker Compose 一键编排。

## 🛠️ 技术栈

- **Agent / LLM**：LangGraph、Function Calling、Prompt Engineering、RAG、DeepSeek、OpenAI SDK
- **检索**：Qdrant、FastEmbed(bge-small-zh)
- **后端**：Java、Spring Boot、Spring Data JPA、H2（开发）/ MySQL（生产可切换）
- **前端**：Vue3、Pinia、Element Plus、Vite
- **部署**：Docker、Docker Compose、Nginx

## 🚀 快速开始

### 1. 配置 DeepSeek API Key

复制 `.env.example` 为 `.env`，填入真实 key（`.env` 已被 gitignore，不会入库）：

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY=sk-你的key
```

### 2. 一键启动

```bash
docker compose up --build
```

首次启动会下载 embedding 模型（约 100MB，走国内 HF 镜像），随后访问 http://localhost 即可。

### 3. 默认账号

| 角色 | 账号 | 密码 |
|---|---|---|
| 超级管理员 | admin | 123456 |
| 普通市民 | user | 123456 |

## 📁 目录结构

```
minsheng_zhitong/
├── ai-service/        # Python FastAPI：多 Agent 编排 + RAG 检索
│   ├── main.py        # LangGraph 多 Agent + Function Calling + RAG
│   ├── requirements.txt
│   └── Dockerfile
├── backend/           # Spring Boot：工单/用户/权限/状态流转
│   ├── src/main/java/com/example/backend/
│   └── Dockerfile
├── frontend/          # Vue3 + Pinia + Element Plus
│   ├── src/
│   └── Dockerfile
└── docker-compose.yml # 编排 backend / ai-service / qdrant / frontend
```

## 🔒 安全说明

- `.env` 不入库，API Key 通过环境变量注入；
- 密码 BCrypt 加密存储，Token 采用 HMAC 无状态签名。

## ⚠️ 说明

- 知识库为**示例数据**（10 条权责条目），正式使用需替换为真实部门权责清单；
- 项目尚未引入评估集与可观测性（tracing），属于后续规划方向。
