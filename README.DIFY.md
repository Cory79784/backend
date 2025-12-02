# GeoGLI Chatbot - Dify微服务集成

> 将GeoGLI Chatbot作为独立微服务部署,通过API在Dify中调用

## 🎯 快速开始 (3分钟)

### 1️⃣ 启动服务

**Windows:**
```bash
start-dify-service.bat
```

**Linux/Mac:**
```bash
docker-compose -f docker-compose.dify.yml up -d
```

### 2️⃣ 验证服务

```bash
# 健康检查
curl http://localhost:8000/api/dify/health

# 测试聊天
curl -X POST http://localhost:8000/api/dify/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Saudi Arabia drought"}'
```

### 3️⃣ 在Dify中配置

1. 打开Dify工作流编辑器
2. 添加 **HTTP Request** 节点
3. 配置:
   - URL: `http://your-server:8000/api/dify/chat`
   - Method: `POST`
   - Body: `{"query": "{{input.user_query}}"}`
4. 使用输出: `{{http_request.data.answer}}`

## 📡 API端点

### `/api/dify/chat` - 主要聊天接口

**请求:**
```json
{
  "query": "What are the drought trends in Saudi Arabia?",
  "conversation_id": "optional-session-id"
}
```

**响应:**
```json
{
  "event": "message",
  "message_id": "msg_1234567890",
  "conversation_id": "session_abc123",
  "answer": "生成的答案...",
  "metadata": {
    "intent": "ask.country",
    "latency_ms": 150,
    "source": "bm25"
  }
}
```

### `/api/dify/recognize` - 意图识别

**请求:**
```json
{
  "query": "Saudi Arabia wildfires"
}
```

**响应:**
```json
{
  "targets": ["saudi arabia"],
  "domain": "country_profile",
  "section_hint": "stressors/fires",
  "iso3_codes": ["SAU"],
  "query": "Saudi Arabia wildfires"
}
```

## 🏗️ Dify工作流示例

### 简单问答流程

```
Input (user_query)
    ↓
HTTP Request (/api/dify/chat)
    ↓
Output ({{answer}})
```

### 高级路由流程

```
Input (user_query)
    ↓
HTTP Request (/api/dify/recognize)
    ↓
IF/ELSE (根据domain分支)
    ├─ country_profile → 处理国家数据
    ├─ legislation → 处理法律查询
    └─ commitment → 处理承诺查询
    ↓
HTTP Request (/api/dify/chat)
    ↓
Format Output
    ↓
Output
```

## 🔧 配置

### 环境变量 (`.env` 或 `docker-compose.dify.yml`)

```bash
# BM25搜索 (推荐开启)
RAG_BM25_ENABLED=true
BM25_TOP_K=3

# CORS (添加你的Dify URL)
ALLOWED_ORIGINS=http://localhost:3000,https://your-dify.com

# 可选: OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## 🧪 测试

### 自动化测试

```bash
# 安装依赖
pip install requests

# 运行测试
python test-dify-api.py
```

### 手动测试

```bash
# 测试1: 健康检查
curl http://localhost:8000/api/dify/health

# 测试2: 意图识别
curl -X POST http://localhost:8000/api/dify/recognize \
  -H "Content-Type: application/json" \
  -d '{"query": "Ghana logging law"}'

# 测试3: 聊天
curl -X POST http://localhost:8000/api/dify/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "MENA restoration commitments"}'
```

## 📊 监控

### 查看日志

```bash
# 实时日志
docker-compose -f docker-compose.dify.yml logs -f

# 只看后端
docker-compose -f docker-compose.dify.yml logs -f geoglichatbot-backend
```

### 健康检查

```bash
# 持续监控
watch -n 5 'curl -s http://localhost:8000/api/dify/health | jq'
```

## 🚀 生产部署

### 使用Nginx反向代理

```nginx
location /api/geoglichatbot/ {
    proxy_pass http://localhost:8000/api/dify/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 使用Caddy (自动HTTPS)

```bash
caddy reverse-proxy --from api.yourdomain.com --to localhost:8000
```

### Docker Swarm / Kubernetes

参考 `DIFY_INTEGRATION.md` 中的高级部署配置

## 🔒 安全建议

1. **启用HTTPS** - 生产环境必须使用HTTPS
2. **API认证** - 添加API Key验证
3. **速率限制** - 防止滥用
4. **输入验证** - 已实现查询长度限制

## 🐛 故障排查

### 问题: 连接被拒绝

```bash
# 检查服务状态
docker ps | grep geoglichatbot

# 检查端口
netstat -tuln | grep 8000
```

### 问题: BM25无结果

```bash
# 检查data目录
docker exec geoglichatbot-backend-dify ls -la /app/data

# 测试BM25
curl "http://localhost:8000/debug/bm25?q=Saudi+Arabia"
```

### 问题: CORS错误

更新 `docker-compose.dify.yml`:
```yaml
environment:
  - ALLOWED_ORIGINS=http://localhost:3000,https://your-dify.com
```

## 📚 文档

- **完整集成指南**: [DIFY_INTEGRATION.md](./DIFY_INTEGRATION.md)
- **工作流规范**: [DIFY_WORKFLOW_SPEC.md](./DIFY_WORKFLOW_SPEC.md)
- **项目README**: [README.md](./README.md)
- **API文档**: http://localhost:8000/docs

## 💡 示例查询

测试这些查询来验证系统:

1. **国家概况**: "Saudi Arabia wildfires"
2. **干旱趋势**: "China drought trends"
3. **法律查询**: "Ghana logging law 2020"
4. **区域承诺**: "MENA restoration commitments"

## 🤝 支持

- **查看日志**: `docker-compose -f docker-compose.dify.yml logs`
- **重启服务**: `docker-compose -f docker-compose.dify.yml restart`
- **停止服务**: `docker-compose -f docker-compose.dify.yml down`

---

**版本**: 1.0.0  
**更新**: 2025-11-28  
**许可**: MIT
