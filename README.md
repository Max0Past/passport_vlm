<<<<<<< HEAD
# 📋 Passport Reader API - MVP

Локальний веб-сервіс для автоматизованого розпізнавання паспортних даних за допомогою Vision-Language Model (VLM) [Microsoft Florence-2-Large](https://github.com/microsoft/Florence).

## 🎯 Перегляд проекту

```
passport_api/
│
├── 📄 api.py                    # FastAPI сервер (точка входу)
├── 📄 inference.py              # Клас-обгортка для моделі Florence-2
├── 📄 model_setup.py            # Скрипт завантаження та патчингу моделі
├── 📄 requirements.txt           # Python залежності
├── 📄 README.md                 # Ця документація
│
├── 📁 models/
│   └── 📁 florence2-large/       # Локальна копія моделі (скачується при виконанні setup)
│       ├── config.json
│       ├── modeling_florence2.py
│       ├── processing_florence2.py
│       ├── model.safetensors
│       └── ... (інші файли моделі)
│
└── 📁 static/
    └── 📄 index.html             # HTML веб-інтерфейс
```

## 🚀 Швидкий старт (3 кроки)

### 1️⃣ Установка залежностей

```bash
# Установка PyTorch з CUDA 12.1 (ВАЖЛИВО: спочатку!)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Установка інших залежностей
pip install -r requirements.txt
```

### 2️⃣ Завантаження моделі

```bash
# Завантажує Florence-2-Large та видаляє залежність від flash_attn
python model_setup.py
```

Очікувати ~15-30 хвилин (залежить від швидкості мережі).

### 3️⃣ Запуск сервера

```bash
python api.py
```

Очікувати повідомлення:

```
🚀 Запуск Passport Reader API на http://127.0.0.1:8000
```

Відкрийте в браузері: **<http://127.0.0.1:8000>**

---

## 📖 Використання

### Веб-інтерфейс

1. **Введіть абсолютний шлях** до файлу зображення:

   ```
   D:\Images\passport_scan.jpg
   C:\Users\User\Desktop\photo.png
   ```

2. **Натисніть "Опрацювати"**

3. **Отримайте результати:**
   - 📸 Обробленое зображення
   - 📝 Розпізнаний номер паспорта
   - ⏱️ Час обробки

### API (cURL приклади)

#### Обробка зображення

```bash
curl -X POST http://127.0.0.1:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "D:\\Images\\passport.jpg"
  }'
```

**Успішна відповідь (200):**

```json
{
  "status": "success",
  "passport_number": "001234567",
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "ocr_text": "Украї́ни...",
  "processing_time": "0.45s",
  "error_message": null
}
```

**Помилка (404):**

```json
{
  "detail": "Файл не знайдено: D:\\Images\\passport.jpg"
}
```

#### Перевірка здоров'я

```bash
curl http://127.0.0.1:8000/api/health
```

Відповідь:

```json
{
  "status": "ok",
  "model_loaded": true,
  "service": "passport_api",
  "version": "0.1.0"
}
```

#### Інформація про сервіс

```bash
curl http://127.0.0.1:8000/api/info
```

---

## 🛠️ Архітектура системи

```
┌─────────────────────────────────────────────────────┐
│              Веб-браузер (HTML/JS)                   │
│         (input file path + button "Process")         │
└──────────────────────┬────────────────────────────┘
                       │ HTTP (GET / POST)
                       ▼
┌─────────────────────────────────────────────────┐
│            FastAPI Server (api.py)               │
│  ┌──────────────────────────────────────┐       │
│  │ GET /  → Повертає index.html         │       │
│  │ POST /api/process → Обробка запиту   │       │
│  │ GET /api/health  → Статус сервера    │       │
│  │ GET /api/info    → INFO сервіс       │       │
│  └──────────────────────────────────────┘       │
└──────────────────┬───────────────────────────────┘
                   │ (клас PassportOCREngine)
                   ▼
┌──────────────────────────────────────────────────┐
│       Inference Engine (inference.py)             │
│  ┌───────────────────────────────────────┐       │
│  │ 1. Завантажити зображення (PIL)       │       │
│  │ 2. Запустити Florence-2 з <OCR>       │       │
│  │ 3. Видалити спец. токени              │       │
│  │ 4. Рег. вирази для номера паспорта    │       │
│  │ 5. Base64 кодування результату        │       │
│  └───────────────────────────────────────┘       │
└──────────────────┬────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│     Florence-2-Large Model (CUDA GPU)             │
│  Parameter: 0.77B                                │
│  Dtype: FP16 (float16)                           │
│  Attention: SDPA (scaled_dot_product_attention)  │
│  VRAM: ~2.5-3.5 GB                               │
└──────────────────────────────────────────────────┘
```

---

## 📊 Форматы розпізнавання паспортів

### 🇺🇦 Українська ID-картка

- **Формат:** 9 цифр
- **Приклади:**
  - `123 456 789`
  - `123456789`

### 🇺🇦 Паспортна книжечка

- **Формат:** 2 літери + 6 цифр
- **Приклади:**
  - `АБ 123456`
  - `АБ123456`
  - `AB 123456`

### 🌍 Міжнародний паспорт

- **Формат:** 9 символів (літери + цифри)
- **Приклади:**
  - `NA1234567`
  - `ХХ9876543`

---

## ⚙️ Технічні параметри

### Обов'язковий стек

| Компонент | Версія | Примітка |
|-----------|--------|---------|
| Python | 3.10+ | Основна мова |
| PyTorch | 2.0.0+ | CUDA 12.1 support |
| transformers | 4.42.4 | HuggingFace |
| numpy | <2.0 | Обмеження сумісності |
| FastAPI | 0.104+ | Веб-фреймворк |
| Uvicorn | 0.24+ | ASGI сервер |

### Апаратні вимоги

| Ресурс | Мінімум | Рекомендовано |
|--------|---------|---------------|
| GPU VRAM | 4 GB | 6+ GB |
| System RAM | 16 GB | 32 GB |
| CPU | Quad-core | 8+ cores |
| Диск | 5 GB | 10+ GB |
| GPU | NVIDIA | RTX 3050+ |

### Продуктивність

| Метрика | Значення |
|---------|----------|
| Cold Start Time | ~3-5 сек (перший запуск) |
| Warm Inference Time | <1.5 сек на зображення |
| Max Image Size | ~2000x2000 px |
| Batch Processing | 1 запит / ~0.5 сек |
| VRAM Peak Usage | ~3.5 GB |

---

## 🐛 Розв'язання проблем

### ❌ `ModuleNotFoundError: No module named 'flash_attn'`

**Причина:** Недопущена залежність не видалена під час патчингу

**Рішення:**

```bash
python model_setup.py  # Перезапустіть патчинг
```

### ❌ `CUDA out of memory`

**Причина:** Недостатньо VRAM або занадто велике зображення

**Рішення:**

1. Закрийте інші GPU програми
2. Зменшіть розмір зображення (< 1024x1024)
3. Перезавантажте сервер

### ❌ `FileNotFoundError: Папка моделі не знайдена`

**Причина:** Модель не завантажена

**Рішення:**

```bash
python model_setup.py
```

### ❌ HTTP 500 при запуску сервера

**Причина:** Помилка при завантаженні моделі

**Рішення:**

1. Перевірте CUDA установку: `python -c "import torch; print(torch.cuda.is_available())"`
2. Перезавантажте сервер
3. Перевірте логи для деталей

### ⚠️ Повільна обробка (>2 сек)

**Причина:** Великий файл або інші процеси використовують GPU

**Рішення:**

1. Оптимізуйте зображення (< 1000px)
2. Закрийте інші GPU програми
3. Перезавантажте машину

---

## 📝 API Документація (Swagger)

Відкрийте в браузері:

```
http://127.0.0.1:8000/docs
```

Тут можете тестувати всі endpoints конкретно.

---

## 🔐 Безпека та приватність

⚠️ **ВАЖЛИВО для production:**

1. **Локальна обробка** - Дані не відправляються на серверу
2. **Обмеження доступу** - Поточно сервер доступний локально (127.0.0.1)
3. **Видалення тимчасових файлів** - Реалізовано автоматично
4. **HTTPS** - Не налаштовано для MVP (використовується для локального desarrollo)

Для production deployment:

```python
# В api.py змініть на:
uvicorn.run(
    app,
    host="0.0.0.0",  # Слухае на всіх інтерфейсах
    port=443,        # HTTPS порт
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

---

## 📚 Посилання та ресурси

- **Florence-2 GitHub:** <https://github.com/microsoft/Florence>
- **FastAPI Документація:** <https://fastapi.tiangolo.com/>
- **HuggingFace Models:** <https://huggingface.co/microsoft/Florence-2-large>
- **PyTorch CUDA Setup:** <https://pytorch.org/get-started/locally/>

---

## 📄 License

Цей проект створений для освітніх цілей.

- **Florence-2 Model:** Published by Microsoft Research
- **Code:** MIT License (невказано)

---

## 👨‍💻 Розробка

### Додавання нових функцій

1. **Модифікація inference.py** для нових форматів паспортів
2. **Редагування regex** у `_extract_passport_number()`
3. **Додавання нових endpoints** у api.py

### Приклад: додавання нового endpoints

```python
@app.post("/api/extract-text")
async def extract_text(request: ProcessRequest):
    """Новий endpoint для вилучення всього тексту."""
    result = ocr_engine.process_image(request.file_path)
    return {"text": result["ocr_text"]}
```

---

## 💬 Обратный зв'язок та поправки

Якщо виникли проблеми:

1. Перевірте логи сервера (консоль)
2. Переглядайте `/api/info` для информацію про систему
3. Протестуйте з простим зображенням

---

## 📚 Документація проекту

| Документ | Опис |
|----------|------|
| [QUICK_START.md](QUICK_START.md) | ⚡ Швидкий старт (5 хвилин) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 🏗️ Архітектура системи деталь |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 🚀 Production розгортання |
| [api.py](api.py) | 💻 FastAPI реалізація |
| [inference.py](inference.py) | 🤖 Інференс модель |
| [config.py](config.py) | ⚙️ Конфігурація |

---

## 🎓 Освітній матеріал

### Що я дізнався з цього проекту

- **Vision-Language Models (VLM)** - Florence-2 архітектура та можливості
- **CUDA & GPU optimization** - FP16, SDPA attention, VRAM management
- **FastAPI** - розробка асинхронних веб-сервісів з Pydantic
- **Model patching** - видалення залежностей та модифікація коду моделі
- **Local ML deployment** - оптимізація для обмежених ресурсів
- **Regex parsing** - вилучення структурованих даних з сирого тексту

---

**Версія:** 0.1.0 MVP  
**Останнє оновлення:** 2026/02/10  
**Статус:** Active Development 🚀
=======
# 📋 Passport Reader API - MVP

Локальний веб-сервіс для автоматизованого розпізнавання паспортних даних за допомогою Vision-Language Model (VLM) [Microsoft Florence-2-Large](https://github.com/microsoft/Florence).

## 🎯 Перегляд проекту

```
passport_api/
│
├── 📄 api.py                    # FastAPI сервер (точка входу)
├── 📄 inference.py              # Клас-обгортка для моделі Florence-2
├── 📄 model_setup.py            # Скрипт завантаження та патчингу моделі
├── 📄 requirements.txt           # Python залежності
├── 📄 README.md                 # Ця документація
│
├── 📁 models/
│   └── 📁 florence2-large/       # Локальна копія моделі (скачується при виконанні setup)
│       ├── config.json
│       ├── modeling_florence2.py
│       ├── processing_florence2.py
│       ├── model.safetensors
│       └── ... (інші файли моделі)
│
└── 📁 static/
    └── 📄 index.html             # HTML веб-інтерфейс
```

## 🚀 Швидкий старт (3 кроки)

### 1️⃣ Установка залежностей

```bash
# Установка PyTorch з CUDA 12.1 (ВАЖЛИВО: спочатку!)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Установка інших залежностей
pip install -r requirements.txt
```

### 2️⃣ Завантаження моделі

```bash
# Завантажує Florence-2-Large та видаляє залежність від flash_attn
python model_setup.py
```

Очікувати ~15-30 хвилин (залежить від швидкості мережі).

### 3️⃣ Запуск сервера

```bash
python api.py
```

Очікувати повідомлення:

```
🚀 Запуск Passport Reader API на http://127.0.0.1:8000
```

Відкрийте в браузері: **<http://127.0.0.1:8000>**

---

## 📖 Використання

### Веб-інтерфейс

1. **Введіть абсолютний шлях** до файлу зображення:

   ```
   D:\Images\passport_scan.jpg
   C:\Users\User\Desktop\photo.png
   ```

2. **Натисніть "Опрацювати"**

3. **Отримайте результати:**
   - 📸 Обробленое зображення
   - 📝 Розпізнаний номер паспорта
   - ⏱️ Час обробки

### API (cURL приклади)

#### Обробка зображення

```bash
curl -X POST http://127.0.0.1:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "D:\\Images\\passport.jpg"
  }'
