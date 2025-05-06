
# Используем официальный Python-образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем скрипт
COPY script.py .

# Устанавливаем зависимости
RUN pip install requests

# Запускаем скрипт
CMD ["python", "script.py"]
