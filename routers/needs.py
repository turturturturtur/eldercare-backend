from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from database import get_db
from models import ServiceNeed, User
from schemas import ServiceNeedCreate, ServiceNeedOut
from security import get_current_user

router = APIRouter()


# ✅ 获取所有未接单服务需求（服务者端用）
@router.get("/", response_model=List[ServiceNeedOut])
def list_open_needs(db: Session = Depends(get_db)):
    return db.query(ServiceNeed).filter(ServiceNeed.status == "open").all()


# ✅ 创建新服务需求（社区管理员用）
@router.post("/", response_model=ServiceNeedOut)
def create_need(
    data: ServiceNeedCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限：仅管理员可发布服务需求")

    new_need = ServiceNeed(
        title=data.title,
        description=data.description,
        address=data.address,
        time=data.time,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        status="open"
    )
    db.add(new_need)
    db.commit()
    db.refresh(new_need)
    return new_need