```

**Успішна відповідь (200):**

```json
{
  "status": "success",
  "passport_number": "001234567",
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "ocr_text": "Украї́ни...",
  "processing_time": "0.45s",
  "error_message": null
}
```

**Помилка (404):**

```json
{
  "detail": "Файл не знайдено: D:\\Images\\passport.jpg"
}
```

#### Перевірка здоров'я

```bash
curl http://127.0.0.1:8000/api/health
```

Відповідь:

```json
{
  "status": "ok",
  "model_loaded": true,
  "service": "passport_api",
  "version": "0.1.0"
}
```

#### Інформація про сервіс

```bash
curl http://127.0.0.1:8000/api/info
```

---

## 🛠️ Архітектура системи

```
┌─────────────────────────────────────────────────────┐
│              Веб-браузер (HTML/JS)                   │
│         (input file path + button "Process")         │
└──────────────────────┬────────────────────────────┘
                       │ HTTP (GET / POST)
                       ▼
┌─────────────────────────────────────────────────┐
│            FastAPI Server (api.py)               │
│  ┌──────────────────────────────────────┐       │
│  │ GET /  → Повертає index.html         │       │
│  │ POST /api/process → Обробка запиту   │       │
│  │ GET /api/health  → Статус сервера    │       │
│  │ GET /api/info    → INFO сервіс       │       │
│  └──────────────────────────────────────┘       │
└──────────────────┬───────────────────────────────┘
                   │ (клас PassportOCREngine)
                   ▼
