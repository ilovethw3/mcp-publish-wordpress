# 实施计划 v1.1：内容控制平台 (MCP)

本项目将通过一系列定义明确、循序渐进的编码任务来完成。每个任务都构建于前一个任务之上，并强调测试先行，确保项目稳定、可控地推进。

## 1. 后端基础与环境设置

- [ ] **1.1 创建项目初始文件结构**
  - **目标**: 建立符合设计文档 (`design.md` 3.1.1) 的项目目录结构。
  - **参考需求**: `Req. 5.1`

- [ ] **1.2 编写 Docker Compose 配置**
  - **目标**: 在 `docker-compose.yml` 中定义 `fastapi_app`, `postgres`, `nginx` 三个服务。
  - **参考需求**: 设计文档 `2. 系统架构`

- [ ] **1.3 编写 Dockerfile 和 Nginx 配置**
  - **目标**: 创建 `Dockerfile` 以容器化 FastAPI 应用，并编写 `nginx.conf` 实现反向代理。
  - **参考需求**: 设计文档 `2. 系统架构`

- [ ] **1.4 实现数据库模型**
  - **目标**: 在 `mcp/models/` 目录下，使用 SQLModel 创建 `User` 和 `Article` 两个模型。
  - **参考需求**: `Req. 2.3`, `Req. 3.4`

- [ ] **1.5 初始化 FastAPI 应用并配置数据库**
  - **目标**: 在 `main.py` 中创建 FastAPI 应用实例，并设置数据库会话管理。
  - **参考需求**: `Req. 5.1`

- [ ] **1.6 (新) 配置数据库迁移工具 (Alembic)**
  - **目标**: 在项目中集成 Alembic，配置好使其能识别 SQLModel 的模型变化。
  - **行动**:
    - `alembic init alembic`
    - 配置 `alembic.ini` 和 `env.py`。
    - 生成第一个迁移版本：`alembic revision --autogenerate -m "Create initial tables"`
    - 运行迁移以创建表：`alembic upgrade head`
  - **参考需求**: `Req. 5.1`

- [ ] **1.7 (新) 在 FastAPI 中配置 CORS 中间件**
  - **目标**: 在 `main.py` 中添加 `CORSMiddleware`，以允许前端应用的跨域请求。
  - **细节**: 从 `.env` 文件中读取 `FRONTEND_CORS_ORIGINS` 并进行配置。
  - **参考需求**: 设计文档 `3.2 前端组件`

## 2. 用户认证 (JWT)

- [ ] **2.1 实现密码哈希与验证功能**
  - **目标**: 在 `mcp/core/security.py` 中，使用 `passlib` 库创建 `verify_password` 和 `get_password_hash` 两个函数。
  - **测试**: 编写单元测试，确保密码哈希和验证功能按预期工作。
  - **参考需求**: `Req. 2.3`

- [ ] **2.2 实现 JWT Token 创建与解码功能**
  - **目标**: 在 `mcp/core/security.py` 中，使用 `python-jose` 库创建生成和解码JWT的函数。
  - **参考需求**: `Req. 2.1`, `Req. 2.2`

- [ ] **2.3 创建用户认证 API 端点**
  - **目标**: 在 `mcp/api/v1/auth.py` 中，创建 `POST /token` 端点。
  - **测试**: 编写集成测试，覆盖成功登录、密码错误、用户不存在等场景。
  - **参考需求**: `Req. 2.1`

- [ ] **2.4 创建依赖注入函数以保护路由**
  - **目标**: 在 `mcp/core/security.py` 中创建一个依赖函数 `get_current_user`，用于验证 JWT 并返回用户对象。
  - **参考需求**: `Req. 2.2`

- [ ] **2.5 (新) 创建初始用户脚本**
  - **目标**: 编写一个可通过命令行执行的简单脚本，用于创建第一个管理员用户。
  - **参考需求**: `Req. 2.1`

## 3. 核心文章功能

- [ ] **3.1 实现 Agent 提交文章的 API 端点**
  - **目标**: 在 `mcp/api/v1/articles.py` 中创建 `POST /submit` 端点，并使用 API Key 进行保护。
  - **测试**: 编写集成测试，覆盖成功提交、API Key 错误、数据格式错误等场景。
  - **参考需求**: `Req. 1.1`, `Req. 1.2`, `Req. 1.3`

- [ ] **3.2 实现获取文章列表的 API 端点**
  - **目标**: 在 `mcp/api/v1/articles.py` 中创建 `GET /` 端点，并实现搜索与排序。
  - **测试**: 编写集成测试，确保 JWT 保护、搜索和排序功能正常工作。
  - **参考需求**: `Req. 3.1`, `Req. 3.2`

- [ ] **3.3 实现文章详情、编辑和删除的 API 端点**
  - **目标**: 在 `mcp/api/v1/articles.py` 中创建 `GET /{id}`, `PUT /{id}`, `DELETE /{id}` 端点。
  - **测试**: 编写集成测试，验证权限和正确的数据库操作。
  - **参考需求**: `Req. 3.3`, `Req. 3.5`

## 4. WordPress 集成与发布流程

- [ ] **4.1 创建 WordPress 客户端服务**
  - **目标**: 在 `mcp/core/wordpress_client.py` 中创建一个 `WordPressClient` 类。
  - **测试**: 编写单元测试（可使用 `pytest-mock` 模拟 `requests`），验证与 WordPress API 的交互逻辑。
  - **参考需求**: `Req. 4.1`

- [ ] **4.2 实现批准与重试发布的 API 端点**
  - **目标**: 创建 `POST /{id}/approve` 和 `POST /{id}/retry` 端点。
  - **测试**: 编写集成测试，模拟成功和失败的发布场景，并验证文章状态的正确变化。
  - **参考需求**: `Req. 3.4`, `Req. 4.3`

## 5. 前端开发 (Vue.js)

- [ ] **5.1 初始化 Vue.js 项目并设置 API 客户端**
  - **目标**: 使用 Vite 创建 Vue.js 项目，安装 Axios，并设置好包含拦截器的 `apiClient.js`。
  - **参考需求**: 设计文档 `3.2 前端组件`

- [ ] **5.2 创建登录页面**
  - **目标**: 创建 `Login.vue` 视图，实现登录逻辑和 UI 状态反馈（按钮禁用等）。
  - **参考需求**: `Req. 2.1`

- [ ] **5.3 创建仪表盘页面以展示文章列表**
  - **目标**: 创建 `Dashboard.vue` 视图，实现文章列表的获取、展示、搜索和排序。
  - **参考需求**: `Req. 3.1`, `Req. 3.2`

- [ ] **5.4 创建文章详情/编辑页面**
  - **目标**: 创建 `ArticleDetail.vue` 视图，实现文章的查看、编辑、批准、拒绝和重试功能。
  - **参考需求**: `Req. 3.3`, `Req. 3.4`, `Req. 3.5`, `Req. 4.3`
