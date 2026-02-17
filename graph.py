import json
import os
import re
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from db import SessionLocal, Dialog

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY не найден! Проверьте файл .env")

# pydantic or just remove api_key here
llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)


class State(TypedDict):
    question: str
    cuisine: str
    answer: str


# ----------------------
# Шаг 1: Классификация кухни
# ----------------------
def classify_cuisine(state: State):
    prompt = f"Определи кухню для блюда: {state['question']}. Верни только название кухни (одним-двумя словами)."

    # Используем цепочку с парсером, чтобы всегда получать чистую строку
    chain = llm | StrOutputParser()
    cuisine = chain.invoke(prompt)

    return {**state, "cuisine": cuisine.strip()}


# ----------------------
# Шаг 2: Генерация рецепта
# ----------------------
def generate_recipe(state: State):
    prompt = (
        f"Дай подробный рецепт блюда {state['question']} для кухни {state['cuisine']}. "
        f"Верни ответ строго в формате JSON: {{\"answer\": \"текст рецепта\"}}"
    )

    chain = llm | StrOutputParser()
    content = chain.invoke(prompt)

    # Очистка JSON от маркдауна (бывает, что модели пишут ```json ...)
    clean_content = re.sub(r"```json|```", "", content, flags=re.IGNORECASE).strip()

    try:
        data = json.loads(clean_content)
        answer = data.get('answer', clean_content)
    except Exception:
        answer = clean_content

    return {**state, "answer": answer}


# ----------------------
# Шаг 2.5: Добавление рекламы (если японская кухня)
# ----------------------
def add_ad_message(state: State):
    ad_text = "\n\n🍣 Хотите настоящие суши? Закажите в 'Ninja Sushi' со скидкой 20% (промокод SUSHI20)!"

    current_answer = state.get('answer', "")
    return {**state, "answer": current_answer + ad_text}


# ----------------------
# Шаг 3: Сохранение в базу
# ----------------------
def save_to_db(state: State):
    db = SessionLocal()
    try:
        new_dialog = Dialog(
            question=state['question'],
            answer=state['answer'],
            cuisine=state['cuisine']
        )
        db.add(new_dialog)
        db.commit()
    except Exception as e:
        print(f"DB Error: {e}")
        db.rollback()
    finally:
        db.close()
    return state


# ----------------------
# Логика роутинга
# ----------------------
def route_based_on_cuisine(state: State):
    cuisine = state.get("cuisine", "").lower()
    # Проверка на ключевые слова японской кухни
    if any(word in cuisine for word in ["япон", "japan", "sushi", "суши"]):
        return "add_ad"
    return "save"


# ----------------------
# Построение графа
# ----------------------
builder = StateGraph(State)

builder.add_node("classify_cuisine", classify_cuisine)
builder.add_node("generate_recipe", generate_recipe)
builder.add_node("add_ad_message", add_ad_message)
builder.add_node("save_to_db", save_to_db)

builder.set_entry_point("classify_cuisine")
builder.add_edge("classify_cuisine", "generate_recipe")

# Условный переход после генерации рецепта
builder.add_conditional_edges(
    "generate_recipe",
    route_based_on_cuisine,
    {
        "add_ad": "add_ad_message",
        "save": "save_to_db"
    }
)

builder.add_edge("add_ad_message", "save_to_db")
builder.add_edge("save_to_db", END)

# Компиляция
graph = builder.compile().with_config(recursion_limit=10)
