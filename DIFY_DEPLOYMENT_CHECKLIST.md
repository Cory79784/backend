# GeoGLI Chatbot - Dify集成部署检查清单

## 📋 部署前检查

### 环境准备

- [ ] Docker已安装并运行
  ```bash
  docker --version
  docker info
  ```

- [ ] Docker Compose已安装
  ```bash
  docker-compose --version
  ```

- [ ] Git已安装(用于克隆项目)
  ```bash
  git --version
  ```

- [ ] curl或wget可用(用于测试API)
  ```bash
  curl --version
  ```

### 项目文件

- [ ] 项目已克隆到本地
  ```bash
  git clone <repo-url>
  cd GeoGLI-Chatbot
  ```

- [ ] 必需文件存在:
  - [ ] `docker-compose.dify.yml`
  - [ ] `backend/app/routes/dify.py`
  - [ ] `backend/requirements.txt`
  - [ ] `backend/Dockerfile`

- [ ] 数据文件存在:
  - [ ] `backend/data/` 目录
  - [ ] `backend/corpus/` 目录(BM25索引)

### 配置文件

- [ ] 环境变量已配置
  ```bash
  # 检查或创建 .env 文件
  cat backend/.env
  ```

- [ ] CORS配置正确
  ```bash
  # 在 docker-compose.dify.yml 中
  ALLOWED_ORIGINS=http://localhost:3000,https://your-dify.com
  ```

- [ ] 端口未被占用
  ```bash
  # Windows
  netstat -ano | findstr :8000
  
  # Linux/Mac
  lsof -i :8000
  ```

## 🚀 部署步骤

### 1. 启动服务

- [ ] 停止旧容器(如果存在)
  ```bash
  docker-compose -f docker-compose.dify.yml down
  ```

- [ ] 构建并启动服务
  ```bash
  docker-compose -f docker-compose.dify.yml up -d --build
  ```

- [ ] 检查容器状态
  ```bash
  docker-compose -f docker-compose.dify.yml ps
  ```
  
  预期输出:
  ```
  NAME                          STATUS    PORTS
  geoglichatbot-backend-dify    Up        0.0.0.0:8000->8000/tcp
  ```

### 2. 验证服务

- [ ] 健康检查通过
  ```bash
  curl http://localhost:8000/api/dify/health
  ```
  
  预期响应:
  ```json
  {
    "status": "ok",
    "service": "GeoGLI-Chatbot-Dify",
    "version": "1.0.0",
    "bm25_enabled": true
  }
  ```

- [ ] API文档可访问
  ```bash
  # 在浏览器中打开
  http://localhost:8000/docs
  ```

- [ ] 测试聊天端点
  ```bash
  curl -X POST http://localhost:8000/api/dify/chat \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}'
  ```

- [ ] 测试识别端点
  ```bash
  curl -X POST http://localhost:8000/api/dify/recognize \
    -H "Content-Type: application/json" \
    -d '{"query": "Saudi Arabia"}'
  ```

### 3. 运行自动化测试

- [ ] 安装测试依赖
  ```bash
  pip install requests
  ```

- [ ] 运行测试脚本
  ```bash
  python test-dify-api.py
  ```

- [ ] 所有测试通过
  ```
  ✅ All tests passed! The API is ready for Dify integration.
  ```

## 🔗 Dify集成

### 1. 获取服务URL

- [ ] 确定服务访问URL
  - 本地开发: `http://localhost:8000`
  - 生产环境: `https://your-domain.com`

- [ ] 测试从Dify服务器到GeoGLI的连接
  ```bash
  # 在Dify服务器上运行
  curl http://your-geoglichatbot-server:8000/api/dify/health
  ```

### 2. 配置Dify工作流

- [ ] 创建新的Dify工作流

- [ ] 添加Start节点
  - 输入变量: `user_query` (string)

- [ ] 添加HTTP Request节点
  - Name: `GeoGLI Chat`
  - Method: `POST`
  - URL: `http://your-server:8000/api/dify/chat`
  - Headers: `Content-Type: application/json`
  - Body:
    ```json
    {
      "query": "{{input.user_query}}"
    }
    ```

- [ ] 添加Answer节点
  - Output: `{{http_request.data.answer}}`

- [ ] 保存工作流

### 3. 测试Dify工作流

- [ ] 在Dify中测试工作流
  - 输入: "Saudi Arabia drought"
  - 预期: 返回相关答案

- [ ] 测试多个查询
  - [ ] "China wildfires"
  - [ ] "Ghana logging law"
  - [ ] "MENA restoration"

- [ ] 检查响应时间
  - 预期: < 1秒

## 🔒 安全配置

### 生产环境必需

- [ ] 启用HTTPS
  ```bash
  # 使用Caddy
  caddy reverse-proxy --from api.yourdomain.com --to localhost:8000
  
  # 或使用Nginx + Let's Encrypt
  certbot --nginx -d api.yourdomain.com
  ```

