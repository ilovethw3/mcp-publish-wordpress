# 实施计划：MCP WordPress发布服务器 v2.0

本实施计划将现有REST API系统重构为符合Model Context Protocol标准的MCP服务器。每个任务构建于前一个任务之上，采用测试驱动开发，确保代码质量和MCP协议兼容性。

## 1. MCP基础架构重构

- [ ] **1.1 安装MCP Python SDK依赖**
  - 添加`mcp`包到requirements.txt
  - 更新项目依赖管理配置
  - 参考需求：Req. 2.1.1 - MCP协议通信支持

- [ ] **1.2 创建MCP服务器主入口**
  - 重写`mcp/main.py`使用FastMCP而非FastAPI
  - 实现基础的服务器初始化和能力声明
  - 添加stdio传输支持
  - 参考需求：Req. 2.1.2 - 服务器能力声明

- [ ] **1.3 实现MCP协议握手和初始化**
  - 实现initialize/initialized消息处理
  - 配置服务器能力（tools, resources, prompts, logging）
  - 添加协议版本协商
  - 参考需求：Req. 2.10.1 - initialize请求处理

- [ ] **1.4 编写MCP连接测试**
  - 创建基础的MCP客户端连接测试
  - 验证JSON-RPC 2.0消息格式
  - 测试能力协商流程
  - 参考需求：Req. 2.1.1, 2.1.2

## 2. 核心Tools实现

- [ ] **2.1 实现submit_article Tool**
  - 在`mcp_wordpress/tools/articles.py`中实现文章提交Tool
  - 定义Tool schema和参数验证
  - 实现文章数据存储逻辑
  - 编写Tool功能测试
  - 参考需求：Req. 2.2.1 - 文章提交Tool

- [ ] **2.2 实现list_articles Tool**
  - 实现文章列表查询Tool，支持状态过滤
  - 添加搜索和分页功能
  - 实现Tool输出格式标准化
  - 编写列表查询测试
  - 参考需求：Req. 2.2.2 - 文章列表Tool

- [ ] **2.3 实现get_article_status Tool**
  - 实现单篇文章状态查询Tool
  - 返回详细的文章信息和发布状态
  - 包含WordPress发布错误信息
  - 编写状态查询测试
  - 参考需求：Req. 2.2.5 - 文章状态Tool

- [ ] **2.4 实现approve_article Tool**
  - 实现文章批准和WordPress发布Tool
  - 集成现有的WordPress发布逻辑
  - 实现异步发布状态更新
  - 编写批准流程测试
  - 参考需求：Req. 2.2.3 - 文章批准Tool

- [ ] **2.5 实现reject_article Tool**
  - 实现文章拒绝Tool，包含拒绝原因
  - 更新文章状态为rejected
  - 记录审核员操作日志
  - 编写拒绝流程测试
  - 参考需求：Req. 2.2.4 - 文章拒绝Tool

## 3. Resources数据暴露

- [ ] **3.1 实现文章数据Resources**
  - 创建`mcp_wordpress/resources/articles.py`
  - 实现article://pending, article://{id}, article://published Resources
  - 支持Resources订阅和变更通知
  - 编写Resources访问测试
  - 参考需求：Req. 2.3.1, 2.3.2 - 文章数据Resources

- [ ] **3.2 实现系统状态Resources**
  - 实现wordpress://config Resource暴露WordPress配置
  - 实现stats://summary Resource提供统计数据
  - 添加stats://performance Resource显示性能指标
  - 编写系统状态Resources测试
  - 参考需求：Req. 2.3.3, 2.3.4 - 系统状态Resources

- [ ] **3.3 实现Resources变更通知**
  - 实现Resources订阅机制
  - 在文章状态变更时发送通知
  - 支持客户端实时状态更新
  - 编写变更通知测试
  - 参考需求：Req. 2.1.2 - capabilities中的subscribe支持

## 4. Prompts模板系统

