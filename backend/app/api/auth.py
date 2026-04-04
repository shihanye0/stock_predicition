"""
认证API路由
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

from app.core.database import get_db
from app.core.auth import (
    Token, UserCreate, UserLogin, UserResponse, TokenData,
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_user_optional
)
from app.core.config import settings
from app.models.schemas import Response

router = APIRouter(prefix="/auth", tags=["认证"])


# ========== 用户CRUD ==========

def get_user_by_username(db: Session, username: str):
    """通过用户名获取用户"""
    result = db.execute(
        text("SELECT id, username, email, hashed_password, nickname, avatar, role, is_active, created_at FROM users WHERE username = :username"),
        {"username": username}
    )
    row = result.fetchone()
    if row:
        return {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "hashed_password": row[3],
            "nickname": row[4],
            "avatar": row[5],
            "role": row[6],
            "is_active": row[7],
            "created_at": row[8]
        }
    return None


def get_user_by_id(db: Session, user_id: int):
    """通过ID获取用户"""
    result = db.execute(
        text("SELECT id, username, email, nickname, avatar, role, is_active, created_at FROM users WHERE id = :id"),
        {"id": user_id}
    )
    row = result.fetchone()
    if row:
        return {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "nickname": row[3],
            "avatar": row[4],
            "role": row[5],
            "is_active": row[6],
            "created_at": row[7]
        }
    return None


def create_user(db: Session, user: UserCreate):
    """创建用户"""
    hashed_password = get_password_hash(user.password)
    
    db.execute(
        text("INSERT INTO users (username, email, hashed_password, nickname) VALUES (:username, :email, :hashed_password, :nickname)"),
        {
            "username": user.username,
            "email": user.email,
            "hashed_password": hashed_password,
            "nickname": user.nickname or user.username
        }
    )
    db.commit()
    
    return get_user_by_username(db, user.username)


def update_last_login(db: Session, user_id: int):
    """更新最后登录时间"""
    db.execute(
        text("UPDATE users SET last_login = :now WHERE id = :id"),
        {"now": datetime.now(), "id": user_id}
    )
    db.commit()


# ========== API端点 ==========

@router.post("/register", response_model=Response, summary="用户注册")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册
    
    - username: 用户名（唯一）
    - password: 密码
    - email: 邮箱（可选）
    - nickname: 昵称（可选）
    """
    # 检查用户名是否已存在
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 验证用户名格式
    if len(user.username) < 3 or len(user.username) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名长度应为3-20个字符"
        )
    
    # 验证密码强度
    if len(user.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少6个字符"
        )
    
    try:
        new_user = create_user(db, user)
        logger.info(f"New user registered: {user.username}")
        
        return Response(
            code=200,
            message="注册成功",
            data={
                "id": new_user["id"],
                "username": new_user["username"],
                "nickname": new_user["nickname"]
            }
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=Response, summary="用户登录")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    用户登录
    
    使用表单提交: username, password
    返回JWT Token
    """
    # 查找用户
    user = get_user_by_username(db, form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查账号状态
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    # 更新登录时间
    update_last_login(db, user["id"])
    
    # 创建Token
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]}
    )
    
    logger.info(f"User login: {user['username']}")
    
    return Response(
        code=200,
        message="登录成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "nickname": user["nickname"],
                "avatar": user["avatar"],
                "role": user["role"]
            }
        }
    )


@router.post("/login/json", response_model=Response, summary="用户登录(JSON)")
async def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录（JSON格式）
    
    - username: 用户名
    - password: 密码
    """
    # 查找用户
    user = get_user_by_username(db, user_login.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 验证密码
    if not verify_password(user_login.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 检查账号状态
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    # 更新登录时间
    update_last_login(db, user["id"])
    
    # 创建Token
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]}
    )
    
    logger.info(f"User login: {user['username']}")
    
    return Response(
        code=200,
        message="登录成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "nickname": user["nickname"],
                "avatar": user["avatar"],
                "role": user["role"]
            }
        }
    )


@router.get("/me", response_model=Response, summary="获取当前用户信息")
async def get_me(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前登录用户信息"""
    user = get_user_by_id(db, current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return Response(
        code=200,
        message="success",
        data=user
    )


@router.post("/logout", response_model=Response, summary="退出登录")
async def logout(current_user: TokenData = Depends(get_current_user_optional)):
    """退出登录"""
    # JWT是无状态的，客户端删除token即可
    return Response(
        code=200,
        message="退出成功",
        data=None
    )


@router.put("/password", response_model=Response, summary="修改密码")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 获取用户
    user = get_user_by_username(db, current_user.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证旧密码
    if not verify_password(old_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 验证新密码
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少6个字符"
        )
    
    # 更新密码
    new_hash = get_password_hash(new_password)
    db.execute(
        text("UPDATE users SET hashed_password = :password WHERE id = :id"),
        {"password": new_hash, "id": user["id"]}
    )
    db.commit()
    
    logger.info(f"Password changed: {current_user.username}")
    
    return Response(
        code=200,
        message="密码修改成功",
        data=None
    )
