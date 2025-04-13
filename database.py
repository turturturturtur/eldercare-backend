import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ 从环境变量中读取数据库连接字符串
DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ 创建数据库引擎
engine = create_engine(DATABASE_URL)

# ✅ 创建数据库会话类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ 定义 ORM 基类
Base = declarative_base()

# ✅ 提供给 FastAPI 路由使用的数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
