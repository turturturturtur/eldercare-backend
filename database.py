from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# PostgreSQL 连接信息
DATABASE_URL = "postgresql://admin:admin@localhost/eldercare"

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 定义 ORM 模型基类
Base = declarative_base()

# 依赖注入：用于 FastAPI 路由
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
