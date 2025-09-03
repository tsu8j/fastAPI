# app/schemas.py

from typing import Optional

from pydantic import BaseModel, Field

class Task(BaseModel):

   #  レスポンス用：サーバーが返す完全なタスク形

    id: int = Field(..., ge=1, description="自動採番された一意のID")

    title: str = Field(..., min_length=1, max_length=200, description="タスク名")

    description: Optional[str] = Field(None, max_length=2000, description="詳細（任意）")

    completed: bool = Field(False, description="完了フラグ（既定 False）")

class TaskCreate(BaseModel):

   #  作成リクエスト用：クライアントから受け取る形
   #  for creation request

    title: str = Field(..., min_length=1, max_length=200)

    description: Optional[str] = Field(None, max_length=2000)

class TaskUpdate(BaseModel):

   #  更新リクエスト用：任意フィールドだけ送れる
   #  for update request 

    title: Optional[str] = Field(None, min_length=1, max_length=200)

    description: Optional[str] = Field(None, max_length=2000)

    completed: Optional[bool] = None
 