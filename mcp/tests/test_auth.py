import pytest
from unittest.mock import patch
from fastapi import HTTPException
from datetime import datetime, timedelta
from mcp.core.security import (
    get_password_hash, verify_password, create_access_token, 
    decode_access_token, authenticate_user, verify_api_key
)
from mcp.models.user import User


@pytest.mark.unit
@pytest.mark.auth
class TestSecurityFunctions:
    """安全功能单元测试"""
    
    def test_password_hashing(self):
        """测试密码哈希和验证"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # 验证哈希后的密码不等于原密码
        assert hashed != password
        assert len(hashed) > 0
        
        # 验证密码验证功能
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
        assert verify_password("", hashed) is False

    def test_jwt_token_creation_and_validation(self):
        """测试JWT令牌创建和验证"""
        user_data = {"sub": "testuser"}
        token = create_access_token(user_data)
        
        # 验证令牌基本属性
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌解码
        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"
        assert "exp" in payload
        
        # 验证过期时间设置
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        assert exp_time > now

    def test_jwt_token_with_custom_expiry(self):
        """测试自定义过期时间的JWT令牌"""
        user_data = {"sub": "testuser"}
        custom_delta = timedelta(minutes=60)
        token = create_access_token(user_data, expires_delta=custom_delta)
        
        payload = decode_access_token(token)
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + custom_delta
        
        # 允许1分钟的时间差异
        assert abs((exp_time - expected_exp).total_seconds()) < 60

    def test_invalid_token_raises_exception(self):
        """测试无效令牌抛出异常"""
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid_token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in str(exc_info.value.detail)

    def test_expired_token_raises_exception(self):
        """测试过期令牌抛出异常"""
        # 创建已过期的令牌
        past_time = datetime.utcnow() - timedelta(hours=1)
        with patch('mcp.core.security.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = past_time
            expired_token = create_access_token({"sub": "testuser"})
        
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(expired_token)
        
        assert exc_info.value.status_code == 401

    def test_authenticate_user_success(self, db_session, sample_user_data):
        """测试用户认证成功"""
        # 创建测试用户
        user = User(
            username=sample_user_data["username"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # 认证测试
        authenticated_user = authenticate_user(
            db_session, 
            sample_user_data["username"], 
            sample_user_data["password"]
        )
        
        assert authenticated_user is not None
        assert authenticated_user.username == sample_user_data["username"]
        assert authenticated_user.is_active is True

    def test_authenticate_user_wrong_password(self, db_session, sample_user_data):
        """测试错误密码认证失败"""
        user = User(
            username=sample_user_data["username"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_user = authenticate_user(
            db_session, 
            sample_user_data["username"], 
            "wrongpassword"
        )
        
        assert authenticated_user is None

    def test_authenticate_user_nonexistent(self, db_session):
        """测试不存在用户的认证"""
        authenticated_user = authenticate_user(
            db_session, 
            "nonexistent_user", 
            "anypassword"
        )
        
        assert authenticated_user is None

    def test_authenticate_user_inactive(self, db_session, sample_user_data):
        """测试非活跃用户认证失败"""
        user = User(
            username=sample_user_data["username"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            is_active=False  # 设置为非活跃
        )
        db_session.add(user)
        db_session.commit()
        
        authenticated_user = authenticate_user(
            db_session, 
            sample_user_data["username"], 
            sample_user_data["password"]
        )
        
        assert authenticated_user is None

    @patch('mcp.core.config.settings.agent_api_key', 'test-api-key')
    def test_verify_api_key_success(self):
        """测试API密钥验证成功"""
        result = verify_api_key('test-api-key')
        assert result is True

    @patch('mcp.core.config.settings.agent_api_key', 'test-api-key')
    def test_verify_api_key_failure(self):
        """测试API密钥验证失败"""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key('wrong-api-key')
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value.detail)

    def test_empty_password_handling(self):
        """测试空密码处理"""
        # passlib/bcrypt实际上可以处理空密码
        hashed = get_password_hash("")
        assert hashed != ""
        assert len(hashed) > 0
        # 验证空密码可以正确验证
        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False

    def test_password_complexity_validation(self):
        """测试不同复杂度密码的哈希"""
        passwords = [
            "simple",
            "ComplexPassword123!",
            "中文密码测试",
            "a" * 100,  # 长密码
        ]
        
        for password in passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True
            assert hashed != password


@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPIEndpoints:
    """认证API端点集成测试"""
    
    def test_login_endpoint_success(self, client, db_session):
        """测试登录端点成功流程"""
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
        assert "expires_in" in data
        assert isinstance(data["expires_in"], int)

    def test_login_endpoint_invalid_credentials(self, client, db_session):
        """测试登录端点无效凭据"""
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "nonexistent", "password": "wrongpass"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_me_endpoint_with_valid_token(self, client, auth_headers):
        """测试获取用户信息端点"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "id" in data
        assert "created_at" in data

    def test_me_endpoint_without_token(self, client):
        """测试无令牌访问用户信息"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # FastAPI默认403对于缺少认证

    def test_me_endpoint_with_invalid_token(self, client):
        """测试无效令牌访问用户信息"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401

    def test_refresh_token_endpoint(self, client, auth_headers):
        """测试令牌刷新端点"""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data