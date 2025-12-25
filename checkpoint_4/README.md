# Отчёт по Чекпоинту 4

## 1. Запуск приложения

Шаг 1. Установка зависимостей:

```pip install -r requirements.txt```

Шаг 2. Положите в checkpoint_4/.env Ваш groq-токен GROQ_API_KEY (можно получить бесплатно на сайте https://groq.com/).

Шаг 3. Запуск fastapi-приложения:

```
python -m uvicorn app.main:app --reload
```

После этого сервер будет доступен по адресу: http://127.0.0.1:8000.
(мы сделали минимальный интерфейс, поэтому запрос forward можно отправлять через окно на сайте)

<img width="1352" height="617" alt="image" src="https://github.com/user-attachments/assets/0fa1a850-096b-4a46-be22-969511489719" />

## 2. Примеры использования API

В терминале в одной вкладке запустить приложение, а в другой отправлять curl-запросы.

### Эндпоинт `/forward` (POST)

```
curl -X POST "http://127.0.0.1:8000/forward" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why am I so sad?",
    "character": "CAROLYN"
  }'
```

### Эндпоинт `/history` (GET)

```
curl -X GET "http://127.0.0.1:8000/history"
```

### Эндпоинт `/history` (DELETE)
```
curl -X DELETE "http://127.0.0.1:8000/history" \
-H "X-Auth-Token: your_secure_token"
```
Данные админа находятся в файле *checkpoint_4/app/api/auth.py* в переменной ADMIN_DATA. Если данные человека (почта и пароль) не совпадают с админскими, то приложение запрещает человеку доступ к эндпоинтам удаления истории и к эндпоинту статистики.

Получить токен, если Вы администратор, можно следующей командой:

```
curl -X POST "http://127.0.0.1:8000/auth/login" \
-H "Content-Type: application/json" \
-d '{"email": "admin@example.com", "password": "admin123"}'
```

Сохраните аутпут и используйте внутри curl-запросов.

### Эндпоинт `/stats` (GET)

```
curl -X GET "http://127.0.0.1:8000/stats" \
  -H "Authorization: Bearer <Your_token>"
```

### Эндпоинт `/auth/login` (POST)
Генерирует JWT-токен администратора по email и паролю.

```
curl -X POST "http://127.0.0.1:8000/auth/login" \
-H "Content-Type: application/json" \
-d '{"email": "admin@example.com", "password": "admin123"}'
```

# Распределение обязанностей

| Участник        | Обязанности |
|-----------------|-------------|
| Мария Годунова  | Работа с основной логикой приложения: <br> - Эндпоинт `/forward` (POST) для обработки текста с сохранением истории запросов в БД <br> - Эндпоинт `/history` (GET) для получения истории запросов <br> - Эндпоинт `/history` (DELETE) для удаления истории запросов
| Алина Аванесян  | - Эндпоинт `stats` <br> - Миграции БД чере Alembic <br> - реализация JWT-авторизация и проверка прав администратора|
