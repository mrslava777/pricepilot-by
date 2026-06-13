FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код
COPY . .

# Папка для БД
RUN mkdir -p /app/data

# По умолчанию запускаем бота. Сервис api переопределяет команду в compose.
CMD ["python", "run.py"]
