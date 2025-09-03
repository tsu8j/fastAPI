# app/storage.py

from typing import List, Optional

from .schemes import Task

# メモリ上の簡易ストレージ（アプリ再起動で消える）
# Simple storage in memory (disappears when the app is restarted)

tasks: List[Task] = []

# 自動採番用のカウンタ
# Automatic numbering counter

_next_id: int = 1

def alloc_id() -> int:

   #  新しい一意IDを払い出す（1,2,3,... と連番）
   # Issue a new unique ID (sequential numbers 1, 2, 3, ...)

    global _next_id

    value = _next_id

    _next_id += 1

    return value

def find_index(task_id: int) -> Optional[int]:

   #  指定idのタスクが tasks の何番目にあるかを返す。見つからなければ None。
   # Returns the position of the task with the specified id in tasks. If not found, returns None.

    for i, t in enumerate(tasks):

        if t.id == task_id:

            return i

    return None
 