┌──────────────────────────────────────────────────┐
│       Inference Engine (inference.py)             │
│  ┌───────────────────────────────────────┐       │
│  │ 1. Завантажити зображення (PIL)       │       │
│  │ 2. Запустити Florence-2 з <OCR>       │       │
│  │ 3. Видалити спец. токени              │       │
│  │ 4. Рег. вирази для номера паспорта    │       │
│  │ 5. Base64 кодування результату        │       │
│  └───────────────────────────────────────┘       │
└──────────────────┬────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│     Florence-2-Large Model (CUDA GPU)             │
│  Parameter: 0.77B                                │
│  Dtype: FP16 (float16)                           │
│  Attention: SDPA (scaled_dot_product_attention)  │
│  VRAM: ~2.5-3.5 GB                               │
└──────────────────────────────────────────────────┘
```

---

## 📊 Форматы розпізнавання паспортів

### 🇺🇦 Українська ID-картка

- **Формат:** 9 цифр
- **Приклади:**
  - `123 456 789`
  - `123456789`

### 🇺🇦 Паспортна книжечка

- **Формат:** 2 літери + 6 цифр
- **Приклади:**
  - `АБ 123456`
  - `АБ123456`
  - `AB 123456`

### 🌍 Міжнародний паспорт

- **Формат:** 9 символів (літери + цифри)
- **Приклади:**
  - `NA1234567`
  - `ХХ9876543`

---

## ⚙️ Технічні параметри

### Обов'язковий стек

| Компонент | Версія | Примітка |
|-----------|--------|---------|
| Python | 3.10+ | Основна мова |
| PyTorch | 2.0.0+ | CUDA 12.1 support |
| transformers | 4.42.4 | HuggingFace |
| numpy | <2.0 | Обмеження сумісності |
| FastAPI | 0.104+ | Веб-фреймворк |
| Uvicorn | 0.24+ | ASGI сервер |

### Апаратні вимоги

| Ресурс | Мінімум | Рекомендовано |
|--------|---------|---------------|
| GPU VRAM | 4 GB | 6+ GB |
| System RAM | 16 GB | 32 GB |
| CPU | Quad-core | 8+ cores |
| Диск | 5 GB | 10+ GB |
| GPU | NVIDIA | RTX 3050+ |

### Продуктивність

| Метрика | Значення |
|---------|----------|
| Cold Start Time | ~3-5 сек (перший запуск) |
| Warm Inference Time | <1.5 сек на зображення |
| Max Image Size | ~2000x2000 px |
| Batch Processing | 1 запит / ~0.5 сек |
| VRAM Peak Usage | ~3.5 GB |

---

## 🐛 Розв'язання проблем

### ❌ `ModuleNotFoundError: No module named 'flash_attn'`

**Причина:** Недопущена залежність не видалена під час патчингу

**Рішення:**

```bash
python model_setup.py  # Перезапустіть патчинг
```

### ❌ `CUDA out of memory`

**Причина:** Недостатньо VRAM або занадто велике зображення

**Рішення:**

1. Закрийте інші GPU програми
2. Зменшіть розмір зображення (< 1024x1024)
3. Перезавантажте сервер

### ❌ `FileNotFoundError: Папка моделі не знайдена`

**Причина:** Модель не завантажена

**Рішення:**

```bash
python model_setup.py
```

### ❌ HTTP 500 при запуску сервера

**Причина:** Помилка при завантаженні моделі

**Рішення:**

1. Перевірте CUDA установку: `python -c "import torch; print(torch.cuda.is_available())"`
2. Перезавантажте сервер
3. Перевірте логи для деталей

### ⚠️ Повільна обробка (>2 сек)

**Причина:** Великий файл або інші процеси використовують GPU

**Рішення:**

1. Оптимізуйте зображення (< 1000px)
2. Закрийте інші GPU програми
3. Перезавантажте машину

---

## 📝 API Документація (Swagger)

Відкрийте в браузері:

```
http://127.0.0.1:8000/docs
```

Тут можете тестувати всі endpoints конкретно.

---

## 🔐 Безпека та приватність

⚠️ **ВАЖЛИВО для production:**

1. **Локальна обробка** - Дані не відправляються на серверу
2. **Обмеження доступу** - Поточно сервер доступний локально (127.0.0.1)
3. **Видалення тимчасових файлів** - Реалізовано автоматично
4. **HTTPS** - Не налаштовано для MVP (використовується для локального desarrollo)

Для production deployment:

```python
# В api.py змініть на:
uvicorn.run(
    app,
    host="0.0.0.0",  # Слухае на всіх інтерфейсах
    port=443,        # HTTPS порт
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

---

## 📚 Посилання та ресурси

- **Florence-2 GitHub:** <https://github.com/microsoft/Florence>
- **FastAPI Документація:** <https://fastapi.tiangolo.com/>
- **HuggingFace Models:** <https://huggingface.co/microsoft/Florence-2-large>
- **PyTorch CUDA Setup:** <https://pytorch.org/get-started/locally/>

---

## 📄 License

Цей проект створений для освітніх цілей.

- **Florence-2 Model:** Published by Microsoft Research
- **Code:** MIT License (невказано)

---

## 👨‍💻 Розробка

### Додавання нових функцій

1. **Модифікація inference.py** для нових форматів паспортів
2. **Редагування regex** у `_extract_passport_number()`
3. **Додавання нових endpoints** у api.py

### Приклад: додавання нового endpoints

```python
@app.post("/api/extract-text")
async def extract_text(request: ProcessRequest):
    """Новий endpoint для вилучення всього тексту."""
    result = ocr_engine.process_image(request.file_path)
    return {"text": result["ocr_text"]}
```

---

## 💬 Обратный зв'язок та поправки

Якщо виникли проблеми:

1. Перевірте логи сервера (консоль)
2. Переглядайте `/api/info` для информацію про систему
3. Протестуйте з простим зображенням

---

## 📚 Документація проекту

| Документ | Опис |
|----------|------|
| [QUICK_START.md](QUICK_START.md) | ⚡ Швидкий старт (5 хвилин) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 🏗️ Архітектура системи деталь |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 🚀 Production розгортання |
| [api.py](api.py) | 💻 FastAPI реалізація |
| [inference.py](inference.py) | 🤖 Інференс модель |
| [config.py](config.py) | ⚙️ Конфігурація |

---

## 🎓 Освітній матеріал

### Що я дізнався з цього проекту

- **Vision-Language Models (VLM)** - Florence-2 архітектура та можливості
- **CUDA & GPU optimization** - FP16, SDPA attention, VRAM management
- **FastAPI** - розробка асинхронних веб-сервісів з Pydantic
- **Model patching** - видалення залежностей та модифікація коду моделі
- **Local ML deployment** - оптимізація для обмежених ресурсів
- **Regex parsing** - вилучення структурованих даних з сирого тексту

---

**Версія:** 0.1.0 MVP  
**Останнє оновлення:** 2026/02/10  
**Статус:** Active Development 🚀
>>>>>>> 2c20b5e9f2f991ffd3514886a9a19b5f72e8475d
