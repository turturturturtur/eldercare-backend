from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List

from database import get_db
from models import Task, ServiceNeed, User, Feedback
from schemas import TaskCreate, TaskOut, FeedbackCreate, FeedbackOut
from security import get_current_user

router = APIRouter()


# ✅ 服务者接单（创建 Task）
@router.post("/", response_model=TaskOut)
def accept_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "provider":
        raise HTTPException(status_code=403, detail="仅服务者可接单")

    need = db.query(ServiceNeed).filter(ServiceNeed.id == data.need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="该服务需求不存在")
    if need.status != "open":
        raise HTTPException(status_code=400, detail="该服务需求已被接单")

    # 创建接单任务记录
    task = Task(
        need_id=data.need_id,
        provider_id=current_user.id,
        accepted_at=datetime.utcnow(),
        status="ongoing"
    )
    db.add(task)
    need.status = "accepted"  # 同时更新需求状态
    db.commit()
    db.refresh(task)
    return task


# ✅ 获取我已接的任务（服务者看自己）
@router.get("/my", response_model=List[TaskOut])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "provider":
        raise HTTPException(status_code=403, detail="仅服务者可查看")

    # 加载任务关联的服务需求（title、address、time）
    return db.query(Task).options(joinedload(Task.need)).filter(Task.provider_id == current_user.id).all()


# ✅ 服务者完成任务
@router.put("/complete/{task_id}", response_model=TaskOut)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "provider":
        raise HTTPException(status_code=403, detail="仅服务者可操作")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改他人任务")
    if task.status == "completed":
        raise HTTPException(status_code=400, detail="该任务已完成")

    task.status = "completed"
    db.commit()
    db.refresh(task)
    return task


# ✅ 社区管理员提交反馈
@router.post("/feedback/{task_id}", response_model=FeedbackOut)
def submit_feedback(
    task_id: int,
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅社区管理员可提交反馈")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务未完成，无法反馈")

    new_feedback = Feedback(
        task_id=task.id,
        elder_name=feedback.elder_name,
        comment=feedback.comment,
        rating=feedback.rating,
        created_at=datetime.utcnow(),
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback


# ✅ 获取所有服务反馈
@router.get("/feedbacks", response_model=List[FeedbackOut])
def list_feedbacks(db: Session = Depends(get_db)):
    return db.query(Feedback).all()

@router.get("/completed", response_model=List[TaskOut])
def list_completed_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅社区管理员可访问")
    return db.query(Task).filter(Task.status == "completed").all()

# ✅ 获取某个服务者的所有任务（社区端查看）
@router.get("/by-provider/{provider_id}", response_model=List[TaskOut])
def get_tasks_by_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅社区管理员可查看服务者任务")

    return db.query(Task).filter(Task.provider_id == provider_id).all()
