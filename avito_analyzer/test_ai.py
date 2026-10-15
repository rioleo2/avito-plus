import json
from openai import OpenAI

# Подключение к локальному серверу LM Studio
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="not-needed"
)

def test_connection():
    print("Отправляем тестовый запрос в LM Studio...")
    
    prompt = """
    У меня есть текст объявления с Авито:
    "Продам MacBook Pro 14 M1 Pro 16/512GB, цвет Space Gray. Состояние идеальное, батарея 92% (115 циклов). Полный комплект с коробкой и зарядкой. Никаких дефектов нет, любые проверки."

    Извлеки из текста характеристики и верни СТРОГО в формате JSON с полями:
    - model (строка)
    - ram (число GB)
    - ssd (число GB)
    - battery_health (процент или null)
    - cycles (число или null)
    - defects (есть ли дефекты, строка)
    - is_full_set (булево)
    
    В ответе выдай ТОЛЬКО чистый JSON без вступительных слов и комментариев.
    """

    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": "Ты полезный ассистент-аналитик. Отвечай строго на русском языке и выдавай валидный JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content
        print("\nУСПЕХ! Ответ от локальной нейросети:\n")
        print(content)
    except Exception as e:
        print(f"\nОшибка подключения: {e}")
        print("\nУбедись, что в LM Studio нажат 'Start Server' на порту 1234!")

if __name__ == "__main__":
    test_connection()
