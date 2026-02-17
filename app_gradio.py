import gradio as gr

from graph import graph


def ask_dish(question: str):
    # Формируем начальное состояние графа
    state = {"question": question, "cuisine": "", "answer": ""}
    result = graph.invoke(state)

    # Возвращаем удобный текст
    cuisine = result.get("cuisine", "Не определено")
    answer = result.get("answer", "Нет ответа")
    return f"**Кухня:** {cuisine}\n\n**Рецепт:**\n{answer}"


# Создаём UI Gradio
demo = gr.Interface(
    fn=ask_dish,
    inputs=gr.Textbox(label="Введите блюдо"),
    outputs=gr.Textbox(label="Ответ AI"),
    title="AI Рецепты",
    description="Введите название блюда, AI сгенерирует рецепт и определит кухню"
)

# Запуск локального сервера
if __name__ == "__main__":
    demo.launch()
