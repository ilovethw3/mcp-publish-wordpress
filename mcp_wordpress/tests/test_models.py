"""Tests for database models."""

import pytest
from datetime import datetime, timezone
from sqlmodel import SQLModel, create_engine, Session

from mcp_wordpress.models.article import Article, ArticleStatus
from mcp_wordpress.models.user import User


class TestArticleModel:
    """Test Article model validation and constraints."""
    
    def test_article_creation_valid(self):
        """Test creating a valid article."""
        article = Article(
            title="Test Article",
            content_markdown="# Test Content",
            status=ArticleStatus.PENDING_REVIEW
        )
        
        assert article.title == "Test Article"
        assert article.content_markdown == "# Test Content"
        assert article.status == ArticleStatus.PENDING_REVIEW
        assert article.tags is None
        assert article.category is None
    
    def test_article_with_optional_fields(self):
        """Test article with all optional fields."""
        article = Article(
            title="Test Article",
            content_markdown="# Test Content", 
            tags="python,mcp,wordpress",
            category="Technology",
            status=ArticleStatus.PUBLISHED,
            reviewer_notes="Looks good!",
            wordpress_post_id=123,
            wordpress_permalink="https://site.com/test-article"
        )
        
        assert article.tags == "python,mcp,wordpress"
        assert article.category == "Technology"
        assert article.reviewer_notes == "Looks good!"
        assert article.wordpress_post_id == 123
        assert article.wordpress_permalink == "https://site.com/test-article"
    
    def test_article_status_enum(self):
        """Test article status enumeration."""
        # Test all valid statuses
        valid_statuses = [
            ArticleStatus.PENDING_REVIEW,
            ArticleStatus.PUBLISHING, 
            ArticleStatus.PUBLISHED,
            ArticleStatus.REJECTED,
            ArticleStatus.PUBLISH_FAILED
        ]
        
        for status in valid_statuses:
            article = Article(
                title="Test",
                content_markdown="Content",
                status=status
            )
            assert article.status == status
    
    def test_article_timestamps_auto_set(self):
        """Test automatic timestamp setting."""
        before_creation = datetime.now(timezone.utc)
        article = Article(
            title="Test Article",
            content_markdown="# Test Content",
            status=ArticleStatus.PENDING_REVIEW
        )
        after_creation = datetime.now(timezone.utc)
        
        # Timestamps should be set automatically
        assert article.created_at is not None
        assert article.updated_at is not None
        assert before_creation <= article.created_at <= after_creation
        assert before_creation <= article.updated_at <= after_creation


class TestUserModel:
    """Test User model validation and constraints."""
    
    def test_user_creation_valid(self):
        """Test creating a valid user."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.is_active is True  # Default value
        assert user.is_reviewer is False  # Default value
    
    def test_user_with_reviewer_privileges(self):
        """Test user with reviewer privileges."""
        user = User(
            username="reviewer",
            email="reviewer@example.com", 
            password_hash="hashed_password_456",
            is_reviewer=True
        )
        
        assert user.is_reviewer is True
        assert user.is_active is True
    
    def test_user_timestamps_auto_set(self):
        """Test automatic timestamp setting."""
        before_creation = datetime.now(timezone.utc)
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        after_creation = datetime.now(timezone.utc)
        
        # Timestamps should be set automatically
        assert user.created_at is not None
        assert user.updated_at is not None
        assert before_creation <= user.created_at <= after_creation
        assert before_creation <= user.updated_at <= after_creation


class TestModelIntegration:
    """Test model integration and database operations."""
    
    @pytest.fixture
    def test_engine(self):
        """Create in-memory SQLite engine for testing."""
        engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(engine)
        return engine
    
    def test_article_database_operations(self, test_engine):
        """Test article CRUD operations."""
        with Session(test_engine) as session:
            # Create
            article = Article(
                title="Database Test Article",
                content_markdown="# Database Test Content",
                status=ArticleStatus.PENDING_REVIEW
            )
            session.add(article)
            session.commit()
            session.refresh(article)
            
            assert article.id is not None
            
            # Read
            retrieved = session.get(Article, article.id)
            assert retrieved is not None
            assert retrieved.title == "Database Test Article"
            
            # Update
            retrieved.status = ArticleStatus.PUBLISHED
            session.add(retrieved)
            session.commit()
            
            updated = session.get(Article, article.id)
            assert updated.status == ArticleStatus.PUBLISHED
            
            # Delete
            session.delete(updated)
            session.commit()
            
            deleted = session.get(Article, article.id)
            assert deleted is None
    
    def test_user_database_operations(self, test_engine):
        """Test user CRUD operations."""
        with Session(test_engine) as session:
            # Create
            user = User(
                username="dbtest",
                email="dbtest@example.com",
                password_hash="test_hash"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            assert user.id is not None
            
            # Test unique constraints would be handled by the database
            # In real usage, attempting to create duplicate username/email
            # would raise an IntegrityError
            
            # Read
            retrieved = session.get(User, user.id)
            assert retrieved is not None
            assert retrieved.username == "dbtest"
            assert retrieved.email == "dbtest@example.com"