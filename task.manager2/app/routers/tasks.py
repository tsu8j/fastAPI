# app/routers/tasks.py

from typing import List

from fastapi import APIRouter, HTTPException, status

from app.schemes import Task, TaskCreate, TaskUpdate

from app.storage import tasks, alloc_id, find_index

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)

def create_task(payload: TaskCreate) -> Task:

    # タスクを新規作成（idはサーバー側で採番、completedはFalse固定）
    # create new task
    
    

    new_task = Task(

        id=alloc_id(),

        title=payload.title,

        description=payload.description,

        completed=False,

    )

    tasks.append(new_task)

    return new_task

@router.get("/", response_model=List[Task])

def list_tasks() -> List[Task]:

    # 全タスクを配列で返す
    # return all tasks as an array
    return tasks

@router.get("/{task_id}", response_model=Task)

def get_task(task_id: int) -> Task:

    # id指定で単一タスクを返す。無ければ404
    # return a single task by id. if no task exist return 404

    idx = find_index(task_id)

    if idx is None:

        raise HTTPException(status_code=404, detail="Task not found")

    return tasks[idx]

@router.put("/{task_id}", response_model=Task)

def update_task(task_id: int, payload: TaskUpdate) -> Task:

    # 任意フィールド（title/description/completed）の部分更新。無ければ404
    # partial update of any field (title/description/completed) .if no task exist return 404

    idx = find_index(task_id)

    if idx is None:

        raise HTTPException(status_code=404, detail="Task not found")

    current = tasks[idx]

    # None（未指定）は無視。指定があれば上書き。
    # None will be ignored. if specified it will be overwritten

    updated = current.copy(update={

        "title": payload.title if payload.title is not None else current.title,

        "description": payload.description if payload.description is not None else current.description,

        "completed": payload.completed if payload.completed is not None else current.completed,

    })

    tasks[idx] = updated

    return updated

@router.delete("/{task_id}")

def delete_task(task_id: int):

    # id指定で削除。無ければ404。成功時はメッセージを返す
    # delete by id. if no task exist return 404. if succeseful return message 
    idx = find_index(task_id)

    if idx is None:

        raise HTTPException(status_code=404, detail="Task not found")

    del tasks[idx]

    return {"message": "Task deleted successfully."}
 