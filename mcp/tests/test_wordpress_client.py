import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from mcp.core.wordpress_client import WordPressClient


@pytest.mark.unit
@pytest.mark.wordpress
class TestWordPressClient:
    """WordPress客户端单元测试"""
    
    @pytest.fixture
    def wp_client(self):
        """WordPress客户端实例"""
        with patch('mcp.core.config.settings') as mock_settings:
            mock_settings.wordpress_api_url = "https://test.com/wp-json/wp/v2"
            mock_settings.wordpress_username = "testuser"
            mock_settings.wordpress_app_password = "testpass"
            return WordPressClient()
    
    def test_client_initialization(self, wp_client):
        """测试客户端初始化"""
        assert wp_client.api_url == "https://test.com/wp-json/wp/v2"
        assert wp_client.auth is not None
        assert wp_client.session is not None

    @patch('mcp.core.wordpress_client.requests.Session')
    def test_make_request_success(self, mock_session, wp_client):
        """测试成功的HTTP请求"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.request.return_value = mock_response
        
        result = wp_client._make_request('GET', '/posts')
        
        assert result == {"status": "success"}
        mock_session.return_value.request.assert_called_once()

    @patch('mcp.core.wordpress_client.requests.Session')
    def test_make_request_failure(self, mock_session, wp_client):
        """测试HTTP请求失败"""
        # 模拟请求异常
        mock_session.return_value.request.side_effect = requests.exceptions.RequestException("连接失败")
        
        with pytest.raises(requests.exceptions.RequestException):
            wp_client._make_request('GET', '/posts')

    def test_get_categories_success(self, wp_client):
        """测试获取分类成功"""
        mock_categories = [
            {'name': 'Tech', 'id': 1},
            {'name': 'News', 'id': 2},
            {'name': '科技', 'id': 3}
        ]
        
        with patch.object(wp_client, '_make_request', return_value=mock_categories):
            result = wp_client.get_categories()
            
            expected = {'Tech': 1, 'News': 2, '科技': 3}
            assert result == expected

    def test_get_categories_failure(self, wp_client):
        """测试获取分类失败"""
        with patch.object(wp_client, '_make_request', side_effect=Exception("API错误")):
            result = wp_client.get_categories()
            
            assert result == {}

    def test_get_tags_success(self, wp_client):
        """测试获取标签成功"""
        mock_tags = [
            {'name': 'Python', 'id': 1},
            {'name': 'AI', 'id': 2},
            {'name': '机器学习', 'id': 3}
        ]
        
        with patch.object(wp_client, '_make_request', return_value=mock_tags):
            result = wp_client.get_tags()
            
            expected = {'Python': 1, 'AI': 2, '机器学习': 3}
            assert result == expected

    def test_get_tags_failure(self, wp_client):
        """测试获取标签失败"""
        with patch.object(wp_client, '_make_request', side_effect=Exception("网络错误")):
            result = wp_client.get_tags()
            
            assert result == {}

    def test_create_tag_success(self, wp_client):
        """测试创建标签成功"""
        mock_response = {'id': 123, 'name': '新标签'}
        
        with patch.object(wp_client, '_make_request', return_value=mock_response):
            result = wp_client.create_tag('新标签')
            
            assert result == 123

    def test_create_tag_failure(self, wp_client):
        """测试创建标签失败"""
        with patch.object(wp_client, '_make_request', side_effect=Exception("创建失败")):
            result = wp_client.create_tag('新标签')
            
            assert result is None

    def test_create_category_success(self, wp_client):
        """测试创建分类成功"""
        mock_response = {'id': 456, 'name': '新分类'}
        
        with patch.object(wp_client, '_make_request', return_value=mock_response):
            result = wp_client.create_category('新分类')
            
            assert result == 456

    def test_create_category_failure(self, wp_client):
        """测试创建分类失败"""
        with patch.object(wp_client, '_make_request', side_effect=Exception("权限不足")):
            result = wp_client.create_category('新分类')
            
            assert result is None

    def test_resolve_tag_ids_existing_tags(self, wp_client):
        """测试解析已存在标签ID"""
        existing_tags = {'Python': 1, 'AI': 2, '机器学习': 3}
        
        with patch.object(wp_client, 'get_tags', return_value=existing_tags):
            result = wp_client.resolve_tag_ids(['Python', 'AI'])
            
            assert result == [1, 2]

    def test_resolve_tag_ids_create_new_tags(self, wp_client):
        """测试创建新标签"""
        existing_tags = {'Python': 1}
        
        with patch.object(wp_client, 'get_tags', return_value=existing_tags), \
             patch.object(wp_client, 'create_tag', return_value=4):
            result = wp_client.resolve_tag_ids(['Python', '新标签'])
            
            assert result == [1, 4]

    def test_resolve_tag_ids_empty_input(self, wp_client):
        """测试空标签输入"""
        result = wp_client.resolve_tag_ids([])
        assert result == []
        
        result = wp_client.resolve_tag_ids(['', '  ', None])
        assert result == []

    def test_resolve_category_id_existing(self, wp_client):
        """测试解析已存在分类"""
        existing_categories = {'Tech': 1, 'News': 2}
        
        with patch.object(wp_client, 'get_categories', return_value=existing_categories):
            result = wp_client.resolve_category_id('Tech')
            
            assert result == 1

    def test_resolve_category_id_create_new(self, wp_client):
        """测试创建新分类"""
        existing_categories = {'Tech': 1}
        
        with patch.object(wp_client, 'get_categories', return_value=existing_categories), \
             patch.object(wp_client, 'create_category', return_value=3):
            result = wp_client.resolve_category_id('新分类')
            
            assert result == 3

    def test_resolve_category_id_empty_input(self, wp_client):
        """测试空分类输入"""
        assert wp_client.resolve_category_id('') is None
        assert wp_client.resolve_category_id('   ') is None
        assert wp_client.resolve_category_id(None) is None

    def test_create_post_success(self, wp_client):
        """测试成功创建文章"""
        mock_response = {
            'id': 123,
            'link': 'https://example.com/test-post',
            'title': {'rendered': '测试文章'}
        }
        
        with patch.object(wp_client, '_make_request', return_value=mock_response), \
             patch.object(wp_client, 'resolve_tag_ids', return_value=[1, 2]), \
             patch.object(wp_client, 'resolve_category_id', return_value=1):
            
            result = wp_client.create_post(
                title="测试文章",
                content="测试内容",
                tags="Python,AI",
                category="Tech"
            )
        
        assert result['success'] is True
        assert result['post_id'] == 123
        assert result['permalink'] == 'https://example.com/test-post'
        assert 'data' in result

    def test_create_post_minimal_data(self, wp_client):
        """测试最少数据创建文章"""
        mock_response = {
            'id': 124,
            'link': 'https://example.com/minimal-post'
        }
        
        with patch.object(wp_client, '_make_request', return_value=mock_response):
            result = wp_client.create_post(
                title="最简文章",
                content="最简内容"
            )
        
        assert result['success'] is True
        assert result['post_id'] == 124

    def test_create_post_failure(self, wp_client):
        """测试创建文章失败"""
        with patch.object(wp_client, '_make_request', side_effect=Exception("发布失败")):
            result = wp_client.create_post(
                title="失败文章",
                content="失败内容"
            )
        
        assert result['success'] is False
        assert '发布失败' in result['error']

    def test_create_post_with_special_characters(self, wp_client):
        """测试包含特殊字符的文章创建"""
        mock_response = {
            'id': 125,
            'link': 'https://example.com/special-post'
        }
        
        with patch.object(wp_client, '_make_request', return_value=mock_response):
            result = wp_client.create_post(
                title="特殊字符测试 <>&\"'",
                content="内容包含 HTML <strong>标签</strong> 和 & 符号"
            )
        
        assert result['success'] is True

    def test_update_post_success(self, wp_client):
        """测试更新文章成功"""
        mock_response = {
            'id': 123,
            'link': 'https://example.com/updated-post'
        }
        
        with patch.object(wp_client, '_make_request', return_value=mock_response):
            result = wp_client.update_post(123, title="更新标题")
        
        assert result['success'] is True
        assert result['post_id'] == 123

    def test_update_post_failure(self, wp_client):
        """测试更新文章失败"""
        with patch.object(wp_client, '_make_request', side_effect=Exception("更新失败")):
            result = wp_client.update_post(123, title="更新标题")
        
        assert result['success'] is False
        assert '更新失败' in result['error']

    def test_delete_post_success(self, wp_client):
        """测试删除文章成功"""
        mock_response = {'deleted': True}
        
        with patch.object(wp_client, '_make_request', return_value=mock_response):
            result = wp_client.delete_post(123)
        
        assert result['success'] is True

    def test_delete_post_failure(self, wp_client):
        """测试删除文章失败"""
        with patch.object(wp_client, '_make_request', side_effect=Exception("删除失败")):
            result = wp_client.delete_post(123)
        
        assert result['success'] is False
        assert '删除失败' in result['error']


@pytest.mark.integration
@pytest.mark.wordpress
@pytest.mark.slow
class TestWordPressClientIntegration:
    """WordPress客户端集成测试"""
    
    def test_full_post_workflow(self, mock_wordpress_client):
        """测试完整文章发布工作流"""
        # 模拟完整的发布流程
        mock_wordpress_client.get_categories.return_value = {'Tech': 1}
        mock_wordpress_client.get_tags.return_value = {'Python': 1}
        mock_wordpress_client.resolve_tag_ids.return_value = [1, 2]
        mock_wordpress_client.resolve_category_id.return_value = 1
        mock_wordpress_client.create_post.return_value = {
            'success': True,
            'post_id': 100,
            'permalink': 'https://test.com/workflow-test'
        }
        
        # 执行发布流程
        result = mock_wordpress_client.create_post(
            title="集成测试文章",
            content="这是集成测试内容",
            tags="Python,测试",
            category="Tech"
        )
        
        # 验证结果
        assert result['success'] is True
        assert 'post_id' in result
        assert 'permalink' in result

    def test_error_handling_chain(self, wp_client):
        """测试错误处理链"""
        # 测试网络错误、API错误、权限错误等的处理
        error_scenarios = [
            requests.exceptions.ConnectionError("网络连接失败"),
            requests.exceptions.Timeout("请求超时"),
            requests.exceptions.HTTPError("HTTP 403 禁止访问"),
            Exception("未知错误")
        ]
        
        for error in error_scenarios:
            with patch.object(wp_client, '_make_request', side_effect=error):
                result = wp_client.create_post("测试", "内容")
                assert result['success'] is False
                assert 'error' in result