from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Feedback, Task, User
from schemas import FeedbackCreate, FeedbackOut
from security import get_current_user

router = APIRouter()


# ✅ 提交反馈（社区端）
@router.post("/{task_id}", response_model=FeedbackOut)
def create_feedback(
    task_id: int,
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅社区管理员可提交反馈")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.feedback:
        raise HTTPException(status_code=400, detail="该任务已存在反馈")

    feedback = Feedback(
        task_id=task_id,
        elder_name=data.elder_name,
        comment=data.comment,
        rating=data.rating
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


# ✅ 服务者查看自己的评价
@router.get("/mine", response_model=List[FeedbackOut])
def get_my_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "provider":
        raise HTTPException(status_code=403, detail="仅服务者可查看评价")

    return db.query(Feedback).join(Task).filter(Task.provider_id == current_user.id).all()


# ✅ 社区查看所有评价（建议使用 /all，避免和 GET / 冲突）
@router.get("/all", response_model=List[FeedbackOut])
def list_all_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅社区管理员可查看所有反馈")

    return db.query(Feedback).all()

# ✅ 获取某个服务者收到的所有反馈（社区端查看）
@router.get("/by-provider/{provider_id}", response_model=List[FeedbackOut])
def get_feedback_by_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅社区管理员可查看服务者评价")

    feedbacks = db.query(Feedback).join(Task).filter(Task.provider_id == provider_id).all()
    return feedbacks
