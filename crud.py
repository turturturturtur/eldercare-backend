from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext

from models import User, Appointment, HealthData
from schemas import UserRegister, AppointmentCreate, HealthDataCreate

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12  # ✅ 指定默认轮次，确保一致性
)


# 哈希密码
def hash_password(password: str):
    return pwd_context.hash(password)

# 验证密码
def verify_password(plain_password, hashed_password):
    print("🧪 登录输入的密码：", plain_password)
    print("🔍 数据库存储的哈希：", hashed_password)
    result = pwd_context.verify(plain_password, hashed_password)
    print("✅ 验证结果：", result)
    return result


# 注册用户（含查重）
def create_user(db: Session, user: UserRegister):
    existing_user = db.query(User).filter((User.email == user.email) | (User.phone == user.phone)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or phone already registered")

    # ✅ 调试打印注册密码和加密结果
    print("📨 注册原始密码：", user.password)
    hashed = hash_password(user.password)
    print("🔐 加密后密码：", hashed)

    db_user = User(
        name=user.name,
        age=user.age,
        email=user.email,
        phone=user.phone,
        hashed_password=hashed,
        role=user.role or "provider"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# 登录验证
def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        print("❌ 用户不存在")
        return None
    if not verify_password(password, user.hashed_password):
        print("❌ 密码错误")
        return None
    print("✅ 登录验证通过")
    return user


# 根据邮箱获取用户
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


# 获取所有用户
def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()


# 获取单个用户
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


# 删除用户
def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


# 更新用户
def update_user(db: Session, user_id: int, user_data: dict):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    for key, value in user_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


# 创建预约
def create_appointment(db: Session, appointment: AppointmentCreate):
    db_appointment = Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


# 获取预约
def get_appointments(db: Session, user_id: int):
    return db.query(Appointment).filter(Appointment.user_id == user_id).all()


# 删除预约
def delete_appointment(db: Session, appointment_id: int):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if db_appointment:
        db.delete(db_appointment)
        db.commit()
    return db_appointment


# 创建健康数据
def create_health_data(db: Session, health_data: HealthDataCreate):
    db_health = HealthData(**health_data.dict())
    db.add(db_health)
    db.commit()
    db.refresh(db_health)
    return db_health


# 获取健康数据
def get_health_data(db: Session, user_id: int):
    return db.query(HealthData).filter(HealthData.user_id == user_id).all()
