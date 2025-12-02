# GeoGLI Chatbot - Dify Integration Guide

## 概述

本指南说明如何将GeoGLI Chatbot作为微服务部署,并在Dify中通过HTTP请求调用其API。

## 架构

```
┌─────────────────┐
│  Dify Workflow  │
│                 │
│  ┌───────────┐  │
│  │ HTTP Node │──┼──────┐
│  └───────────┘  │      │
└─────────────────┘      │
                         │ HTTP Request
                         ▼
              ┌──────────────────────┐
              │ GeoGLI Chatbot API   │
              │                      │
              │ • /api/dify/chat     │
              │ • /api/dify/recognize│
              │ • /api/dify/health   │
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  BM25 Search Engine  │
              │  + LangGraph Router  │
              └──────────────────────┘
```

## 快速开始

### 1. 部署GeoGLI Chatbot微服务

#### 使用Docker Compose (推荐)

```bash
# 克隆项目
git clone <your-repo-url>
cd GeoGLI-Chatbot

# 启动服务
docker-compose -f docker-compose.dify.yml up -d

# 检查服务状态
curl http://localhost:8000/api/dify/health
```

#### 手动部署

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. 验证API可用性

```bash
# 健康检查
curl http://localhost:8000/api/dify/health

# 测试聊天端点
curl -X POST http://localhost:8000/api/dify/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the drought trends in Saudi Arabia?",
    "user": "test_user",
    "response_mode": "blocking"
  }'

# 测试意图识别端点
curl -X POST http://localhost:8000/api/dify/recognize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Saudi Arabia wildfires"
  }'
```

## API端点详解

### 1. `/api/dify/chat` - 聊天端点

**用途**: 主要的问答接口,返回完整的答案和元数据

**请求格式**:
```json
{
  "query": "用户查询文本",
  "user": "用户ID (可选)",
  "conversation_id": "会话ID (可选)",
  "inputs": {},
  "response_mode": "blocking"
}
```

**响应格式**:
```json
{
  "event": "message",
  "message_id": "msg_1234567890",
  "conversation_id": "session_abc123",
  "mode": "chat",
  "answer": "生成的答案文本...",
  "metadata": {
    "intent": "ask.country",
    "hits": [...],
    "latency_ms": 150,
    "source": "bm25"
  },
  "created_at": 1234567890
}
```

**在Dify中使用**:
1. 添加 **HTTP Request** 节点
2. 配置:
   - Method: `POST`
   - URL: `http://your-server:8000/api/dify/chat`
   - Headers: `Content-Type: application/json`
   - Body:
     ```json
     {
       "query": "{{input.user_query}}",
       "conversation_id": "{{conversation_id}}"
     }
     ```
3. 输出变量: `{{http_chat.data.answer}}`

### 2. `/api/dify/recognize` - 意图识别端点

**用途**: 提取查询中的结构化信息(国家、领域、ISO3代码等)

**请求格式**:
```json
{
  "query": "Saudi Arabia wildfires"
}
```

**响应格式**:
```json
{
  "targets": ["saudi arabia"],
  "domain": "country_profile",
  "section_hint": "stressors/fires",
  "iso3_codes": ["SAU"],
  "query": "Saudi Arabia wildfires"
}
```

**在Dify中使用**:
1. 添加 **HTTP Request** 节点
2. 配置:
   - Method: `POST`
   - URL: `http://your-server:8000/api/dify/recognize`
   - Headers: `Content-Type: application/json`
   - Body:
     ```json
     {
       "query": "{{input.user_query}}"
     }
     ```
3. 输出变量:
   - `{{http_recognize.data.domain}}`
   - `{{http_recognize.data.targets}}`
   - `{{http_recognize.data.iso3_codes}}`

### 3. `/api/dify/health` - 健康检查

**用途**: 监控服务状态

**响应格式**:
```json
{
  "status": "ok",
  "service": "GeoGLI-Chatbot-Dify",
  "version": "1.0.0",
  "bm25_enabled": true
}
```

## Dify工作流示例

### 示例1: 简单问答流程

```
START
  │
  ▼
┌─────────────────┐
│  Input Node     │
│  user_query     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP Request   │
│  /api/dify/chat │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Output Node    │
│  {{answer}}     │
└─────────────────┘
```

**配置步骤**:
1. **Start节点**: 定义输入变量 `user_query`
2. **HTTP Request节点**:
   - URL: `http://your-server:8000/api/dify/chat`
   - Method: POST
   - Body:
     ```json
     {
       "query": "{{input.user_query}}"
     }
     ```
3. **Output节点**: 输出 `{{http_request.data.answer}}`

### 示例2: 意图识别 + 条件路由

```
START
  │
  ▼
┌─────────────────────┐
│  HTTP Request       │
│  /api/dify/recognize│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  IF/ELSE Node       │
│  Route by domain    │
└─┬────────┬────────┬─┘
  │        │        │
  A        B        C
  │        │        │
  ▼        ▼        ▼
Country  Legis-  Commit-
Profile  lation  ment
```

**配置步骤**:
1. **HTTP Request节点** (recognize):
   - URL: `http://your-server:8000/api/dify/recognize`
   - Body: `{"query": "{{input.user_query}}"}`

