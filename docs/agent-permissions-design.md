# AI Agent权限控制设计方案

**类型**: AI Agent权限管理系统  
**日期**: 2025-08-15  
**状态**: 已实施

## 重要说明

本文档定义了MCP WordPress发布系统中AI Agent的权限控制体系。该系统专注于基于现有MCP工具的实际权限需求，提供实用且可扩展的权限管理方案。

## 目录

1. [现状分析](#现状分析)
2. [Agent权限模型设计](#agent权限模型设计)
3. [角色模板系统](#角色模板系统)
4. [技术实现方案](#技术实现方案)
5. [Web UI权限管理](#web-ui权限管理)
6. [实施状态](#实施状态)
7. [技术参考](#技术参考)

## 现状分析

### 1.1 当前可用的MCP Tools

基于实际实现的MCP工具，系统支持以下操作：

**文章操作类工具**:
- `submit_article()` - 提交新文章
- `list_articles()` - 查看文章列表 
- `get_article_status()` - 获取文章状态详情
- `edit_article()` - 编辑文章内容

**工作流操作类工具**:
- `approve_article()` - 审批文章（原名approve_article_only已更名）
- `publish_article()` - 发布文章到WordPress
- `reject_article()` - 拒绝文章

**系统信息类工具**:
- `list_agents()` - 查看代理列表
- `list_sites()` - 查看站点列表
- `get_agent_stats()` - 获取代理统计
- `get_site_health()` - 获取站点健康状态

### 1.2 权限控制需求

**安全性需求**:
- 不同Agent应具有不同的操作权限
- 防止Agent执行未授权操作
- 支持细粒度的权限控制

**管理性需求**:
- 支持角色模板快速分配权限
- 支持权限的个性化覆盖
- 支持配额和时间限制

**可扩展性需求**:
- 权限体系易于扩展
- 支持新工具的权限集成
- 权限检查性能良好

## Agent权限模型设计

### 2.1 基于实际Tools的权限分类

#### **基于实际MCP工具的权限分类**

根据当前实际实现的MCP工具，权限系统包含以下权限类型：

```python
# 文章操作权限
"can_submit_articles": bool,           # 提交新文章 (submit_article)
"can_edit_own_articles": bool,         # 编辑自己提交的文章 (edit_article)
"can_edit_others_articles": bool,      # 编辑其他Agent的文章 (edit_article)

# 工作流权限
"can_approve_articles": bool,          # 审批文章 (approve_article)
"can_publish_articles": bool,          # 发布文章到WordPress (publish_article)

# 查看权限
"can_view_statistics": bool,           # 查看统计信息 (list_articles, get_article_status)

# 内容限制权限
"allowed_categories": List[str],       # 允许的文章分类
"allowed_tags": List[str],            # 允许的文章标签

# 特殊权限
"can_review_agents": List[str],        # 可审核的Agent列表（预留）
```

### 2.2 权限检查逻辑层次

```
┌─────────────────────────────────────────────────────────────────┐
│                    权限检查分层架构                                │
├─────────────────────────────────────────────────────────────────┤
│ 1. 基础权限检查                                                   │
│    └─ 验证Agent是否具有执行特定操作的基本权限                        │
├─────────────────────────────────────────────────────────────────┤
│ 2. 所有权验证                                                     │
│    └─ 对于edit_own_articles权限，验证文章所有权                    │
├─────────────────────────────────────────────────────────────────┤
│ 3. 内容限制检查                                                   │
│    └─ 验证分类和标签是否在允许范围内                               │
├─────────────────────────────────────────────────────────────────┤
│ 4. 配额检查                                                       │
│    └─ 验证是否超出日/月配额限制                                    │
├─────────────────────────────────────────────────────────────────┤
│ 5. 工作时间检查                                                   │
│    └─ 验证是否在允许的工作时间内                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 配额和时间限制

#### **配额类型**
```python
class QuotaLimits:
    daily_articles: int = 0           # 每日文章数限制，0表示无限制
    monthly_articles: int = 0         # 每月文章数限制，0表示无限制
    max_article_length: int = 50000   # 文章长度限制（字符数）
```

#### **工作时间控制**
```python
class WorkingHours:
    enabled: bool = False             # 是否启用时间限制
    start: str = "09:00"              # 工作开始时间
    end: str = "18:00"                # 工作结束时间
    timezone: str = "Asia/Shanghai"   # 时区
    working_days: List[int] = [1,2,3,4,5]  # 工作日（1=周一，7=周日）
```

## 角色模板系统

### 3.1 Agent角色模板设计

#### **内容创建Agent (Content Creator)**
```python
{
    "name": "内容创建Agent",
    "description": "专注于内容创建",
    "permissions": {
        "can_submit_articles": True,
        "can_edit_own_articles": True,
        "can_view_statistics": True,
        "can_approve_articles": False,
        "can_publish_articles": False,
        "can_edit_others_articles": False,
        "can_review_agents": [],
        "allowed_categories": [],
        "allowed_tags": []
    },
    "quota_limits": {
        "daily_articles": 5,
        "monthly_articles": 100,
        "working_hours": {
            "enabled": True,
            "start": "09:00",
            "end": "18:00",
            "timezone": "Asia/Shanghai",
            "working_days": [1,2,3,4,5]
        }
    }
}
```

#### **内容审核Agent (Content Reviewer)**
```python
{
    "name": "内容审核Agent",
    "description": "负责内容审核和质量控制",
    "permissions": {
        "can_submit_articles": False,
        "can_edit_own_articles": False,
        "can_view_statistics": True,
        "can_approve_articles": True,
        "can_publish_articles": False,
        "can_edit_others_articles": True,
        "can_review_agents": [],
        "allowed_categories": [],
        "allowed_tags": []
    },
    "quota_limits": {
        "daily_articles": 50,      # 审核数量
        "monthly_articles": 1000
    }
}
```

#### **发布Agent (Publishing Agent)**
```python
{
    "name": "发布Agent",
    "description": "负责文章发布",
    "permissions": {
        "can_submit_articles": False,
        "can_edit_own_articles": False,
        "can_view_statistics": True,
        "can_approve_articles": False,
        "can_publish_articles": True,
        "can_edit_others_articles": False,
        "can_review_agents": [],
        "allowed_categories": [],
        "allowed_tags": []
    },
    "quota_limits": {
        "daily_articles": 100,     # 发布数量
        "monthly_articles": 2000
    }
}
```

#### **全能Agent (Full Access Agent)**
```python
{
    "name": "全能Agent",
    "description": "具备完整工作流权限的高级Agent",
    "permissions": {
        "can_submit_articles": True,
        "can_edit_own_articles": True,
        "can_edit_others_articles": True,
        "can_approve_articles": True,
        "can_publish_articles": True,
        "can_view_statistics": True,
        "can_review_agents": [],
        "allowed_categories": [],
        "allowed_tags": []
    },
    "quota_limits": {
        "daily_articles": 0,       # 无限制
        "monthly_articles": 0      # 无限制
    }
}
```

#### **只读监控Agent (Read-Only Monitor)**
```python
{
    "name": "只读监控Agent",
    "description": "监控和统计信息收集",
    "permissions": {
        "can_submit_articles": False,
        "can_edit_own_articles": False,
        "can_edit_others_articles": False,
        "can_approve_articles": False,
        "can_publish_articles": False,
        "can_view_statistics": True,
        "can_review_agents": [],
        "allowed_categories": [],
        "allowed_tags": []
    },
    "quota_limits": {
        "daily_articles": 0,       # 不提交文章
        "monthly_articles": 0      # 不提交文章
    }
}
```

### 3.2 数据库设计

#### **角色模板表结构**

基于实际实现的数据库架构：

```sql
-- 角色模板主表
CREATE TABLE role_templates (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '{}',
    quota_limits JSONB DEFAULT '{}',
    is_system_role BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 角色模板变更历史表
CREATE TABLE role_template_history (
    id BIGSERIAL PRIMARY KEY,
    role_template_id VARCHAR(50) REFERENCES role_templates(id),
    action VARCHAR(20) NOT NULL, -- 'created', 'updated', 'deleted'
    old_config JSONB,
    new_config JSONB,
    changed_by VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent表扩展（已实现）
ALTER TABLE agents ADD COLUMN role_template_id VARCHAR(50) REFERENCES role_templates(id);
ALTER TABLE agents ADD COLUMN permissions_override JSONB DEFAULT '{}';
```

**系统预定义角色模板**：
- `content_creator` - 内容创建者
- `content_reviewer` - 内容审核者  
- `content_publisher` - 内容发布者
- `content_manager` - 内容管理者

## 技术实现方案

### 4.1 MCP工具权限映射

#### **文章操作Tools权限检查**
```python
# 文章提交
@require_permission("can_submit_articles")
async def submit_article(title, content, tags, category):
    # 额外检查: allowed_categories 和 allowed_tags
    pass

# 文章查看
@require_permission("can_view_statistics") 
async def list_articles(status, limit, offset):
    # 自动过滤: 只显示有权限查看的文章
    pass

@require_permission("can_view_statistics")
async def get_article_status(article_id):
    # 检查文章可见性权限
    pass

# 文章编辑
@require_any_permission(["can_edit_own_articles", "can_edit_others_articles"])
async def edit_article(article_id, title, content, tags, category):
    # 所有权检查: 如果只有 can_edit_own_articles，验证文章所有者
    # 内容检查: 验证 allowed_categories 和 allowed_tags
    pass
```

#### **工作流Tools权限检查**
```python
# 文章审批
@require_permission("can_approve_articles")
async def approve_article(article_id, reviewer_notes):
    pass

# 文章拒绝
@require_permission("can_approve_articles") 
async def reject_article(article_id, rejection_reason):
    pass

# 文章发布
@require_permission("can_publish_articles")
async def publish_article(article_id, site_id):
    pass
```

#### **系统信息Tools权限检查**
```python
# 系统信息查看
@require_permission("can_view_statistics")
async def list_agents(include_inactive):
    pass

@require_permission("can_view_statistics")
async def get_agent_stats(agent_id):
    pass

@require_permission("can_view_statistics")
async def list_sites(include_inactive):
    pass

@require_permission("can_view_statistics") 
async def get_site_health(site_id):
    pass
```

### 4.2 权限检查装饰器

#### **权限检查装饰器实现**
```python
# mcp_wordpress/auth/permissions.py
from functools import wraps
from typing import List, Callable, Any
from fastmcp.server.dependencies import get_access_token
from mcp_wordpress.core.errors import PermissionDeniedError
from mcp_wordpress.services.role_template_service import role_template_service

def require_permission(permission: str) -> Callable:
    """权限检查装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 获取当前用户访问令牌
            access_token = get_access_token()
            if not access_token:
                raise PermissionDeniedError("未找到有效的访问令牌")
            
            # 执行权限检查
            permission_checker = PermissionChecker()
            has_permission = await permission_checker.check_permission(
                agent_id=access_token.client_id,
                permission=permission,
                kwargs=kwargs
            )
            
            if not has_permission:
                raise PermissionDeniedError(f"权限不足: 需要 {permission} 权限")
            
            # 执行原函数
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(permissions: List[str]) -> Callable:
    """多权限检查装饰器 - 满足任一权限即可"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            access_token = get_access_token()
            if not access_token:
                raise PermissionDeniedError("未找到有效的访问令牌")
            
            permission_checker = PermissionChecker()
            
            # 检查是否有任一权限
            for permission in permissions:
                if await permission_checker.check_permission(
                    agent_id=access_token.client_id,
                    permission=permission,
                    kwargs=kwargs
                ):
                    return await func(*args, **kwargs)
            
            raise PermissionDeniedError(f"权限不足: 需要以下权限之一: {', '.join(permissions)}")
        return wrapper
    return decorator
```

### 4.3 权限检查器

#### **分层权限验证逻辑**
```python
# mcp_wordpress/auth/permission_checker.py
class PermissionChecker:
    """Agent权限检查器"""
    
    async def check_permission(
        self,
        agent_id: str,
        permission: str,
        kwargs: Optional[Dict[str, Any]] = None
    ) -> bool:
        """分层权限检查"""
        
        # 1. 获取有效权限（包括角色模板权限）
        effective_permissions = await role_template_service.get_effective_permissions(agent_id)
        
        # 2. 基础权限检查
        if not effective_permissions.get(permission, False):
            return False
        
        # 3. 所有权检查 (对于 own_articles 权限)
        if permission == "can_edit_own_articles" and kwargs:
            if not await self._check_ownership(agent_id, kwargs):
                return False
        
        # 4. 内容限制检查 (分类和标签)
        if not await self._check_content_restrictions(effective_permissions, kwargs):
            return False
        
        # 5. 配额检查
        if not await self._check_quota_limits(agent_id, effective_permissions):
            return False
        
        # 6. 工作时间检查
        if not await self._check_working_hours(effective_permissions):
            return False
        
        return True
    
    async def _check_ownership(self, agent_id: str, kwargs: Dict[str, Any]) -> bool:
        """检查文章所有权"""
        article_id = kwargs.get("article_id")
        if not article_id:
            return True
        
        async with get_session() as session:
            result = await session.execute(
                select(Article).where(Article.id == article_id)
            )
            article = result.scalars().first()
            return article and article.submitting_agent_id == agent_id
    
    async def _check_content_restrictions(self, permissions: Dict, kwargs: Optional[Dict[str, Any]]) -> bool:
        """检查内容限制 (分类和标签)"""
        if not kwargs:
            return True
        
        # 检查分类限制
        category = kwargs.get("category")
        if category:
            allowed_categories = permissions.get("allowed_categories", [])
            if allowed_categories and category not in allowed_categories:
                return False
        
        # 检查标签限制
        tags = kwargs.get("tags", "")
        if tags:
            allowed_tags = permissions.get("allowed_tags", [])
            if allowed_tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                if not all(tag in allowed_tags for tag in tag_list if tag):
                    return False
        
        return True
    
    async def _check_quota_limits(self, agent_id: str, permissions: Dict) -> bool:
        """检查配额限制"""
        quota_limits = permissions.get("quota_limits", {})
        if not quota_limits:
            return True
        
        # 检查日配额
        daily_limit = quota_limits.get("daily_articles", 0)
        if daily_limit > 0:
            daily_count = await self._get_daily_article_count(agent_id)
            if daily_count >= daily_limit:
                return False
        
        # 检查月配额
        monthly_limit = quota_limits.get("monthly_articles", 0)
        if monthly_limit > 0:
            monthly_count = await self._get_monthly_article_count(agent_id)
            if monthly_count >= monthly_limit:
                return False
        
        return True
    
    async def _check_working_hours(self, permissions: Dict) -> bool:
        """检查工作时间限制"""
        quota_limits = permissions.get("quota_limits", {})
        working_hours = quota_limits.get("working_hours", {})
        
        if not working_hours.get("enabled", False):
            return True
        
        import pytz
        from datetime import datetime, time
        
        timezone = pytz.timezone(working_hours.get("timezone", "UTC"))
        now = datetime.now(timezone)
        
        # 检查工作日
        working_days = working_hours.get("working_days", list(range(1, 8)))
        if now.weekday() + 1 not in working_days:
            return False
        
        # 检查工作时间
        start_time = time.fromisoformat(working_hours.get("start", "00:00"))
        end_time = time.fromisoformat(working_hours.get("end", "23:59"))
        current_time = now.time()
        
        return start_time <= current_time <= end_time
```

## Web UI权限管理

### 5.1 Agent权限配置界面

#### **Agent表单中的角色模板选择**
```typescript
// Web UI Agent配置界面结构
const AgentFormModal = () => {
  return (
    <div className="space-y-6">
      {/* 基础信息 */}
      <div>
        <h3>Agent基本信息</h3>
        {/* Agent ID, 名称, 描述等 */}
      </div>

      {/* 角色模板选择 */}
      <div>
        <h3>角色模板 (可选)</h3>
        <select onChange={handleRoleTemplateChange}>
          <option value="">自定义权限（不使用模板）</option>
          <option value="content_creator">内容创建Agent</option>
          <option value="content_reviewer">内容审核Agent</option>
          <option value="publishing_agent">发布Agent</option>
          <option value="full_access_agent">全能Agent</option>
          <option value="read_only_monitor">只读监控Agent</option>
        </select>
        <p className="text-sm text-gray-500">
          选择角色模板将自动设置基本权限。选择"自定义权限"以手动配置所有权限。
        </p>
      </div>

      {/* 权限配置 */}
      <div>
        <h3>权限配置</h3>
        {roleTemplateId && (
          <div className="bg-blue-50 p-4 rounded">
            <p>已选择角色模板。以下权限设置将作为模板权限的覆盖配置。</p>
          </div>
        )}
        
        {/* 权限矩阵 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4>文章操作权限</h4>
            <label><input type="checkbox" /> 提交文章</label>
            <label><input type="checkbox" /> 编辑自己的文章</label>
            <label><input type="checkbox" /> 编辑他人文章</label>
          </div>
          
          <div>
            <h4>工作流权限</h4>
            <label><input type="checkbox" /> 审批文章</label>
            <label><input type="checkbox" /> 发布文章</label>
          </div>
          
          <div>
            <h4>系统权限</h4>
            <label><input type="checkbox" /> 查看统计信息</label>
          </div>
          
          <div>
            <h4>内容限制</h4>
            <input placeholder="允许的分类（逗号分隔）" />
            <input placeholder="允许的标签（逗号分隔）" />
          </div>
        </div>
      </div>

      {/* 配额设置 */}
      <div>
        <h3>配额设置</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label>每日文章数限制</label>
            <input type="number" placeholder="0表示无限制" />
          </div>
          <div>
            <label>每月文章数限制</label>
            <input type="number" placeholder="0表示无限制" />
          </div>
        </div>
      </div>

      {/* 工作时间 */}
      <div>
        <h3>工作时间限制</h3>
        <label>
          <input type="checkbox" /> 启用工作时间限制
        </label>
        {workingHoursEnabled && (
          <div className="grid grid-cols-2 gap-4">
            <input type="time" placeholder="开始时间" />
            <input type="time" placeholder="结束时间" />
            <select>
              <option>时区选择</option>
              <option value="Asia/Shanghai">Asia/Shanghai</option>
            </select>
            <div>
              <label>工作日选择</label>
              {/* 工作日选择器 */}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
```

### 5.2 角色模板管理界面

#### **角色模板列表和编辑**
```typescript
// 角色模板管理界面结构
const RoleTemplateManager = () => {
  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="flex justify-between items-center">
        <div>
          <h1>角色模板管理</h1>
          <p>管理系统角色模板和权限配置</p>
        </div>
        <button>创建角色模板</button>
      </div>

      {/* 角色模板卡片列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {roleTemplates.map(role => (
          <div key={role.id} className="bg-white border rounded-lg p-6">
            <div className="flex justify-between mb-4">
              <div>
                <h3>{role.name}</h3>
                <p className="text-gray-600">{role.description}</p>
              </div>
              <div>
                {role.is_system_role && (
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    系统
                  </span>
                )}
              </div>
            </div>

            {/* 权限概览 */}
            <div className="mb-4">
              <h4>权限概览</h4>
              <div className="space-y-1">
                {Object.entries(role.permissions)
                  .filter(([key, value]) => typeof value === 'boolean' && value)
                  .map(([key]) => (
                    <div key={key} className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-xs text-gray-600">
                        {getPermissionLabel(key)}
                      </span>
                    </div>
                  ))
                }
              </div>
            </div>

            {/* 配额信息 */}
            {role.quota_limits && (
              <div className="mb-4">
                <h4>配额限制</h4>
                <div className="text-xs text-gray-600">
                  日配额: {role.quota_limits.daily_articles || '无限制'}
                </div>
                <div className="text-xs text-gray-600">
                  月配额: {role.quota_limits.monthly_articles || '无限制'}
                </div>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex space-x-2">
              <button onClick={() => editRole(role)}>编辑</button>
              {!role.is_system_role && (
                <>
                  <button onClick={() => toggleStatus(role)}>
                    {role.is_active ? '停用' : '启用'}
                  </button>
                  <button onClick={() => deleteRole(role)}>删除</button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const getPermissionLabel = (key: string): string => {
  const labels = {
    'can_submit_articles': '提交文章',
    'can_edit_own_articles': '编辑自己的文章',
    'can_edit_others_articles': '编辑他人文章',
    'can_approve_articles': '审批文章',
    'can_publish_articles': '发布文章',
    'can_view_statistics': '查看统计信息'
  };
  return labels[key] || key;
};
```

## 实施状态

### 6.1 已完成的实施阶段

#### **✅ 阶段1：数据库设计和迁移**
- 创建角色模板数据库表结构
- 创建角色模板历史记录表
- 扩展Agent表添加角色关联字段
- 初始化系统预定义角色模板

#### **✅ 阶段2：角色模板服务实现**
- 实现RoleTemplateService服务类
- 实现角色模板CRUD操作
- 实现角色应用到Agent的逻辑
- 实现有效权限计算（角色+覆盖）

#### **✅ 阶段3：权限检查机制**
- 实现权限检查装饰器
- 实现分层权限验证逻辑
- 更新所有MCP工具集成权限检查
- 实现配额和时间限制检查

#### **✅ 阶段4：Web UI集成**
- 创建角色模板管理页面
- 实现角色模板创建和编辑功能
- 更新Agent配置表单支持角色选择
- 实现权限覆盖配置界面

#### **✅ 阶段5：系统测试和优化**
- 完成功能测试和集成测试
- 修复角色模板创建时的时间戳问题
- 优化权限检查性能
- 完善错误处理和用户反馈

### 6.2 系统运行状态

**✅ 系统组件运行正常**:
- MCP服务器: 运行在 http://0.0.0.0:8000/sse
- Web UI: 运行在 http://localhost:3000
- 数据库: PostgreSQL，所有表创建完成
- 角色模板: 4个系统角色已初始化
- 角色管理页面: http://localhost:3000/roles

**✅ 权限检查功能验证**:
- MCP工具权限装饰器正常工作
- 角色模板权限计算正确
- 配额和时间限制检查有效
- 权限错误处理友好
- 角色模板CRUD操作功能完整

## 技术参考

### 7.1 错误处理和反馈

#### **权限错误类型**
```python
class PermissionError:
    INSUFFICIENT_PERMISSION = "权限不足"
    CONTENT_RESTRICTION = "内容限制违规"
    QUOTA_EXCEEDED = "配额超限"
    OUTSIDE_WORKING_HOURS = "非工作时间"
    OWNERSHIP_VIOLATION = "所有权验证失败"
```

#### **用户友好的错误消息**
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "您没有权限执行此操作",
    "details": {
      "required_permission": "can_approve_articles",
      "current_role": "content_creator",
      "suggestion": "请联系管理员获取审批权限，或将文章提交给审核Agent"
    }
  }
}
```

### 7.2 性能基准

**权限检查性能目标**:
- 基础权限检查: <5ms
- 完整权限验证（含所有层次）: <20ms
- 角色模板权限计算: <10ms
- 配额检查: <15ms

**系统资源使用**:
- 角色模板缓存: <5MB
- 权限检查缓存: <10MB
- 数据库查询: <3 queries/权限检查
- API响应时间: <100ms

### 7.3 扩展指南

#### **添加新权限**
1. 在权限模型中定义新权限
2. 在系统角色模板中配置新权限
3. 在相关MCP工具中添加权限装饰器
4. 更新Web UI权限配置界面
5. 更新权限标签映射

#### **添加新MCP工具**
1. 在工具函数上添加适当的权限装饰器
2. 考虑是否需要新的权限类型
3. 更新角色模板包含新权限
4. 测试权限检查逻辑
5. 更新文档和用户指南

---

**文档状态**: 已实施并验证  
**最后更新**: 2025-08-15  
**负责人**: 开发团队  
**审核状态**: 已完成实施验证