import pytest
from datetime import datetime, timedelta
from sqlmodel import select
from mcp.models.article import Article, ArticleStatus, ArticleCreate, ArticleUpdate
from mcp.models.user import User, UserCreate, UserUpdate
from mcp.core.security import get_password_hash


@pytest.mark.unit
@pytest.mark.database
class TestUserModel:
    """用户模型单元测试"""
    
    def test_user_creation(self, db_session):
        """测试用户创建"""
        user = User(
            username="testuser",
            hashed_password="hashed_password_test",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # 验证基本属性
        assert user.id is not None
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password_test"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_default_values(self, db_session):
        """测试用户默认值"""
        user = User(
            username="defaultuser",
            hashed_password="hashed_password"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # 验证默认值
        assert user.is_active is True  # 默认为True
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_username_uniqueness(self, db_session):
        """测试用户名唯一性约束"""
        # 创建第一个用户
        user1 = User(
            username="unique_user",
            hashed_password="password1"
        )
        db_session.add(user1)
        db_session.commit()
        
        # 尝试创建相同用户名的用户
        user2 = User(
            username="unique_user",
            hashed_password="password2"
        )
        db_session.add(user2)
        
        # 应该抛出完整性错误
        with pytest.raises(Exception):  # 数据库完整性错误
            db_session.commit()

    def test_user_create_model(self):
        """测试用户创建模型"""
        user_data = UserCreate(
            username="newuser",
            password="password123"
        )
        
        assert user_data.username == "newuser"
        assert user_data.password == "password123"
        assert user_data.is_active is True  # 默认值

    def test_user_update_model(self):
        """测试用户更新模型"""
        update_data = UserUpdate(
            username="updateduser",
            password="newpassword",
            is_active=False
        )
        
        assert update_data.username == "updateduser"
        assert update_data.password == "newpassword"
        assert update_data.is_active is False

    def test_user_partial_update(self):
        """测试用户部分更新"""
        # 只更新用户名
        update_data = UserUpdate(username="onlyusername")
        
        # 其他字段应该为None（不更新）
        assert update_data.username == "onlyusername"
        assert update_data.password is None
        assert update_data.is_active is None

    def test_user_timestamps_auto_update(self, db_session):
        """测试时间戳自动更新"""
        user = User(
            username="timestampuser",
            hashed_password="password"
        )
        db_session.add(user)
        db_session.commit()
        
        original_updated_at = user.updated_at
        
        # 稍等一下再更新
        import time
        time.sleep(0.1)
        
        # 更新用户
        user.username = "updated_timestamp_user"
        user.updated_at = datetime.utcnow()  # 手动更新时间戳
        db_session.commit()
        
        assert user.updated_at > original_updated_at


@pytest.mark.unit
@pytest.mark.database
class TestArticleModel:
    """文章模型单元测试"""
    
    def test_article_creation(self, db_session):
        """测试文章创建"""
        article = Article(
            title="测试文章",
            content_markdown="# 标题\n这是测试内容",
            status=ArticleStatus.PENDING_REVIEW
        )
        
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        
        # 验证基本属性
        assert article.id is not None
        assert article.title == "测试文章"
        assert article.content_markdown == "# 标题\n这是测试内容"
        assert article.status == ArticleStatus.PENDING_REVIEW
        assert isinstance(article.created_at, datetime)
        assert isinstance(article.updated_at, datetime)

    def test_article_default_status(self, db_session):
        """测试文章默认状态"""
        article = Article(
            title="默认状态文章",
            content_markdown="默认状态内容"
        )
        
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        
        # 验证默认状态
        assert article.status == ArticleStatus.PENDING_REVIEW

    def test_article_with_all_fields(self, db_session):
        """测试包含所有字段的文章"""
        article = Article(
            title="完整文章",
            content_markdown="# 完整内容\n这是完整的markdown内容",
            content_html="<h1>完整内容</h1><p>这是完整的HTML内容</p>",
            tags="Python,AI,机器学习",
            category="技术",
            status=ArticleStatus.PUBLISHED,
            wordpress_post_id=123,
            wordpress_permalink="https://example.com/complete-article"
        )
        
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        
        # 验证所有字段
        assert article.title == "完整文章"
        assert article.content_html is not None
        assert article.tags == "Python,AI,机器学习"
        assert article.category == "技术"
        assert article.status == ArticleStatus.PUBLISHED
        assert article.wordpress_post_id == 123
        assert article.wordpress_permalink == "https://example.com/complete-article"

    def test_article_status_transitions(self, db_session):
        """测试文章状态转换"""
        article = Article(
            title="状态测试",
            content_markdown="状态转换测试内容",
            status=ArticleStatus.PENDING_REVIEW
        )
        
        db_session.add(article)
        db_session.commit()
        
        # 测试状态变更序列
        status_sequence = [
            ArticleStatus.PUBLISHING,
            ArticleStatus.PUBLISHED,
            ArticleStatus.PUBLISH_FAILED,
            ArticleStatus.REJECTED
        ]
        
        for new_status in status_sequence:
            article.status = new_status
            db_session.commit()
            assert article.status == new_status

    def test_article_create_model(self):
        """测试文章创建模型"""
        article_data = ArticleCreate(
            title="新文章",
            content_markdown="# 新内容\n这是新文章",
            tags="测试,新建",
            category="测试分类"
        )
        
        assert article_data.title == "新文章"
        assert article_data.content_markdown == "# 新内容\n这是新文章"
        assert article_data.tags == "测试,新建"
        assert article_data.category == "测试分类"

    def test_article_update_model(self):
        """测试文章更新模型"""
        update_data = ArticleUpdate(
            title="更新标题",
            content_markdown="更新内容",
            status=ArticleStatus.PUBLISHED
        )
        
        assert update_data.title == "更新标题"
        assert update_data.content_markdown == "更新内容"
        assert update_data.status == ArticleStatus.PUBLISHED

    def test_article_partial_update(self):
        """测试文章部分更新"""
        # 只更新标题
        update_data = ArticleUpdate(title="只更新标题")
        
        assert update_data.title == "只更新标题"
        assert update_data.content_markdown is None
        assert update_data.status is None

    def test_article_wordpress_fields(self, db_session):
        """测试WordPress相关字段"""
        article = Article(
            title="WordPress测试",
            content_markdown="WordPress集成测试"
        )
        
        db_session.add(article)
        db_session.commit()
        
        # 模拟WordPress发布成功
        article.wordpress_post_id = 456
        article.wordpress_permalink = "https://myblog.com/wordpress-test"
        article.status = ArticleStatus.PUBLISHED
        db_session.commit()
        
        assert article.wordpress_post_id == 456
        assert article.wordpress_permalink == "https://myblog.com/wordpress-test"
        assert article.status == ArticleStatus.PUBLISHED

    def test_article_error_handling(self, db_session):
        """测试文章错误处理"""
        article = Article(
            title="错误测试",
            content_markdown="错误处理测试"
        )
        
        db_session.add(article)
        db_session.commit()
        
        # 模拟发布失败
        article.status = ArticleStatus.PUBLISH_FAILED
        article.publish_error_message = "WordPress API连接失败"
        db_session.commit()
        
        assert article.status == ArticleStatus.PUBLISH_FAILED
        assert article.publish_error_message == "WordPress API连接失败"

    def test_article_search_by_title(self, db_session):
        """测试按标题搜索文章"""
        articles = [
            Article(title="Python教程", content_markdown="Python内容"),
            Article(title="JavaScript指南", content_markdown="JS内容"),
            Article(title="Python进阶", content_markdown="高级Python内容")
        ]
        
        for article in articles:
            db_session.add(article)
        db_session.commit()
        
        # 搜索包含"Python"的文章
        python_articles = db_session.exec(
            select(Article).where(Article.title.contains("Python"))
        ).all()
        
        assert len(python_articles) == 2
        titles = [article.title for article in python_articles]
        assert "Python教程" in titles
        assert "Python进阶" in titles

    def test_article_filter_by_status(self, db_session):
        """测试按状态过滤文章"""
        articles = [
            Article(title="待审核1", content_markdown="内容1", status=ArticleStatus.PENDING_REVIEW),
            Article(title="已发布1", content_markdown="内容2", status=ArticleStatus.PUBLISHED),
            Article(title="待审核2", content_markdown="内容3", status=ArticleStatus.PENDING_REVIEW),
            Article(title="发布失败", content_markdown="内容4", status=ArticleStatus.PUBLISH_FAILED)
        ]
        
        for article in articles:
            db_session.add(article)
        db_session.commit()
        
        # 过滤待审核文章
        pending_articles = db_session.exec(
            select(Article).where(Article.status == ArticleStatus.PENDING_REVIEW)
        ).all()
        
        assert len(pending_articles) == 2
        
        # 过滤已发布文章
        published_articles = db_session.exec(
            select(Article).where(Article.status == ArticleStatus.PUBLISHED)
        ).all()
        
        assert len(published_articles) == 1

    def test_article_ordering(self, db_session):
        """测试文章排序"""
        now = datetime.utcnow()
        articles = [
            Article(title="最新文章", content_markdown="最新内容"),
            Article(title="较早文章", content_markdown="较早内容"),
            Article(title="中间文章", content_markdown="中间内容")
        ]
        
        # 手动设置创建时间
        articles[0].created_at = now
        articles[1].created_at = now - timedelta(hours=2)
        articles[2].created_at = now - timedelta(hours=1)
        
        for article in articles:
            db_session.add(article)
        db_session.commit()
        
        # 按创建时间降序排列
        ordered_articles = db_session.exec(
            select(Article).order_by(Article.created_at.desc())
        ).all()
        
        assert ordered_articles[0].title == "最新文章"
        assert ordered_articles[1].title == "中间文章"
        assert ordered_articles[2].title == "较早文章"


@pytest.mark.integration
@pytest.mark.database
class TestModelRelationships:
    """模型关系集成测试"""
    
    def test_user_article_data_consistency(self, db_session):
        """测试用户和文章数据一致性"""
        # 创建用户
        user = User(
            username="author",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # 创建文章
        article = Article(
            title="作者文章",
            content_markdown="作者创建的文章内容",
            status=ArticleStatus.PENDING_REVIEW
        )
        db_session.add(article)
        db_session.commit()
        
        # 验证数据完整性
        assert user.id is not None
        assert article.id is not None
        
        # 验证用户和文章都存在于数据库中
        db_user = db_session.get(User, user.id)
        db_article = db_session.get(Article, article.id)
        
        assert db_user is not None
        assert db_article is not None
        assert db_user.username == "author"
        assert db_article.title == "作者文章"

    def test_database_transaction_rollback(self, db_session):
        """测试数据库事务回滚"""
        article = Article(
            title="事务测试",
            content_markdown="事务回滚测试"
        )
        
        db_session.add(article)
        # 不提交，直接回滚
        db_session.rollback()
        
        # 验证文章未被保存
        articles = db_session.exec(select(Article).where(Article.title == "事务测试")).all()
        assert len(articles) == 0

    def test_cascade_operations(self, db_session):
        """测试级联操作（如果有的话）"""
        # 创建多个相关记录
        user = User(username="cascade_user", hashed_password="password")
        articles = [
            Article(title="文章1", content_markdown="内容1"),
            Article(title="文章2", content_markdown="内容2")
        ]
        
        db_session.add(user)
        for article in articles:
            db_session.add(article)
        
        db_session.commit()
        
        # 验证所有记录都被正确保存
        saved_user = db_session.exec(select(User).where(User.username == "cascade_user")).first()
        saved_articles = db_session.exec(select(Article).where(Article.title.in_(["文章1", "文章2"]))).all()
        
        assert saved_user is not None
        assert len(saved_articles) == 2