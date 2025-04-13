import os
os.environ["CURL_CA_BUNDLE"] = ""  # 可选：避免部分 SSL 报错

from fastapi import FastAPI, Depends, HTTPException, status, Query, Form, BackgroundTasks
from routers import needs, tasks  # ✅ 导入新模块
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import smtplib, random, jwt
from jwt import PyJWTError
from email.mime.text import MIMEText
from email.utils import formataddr

# 项目内部模块
from database import get_db
from models import User, Task, Feedback
from routers import feedback  # ✅ 加在顶端
import crud
from security import authenticate_user, create_access_token, get_current_user
from schemas import (
    UserRegister, UserLogin, Token,
    ForgotPasswordRequest, VerifyCodeRequest, ResetPasswordRequest,
    UserCreate, UserResponse,
    AppointmentCreate, AppointmentResponse,
    HealthDataCreate, HealthDataResponse
)

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

reset_code_store = {}  # {email: (code, expiration_timestamp)}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def send_reset_email(to_email: str, code: str):
    sender = "3668515797@qq.com"
    password = "duogomblwaguchge"
    smtp_server = "smtp.qq.com"
    port = 465

    message = MIMEText(f"您正在找回密码，验证码为：{code}（5分钟内有效）。请勿泄露给他人。", "plain", "utf-8")
    message["From"] = formataddr(("颐康云平台", sender))
    message["To"] = formataddr(("用户", to_email))
    message["Subject"] = "【颐康云】找回密码验证码"

    try:
        smtp = smtplib.SMTP_SSL(smtp_server, port)
        smtp.login(sender, password)
        smtp.sendmail(sender, [to_email], message.as_string())
        smtp.quit()
        print("✅ 重置验证码邮件发送成功")
    except Exception as e:
        print("❌ 邮件发送失败：", e)


app = FastAPI()


# ✅ 挂载接口
app.include_router(needs.router, prefix="/api/needs", tags=["需求"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务"])

app.include_router(feedback.router, prefix="/api/feedback", tags=["反馈"])  # ✅ 加在挂载处


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://eldercare-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
def home():
    return {"message": "养老服务系统后端运行成功"}


@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[UserResponse])
def get_users(
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(User)

    # ✅ 正确添加 role=provider 的筛选逻辑
    if role:
        query = query.filter(User.role == role)

    if search:
        query = query.filter(User.name.contains(search) | User.email.contains(search))

    users = query.all()

    results = []
    for user in users:
        # ✅ 统计该用户接过多少个任务
        service_count = db.query(Task).filter(Task.provider_id == user.id).count()

        # ✅ 统计其平均评分：关联 Task -> Feedback，条件是 task.provider_id == user.id
        avg_rating = db.query(func.avg(Feedback.rating))\
            .join(Task, Feedback.task_id == Task.id)\
            .filter(Task.provider_id == user.id)\
            .scalar()

        results.append(UserResponse(
            id=user.id,
            name=user.name,
            age=user.age,
            email=user.email,
            phone=user.phone,
            role=user.role,
            serviceCount=service_count,
            averageRating=round(avg_rating or 0.0, 1)
        ))

    return results


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return db_user


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.delete_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return {"message": "用户已删除"}


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: dict, db: Session = Depends(get_db)):
    db_user = crud.update_user(db, user_id, user_data)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return db_user

@app.get("/users/", response_model=List[UserResponse])
def get_users(
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if search:
        query = query.filter(User.name.contains(search) | User.email.contains(search))

    users = query.all()

    # 手动添加 serviceCount 和 averageRating 字段
    results = []
    for user in users:
        service_count = db.query(Task).filter(Task.provider_id == user.id).count()
        avg_rating = db.query(Feedback).join(Task).filter(Task.provider_id == user.id).with_entities(
            func.avg(Feedback.rating)
        ).scalar()

        results.append(UserResponse(
            id=user.id,
            name=user.name,
            age=user.age,
            email=user.email,
            phone=user.phone,
            role=user.role,
            serviceCount=service_count,
            averageRating=round(avg_rating or 0.0, 1)
        ))

    return results


@app.post("/appointments/")
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    return crud.create_appointment(db, appointment)


@app.get("/appointments/{user_id}")
def get_appointments(user_id: int, db: Session = Depends(get_db)):
    return crud.get_appointments(db, user_id)


@app.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    db_appointment = crud.delete_appointment(db, appointment_id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="预约未找到")
    return {"message": "预约已取消"}


@app.post("/health/")
def create_health_data(health_data: HealthDataCreate, db: Session = Depends(get_db)):
    db_health = crud.create_health_data(db, health_data)
    return db_health


@app.get("/health/{user_id}")
def get_health_data(user_id: int, db: Session = Depends(get_db)):
    return crud.get_health_data(db, user_id)


@app.post("/auth/register", response_model=Token)
def register(user: UserRegister, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = crud.create_user(db, user)  # ✅ 删除手动加密这一步，交由 crud 内部处理
    access_token = create_access_token(
        data={"sub": created_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/auth/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    print("✅ 接收到来自前端的登录请求:", user_data.dict())

    user = crud.get_user_by_email(db, user_data.email)
    if not user:
        print("❌ 用户不存在")
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    if not pwd_context.verify(user_data.password, user.hashed_password):
        print("❌ 密码错误")
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@app.post("/auth/forgot-password")
def forgot_password(data: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="该邮箱未注册")

    code = str(random.randint(100000, 999999))
    expire = datetime.utcnow().timestamp() + 300
    reset_code_store[data.email] = (code, expire)
    background_tasks.add_task(send_reset_email, data.email, code)
    return {"message": "验证码已发送"}


@app.post("/auth/verify-code")
def verify_code(data: VerifyCodeRequest):
    if data.email not in reset_code_store:
        raise HTTPException(status_code=400, detail="请先请求验证码")
    code, expire = reset_code_store[data.email]
    if datetime.utcnow().timestamp() > expire:
        raise HTTPException(status_code=400, detail="验证码已过期")
    if data.code != code:
        raise HTTPException(status_code=400, detail="验证码错误")
    return {"message": "验证码验证通过"}


@app.post("/auth/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    if data.email not in reset_code_store:
        raise HTTPException(status_code=400, detail="请先请求验证码")
    code, expire = reset_code_store[data.email]
    if datetime.utcnow().timestamp() > expire:
        raise HTTPException(status_code=400, detail="验证码已过期")
    if data.code != code:
        raise HTTPException(status_code=400, detail="验证码错误")
    user = crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "密码重置成功"}


    # 获取当前用户的个人资料
@app.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


# 更新当前用户的个人资料
@app.put("/profile", response_model=UserResponse)
def update_profile(
    updated: UserCreate,  # 👈 注意：你也可以新建一个 ProfileUpdate schema 更合理
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_user = crud.update_user(db, user_id=current_user.id, user_data=updated.dict())
    if not db_user:
        raise HTTPException(status_code=404, detail="用户未找到")
    return db_user
