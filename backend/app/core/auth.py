"""
JWT认证模块
"""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ========== Schemas ==========

class Token(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token数据"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class UserCreate(BaseModel):
    """用户注册请求"""
    username: str
    password: str
    email: Optional[str] = None
    nickname: Optional[str] = None


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """数据库中的用户"""
    hashed_password: str


# ========== 密码工具函数 ==========

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


# ========== JWT工具函数 ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """解码访问令牌"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None:
            return None
            
        return TokenData(username=username, user_id=user_id)
        
    except JWTError:
        return None


# ========== 依赖注入 ==========

async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)):
    """获取当前用户（可选，未登录返回None）"""
    if token is None:
        return None
    
    token_data = decode_access_token(token)
    if token_data is None:
        return None
    
    return token_data


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户（必须登录）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        raise credentials_exception
    
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception
    
    return token_data


async def get_admin_user(current_user: TokenData = Depends(get_current_user)):
    """获取管理员用户"""
    # 这里需要从数据库查询用户角色
    # 简化处理：暂时只检查是否登录
    return current_user
