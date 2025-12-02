# Dify集成快速参考卡

## 🚀 一键启动

```bash
# Windows
start-dify-service.bat

# Linux/Mac
docker-compose -f docker-compose.dify.yml up -d
```

## 📡 API端点速查

| 端点 | 方法 | 用途 | 响应时间 |
|------|------|------|----------|
| `/api/dify/health` | GET | 健康检查 | <50ms |
| `/api/dify/chat` | POST | 主要问答 | 100-500ms |
| `/api/dify/recognize` | POST | 意图识别 | 50-200ms |

## 💻 Dify HTTP节点配置

### 聊天节点 (最简单)

```
URL: http://your-server:8000/api/dify/chat
Method: POST
Headers: Content-Type: application/json
Body:
{
  "query": "{{input.user_query}}"
}
Output: {{http_request.data.answer}}
```

### 意图识别节点

```
URL: http://your-server:8000/api/dify/recognize
Method: POST
Body:
{
  "query": "{{input.user_query}}"
}
Outputs:
  - {{http_request.data.domain}}
  - {{http_request.data.targets}}
  - {{http_request.data.iso3_codes}}
```

## 🧪 测试命令

```bash
# 1. 健康检查
curl http://localhost:8000/api/dify/health

# 2. 测试聊天
curl -X POST http://localhost:8000/api/dify/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Saudi Arabia drought"}'

# 3. 测试识别
curl -X POST http://localhost:8000/api/dify/recognize \
  -H "Content-Type: application/json" \
  -d '{"query": "Ghana logging law"}'

# 4. 运行完整测试
python test-dify-api.py
```

## 🔍 监控命令

```bash
# 查看日志
docker-compose -f docker-compose.dify.yml logs -f

# 查看状态
docker-compose -f docker-compose.dify.yml ps

# 重启服务
docker-compose -f docker-compose.dify.yml restart

# 停止服务
docker-compose -f docker-compose.dify.yml down
```

## 🎯 示例查询

| 查询 | 预期Domain | 预期结果 |
|------|-----------|----------|
| "Saudi Arabia wildfires" | country_profile | 沙特阿拉伯野火数据 |
| "China drought trends" | country_profile | 中国干旱趋势 |
| "Ghana logging law 2020" | legislation | 加纳伐木法律 |
| "MENA restoration commitments" | commitment | MENA地区恢复承诺 |

## 🔧 常用环境变量

```bash
# 必需
ALLOWED_ORIGINS=http://localhost:3000,https://your-dify.com

# 推荐
RAG_BM25_ENABLED=true
BM25_TOP_K=3

# 可选
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## 🐛 快速故障排查

| 问题 | 解决方案 |
|------|----------|
| 连接被拒绝 | `docker ps` 检查服务是否运行 |
| CORS错误 | 更新 `ALLOWED_ORIGINS` 环境变量 |
| 无搜索结果 | 检查 `backend/data/` 目录是否存在 |
| 响应慢 | 增加 `BM25_TOP_K` 或检查资源使用 |

## 📊 响应格式

### Chat响应
```json
{
  "answer": "答案文本",
  "metadata": {
    "intent": "ask.country",
    "latency_ms": 150,
    "source": "bm25"
  },
  "conversation_id": "session_123"
}
```

### Recognize响应
```json
{
  "targets": ["saudi arabia"],
  "domain": "country_profile",
  "section_hint": "stressors/fires",
  "iso3_codes": ["SAU"]
}
```

## 🔗 相关文档

- **完整指南**: [DIFY_INTEGRATION.md](./DIFY_INTEGRATION.md)
- **简明教程**: [README.DIFY.md](./README.DIFY.md)
- **工作流规范**: [DIFY_WORKFLOW_SPEC.md](./DIFY_WORKFLOW_SPEC.md)
- **API文档**: http://localhost:8000/docs

## 📞 支持

```bash
# 查看完整日志
docker-compose -f docker-compose.dify.yml logs --tail=100

# 进入容器调试
docker exec -it geoglichatbot-backend-dify bash

# 检查数据目录
docker exec geoglichatbot-backend-dify ls -la /app/data
```

---
**提示**: 将此文件打印或保存为书签,方便快速查阅!
