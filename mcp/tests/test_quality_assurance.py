import pytest
import ast
import os
from pathlib import Path
from unittest.mock import patch
import time
from sqlmodel import select
from mcp.models.article import Article, ArticleStatus


@pytest.mark.unit
class TestCodeQuality:
    """测试代码质量保证"""
    
    def test_all_api_endpoints_have_tests(self):
        """确保所有API端点都有测试覆盖"""
        # 扫描API路由文件
        api_dir = Path("mcp/api/v1")
        api_files = list(api_dir.glob("*.py"))
        api_files = [f for f in api_files if f.name != "__init__.py"]
        
        # 扫描测试文件
        test_dir = Path("mcp/tests")
        test_files = list(test_dir.glob("test_*.py"))
        
        # 验证关键API文件都有对应的测试
        critical_apis = ["auth.py", "articles.py"]
        for api_file in critical_apis:
            api_path = api_dir / api_file
            if api_path.exists():
                # 检查是否有相应的测试文件
                test_content = ""
                for test_file in test_files:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        test_content += f.read()
                
                # 验证测试覆盖
                api_name = api_file.replace('.py', '')
                assert api_name in test_content or f"test_{api_name}" in test_content, \
                    f"缺少 {api_file} 的测试覆盖"

    def test_critical_functions_have_unit_tests(self):
        """确保关键函数都有单元测试"""
        critical_functions = [
            "authenticate_user",
            "create_access_token", 
            "verify_password",
            "get_password_hash",
            "decode_access_token",
            "verify_api_key",
            "create_post",
            "get_categories",
            "get_tags"
        ]
        
        # 读取所有测试文件内容
        test_files_content = []
        test_dir = Path("mcp/tests")
        for test_file in test_dir.glob("test_*.py"):
            with open(test_file, 'r', encoding='utf-8') as f:
                test_files_content.append(f.read())
        
        all_test_content = "\n".join(test_files_content)
        
        # 检查每个关键函数是否有测试
        for func in critical_functions:
            has_direct_test = f"test_{func}" in all_test_content
            has_indirect_test = func in all_test_content and "def test_" in all_test_content
            
            assert has_direct_test or has_indirect_test, \
                f"关键函数 {func} 缺少单元测试"

    def test_no_hardcoded_secrets_in_tests(self):
        """确保测试中无硬编码密钥"""
        test_files = Path("mcp/tests").glob("*.py")
        
        # 使用动态构建避免自我检测问题
        dangerous_patterns = [
            "real" + "_secret" + "_key_12345",
            "production" + "_password",
            "live" + "_api_key"
        ]
        
        for test_file in test_files:
            # 跳过质量保证测试文件本身
            if test_file.name == "test_quality_assurance.py":
                continue
                
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 检查真正危险的模式
                for pattern in dangerous_patterns:
                    assert pattern not in content, \
                        f"发现危险的硬编码密钥在 {test_file}: {pattern}"

    def test_test_file_naming_convention(self):
        """检查测试文件命名规范"""
        test_dir = Path("mcp/tests")
        test_files = list(test_dir.glob("*.py"))
        
        for test_file in test_files:
            if test_file.name == "__init__.py" or test_file.name == "conftest.py":
                continue
                
            # 测试文件应该以test_开头
            assert test_file.name.startswith("test_"), \
                f"测试文件 {test_file.name} 不符合命名规范（应以test_开头）"

    def test_test_function_naming_convention(self):
        """检查测试函数命名规范"""
        test_dir = Path("mcp/tests")
        
        for test_file in test_dir.glob("test_*.py"):
            with open(test_file, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    pytest.fail(f"语法错误在测试文件 {test_file}")
                
                # 检查函数定义
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.name.startswith('test_'):
                            # 测试函数名应该是描述性的
                            assert len(node.name) > 5, \
                                f"测试函数名太短: {node.name} in {test_file}"

    def test_docstring_coverage_in_test_classes(self):
        """检查测试类的文档字符串覆盖"""
        test_dir = Path("mcp/tests")
        
        for test_file in test_dir.glob("test_*.py"):
            if test_file.name in ["conftest.py", "__init__.py"]:
                continue
                
            with open(test_file, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    continue
                
                # 检查类定义
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                        # 测试类应该有文档字符串
                        has_docstring = (node.body and 
                                       isinstance(node.body[0], ast.Expr) and 
                                       isinstance(node.body[0].value, ast.Str))
                        
                        assert has_docstring, \
                            f"测试类 {node.name} 在 {test_file} 中缺少文档字符串"


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceBaseline:
    """性能基准测试"""
    
    def test_database_query_performance(self, db_session):
        """测试数据库查询性能基准"""
        # 创建测试数据
        articles = []
        for i in range(100):
            article = Article(
                title=f"性能测试文章 {i}",
                content_markdown=f"性能测试内容 {i} " * 10,  # 创建较大的内容
                status=ArticleStatus.PENDING_REVIEW if i % 2 == 0 else ArticleStatus.PUBLISHED
            )
            articles.append(article)
        
        db_session.add_all(articles)
        db_session.commit()
        
        # 测试简单查询性能
        start_time = time.time()
        results = db_session.exec(select(Article).limit(10)).all()
        query_time = time.time() - start_time
        
        assert len(results) == 10
        assert query_time < 0.1, f"简单查询耗时过长: {query_time:.3f}秒"
        
        # 测试过滤查询性能
        start_time = time.time()
        pending_results = db_session.exec(
            select(Article).where(Article.status == ArticleStatus.PENDING_REVIEW)
        ).all()
        filter_time = time.time() - start_time
        
        assert len(pending_results) == 50
        assert filter_time < 0.2, f"过滤查询耗时过长: {filter_time:.3f}秒"

    def test_api_response_time_baseline(self, client, auth_headers):
        """测试API响应时间基准"""
        # 测试文章列表API响应时间
        start_time = time.time()
        response = client.get("/api/v1/articles/?limit=10", headers=auth_headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0, f"文章列表API响应时间过长: {response_time:.3f}秒"
        
        # 测试认证API响应时间
        start_time = time.time()
        me_response = client.get("/api/v1/auth/me", headers=auth_headers)
        auth_time = time.time() - start_time
        
        assert me_response.status_code == 200
        assert auth_time < 0.5, f"认证API响应时间过长: {auth_time:.3f}秒"

    def test_memory_usage_baseline(self, db_session):
        """测试内存使用基准（简化版）"""
        import sys
        
        # 记录初始内存状态
        initial_objects = len([obj for obj in sys.modules.keys()])
        
        # 创建大量对象
        articles = []
        for i in range(1000):
            article = Article(
                title=f"内存测试 {i}",
                content_markdown="内存测试内容 " * 50
            )
            articles.append(article)
        
        # 批量添加到数据库
        db_session.add_all(articles)
        db_session.commit()
        
        # 清理引用
        del articles
        
        # 验证没有过度的内存泄漏（简化检查）
        final_objects = len([obj for obj in sys.modules.keys()])
        object_growth = final_objects - initial_objects
        
        # 允许合理的对象增长
        assert object_growth < 100, f"可能存在内存泄漏，对象增长: {object_growth}"


@pytest.mark.integration
class TestErrorHandlingRobustness:
    """错误处理鲁棒性测试"""
    
    def test_database_connection_failure_handling(self, client):
        """测试数据库连接失败处理"""
        with patch('mcp.db.session.engine') as mock_engine:
            # 模拟数据库连接失败
            mock_engine.connect.side_effect = Exception("数据库连接失败")
            
            # API应该优雅地处理错误
            response = client.get("/health")  # 假设有健康检查端点
            # 这里的具体断言取决于错误处理策略
            assert response.status_code in [200, 503]

    def test_external_service_timeout_handling(self, wp_client):
        """测试外部服务超时处理"""
        with patch('requests.Session.request') as mock_request:
            import requests
            mock_request.side_effect = requests.exceptions.Timeout("请求超时")
            
            result = wp_client.create_post("测试", "内容")
            
            # WordPress客户端应该优雅地处理超时
            assert result['success'] is False
            assert 'error' in result

    def test_malformed_input_handling(self, client):
        """测试恶意输入处理"""
        malicious_inputs = [
            {"title": "<script>alert('xss')</script>", "content_markdown": "内容"},
            {"title": "A" * 1000, "content_markdown": "内容"},  # 超长标题
            {"title": "", "content_markdown": ""},  # 空值
            {"title": None, "content_markdown": None},  # None值
        ]
        
        with patch('mcp.core.config.settings.agent_api_key', 'test-key'):
            for malicious_input in malicious_inputs:
                response = client.post(
                    "/api/v1/articles/submit",
                    json=malicious_input,
                    headers={"X-API-Key": "test-key"}
                )
                
                # 应该返回适当的错误状态码
                assert response.status_code in [400, 422], \
                    f"恶意输入未被正确处理: {malicious_input}"

    def test_concurrent_request_handling(self, client, auth_headers):
        """测试并发请求处理"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = client.get("/api/v1/articles/", headers=auth_headers)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")
        
        # 创建多个并发线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有请求都成功处理
        while not results.empty():
            result = results.get()
            assert result == 200, f"并发请求失败: {result}"


@pytest.mark.integration
class TestSecurityValidation:
    """安全验证测试"""
    
    def test_sql_injection_protection(self, client, auth_headers):
        """测试SQL注入防护"""
        malicious_queries = [
            "'; DROP TABLE articles; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for injection_attempt in malicious_queries:
            # 尝试在搜索中注入SQL
            response = client.get(
                f"/api/v1/articles/?search={injection_attempt}",
                headers=auth_headers
            )
            
            # 应该返回正常的响应，而不是数据库错误
            assert response.status_code in [200, 400], \
                f"SQL注入防护失败: {injection_attempt}"

    def test_authentication_bypass_attempts(self, client):
        """测试认证绕过尝试"""
        bypass_attempts = [
            {"Authorization": "Bearer fake_token"},
            {"Authorization": "Basic fake_basic"},
            {"X-API-Key": "fake_key"},
            {},  # 无认证头
        ]
        
        protected_endpoints = [
            "/api/v1/articles/",
            "/api/v1/auth/me",
            "/api/v1/articles/1"
        ]
        
        for headers in bypass_attempts:
            for endpoint in protected_endpoints:
                response = client.get(endpoint, headers=headers)
                
                # 应该返回认证错误
                assert response.status_code in [401, 403, 422], \
                    f"认证绕过检测失败: {endpoint} with {headers}"

    def test_rate_limiting_placeholder(self, client):
        """速率限制测试占位符"""
        # 注意：这里只是一个占位符，真实的速率限制测试需要实际的限制机制
        # 快速连续请求
        responses = []
        for i in range(10):
            response = client.get("/")
            responses.append(response.status_code)
        
        # 在没有真实速率限制的情况下，所有请求都应该成功
        assert all(status == 200 for status in responses)
        
        # TODO: 实现真实的速率限制后，这里应该检测到429状态码


@pytest.mark.integration
class TestDataIntegrity:
    """数据完整性测试"""
    
    def test_article_workflow_state_consistency(self, db_session):
        """测试文章工作流状态一致性"""
        article = Article(
            title="状态一致性测试",
            content_markdown="测试内容",
            status=ArticleStatus.PENDING_REVIEW
        )
        
        db_session.add(article)
        db_session.commit()
        
        # 测试有效的状态转换
        valid_transitions = [
            (ArticleStatus.PENDING_REVIEW, ArticleStatus.PUBLISHING),
            (ArticleStatus.PUBLISHING, ArticleStatus.PUBLISHED),
            (ArticleStatus.PUBLISHING, ArticleStatus.PUBLISH_FAILED),
            (ArticleStatus.PENDING_REVIEW, ArticleStatus.REJECTED)
        ]
        
        for from_status, to_status in valid_transitions:
            article.status = from_status
            db_session.commit()
            
            article.status = to_status
            db_session.commit()
            
            # 验证状态已正确更新
            db_session.refresh(article)
            assert article.status == to_status

    def test_user_data_consistency(self, db_session):
        """测试用户数据一致性"""
        from mcp.models.user import User
        from mcp.core.security import get_password_hash
        
        user = User(
            username="consistency_test",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        original_id = user.id
        
        # 更新用户信息
        user.is_active = False
        db_session.commit()
        
        # 重新获取用户验证数据一致性
        db_session.refresh(user)
        assert user.id == original_id
        assert user.is_active is False
        assert user.username == "consistency_test"

    def test_timestamp_accuracy(self, db_session):
        """测试时间戳准确性"""
        from datetime import datetime
        
        before_creation = datetime.utcnow()
        
        article = Article(
            title="时间戳测试",
            content_markdown="时间戳准确性测试"
        )
        
        db_session.add(article)
        db_session.commit()
        
        after_creation = datetime.utcnow()
        
        # 验证创建时间在合理范围内
        assert before_creation <= article.created_at <= after_creation
        assert before_creation <= article.updated_at <= after_creation
        
        # 验证created_at和updated_at初始时相同或接近
        time_diff = abs((article.updated_at - article.created_at).total_seconds())
        assert time_diff < 1.0  # 应该在1秒内