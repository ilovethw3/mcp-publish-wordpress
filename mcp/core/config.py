from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # 应用基础配置
    app_name: str = Field(default="MCP - 内容控制平台", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 数据库配置
    database_url: str = Field(description="PostgreSQL数据库连接字符串")
    
    # JWT认证配置
    secret_key: str = Field(description="JWT签名密钥")
    algorithm: str = Field(default="HS256", description="JWT签名算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    
    # Agent API Key配置
    agent_api_key: str = Field(description="外部Agent访问API的密钥")
    
    # WordPress集成配置
    wordpress_api_url: str = Field(description="WordPress REST API地址")
    wordpress_username: str = Field(description="WordPress用户名")
    wordpress_app_password: str = Field(description="WordPress应用密码")
    
    # CORS配置
    frontend_cors_origins: List[str] = Field(
        default=["http://localhost:3000"], 
        description="允许的前端跨域来源"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()