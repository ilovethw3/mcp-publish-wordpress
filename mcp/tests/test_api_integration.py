import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from mcp.models.user import User
from mcp.models.article import Article, ArticleStatus
from mcp.core.security import get_password_hash, create_access_token


@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPIIntegration:
    """认证API集成测试"""
    
    def test_complete_login_flow(self, client, db_session):
        """测试完整登录流程"""
        # 创建测试用户
        user = User(
            username="apitest",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # 测试登录
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "apitest", "password": "password123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        
        # 测试使用token访问受保护端点
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["username"] == "apitest"
        assert "id" in user_data
        assert "created_at" in user_data

    def test_login_with_invalid_credentials(self, client):
        """测试无效凭据登录"""
        # 测试不存在的用户
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "nonexistent", "password": "wrongpass"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
        
        # 测试空凭据
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "", "password": ""}
        )
        assert response.status_code == 422  # 验证错误

    def test_protected_endpoint_without_token(self, client):
        """测试无令牌访问受保护端点"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403

    def test_protected_endpoint_with_invalid_token(self, client):
        """测试无效令牌访问"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    def test_token_refresh_flow(self, client, auth_headers):
        """测试令牌刷新流程"""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        
        # 验证新令牌可用
        new_headers = {"Authorization": f"Bearer {data['access_token']}"}
        me_response = client.get("/api/v1/auth/me", headers=new_headers)
        assert me_response.status_code == 200


@pytest.mark.integration
class TestArticleAPIIntegration:
    """文章API集成测试"""
    
    @pytest.fixture
    def reviewer_headers(self, db_session):
        """审核员认证头部"""
        user = User(
            username="reviewer",
            hashed_password=get_password_hash("reviewpass"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        token = create_access_token({"sub": "reviewer"})
        return {"Authorization": f"Bearer {token}"}

    def test_article_submission_with_api_key(self, client):
        """测试通过API密钥提交文章"""
        with patch('mcp.core.config.settings.agent_api_key', 'test-api-key'):
            response = client.post(
                "/api/v1/articles/submit",
                json={
                    "title": "API提交测试文章",
                    "content_markdown": "# 测试标题\n这是通过API提交的文章内容，包含**粗体**和*斜体*文本。",
                    "tags": "测试,API,自动化",
                    "category": "技术文档"
                },
                headers={"X-API-Key": "test-api-key"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "API提交测试文章"
        assert data["status"] == "pending_review"
        assert data["tags"] == "测试,API,自动化"
        assert data["category"] == "技术文档"
        assert "content_html" in data
        assert data["id"] is not None

    def test_article_submission_invalid_api_key(self, client):
        """测试无效API密钥提交"""
        with patch('mcp.core.config.settings.agent_api_key', 'valid-key'):
            response = client.post(
                "/api/v1/articles/submit",
                json={
                    "title": "测试文章",
                    "content_markdown": "测试内容"
                },
                headers={"X-API-Key": "invalid-key"}
            )
        
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_article_submission_missing_api_key(self, client):
        """测试缺少API密钥提交"""
        response = client.post(
            "/api/v1/articles/submit",
            json={
                "title": "测试文章",
                "content_markdown": "测试内容"
            }
        )
        
        assert response.status_code == 422  # 缺少必需的header

    def test_complete_article_workflow(self, client, reviewer_headers, mock_wordpress_client):
        """测试完整文章工作流程"""
        # 1. 提交文章
        with patch('mcp.core.config.settings.agent_api_key', 'workflow-test-key'):
            submit_response = client.post(
                "/api/v1/articles/submit",
                json={
                    "title": "完整工作流测试",
                    "content_markdown": "# 工作流测试\n\n这是完整工作流程的测试文章。\n\n- 包含列表\n- 多段内容\n- [链接](https://example.com)",
                    "tags": "工作流,测试,完整流程",
                    "category": "测试分类"
                },
                headers={"X-API-Key": "workflow-test-key"}
            )
        
        assert submit_response.status_code == 200
        article_data = submit_response.json()
        article_id = article_data["id"]
        
        # 2. 获取文章列表
        list_response = client.get("/api/v1/articles/", headers=reviewer_headers)
        assert list_response.status_code == 200
        articles = list_response.json()
        assert len(articles) >= 1
        
        # 查找我们的文章
        our_article = next((a for a in articles if a["id"] == article_id), None)
        assert our_article is not None
        assert our_article["status"] == "pending_review"
        
        # 3. 获取文章详情
        detail_response = client.get(f"/api/v1/articles/{article_id}", headers=reviewer_headers)
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["title"] == "完整工作流测试"
        assert "content_html" in detail_data
        
        # 4. 更新文章
        update_response = client.put(
            f"/api/v1/articles/{article_id}",
            json={
                "title": "更新后的标题",
                "content_markdown": "# 更新后的内容\n\n文章已被审核人员更新。"
            },
            headers=reviewer_headers
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["title"] == "更新后的标题"
        
        # 5. 批准文章（模拟WordPress发布）
        with patch('mcp.core.wordpress_client.WordPressClient', return_value=mock_wordpress_client):
            approve_response = client.post(
                f"/api/v1/articles/{article_id}/approve", 
                headers=reviewer_headers
            )
        
        assert approve_response.status_code == 200
        approve_data = approve_response.json()
        assert "publishing started" in approve_data["message"]

    def test_article_rejection_workflow(self, client, reviewer_headers):
        """测试文章拒绝工作流"""
        # 提交文章
        with patch('mcp.core.config.settings.agent_api_key', 'reject-test-key'):
            submit_response = client.post(
                "/api/v1/articles/submit",
                json={
                    "title": "将被拒绝的文章",
                    "content_markdown": "这是一篇将被拒绝的文章内容"
                },
                headers={"X-API-Key": "reject-test-key"}
            )
        
        article_id = submit_response.json()["id"]
        
        # 拒绝文章
        reject_response = client.post(
            f"/api/v1/articles/{article_id}/reject",
            headers=reviewer_headers
        )
        
        assert reject_response.status_code == 200
        assert "rejected" in reject_response.json()["message"]
        
        # 验证文章状态已更新
        detail_response = client.get(f"/api/v1/articles/{article_id}", headers=reviewer_headers)
        assert detail_response.json()["status"] == "rejected"

    def test_article_search_and_filtering(self, client, reviewer_headers, db_session):
        """测试文章搜索和过滤功能"""
        # 创建测试文章
        test_articles = [
            Article(title="Python机器学习教程", content_markdown="Python内容", tags="python,机器学习,教程"),
            Article(title="JavaScript前端开发", content_markdown="JS内容", tags="javascript,前端,开发"),
            Article(title="Python Web开发指南", content_markdown="Python Web内容", category="编程"),
            Article(title="数据科学入门", content_markdown="数据科学内容", category="科学", status=ArticleStatus.PUBLISHED)
        ]
        
        for article in test_articles:
            db_session.add(article)
        db_session.commit()
        
        # 测试标题搜索
        search_response = client.get(
            "/api/v1/articles/?search=Python", 
            headers=reviewer_headers
        )
        assert search_response.status_code == 200
        results = search_response.json()
        assert len(results) == 2
        titles = [r["title"] for r in results]
        assert "Python机器学习教程" in titles
        assert "Python Web开发指南" in titles
        
        # 测试状态过滤
        published_response = client.get(
            "/api/v1/articles/?status=published",
            headers=reviewer_headers
        )
        assert published_response.status_code == 200
        published_results = published_response.json()
        assert len(published_results) == 1
        assert published_results[0]["title"] == "数据科学入门"
        
        # 测试组合搜索（搜索+过滤）
        combo_response = client.get(
            "/api/v1/articles/?search=Python&status=pending_review",
            headers=reviewer_headers
        )
        assert combo_response.status_code == 200
        combo_results = combo_response.json()
        assert len(combo_results) == 2

    def test_article_pagination(self, client, reviewer_headers, db_session):
        """测试文章分页功能"""
        # 创建多篇文章
        articles = [
            Article(title=f"分页测试文章 {i}", content_markdown=f"内容 {i}")
            for i in range(15)
        ]
        
        for article in articles:
            db_session.add(article)
        db_session.commit()
        
        # 测试第一页
        page1_response = client.get(
            "/api/v1/articles/?skip=0&limit=10",
            headers=reviewer_headers
        )
        assert page1_response.status_code == 200
        page1_results = page1_response.json()
        assert len(page1_results) == 10
        
        # 测试第二页
        page2_response = client.get(
            "/api/v1/articles/?skip=10&limit=10",
            headers=reviewer_headers
        )
        assert page2_response.status_code == 200
        page2_results = page2_response.json()
        assert len(page2_results) == 5  # 剩余5篇
        
        # 验证没有重复
        page1_ids = {r["id"] for r in page1_results}
        page2_ids = {r["id"] for r in page2_results}
        assert len(page1_ids.intersection(page2_ids)) == 0

    def test_article_sorting(self, client, reviewer_headers, db_session):
        """测试文章排序功能"""
        from datetime import datetime, timedelta
        
        base_time = datetime.utcnow()
        articles = [
            Article(title="最新文章", content_markdown="最新", created_at=base_time),
            Article(title="中间文章", content_markdown="中间", created_at=base_time - timedelta(hours=1)),
            Article(title="最早文章", content_markdown="最早", created_at=base_time - timedelta(hours=2))
        ]
        
        for article in articles:
            db_session.add(article)
        db_session.commit()
        
        # 测试按创建时间降序排列
        desc_response = client.get(
            "/api/v1/articles/?sort_by=created_at&sort_order=desc",
            headers=reviewer_headers
        )
        assert desc_response.status_code == 200
        desc_results = desc_response.json()
        assert desc_results[0]["title"] == "最新文章"
        assert desc_results[-1]["title"] == "最早文章"
        
        # 测试按标题升序排列
        title_response = client.get(
            "/api/v1/articles/?sort_by=title&sort_order=asc",
            headers=reviewer_headers
        )
        assert title_response.status_code == 200
        title_results = title_response.json()
        titles = [r["title"] for r in title_results]
        assert titles == sorted(titles)

    def test_article_deletion(self, client, reviewer_headers, db_session):
        """测试文章删除"""
        # 创建测试文章
        article = Article(
            title="待删除文章",
            content_markdown="即将被删除的内容"
        )
        db_session.add(article)
        db_session.commit()
        article_id = article.id
        
        # 删除文章
        delete_response = client.delete(
            f"/api/v1/articles/{article_id}",
            headers=reviewer_headers
        )
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]
        
        # 验证文章已删除
        get_response = client.get(f"/api/v1/articles/{article_id}", headers=reviewer_headers)
        assert get_response.status_code == 404

    def test_article_retry_failed_publish(self, client, reviewer_headers, mock_wordpress_client):
        """测试重试失败的发布"""
        # 创建发布失败的文章
        article = Article(
            title="发布失败文章",
            content_markdown="发布失败的内容",
            status=ArticleStatus.PUBLISH_FAILED,
            publish_error_message="WordPress连接失败"
        )
        
        with patch('mcp.db.session.get_session') as mock_get_session:
            mock_session = mock_get_session.return_value.__enter__.return_value
            mock_session.exec.return_value.first.return_value = article
            
            # 重试发布
            with patch('mcp.core.wordpress_client.WordPressClient', return_value=mock_wordpress_client):
                retry_response = client.post(
                    f"/api/v1/articles/{article.id}/retry",
                    headers=reviewer_headers
                )
            
            assert retry_response.status_code == 200
            assert "retry started" in retry_response.json()["message"]

    def test_unauthorized_access_attempts(self, client):
        """测试未授权访问尝试"""
        unauthorized_endpoints = [
            ("GET", "/api/v1/articles/"),
            ("GET", "/api/v1/articles/1"),
            ("PUT", "/api/v1/articles/1"),
            ("DELETE", "/api/v1/articles/1"),
            ("POST", "/api/v1/articles/1/approve"),
            ("POST", "/api/v1/articles/1/reject"),
            ("POST", "/api/v1/articles/1/retry")
        ]
        
        for method, endpoint in unauthorized_endpoints:
            response = getattr(client, method.lower())(endpoint)
            assert response.status_code in [401, 403], f"Failed for {method} {endpoint}"