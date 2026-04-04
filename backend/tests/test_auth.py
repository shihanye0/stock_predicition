"""
认证模块单元测试
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.core.config import settings


class TestPasswordHashing:
    """密码哈希测试"""
    
    def test_hash_password(self):
        """测试密码哈希"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # 哈希后应该不同于原密码
        assert hashed != password
        # 哈希应该有一定长度
        assert len(hashed) > 20
    
    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "my_secure_password"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "my_secure_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """测试不同密码产生不同哈希"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """测试相同密码每次哈希不同（因为盐值）"""
        password = "same_password"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # 因为随机盐，哈希值应该不同
        assert hash1 != hash2
        # 但两者都能验证通过
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """JWT Token测试"""
    
    def test_create_token(self):
        """测试创建Token"""
        data = {"sub": "test_user"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_token_has_three_parts(self):
        """测试Token有三部分"""
        data = {"sub": "test_user"}
        token = create_access_token(data)
        
        parts = token.split(".")
        assert len(parts) == 3
    
    def test_create_token_with_expiry(self):
        """测试创建带过期时间的Token"""
        data = {"sub": "test_user"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)
        
        assert token is not None
    
    def test_token_decode(self):
        """测试Token解码"""
        from jose import jwt
        
        data = {"sub": "test_user", "role": "admin"}
        token = create_access_token(data)
        
        # 解码验证
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert decoded["sub"] == "test_user"
        assert decoded["role"] == "admin"
        assert "exp" in decoded
    
    def test_token_expiry_in_payload(self):
        """测试Token包含过期时间"""
        from jose import jwt
        
        data = {"sub": "test_user"}
        token = create_access_token(data)
        
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 检查过期时间存在且在未来
        assert "exp" in decoded
        exp_timestamp = decoded["exp"]
        assert exp_timestamp > datetime.utcnow().timestamp()


class TestAuthConfig:
    """认证配置测试"""
    
    def test_jwt_config_exists(self):
        """测试JWT配置存在"""
        assert hasattr(settings, "JWT_SECRET_KEY")
        assert hasattr(settings, "JWT_ALGORITHM")
        assert hasattr(settings, "JWT_EXPIRE_MINUTES")
    
    def test_jwt_algorithm(self):
        """测试JWT算法配置"""
        assert settings.JWT_ALGORITHM == "HS256"
    
    def test_jwt_expire_reasonable(self):
        """测试JWT过期时间合理"""
        # 至少1小时，最多7天
        assert settings.JWT_EXPIRE_MINUTES >= 60
        assert settings.JWT_EXPIRE_MINUTES <= 10080


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