- [ ] **4.1 实现article_template Prompt**
  - 创建`mcp_wordpress/prompts/templates.py`
  - 实现文章模板生成Prompt，支持主题和受众参数
  - 提供最佳实践的文章结构模板
  - 编写Prompt生成测试
  - 参考需求：Req. 2.4.1 - 文章模板Prompt

- [ ] **4.2 实现review_checklist Prompt**
  - 实现审核清单生成Prompt
  - 根据内容类型生成相应的审核标准
  - 支持自定义审核规则
  - 编写清单生成测试
  - 参考需求：Req. 2.4.2 - 审核清单Prompt

- [ ] **4.3 实现wordpress_formatting Prompt**
  - 实现WordPress格式化指南Prompt
  - 提供WordPress特定的内容格式建议
  - 包含SEO和可读性优化建议
  - 编写格式化指南测试
  - 参考需求：Req. 2.4.3 - WordPress格式化Prompt

## 5. 传输层扩展

- [ ] **5.1 实现SSE传输支持**
  - 添加Server-Sent Events传输实现
  - 配置HTTP端点用于SSE连接
  - 实现WebSocket-like的双向通信
  - 编写SSE传输测试
  - 参考需求：Req. 2.5.2 - SSE传输支持

- [ ] **5.2 实现传输层配置**
  - 添加环境变量控制传输方式选择
  - 实现传输层工厂模式
  - 支持运行时传输配置切换
  - 编写传输配置测试
  - 参考需求：Req. 2.5.3 - 传输方式配置

- [ ] **5.3 实现连接管理**
  - 添加连接状态跟踪
  - 实现优雅的连接断开处理
  - 支持连接重试机制
  - 编写连接管理测试
  - 参考需求：Req. 2.5.4 - 连接清理

## 6. 认证系统迁移

- [ ] **6.1 适配现有认证到MCP**
  - 将现有JWT认证逻辑适配到MCP Tools
  - 实现API密钥验证中间件
  - 保持现有密码哈希兼容性
  - 编写认证适配测试
  - 参考需求：Req. 2.7.1, 2.7.2 - MCP认证机制

- [ ] **6.2 实现MCP安全Tools**
  - 创建用户管理相关的MCP Tools
  - 实现权限验证中间件
  - 添加安全审计日志
  - 编写安全功能测试
  - 参考需求：Req. 2.7.3, 2.7.4 - 安全验证

## 7. 错误处理重构

- [ ] **7.1 实现JSON-RPC 2.0错误处理**
  - 将现有HTTP错误转换为JSON-RPC错误格式
  - 实现标准错误码映射
  - 添加详细的错误数据结构
  - 编写错误处理测试
  - 参考需求：Req. 2.8.1 - JSON-RPC错误响应

- [ ] **7.2 实现MCP日志系统**
  - 集成MCP协议的日志功能
  - 实现结构化日志记录
  - 添加操作审计跟踪
  - 编写日志功能测试
  - 参考需求：Req. 2.8.2, 2.8.3 - 详细日志记录

## 8. WordPress集成适配

- [ ] **8.1 重构WordPress客户端为异步**
  - 将现有WordPressClient转换为async/await模式
  - 保持现有发布逻辑兼容性
  - 优化错误处理和重试机制
  - 编写异步客户端测试
  - 参考需求：Req. 2.6.1, 2.6.2 - WordPress发布集成

- [ ] **8.2 实现WordPress状态同步**
  - 实现文章状态与WordPress同步机制
  - 添加发布失败恢复逻辑
  - 支持重试发布功能
  - 编写状态同步测试
  - 参考需求：Req. 2.6.3, 2.6.4 - 发布状态管理

## 9. 配置管理重构

- [ ] **9.1 更新环境变量配置**
  - 添加MCP特定的配置项
  - 重构Settings类支持MCP传输配置
  - 更新.env.example文件
  - 编写配置加载测试
  - 参考需求：Req. 2.9.1, 2.9.2, 2.9.3 - 环境配置

