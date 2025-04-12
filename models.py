from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# 用户模型
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="provider")  # admin / provider

    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    health_data = relationship("HealthData", back_populates="user", cascade="all, delete-orphan")
    
    service_needs = relationship("ServiceNeed", back_populates="creator", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="provider", cascade="all, delete-orphan")

# 预约模型
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
    details = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="appointments")

# 健康数据模型
class HealthData(Base):
    __tablename__ = "health_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    heart_rate = Column(Integer, nullable=True)
    blood_pressure = Column(String, nullable=True)
    blood_sugar = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    steps = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="health_data")

# 服务需求模型（社区端发布）
class ServiceNeed(Base):
    __tablename__ = "service_needs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    address = Column(String(200), nullable=False)
    time = Column(String(100), nullable=False)
    status = Column(String(20), default="open")  # open / accepted / completed
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="service_needs")
    task = relationship("Task", back_populates="need", uselist=False)

# 接单任务模型（服务者接单）
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    need_id = Column(Integer, ForeignKey("service_needs.id"))
    provider_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="ongoing")  # ongoing / done
    accepted_at = Column(DateTime, default=datetime.utcnow)

    need = relationship("ServiceNeed", back_populates="task")
    provider = relationship("User", back_populates="tasks")
    feedback = relationship("Feedback", back_populates="task", uselist=False)

# 反馈模型（老人提交评价）
class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    elder_name = Column(String(50), nullable=False)
    comment = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="feedback")
