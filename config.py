"""
Глобальні конфігурації для Passport Reader API.
Централізоване управління параметрами системи.
"""

from pathlib import Path
import os

# ============================================================================
# ОСНОВНІ ШЛЯХИ
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.absolute()
MODELS_DIR = PROJECT_ROOT / "models"
STATIC_DIR = PROJECT_ROOT / "static"
LOGS_DIR = PROJECT_ROOT / "logs"

# ============================================================================
# МОДЕЛЬ
# ============================================================================

MODEL_NAME = "microsoft/Florence-2-large"
MODEL_LOCAL_PATH = str(MODELS_DIR / "florence2-large")

# Параметри моделі
MODEL_CONFIG = {
    "torch_dtype": "float16",           # FP16 для економії пам'яті
    "attn_implementation": "sdpa",      # SDPA замість flash_attn
    "device_map": "auto",               # Автоматичне розподілення GPU/CPU
    "trust_remote_code": True,          # HuggingFace трастинг
    "max_new_tokens": 256,              # Максимум токенів в інференсі
}

# ============================================================================
# СЕРВЕР (FastAPI / Uvicorn)
# ============================================================================

API_HOST = "127.0.0.1"  # Локальний IP (невидима ззовні)
API_PORT = 8000
API_WORKERS = 1  # Один воркер для GPU

API_CONFIG = {
    "title": "Passport Reader API",
    "description": "Локальний сервіс розпізнавання паспортних даних",
    "version": "0.1.0",
    "docs_url": "/docs",
    "openapi_url": "/openapi.json",
}

# ============================================================================
# ОБРОБКА ЗОБРАЖЕНЬ
# ============================================================================

# Форматы, які підтримуються
SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff")

# Максимальний розмір файлу (MB)
MAX_FILE_SIZE_MB = 50

# Максимальні розміри зображення (пікселі)
MAX_IMAGE_SIZE = (4096, 4096)  # Ширина, висота

# Якість JPEG при кодуванні Base64
JPEG_QUALITY = 85

# ============================================================================
# ПАСПОРТИ - РОЗПІЗНАВАННЯ
# ============================================================================

PASSPORT_REGEX_PATTERNS = {
    "ukrainian_id_card": r"\b(\d{3}\s?\d{3}\s?\d{3}|\d{9})\b",  # 9 цифр
    "passport_book": r"\b([А-ЯA-Z]{2}\s?\d{6}|[А-ЯA-Z]{2}\d{6})\b",  # 2 літери + 6 цифр
    "international": r"\b([A-Z0-9]{9})\b",  # 9 загальних символів
}

# ============================================================================
# ЖУРНАЛЮВАННЯ (Logging)
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# РЕСУРСИ й ОБМЕЖЕННЯ
# ============================================================================

# CUDA / GPU
GPU_MEMORY_FRACTION = 0.95  # Використовувати 95% VRAM
GPU_GROWTH = True  # Дозволити GPU зростання пам'яті

# Timeout для обробки запиту (секунди)
INFERENCE_TIMEOUT = 30

# Максимальна кількість одночасних обробок
MAX_CONCURRENT_REQUESTS = 1

# ============================================================================
# ФУНКЦІЀНАЛЬНІСТЬ
# ============================================================================

# Дозволити тестовий endpoint
ENABLE_TEST_ENDPOINT = True

# Дозволити Swagger документацію
ENABLE_SWAGGER_DOCS = True

# Включити детальне журналювання інференсу
VERBOSE_INFERENCE = True

# ============================================================================
# ФУНКЦІЇ ДОПОМОГИ
# ============================================================================

def get_config_summary():
    """Повертає резюме конфігурації для логування."""
    return {
        "api": f"http://{API_HOST}:{API_PORT}",
        "model": MODEL_NAME,
        "model_path": MODEL_LOCAL_PATH,
        "dtype": MODEL_CONFIG["torch_dtype"],
        "attention": MODEL_CONFIG["attn_implementation"],
        "max_image_size": MAX_IMAGE_SIZE,
        "supported_formats": SUPPORTED_FORMATS,
        "log_level": LOG_LEVEL,
    }


def ensure_directories():
    """Гарантує існування необхідних директорій."""
    for directory in [MODELS_DIR, STATIC_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


# ============================================================================
# ВНУТРІШНЯ КОНФІГУРАЦІЯ
# ============================================================================

# Словник для швидкого доступу до регулярних виразів
REGEX_PATTERNS = {k: v for k, v in PASSPORT_REGEX_PATTERNS.items()}

# Валідна розширення файлів (без крапки)
VALID_EXTENSIONS = tuple(ext.lstrip('.').upper() for ext in SUPPORTED_FORMATS)

if __name__ == "__main__":
    # Для тестування конфігурації
    import json
    print("[INFO] Passport Reader API Configuration:")
    print(json.dumps(get_config_summary(), indent=2, ensure_ascii=False))
    ensure_directories()
    print("[INFO] Directories checked/created")