2. **IF/ELSE节点**:
   - Branch A: `{{http_recognize.data.domain}} == "country_profile"`
   - Branch B: `{{http_recognize.data.domain}} == "legislation"`
   - Branch C: `{{http_recognize.data.domain}} == "commitment"`

3. 每个分支可以调用不同的处理逻辑

### 示例3: 完整的两阶段流程

```
START → Recognize → Route → Chat → Format → Output
```

**配置步骤**:
1. **Recognize**: 提取意图和实体
2. **Route**: 根据domain分支
3. **Chat**: 调用聊天API获取答案
4. **Format**: 格式化输出
5. **Output**: 返回给用户

## 环境变量配置

在 `docker-compose.dify.yml` 或 `.env` 文件中配置:

```bash
# BM25搜索配置
RAG_BM25_ENABLED=true
BM25_TOP_K=3

# Dense RAG配置 (可选)
RAG_DENSE_ENABLED=false

# CORS配置 (添加你的Dify实例URL)
ALLOWED_ORIGINS=http://localhost:3000,https://your-dify-instance.com

# OpenAI配置 (如果使用LLM功能)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## 部署建议

### 生产环境部署

1. **使用反向代理** (Nginx/Caddy):
   ```nginx
   location /api/geoglichatbot/ {
       proxy_pass http://localhost:8000/api/dify/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

2. **配置HTTPS**:
   ```bash
   # 使用Caddy自动HTTPS
   caddy reverse-proxy --from your-domain.com --to localhost:8000
   ```

3. **监控和日志**:
   ```bash
   # 查看日志
   docker-compose -f docker-compose.dify.yml logs -f geoglichatbot-backend
   
   # 监控健康状态
   watch -n 5 'curl -s http://localhost:8000/api/dify/health | jq'
   ```

### 性能优化

1. **增加worker数量**:
   ```yaml
   # docker-compose.dify.yml
   environment:
     - WORKERS=4
   command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

2. **启用缓存**:
   ```python
   # 在代码中添加Redis缓存
   REDIS_URL=redis://localhost:6379
   ```

3. **数据预加载**:
   - 确保 `backend/data/` 目录包含所有BM25索引
   - 预先构建FAISS索引(如果使用dense RAG)

## 故障排查

### 问题1: 连接被拒绝

**症状**: `Connection refused` 或 `Cannot connect to server`

**解决方案**:
```bash
# 检查服务是否运行
docker ps | grep geoglichatbot

# 检查端口是否开放
netstat -tuln | grep 8000

# 检查防火墙
sudo ufw allow 8000
```

### 问题2: BM25搜索无结果

**症状**: API返回空结果或错误

**解决方案**:
```bash
# 检查data目录是否挂载
docker exec geoglichatbot-backend-dify ls -la /app/data

# 检查BM25是否启用
curl http://localhost:8000/api/dify/health | jq '.bm25_enabled'

# 测试BM25搜索
curl "http://localhost:8000/debug/bm25?q=Saudi+Arabia"
```

### 问题3: CORS错误

**症状**: Dify无法调用API,浏览器显示CORS错误

**解决方案**:
```bash
# 更新ALLOWED_ORIGINS环境变量
# 在docker-compose.dify.yml中添加:
- ALLOWED_ORIGINS=http://localhost:3000,https://your-dify-instance.com

# 重启服务
docker-compose -f docker-compose.dify.yml restart
```

## 安全建议

1. **API认证** (可选):
   ```python
   # 在dify.py中添加API Key验证
   from fastapi import Header
   
   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != os.getenv("DIFY_API_KEY"):
           raise HTTPException(status_code=401)
   ```

2. **速率限制**:
   ```python
   # 使用slowapi限制请求频率
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @router.post("/chat")
   @limiter.limit("10/minute")
   async def dify_chat(...):
       ...
   ```

3. **输入验证**:
   - 已实现: 查询长度限制 (max 4000字符)
   - 建议: 添加内容过滤和敏感词检测

## 监控和日志

### 日志查看

```bash
# 实时日志
docker-compose -f docker-compose.dify.yml logs -f

# 只看后端日志
docker-compose -f docker-compose.dify.yml logs -f geoglichatbot-backend

# 导出日志
docker-compose -f docker-compose.dify.yml logs > logs.txt
```

### 性能监控

```bash
# 查看资源使用
docker stats geoglichatbot-backend-dify

# 查看响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/dify/health
```

## 扩展功能

### 添加自定义端点

在 `backend/app/routes/dify.py` 中添加:

```python
@router.post("/custom")
async def custom_endpoint(request: Request, body: CustomRequest):
    """自定义业务逻辑"""
    # 实现你的逻辑
    return {"result": "..."}
```

### 集成其他服务

```python
# 调用外部API
import httpx

async def call_external_api(data):
    async with httpx.AsyncClient() as client:
        response = await client.post("https://external-api.com", json=data)
        return response.json()
```

## 参考资料

- [Dify官方文档](https://docs.dify.ai/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [GeoGLI Chatbot README](./README.md)
- [Dify Workflow规范](./DIFY_WORKFLOW_SPEC.md)

## 支持

如有问题,请:
1. 查看日志: `docker-compose logs`
2. 检查健康状态: `curl http://localhost:8000/api/dify/health`
3. 提交Issue到项目仓库

---

**最后更新**: 2025-11-28
**版本**: 1.0.0
