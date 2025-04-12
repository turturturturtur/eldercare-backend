from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

# 获取数据库会话
db: Session = SessionLocal()

# 删除所有用户
db.query(User).delete()
db.commit()
db.close()

print("✅ 所有用户数据已删除")
