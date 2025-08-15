### 交互时尽量使用中文
### 有代码规范的需求，使用context7

### python环境变量
source /home/tian/claudecode/mcp-publish-wordpress/venv_mcp_publish_wordpress/bin/activate

### 开发阶段数据库启动命令
docker-compose up -d postgres redis

### 开发阶段web启动命令
cd web-ui/ && npm run dev

### 开发阶段mcp启动命令
source venv_mcp_publish_wordpress/bin/activate && python -m mcp_wordpress.server sse