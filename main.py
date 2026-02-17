import pandas as pd
import plotly.express as px
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from db import init_db, SessionLocal, Dialog
from graph import graph

init_db()

app = FastAPI(title="AI Рецепты + Статистика по кухням")


class RequestSchema(BaseModel):
    question: str


# Эндпоинт для вопросов
@app.post("/ask")
def ask_question(req: RequestSchema):
    # Начальное состояние для графа
    state = {"question": req.question, "cuisine": "", "answer": ""}
    # Вызов графа LangGraph
    result = graph.invoke(state)
    return {"answer": result["answer"], "cuisine": result["cuisine"]}


@app.get("/stats", response_class=HTMLResponse)
def stats():
    db = SessionLocal()
    dialogs = db.query(Dialog).all()
    db.close()

    if not dialogs:
        return "<h3>Нет данных</h3>"

    df = pd.DataFrame([
        {"question": d.question, "answer": d.answer, "cuisine": d.cuisine, "created_at": d.created_at}
        for d in dialogs
    ])

    # График количества вопросов по кухне
    fig = px.bar(
        df.groupby("cuisine").size().reset_index(name="count"),
        x="cuisine",
        y="count",
        title="Количество вопросов по кухням"
    )
    return fig.to_html()


# Запуск сервера напрямую
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
