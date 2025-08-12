# Nginx服务已移除说明

## 📝 变更说明

在MCP WordPress Publisher v2.1系统中，我们已经移除了Nginx反向代理服务，以简化架构并提高性能。

## 🔄 架构变更

### 之前的架构 (7个服务)
1. PostgreSQL Database
2. Redis Cache  
3. MCP Server
4. Web UI
5. **Nginx Reverse Proxy** ❌ (已移除)
6. Prometheus
7. Grafana

### 现在的架构 (6个服务)
1. PostgreSQL Database (直接访问端口5433)
2. Redis Cache (直接访问端口6380)
3. MCP Server (直接访问端口8000)
4. Web UI (直接访问端口3000)
5. Prometheus (直接访问端口9090)
6. Grafana (直接访问端口3001)

## 🚀 访问方式变更

### 直接访问端口
- **Web管理界面**: http://localhost:3000
- **MCP Server API**: http://localhost:8000
- **SSE实时更新**: http://localhost:8000/sse
- **Prometheus监控**: http://localhost:9090
- **Grafana仪表板**: http://localhost:3001

### 服务间通信
- Web UI到MCP Server的API调用通过Docker内部网络: `http://mcp-server:8000`
- 所有服务间通信都通过Docker内部网络进行

## ✅ 移除Nginx的好处

1. **简化架构**: 减少一个服务层，降低系统复杂性
2. **提高性能**: 减少请求转发跳转，直接访问服务
3. **降低资源消耗**: 节省内存和CPU资源
4. **更快启动**: 减少服务依赖，系统启动更快
5. **便于开发调试**: 直接访问服务，调试更方便
6. **减少故障点**: 减少一个可能出错的组件

## ⚠️ 注意事项

### HTTPS支持
如果需要HTTPS，可以在应用层配置：
- **MCP Server**: FastAPI原生支持HTTPS
- **Web UI**: Next.js可以配置HTTPS

### 生产环境建议
如果在生产环境需要以下功能，可以在外部添加负载均衡器：
- SSL/TLS终端处理
- 负载均衡和高可用
- 静态文件缓存
- 安全过滤和防护

### CORS配置
Web UI和MCP Server之间的通信已经通过Docker内部网络处理，无需额外的CORS配置。

## 🔧 如果需要恢复Nginx

如果将来需要恢复Nginx，可以参考 `nginx/` 目录中的配置文件，并在docker-compose中添加相应的服务定义。

## 📊 性能提升

通过移除Nginx代理层：
- **减少延迟**: 消除反向代理的转发延迟
- **简化网络**: 减少网络跳转和端口映射
- **降低资源**: 节省约100-200MB内存占用
- **提高吞吐**: 直接连接提高数据传输效率