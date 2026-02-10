"""
FastAPI сервис для розпізнавання паспортних даних.
Локальна веб-система на базі Florence-2 VLM моделі.
"""

import base64
import logging
from pathlib import Path
from io import BytesIO
from typing import Optional

import fastapi
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from inference import PassportOCREngine
from config import (
    API_CONFIG, MODEL_LOCAL_PATH, LOGS_DIR, STATIC_DIR,
    JPEG_QUALITY, API_HOST, API_PORT, ENABLE_SWAGGER_DOCS,
    get_config_summary, ensure_directories
)

# ========== Конфігурація логування ==========
ensure_directories()  # Гарантуємо існування необхідних директорій

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Консоль
        logging.FileHandler(LOGS_DIR / "passport_api.log")  # Файл логу
    ]
)
logger = logging.getLogger("passport_api")

from contextlib import asynccontextmanager

# ========== Startup/Shutdown события ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    LifeSpan context manager для управління життєвим циклом додатка.
    Завантажує модель при старті та очищає при вимиканні.
    """
    global ocr_engine

    logger.info("[STARTUP] Starting Passport Reader API Server...")
    logger.info("[STARTUP] Loading Florence-2 model...")

    try:
        ocr_engine = PassportOCREngine(model_path=MODEL_LOCAL_PATH)
        logger.info("[STARTUP] Model initialized successfully")
    except Exception as e:
        logger.error(f"[STARTUP] Critical error loading model: {e}")
        raise

    yield

    logger.info("[SHUTDOWN] Stopping server...")
    if ocr_engine is not None:
        ocr_engine.cleanup()


# ========== Приватизування FastAPI ==========
app = FastAPI(**API_CONFIG, lifespan=lifespan)

# ========== Глобальні змінні ==========
ocr_engine: Optional[PassportOCREngine] = None

# ========== Моделі для запитів/відповідей ==========
class ProcessRequest(BaseModel):
    """Запит для обробки зображення."""
    file_path: str  # Абсолютний шлях до файлу на локальній машині


class ProcessResponse(BaseModel):
    """Відповідь з результатами обробки."""
    status: str  # "success" або "error"
    passport_number: Optional[str] = None  # Знайдений номер або null
    image_base64: str  # Зображення в Base64 з MIME-типом
    ocr_text: str = ""  # Сирий текст OCR (для отладки)
    processing_time: str  # Час обробки у форматі "0.45s"
    error_message: Optional[str] = None  # Повідомлення про помилку


# ========== REST API Endpoints ==========

@app.get("/", response_class=FileResponse)
async def root():
    """
    Повертає HTML-інтерфейс користувача.
    """
    static_path = Path("static/index.html")
    
    if not static_path.exists():
        raise HTTPException(
            status_code=404,
            detail="HTML інтерфейс не знайдено. Виконайте: mkdir static та поставте index.html"
        )
    
    return static_path


@app.post("/api/process", response_model=ProcessResponse)
async def process_image(request: ProcessRequest) -> ProcessResponse:
    """
    Обробляє зображення для розпізнавання паспортного номера.

    Query Params:
        file_path (str): Абсолютний шлях до файлу на локальній машині

    Returns:
        ProcessResponse: JSON з результатами

    Error Codes:
        400: Некоректний запит (відсутній file_path)
        404: Файл не знайдено
        500: Помилка моделі або CUDA OOM
    """
    global ocr_engine

    logger.info(f"[INFO] Processing request for file: {request.file_path}")

    # Перевіряємо наявність моделі
    if ocr_engine is None:
        logger.error("[ERROR] Model not loaded!")
        raise HTTPException(
            status_code=500,
            detail="Модель не завантажена. Перезавантажте сервер."
        )

    # Валідація вхідних даних
    if not request.file_path:
        raise HTTPException(
            status_code=400,
            detail="Поле 'file_path' не може бути пусте"
        )

    try:
        # Обробляємо зображення
        result = ocr_engine.process_image(request.file_path)

        # Конвертуємо зображення в Base64
        buffer = BytesIO()
        result["image"].save(buffer, format="JPEG", quality=JPEG_QUALITY)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        image_base64_with_mime = f"data:image/jpeg;base64,{image_base64}"

        logger.info(
            f"[INFO] Processing complete. Passport: {result['passport_number'] or 'Not found'}"
        )

        return ProcessResponse(
            status="success",
            passport_number=result["passport_number"],
            image_base64=image_base64_with_mime,
            ocr_text=result["ocr_text"][:500],  # Обмежуємо для JSON
            processing_time=f"{result['processing_time']:.2f}s",
            error_message=None
        )

    except FileNotFoundError as e:
        logger.warning(f"[WARN] File not found: {request.file_path}")
        raise HTTPException(
            status_code=404,
            detail=f"Файл не знайдено: {request.file_path}"
        )

    except RuntimeError as e:
        error_msg = str(e)
        
        if "Out of Memory" in error_msg:
            logger.error(f"[ERROR] CUDA OOM: {e}")
            raise HTTPException(
                status_code=500,
                detail="CUDA Out of Memory. Спробуйте менше зображення."
            )
        else:
            logger.error(f"[ERROR] Inference error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Помилка при обробці зображення: {error_msg}"
            )

    except Exception as e:
        logger.error(f"[ERROR] Unknown error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Невідома помилка сервера: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """Перевірка здоров'я сервера (для моніторингу)."""
    global ocr_engine

    return {
        "status": "ok",
        "model_loaded": ocr_engine is not None,
        "service": "passport_api",
        "version": "0.1.0"
    }


@app.get("/api/info")
async def api_info():
    """Повертає інформацію про API та ресурси."""
    import torch
    
    return {
        "service_name": "Passport Reader API",
        "version": "0.1.0",
        "model": "Microsoft/Florence-2-Large",
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "endpoints": {
            "GET /": "HTML інтерфейс",
            "POST /api/process": "Обробка зображення",
            "GET /api/health": "Перевірка здоров'я",
            "GET /api/info": "Інформація про сервіс"
        }
    }


# ========== Обробка невизначених ендпоінтів ==========
@app.get("/{path:path}")
async def fallback(path: str):
    """Fallback для невизначених маршрутів."""
    raise HTTPException(
        status_code=404,
        detail=f"Ендпоінт '{path}' не знайдено. Див. GET /api/info"
    )


# ========== точка входу ==========
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" PASSPORT READER API - STARTUP")
    print("=" * 70)
    
    config_summary = get_config_summary()
    for key, value in config_summary.items():
        print(f"  {key:20s}: {value}")
    
    print("\n[INFO] Loading model on GPU...")
    print(f"[INFO] Server available at: http://{API_HOST}:{API_PORT}")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,  # Заборонено перезавантажувати у production
        log_level="info"
    )
