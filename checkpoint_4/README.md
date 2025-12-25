# Отчёт по Чекпоинту 4

## 1. Запуск приложения
Запуск нашего FastAPI-приложения:
```
python -m uvicorn app.main:app --reload
```

После этого сервер будет доступен по адресу: http://127.0.0.1:8000.

## 2. Примеры использования API

В терминале в одной вкладке запустить приложение, а в другой отправлять curl-запросы. Например:

```
curl -X POST "http://127.0.0.1:8000/forward" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why am I so sad?",
    "character": "CAROLYN"
  }'
```

```
curl -X GET "http://127.0.0.1:8000/history"
```
 
curl -X DELETE "http://127.0.0.1:8000/history" \
-H "X-Auth-Token: your_secure_token"
