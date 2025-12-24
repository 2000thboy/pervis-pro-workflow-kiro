"""
用户模型
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import hashlib
import secrets

Base = declarative_base()

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    salt = Column(String(32), nullable=False)
    
    # 用户信息
    full_name = Column(String(100))
    avatar_url = Column(String(500))
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # 登录统计
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password: str):
        """设置密码（加盐哈希）"""
        self.salt = secrets.token_hex(16)
        self.hashed_password = self._hash_password(password, self.salt)
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return self.hashed_password == self._hash_password(password, self.salt)
    
    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """密码哈希函数"""
        return hashlib.pbkdf2_hex(
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000,  # 迭代次数
            64       # 哈希长度
        )
    
    def to_dict(self):
        """转换为字典（不包含敏感信息）"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_admin": self.is_admin,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UserSession(Base):
    """用户会话表"""
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    refresh_token = Column(String(255), nullable=False, unique=True)
    
    # 会话信息
    user_agent = Column(String(500))
    ip_address = Column(String(45))  # 支持IPv6
    device_info = Column(String(200))
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "device_info": self.device_info,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }