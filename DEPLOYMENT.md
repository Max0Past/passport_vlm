<<<<<<< HEAD
# 🚀 Deployment Guide - Passport Reader API

Цей документ описує як розгорнути сервіс Passport Reader API на production.

## Варіанти розгортання

### 1. **Локальна машина (Windows/Linux/macOS)**

Найпростіший варіант для розробки та малого використання.

```bash
# 1. Установка залежностей
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 2. Завантаження моделі
python model_setup.py

# 3. Запуск сервера
python api.py
```

**Переваги:**

- Просто встановити
- Повна контроль над ресурсами
- Без додаткових залежностей

**Недоліки:**

- Не масштабується
- Залежно від OS конкретної машини
- Потребує запуску вручну

---

### 2. **Docker контейнер (Windows/Linux)**

Рекомендується для production deployment.

#### 2.1 Dockerfile

```dockerfile
# Базовий образ с CUDA 12.1 та Python 3.10
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Установка Python 3.10
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка робочої директорії
WORKDIR /app

# Копіюємо файли проекту
COPY requirements.txt .
COPY . .

# Установка PyTorch з CUDA 12.1
RUN pip install --no-cache-dir torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# Установка інших залежностей
RUN pip install --no-cache-dir -r requirements.txt

# Завантаження моделі (за потреби)
# RUN python model_setup.py 

# Expose порт
EXPOSE 8000

# Запуск сервера
CMD ["python", "api.py"]
```

#### 2.2 docker-compose.yml

```yaml
version: '3.8'

services:
  passport-api:
    build:
      context: .
      dockerfile: Dockerfile
    
    ports:
      - "8000:8000"
    
    volumes:
      - ./models:/app/models      # Збереження завантажених моделей
      - ./logs:/app/logs          # Логи сервера
    
    environment:
      - CUDA_VISIBLE_DEVICES=0    # ID GPU (0 - перший GPU)
      - PYTorch_CUDA_ALLOC_CONF=expandable_segments:True
    
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1              # Кількість GPU
              capabilities: [gpu]
    
    restart: unless-stopped
    
    networks:
      - passport-network

  # Опціонально: nginx для проксування та HTTPS
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    
    depends_on:
      - passport-api
    
    networks:
      - passport-network

networks:
  passport-network:
    driver: bridge
```

#### 2.3 Запуск Docker контейнера

```bash
# Збірка образу
docker build -t passport-api:latest .

# Запуск контейнера
docker run --gpus all \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  passport-api:latest

# Або використовуючи docker-compose
docker-compose up -d
```

---

### 3. **云 Deployment (AWS, Google Cloud, Azure)**

#### 3.1 AWS EC2 з GPU

```bash
# 1. Запуск EC2 інстансу (p3.2xlarge або меньше)
# Образ: Deep Learning AMI with CUDA 12.1

# 2. SSH до інстансу
ssh -i key.pem ubuntu@<PUBLIC_IP>

# 3. Клонування репозиторію
git clone <your-repo>
cd passport_api

# 4. Установка і запуск
pip install -r requirements.txt
python model_setup.py
python api.py
```

#### 3.2 Google Cloud Run (без GPU, медленно)

```bash
# Пакування та завантаження на GCR
docker build -t gcr.io/<project>/<service>:latest .
docker push gcr.io/<project>/<service>:latest

# Запуск на Cloud Run (потребує CPU Allocation)
gcloud run deploy passport-reader \
  --image gcr.io/<project>/<service>:latest \
  --memory 8Gi \
  --cpu 4
```

---

## 🔒 Security для Production

### 1. HTTPS (SSL/TLS)

```python
# api.py
import uvicorn

uvicorn.run(
    "api:app",
    host="0.0.0.0",
    port=443,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

### 2. Автентифікація API

```python
# Додати до api.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

@app.post("/api/process")
async def process_image(
    request: ProcessRequest,
    credentials: HTTPAuthCredentials = Depends(security)
):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # ... обробка
```

### 3. Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/process")
@limiter.limit("10/minute")
async def process_image(request: ProcessRequest):
    # ... обробка
```

### 4. CORS (для веб-клієнтів)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

---

## 📊 Моніторинг та Loggin

### 1. Prometheus + Grafana

```bash
pip install prometheus-client
```

```python
from prometheus_client import Counter, Histogram

request_count = Counter('passport_requests_total', 'Total requests')
inference_time = Histogram('inference_seconds', 'Inference time')

@app.post("/api/process")
async def process_image(request: ProcessRequest):
    request_count.inc()
    
    with inference_time.time():
        # ... обробка
    
    return response
```

### 2. ELK Stack (Elasticsearch, Logstash, Kibana)

```python
import logging
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

---

## 🖥️ Рекомендовані конфігурації для різних сценаріїв

### Малий сервіс (< 100 запітів/день)

```
Machine:     Single GPU (4GB VRAM minimum)
OS:          Windows 10/11
Python:      3.10
GPU:         NVIDIA GTX 1650 або вище
Deployment:  Local or Docker
```

### Середній сервіс (100-1000 запітів/день)

```
Machine:     Server з GPU (8GB+ VRAM)
OS:          Linux (Ubuntu 22.04)
Python:      3.10
GPU:         RTX 3080 / RTX 4090
Deployment:  Docker + docker-compose
Scaling:     Kubernetes (k8s) з HPA
```

### Великий сервіс (> 1000 запітів/день)

```
Infrastructure: AWS / Google Cloud / Azure
GPUs:          Multiple GPU nodes (A100 / H100)
Orchestration: Kubernetes (k8s)
Load Balancer: AWS NLB або Nginx
Database:      PostgreSQL для логів
Monitoring:    Prometheus + Grafana + ELK
Caching:       Redis для кеші результатів
```

---

## 🔄 Continuous Integration / Continuous Deployment (CI/CD)

### GitHub Actions

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker Image
        run: docker build -t passport-api:${{ github.sha }} .
      
      - name: Push to Registry
        run: docker push gcr.io/${{ secrets.GCP_PROJECT }}/passport-api:${{ github.sha }}
      
      - name: Deploy to GKE
        run: |
          kubectl set image deployment/passport-api \
          passport-api=gcr.io/${{ secrets.GCP_PROJECT }}/passport-api:${{ github.sha }}
```

---

## ✅ Чек-лист для Production

- [ ] HTTPS налаштовано
- [ ] Автентифікація організована
- [ ] Rate limiting встановлено
- [ ] Логи структуруються та зберігаються
- [ ] Моніторинг налаштовано (Prometheus/Grafana)
- [ ] Backup моделі (на диск або S3)
- [ ] Готовність до відновлення (Disaster Recovery)
- [ ] Health checks до кожного компонента
- [ ] Алерти налаштовані (сервер down, GPU out of memory, etc.)
- [ ] Документація оновлена

---

## 📞 Troubleshooting для Production

### Проблема: GPU Out of Memory

```bash
# Рішення 1: Оптимізація моделі
# - Використовуйте quantization (int8, int4)
# - Оптимізуйте розмір пакета (batch_size)

# Рішення 2: Масштабування
# - Розгорніть на кількох GPU
# - Використовуйте load balancing
```

### Проблема: Повільна обробка

```bash
# Рішення 1: Кеш результатів
# - Redis для кешування часто запитуваних зображень

# Рішення 2: Асинхронна обробка
# - Queue (Celery, RQ)
# - Webhook для результатів
```

### Проблема: Сервер падає

```bash
# Рішення: Graceful Shutdown + Monitoring
# - Обробляйте сигнали (SIGTERM, SIGINT)
# - Перезапускайте контейнер (restart policy)
# - Алерти при зупинці
```

---

**Документація останнього оновлення:** 2026/02/10
=======
# 🚀 Deployment Guide - Passport Reader API

Цей документ описує як розгорнути сервіс Passport Reader API на production.

## Варіанти розгортання

### 1. **Локальна машина (Windows/Linux/macOS)**

Найпростіший варіант для розробки та малого використання.

```bash
# 1. Установка залежностей
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 2. Завантаження моделі
python model_setup.py

# 3. Запуск сервера
python api.py
```

**Переваги:**

- Просто встановити
- Повна контроль над ресурсами
- Без додаткових залежностей

**Недоліки:**

- Не масштабується
- Залежно від OS конкретної машини
- Потребує запуску вручну

---

### 2. **Docker контейнер (Windows/Linux)**

Рекомендується для production deployment.

#### 2.1 Dockerfile

```dockerfile
# Базовий образ с CUDA 12.1 та Python 3.10
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Установка Python 3.10
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка робочої директорії
WORKDIR /app

# Копіюємо файли проекту
COPY requirements.txt .
COPY . .

# Установка PyTorch з CUDA 12.1
RUN pip install --no-cache-dir torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# Установка інших залежностей
RUN pip install --no-cache-dir -r requirements.txt

# Завантаження моделі (за потреби)
# RUN python model_setup.py 

# Expose порт
EXPOSE 8000

# Запуск сервера
CMD ["python", "api.py"]
```

#### 2.2 docker-compose.yml

```yaml
version: '3.8'

services:
  passport-api:
    build:
      context: .
      dockerfile: Dockerfile
    
    ports:
      - "8000:8000"
    
    volumes:
      - ./models:/app/models      # Збереження завантажених моделей
      - ./logs:/app/logs          # Логи сервера
    
    environment:
      - CUDA_VISIBLE_DEVICES=0    # ID GPU (0 - перший GPU)
      - PYTorch_CUDA_ALLOC_CONF=expandable_segments:True
    
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1              # Кількість GPU
              capabilities: [gpu]
    
    restart: unless-stopped
    
    networks:
      - passport-network

  # Опціонально: nginx для проксування та HTTPS
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    
    depends_on:
      - passport-api
    
    networks:
      - passport-network

networks:
  passport-network:
    driver: bridge
```

#### 2.3 Запуск Docker контейнера

```bash
# Збірка образу
docker build -t passport-api:latest .

# Запуск контейнера
docker run --gpus all \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  passport-api:latest

# Або використовуючи docker-compose
docker-compose up -d
```

---

### 3. **云 Deployment (AWS, Google Cloud, Azure)**

#### 3.1 AWS EC2 з GPU

```bash
# 1. Запуск EC2 інстансу (p3.2xlarge або меньше)
# Образ: Deep Learning AMI with CUDA 12.1

# 2. SSH до інстансу
ssh -i key.pem ubuntu@<PUBLIC_IP>

# 3. Клонування репозиторію
git clone <your-repo>
cd passport_api

# 4. Установка і запуск
pip install -r requirements.txt
python model_setup.py
python api.py
```

#### 3.2 Google Cloud Run (без GPU, медленно)

```bash
# Пакування та завантаження на GCR
docker build -t gcr.io/<project>/<service>:latest .
docker push gcr.io/<project>/<service>:latest

# Запуск на Cloud Run (потребує CPU Allocation)
gcloud run deploy passport-reader \
  --image gcr.io/<project>/<service>:latest \
  --memory 8Gi \
  --cpu 4
```

---

## 🔒 Security для Production

### 1. HTTPS (SSL/TLS)

```python
# api.py
import uvicorn

uvicorn.run(
    "api:app",
    host="0.0.0.0",
    port=443,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

### 2. Автентифікація API

```python
# Додати до api.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

@app.post("/api/process")
async def process_image(
    request: ProcessRequest,
    credentials: HTTPAuthCredentials = Depends(security)
):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # ... обробка
```

### 3. Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/process")
@limiter.limit("10/minute")
async def process_image(request: ProcessRequest):
    # ... обробка
```

### 4. CORS (для веб-клієнтів)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

---

## 📊 Моніторинг та Loggin

### 1. Prometheus + Grafana

```bash
pip install prometheus-client
```

```python
from prometheus_client import Counter, Histogram

request_count = Counter('passport_requests_total', 'Total requests')
inference_time = Histogram('inference_seconds', 'Inference time')

@app.post("/api/process")
async def process_image(request: ProcessRequest):
    request_count.inc()
    
    with inference_time.time():
        # ... обробка
    
    return response
```

### 2. ELK Stack (Elasticsearch, Logstash, Kibana)

```python
import logging
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

---

## 🖥️ Рекомендовані конфігурації для різних сценаріїв

### Малий сервіс (< 100 запітів/день)

```
Machine:     Single GPU (4GB VRAM minimum)
OS:          Windows 10/11
Python:      3.10
GPU:         NVIDIA GTX 1650 або вище
Deployment:  Local or Docker
```

### Середній сервіс (100-1000 запітів/день)

```
Machine:     Server з GPU (8GB+ VRAM)
OS:          Linux (Ubuntu 22.04)
Python:      3.10
GPU:         RTX 3080 / RTX 4090
Deployment:  Docker + docker-compose
Scaling:     Kubernetes (k8s) з HPA
```

### Великий сервіс (> 1000 запітів/день)

```
Infrastructure: AWS / Google Cloud / Azure
GPUs:          Multiple GPU nodes (A100 / H100)
Orchestration: Kubernetes (k8s)
Load Balancer: AWS NLB або Nginx
Database:      PostgreSQL для логів
Monitoring:    Prometheus + Grafana + ELK
Caching:       Redis для кеші результатів
```

---

## 🔄 Continuous Integration / Continuous Deployment (CI/CD)

### GitHub Actions

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker Image
        run: docker build -t passport-api:${{ github.sha }} .
      
      - name: Push to Registry
        run: docker push gcr.io/${{ secrets.GCP_PROJECT }}/passport-api:${{ github.sha }}
      
      - name: Deploy to GKE
        run: |
          kubectl set image deployment/passport-api \
          passport-api=gcr.io/${{ secrets.GCP_PROJECT }}/passport-api:${{ github.sha }}
```

---

## ✅ Чек-лист для Production

- [ ] HTTPS налаштовано
- [ ] Автентифікація організована
- [ ] Rate limiting встановлено
- [ ] Логи структуруються та зберігаються
- [ ] Моніторинг налаштовано (Prometheus/Grafana)
- [ ] Backup моделі (на диск або S3)
- [ ] Готовність до відновлення (Disaster Recovery)
- [ ] Health checks до кожного компонента
- [ ] Алерти налаштовані (сервер down, GPU out of memory, etc.)
- [ ] Документація оновлена

---

## 📞 Troubleshooting для Production

### Проблема: GPU Out of Memory

```bash
# Рішення 1: Оптимізація моделі
# - Використовуйте quantization (int8, int4)
# - Оптимізуйте розмір пакета (batch_size)

# Рішення 2: Масштабування
# - Розгорніть на кількох GPU
# - Використовуйте load balancing
```

### Проблема: Повільна обробка

```bash
# Рішення 1: Кеш результатів
# - Redis для кешування часто запитуваних зображень

# Рішення 2: Асинхронна обробка
# - Queue (Celery, RQ)
# - Webhook для результатів
```

### Проблема: Сервер падає

```bash
# Рішення: Graceful Shutdown + Monitoring
# - Обробляйте сигнали (SIGTERM, SIGINT)
# - Перезапускайте контейнер (restart policy)
# - Алерти при зупинці
```

---

**Документація останнього оновлення:** 2026/02/10
>>>>>>> 2c20b5e9f2f991ffd3514886a9a19b5f72e8475d
