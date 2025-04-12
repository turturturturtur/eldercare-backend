from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ✅ 通用用户基类（新增角色）
class UserBase(BaseModel):
    name: str
    age: int
    email: EmailStr
    phone: str
    role: Optional[str] = "provider"  # 默认是服务提供者，可为 "admin" 或 "provider"

# ✅ 注册时用（需要密码）
class UserRegister(UserBase):
    password: str

# ✅ 数据库中创建用户用（也带密码）
class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    serviceCount: Optional[int] = 0
    averageRating: Optional[float] = 0.0

    class Config:
        from_attributes = True


# ✅ 登录请求体
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ✅ 返回的 Token 数据（可扩展 role）
class Token(BaseModel):
    access_token: str
    token_type: str

# ✅ 创建预约
class AppointmentCreate(BaseModel):
    user_id: int
    type: str
    details: str

# ✅ 返回预约信息
class AppointmentResponse(AppointmentCreate):
    id: int
    date: datetime

    class Config:
        from_attributes = True

# ✅ 创建健康数据
class HealthDataCreate(BaseModel):
    user_id: int
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None  # 例如 "120/80"
    blood_sugar: Optional[float] = None
    weight: Optional[float] = None
    steps: Optional[int] = None

# ✅ 返回健康数据
class HealthDataResponse(HealthDataCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# ✅ 忘记密码 - 发送验证码请求
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

# ✅ 验证验证码请求
class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

# ✅ 重置密码请求
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

# ✅ 创建需求时用
class ServiceNeedCreate(BaseModel):
    title: str
    description: str
    address: str
    time: str

# ✅ 返回前端的结构
class ServiceNeedOut(ServiceNeedCreate):
    id: int
    status: str
    created_at: datetime
    created_by: int

    class Config:
        orm_mode = True


# ✅ 接单请求体
class TaskCreate(BaseModel):
    need_id: int

# ✅ 服务需求的简要信息（用于任务嵌套返回）
class NeedInfo(BaseModel):
    title: str
    address: str
    time: str

    class Config:
        orm_mode = True

# ✅ 返回任务信息（含嵌套服务需求）
class TaskOut(BaseModel):
    id: int
    need_id: int
    provider_id: int
    status: str
    accepted_at: datetime
    need: NeedInfo  # ✅ 新增字段

    class Config:
        orm_mode = True

# ✅ 提交反馈（社区端）
class FeedbackCreate(BaseModel):
    elder_name: str
    comment: str
    rating: int

# ✅ 返回反馈（通用）
class FeedbackOut(BaseModel):
    id: int
    task_id: int
    elder_name: str
    comment: str
    rating: int
    created_at: datetime

    class Config:
        from_attributes = True  # ✅ 替代 orm_mode
