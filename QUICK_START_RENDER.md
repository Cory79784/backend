# 🚀 GeoGLI Chatbot - Render部署快速开始

> 10分钟内完成从本地到云端的部署!

## ⚡ 超快速部署 (3步)

### 步骤1: 推送到GitHub (2分钟)

**Windows用户**:
```cmd
deploy-to-github.bat
```

**Mac/Linux用户**:
```bash
python deploy-to-github.py
```

### 步骤2: 在Render创建服务 (5分钟)

1. 访问 https://render.com 并用GitHub登录
2. 点击 "New +" → "Web Service"
3. 选择 `Cory79784/backend` 仓库
4. 点击 "Apply" (Render会自动检测render.yaml)
5. 等待部署完成

### 步骤3: 测试API (1分钟)

```bash
# 替换为你的Render URL
curl https://geoglichatbot-backend.onrender.com/api/dify/health
```

## ✅ 完成!

你的API现在已经在线:
```
https://geoglichatbot-backend.onrender.com
```

## 📡 API端点

### 1. 健康检查
```bash
GET https://geoglichatbot-backend.onrender.com/api/dify/health
```

### 2. 聊天接口
```bash
curl -X POST https://geoglichatbot-backend.onrender.com/api/dify/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Saudi Arabia drought"}'
```

### 3. 意图识别
```bash
curl -X POST https://geoglichatbot-backend.onrender.com/api/dify/recognize \
  -H "Content-Type: application/json" \
  -d '{"query": "Saudi Arabia wildfires"}'
```

## 🔗 在Dify中使用

### HTTP Request节点配置

```json
{
  "url": "https://geoglichatbot-backend.onrender.com/api/dify/chat",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "query": "{{input.user_query}}"
  }
}
```

### 输出变量

- `{{http_request.data.answer}}` - 答案文本
- `{{http_request.data.metadata}}` - 元数据
- `{{http_request.data.conversation_id}}` - 会话ID

## 📊 请求/响应示例

### 请求
```json
{
  "query": "What are the drought trends in Saudi Arabia?",
  "user": "test_user"
}
```

### 响应
```json
{
  "event": "message",
  "message_id": "msg_1732838400123",
  "conversation_id": "session_abc123",
  "answer": "根据GeoGLI数据显示,沙特阿拉伯的干旱趋势...",
  "metadata": {
    "intent": "ask.country",
    "latency_ms": 156,
    "source": "bm25"
  },
  "created_at": 1732838400
}
```

## 🔧 常见问题

### Q: 服务休眠了怎么办?

Render免费计划15分钟无活动会休眠。首次请求需要30-60秒唤醒。

**解决方案**: 使用UptimeRobot保持活跃
1. 访问 https://uptimerobot.com
2. 添加HTTP监控
3. URL: `https://your-service.onrender.com/api/dify/health`
4. 间隔: 5分钟

### Q: 如何查看日志?

在Render Dashboard:
1. 选择你的服务
2. 点击 "Logs" 标签
3. 查看实时日志

### Q: 如何更新代码?

```bash
# 本地修改后
git add .
git commit -m "Update"
git push origin main

# Render会自动重新部署
```

## 📚 完整文档

- **API文档**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **部署指南**: [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md)
- **Dify集成**: [DIFY_INTEGRATION.md](./DIFY_INTEGRATION.md)

## 🎯 测试查询

试试这些查询:

1. "Saudi Arabia wildfires"
2. "China drought trends"
3. "Ghana logging law 2020"
4. "MENA restoration commitments"

## 💡 提示

- ✅ Render自动提供HTTPS
- ✅ 免费计划有750小时/月
- ✅ 支持自动部署
- ⚠️ 15分钟无活动会休眠
- ⚠️ 512MB RAM限制

## 🆘 需要帮助?

查看完整文档或在GitHub提Issue:
https://github.com/Cory79784/backend/issues

---

**快速开始版本**: 1.0.0  
**更新时间**: 2025-11-28
