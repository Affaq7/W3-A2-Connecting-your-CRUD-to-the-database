import sqlite3
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Response
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

app = FastAPI()
DataBase = "tasks.db"

def get_db():
    """Helper connection function that returns rows formatted like dictionaries."""
    conn=sqlite3.connect(DataBase)
    conn.row_factory=sqlite3.Row
    return conn

def init_db():
    """Creates table and seeds default tasks if the database is empty."""
    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("SELECT COUNT(*) AS count FROM tasks")
    row_count = cursor.fetchone()["count"]

    if row_count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES( ?,?)",
            [
                ("Buy milk", 0),
                ("Learn FastAPI", 0),
                ("Complete Stage 0", 1)
            ]
        )
        conn.commit()
    conn.close()

init_db()

class TaskCreate(BaseModel):
    title: str | None = None 

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

# Keeping this temporarily so the app doesn't crash between commits
tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Learn FastAPI", "done": False},
    {"id": 3, "title": "Complete Stage 2", "done": True}
]

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def get_all_tasks():
    return tasks 

@app.get("/tasks/{id}", responses={404: {"description": "Task not found"}})
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

@app.post("/tasks", responses={400: {"description": "Invalid input - Title is missing or empty"}})
def create_task(task_in: TaskCreate):
    if not task_in.title or not task_in.title.strip():
        return JSONResponse(status_code=400, content={"error": "Title is missing or empty"})
    
    if len(tasks) > 0:
        next_id = max(task["id"] for task in tasks) + 1
    else:
        next_id = 1
    
    new_task = {
        "id": next_id,
        "title": task_in.title.strip(),
        "done": False
    }
    tasks.append(new_task)
    return JSONResponse(status_code=201, content=new_task)

@app.put("/tasks/{id}" , responses={400: {"description": "Invalid body"}, 404: {"description": "Task not found"}})
def update_task(id: int, task_in: TaskUpdate):
    if task_in.title is None and task_in.done is None:
        return JSONResponse(status_code=400, content={"error": "Body cannot be empty"})
    if task_in.title is not None and not task_in.title.strip():
        return JSONResponse(status_code=400, content={"error": "Title cannot be empty"})
    
    for task in tasks:
        if task["id"] == id:
            if task_in.title is not None:
                task["title"] = task_in.title.strip()
            if task_in.done is not None:
                task["done"] = task_in.done
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

@app.delete("/tasks/{id}", responses={404: {"description": "Task not found"}})
def delete_task(id: int):
    for i, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(i)
            return Response(status_code = 204)
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})