- [ ] **9.2 实现配置验证**
  - 添加启动时配置验证
  - 实现配置错误提示
  - 支持配置热重载（部分）
  - 编写配置验证测试
  - 参考需求：Req. 2.9.4 - 配置错误提示

## 10. 协议兼容性验证

- [ ] **10.1 实现MCP协议测试套件**
  - 创建完整的MCP协议兼容性测试
  - 验证tools/list, resources/list, prompts/list响应格式
  - 测试JSON-RPC 2.0消息格式合规性
  - 编写协议兼容性测试
  - 参考需求：Req. 2.10.2, 2.10.3, 2.10.4, 2.10.5

- [ ] **10.2 集成MCP客户端测试**
  - 使用标准MCP客户端测试服务器
  - 验证与多种MCP客户端的兼容性
  - 测试长时间连接稳定性
  - 编写客户端兼容性测试
  - 参考需求：Req. 2.10 - MCP协议兼容性

## 11. 部署配置更新

- [ ] **11.1 更新Docker配置**
  - 修改Dockerfile支持MCP服务器运行
  - 更新docker-compose.yml配置传输方式
  - 移除Nginx配置（MCP不需要HTTP代理）
  - 编写容器化部署测试
  - 参考设计：设计文档第7节 - 部署架构

- [ ] **11.2 创建MCP客户端连接示例**
  - 编写Python MCP客户端连接示例
  - 创建CLI工具用于测试MCP服务器
  - 提供不同传输方式的连接示例
  - 编写客户端示例测试
  - 参考设计：设计文档第17节 - 部署策略

## 12. 测试套件完善

- [ ] **12.1 重构现有测试为MCP格式**
  - 将现有API测试转换为MCP Tool测试
  - 更新测试基础设施支持MCP客户端
  - 重写所有集成测试
  - 参考设计：设计文档第16节 - 测试架构

- [ ] **12.2 实现端到端MCP工作流测试**
  - 测试完整的文章提交→审核→发布流程
  - 验证多客户端并发操作
  - 测试异常恢复和重试机制
  - 参考需求：覆盖所有主要用户故事

## 13. 文档和示例更新

- [ ] **13.1 更新README.md为MCP使用说明**
  - 重写README文档说明MCP服务器用法
  - 提供MCP客户端连接示例
  - 更新部署和配置说明
  - 参考设计：设计文档第17节 - 部署策略

- [ ] **13.2 创建MCP工具和资源使用指南**
  - 编写所有Tools的使用示例
  - 提供Resources访问指南
  - 创建Prompts使用教程
  - 更新CLAUDE.md为MCP开发指南

## 14. 性能优化和监控

- [ ] **14.1 实现MCP性能监控**
  - 添加JSON-RPC消息处理时间统计
  - 实现Tool调用频率监控
  - 添加连接状态跟踪
  - 编写性能监控测试
  - 参考设计：设计文档第10.1节 - MCP协议监控

- [ ] **14.2 优化异步处理性能**
  - 优化数据库查询性能
  - 实现Resource缓存机制
  - 添加后台任务队列
  - 编写性能基准测试
  - 参考设计：设计文档第9节 - 性能考虑

## 15. 最终验证和清理

- [ ] **15.1 完整MCP协议兼容性验证**
  - 使用官方MCP测试工具验证兼容性
  - 测试与标准MCP客户端的互操作性
  - 验证所有协议要求的符合性
  - 参考需求：Req. 2.10 - MCP协议兼容性

- [ ] **15.2 清理废弃的REST API代码**
  - 移除不再需要的FastAPI路由
  - 删除HTTP相关的中间件和配置
  - 清理废弃的测试代码
  - 更新项目结构文档
  - 确保向MCP的完全迁移

- [ ] **15.3 最终部署测试**
  - 测试完整的Docker Compose部署
  - 验证MCP服务器在容器环境中的运行
  - 测试不同传输方式的部署配置
  - 编写部署验证脚本