- [ ] 配置防火墙
  ```bash
  # 只允许必要的端口
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw deny 8000/tcp  # 不直接暴露后端端口
  ```

- [ ] 更新CORS配置
  ```yaml
  # docker-compose.dify.yml
  environment:
    - ALLOWED_ORIGINS=https://your-dify-instance.com
  ```

### 可选安全措施

- [ ] 添加API Key认证
  ```python
  # 在 dify.py 中添加
  X-API-Key: your-secret-key
  ```

- [ ] 配置速率限制
  ```python
  # 使用 slowapi
  @limiter.limit("10/minute")
  ```

- [ ] 启用请求日志
  ```yaml
  # docker-compose.dify.yml
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  ```

## 📊 监控设置

### 基础监控

- [ ] 配置健康检查
  ```bash
  # 添加到crontab
  */5 * * * * curl -f http://localhost:8000/api/dify/health || echo "Service down"
  ```

- [ ] 设置日志查看
  ```bash
  # 创建日志查看别名
  alias logs='docker-compose -f docker-compose.dify.yml logs -f'
  ```

### 高级监控(可选)

- [ ] 安装Prometheus
  ```yaml
  # docker-compose.monitoring.yml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  ```

- [ ] 安装Grafana
  ```yaml
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
  ```

- [ ] 配置告警
  - Email通知
  - Slack通知
  - PagerDuty集成

## 🧪 性能测试

### 负载测试

- [ ] 安装测试工具
  ```bash
  pip install locust
  ```

- [ ] 运行负载测试
  ```bash
  locust -f load_test.py --host=http://localhost:8000
  ```

- [ ] 验证性能指标
  - [ ] 平均响应时间 < 500ms
  - [ ] 95th百分位 < 1000ms
  - [ ] 错误率 < 1%

### 压力测试

- [ ] 测试并发请求
  ```bash
  # 使用ab (Apache Bench)
  ab -n 1000 -c 10 http://localhost:8000/api/dify/health
  ```

- [ ] 记录结果
  - Requests per second: ___
  - Time per request: ___
  - Failed requests: ___

## 📚 文档检查

### 内部文档

- [ ] README.DIFY.md 已更新
- [ ] DIFY_INTEGRATION.md 已审阅
- [ ] API端点已记录
- [ ] 环境变量已记录

### 团队培训

- [ ] 团队成员了解部署流程
- [ ] 故障排查指南已分享
- [ ] 监控仪表板访问权限已配置
- [ ] 紧急联系人已确定

## 🔄 备份和恢复

### 备份

- [ ] 数据库备份
  ```bash
  docker exec geoglichatbot-backend-dify \
    sqlite3 /app/chatbot.db ".backup /app/backup.db"
  ```

- [ ] 配置文件备份
  ```bash
  tar -czf config-backup.tar.gz \
    docker-compose.dify.yml \
    backend/.env
  ```

- [ ] 数据文件备份
  ```bash
  tar -czf data-backup.tar.gz backend/data/
  ```

### 恢复测试

- [ ] 测试从备份恢复
  ```bash
  docker-compose -f docker-compose.dify.yml down
  # 恢复文件
  docker-compose -f docker-compose.dify.yml up -d
  ```

## 📝 上线检查清单

### 最终验证

- [ ] 所有测试通过
- [ ] 性能指标达标
- [ ] 安全配置完成
- [ ] 监控已设置
- [ ] 备份已配置
- [ ] 文档已更新
- [ ] 团队已培训

### 上线步骤

1. [ ] 通知相关团队
2. [ ] 在Dify中更新API URL
3. [ ] 执行最终测试
4. [ ] 监控初始流量
5. [ ] 记录上线时间和版本

### 上线后

- [ ] 监控错误日志(前24小时)
- [ ] 检查性能指标
- [ ] 收集用户反馈
- [ ] 记录遇到的问题
- [ ] 更新文档(如需要)

## 🐛 故障排查清单

### 常见问题

- [ ] 服务无法启动
  - 检查Docker是否运行
  - 检查端口是否被占用
  - 查看容器日志

- [ ] API返回错误
  - 检查请求格式
  - 查看后端日志
  - 验证CORS配置

- [ ] 响应慢
  - 检查BM25索引
  - 查看资源使用
  - 优化查询

- [ ] Dify无法连接
  - 验证网络连接
  - 检查CORS配置
  - 测试URL可访问性

### 紧急联系

- 技术负责人: _______________
- 运维团队: _______________
- Dify支持: _______________

## ✅ 签署确认

部署完成后,请确认:

- [ ] 我已完成所有必需的检查项
- [ ] 服务运行正常
- [ ] 监控已配置
- [ ] 团队已通知

**部署人员**: _______________  
**部署日期**: _______________  
**服务版本**: 1.0.0  
**签名**: _______________

---

**检查清单版本**: 1.0.0  
**最后更新**: 2025-11-28
