"""
Скрипт тестування Passport Reader API.

Цей скрипт допомагає перевірити, чи коректно налаштована система.

Використання:
    python test.py                    # Базова перевірка
    python test.py --endpoint-test    # Тестування endpoints
    python test.py --full             # Повне тестування з прикладом зображення
"""

import sys
import argparse
import json
from pathlib import Path
from io import BytesIO

# ============================================================================
# ТЕСТИ СИСТЕМИ
# ============================================================================

def test_imports():
    """Перевіряє всі необхідні імпорти."""
    print("\nТестування імпортів...")
    
    imports_ok = True
    critical_modules = [
        ("torch", "PyTorch"),
        ("transformers", "HuggingFace Transformers"),
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("PIL", "Pillow"),
        ("uvicorn", "Uvicorn"),
    ]
    
    for module_name, display_name in critical_modules:
        try:
            __import__(module_name)
            print(f"  {display_name:30s} - OK")
        except ImportError as e:
            print(f"  {display_name:30s} - MISSING")
            print(f"     Install: pip install {module_name}")
            imports_ok = False
    
    return imports_ok


def test_config():
    """Перевіряє конфігурацію проекту."""
    print("\nТестування конфігурації...")
    
    try:
        from config import (
            get_config_summary, ensure_directories,
            MODEL_LOCAL_PATH, MODELS_DIR, STATIC_DIR
        )
        
        print(f"  Конфігурація загружена")
        
        # Гарантуємо директорії
        ensure_directories()
        print(f"  Директорії завірені/створені")
        
        # Показуємо конфіг
        summary = get_config_summary()
        print(f"\n  Параметры:")
        for key, value in summary.items():
            print(f"    {key:20s}: {value}")
        
        return True
    
    except Exception as e:
        print(f"  Помилка конфіґурації: {e}")
        return False


def test_cuda():
    """Перевіряє доступність CUDA/GPU."""
    print("\nТестування GPU/CUDA...")
    
    try:
        import torch
        
        cuda_available = torch.cuda.is_available()
        
        if cuda_available:
            print(f"  CUDA available - YES")
            print(f"  GPU count: {torch.cuda.device_count()}")
            print(f"  Current device: {torch.cuda.current_device()}")
            print(f"  Device name: {torch.cuda.get_device_name(0)}")
            
            # VRAM інформація
            total_memory = torch.cuda.get_device_properties(0).total_memory
            vram_gb = total_memory / (1024**3)
            print(f"  Total VRAM: {vram_gb:.2f} GB")
            
            if vram_gb < 4:
                print(f"  WARNING: VRAM менше 4GB (потребується мінімум 4GB)")
                return False
            
            return True
        else:
            print(f"  CUDA available - NO")
            print(f"  GPU не знайдено. Модель буде запущена на CPU (повільно)")
            return False  # Це попередження, але не критична помилка
    
    except Exception as e:
        print(f"  Помилка CUDA перевірки: {e}")
        return False


def test_model_files():
    """Перевіряє наявність файлів моделі."""
    print("\nТестування файлів моделі...")
    
    try:
        from config import MODEL_LOCAL_PATH
        from pathlib import Path
        
        model_path = Path(MODEL_LOCAL_PATH)
        
        if not model_path.exists():
            print(f"  Папка моделі не знайдена: {model_path}")
            print(f"  Виконайте: python model_setup.py")
            return False
        
        print(f"  Папка моделі знайдена: {model_path}")
        
        # Перевіряємо ключові файли
        required_files = [
            "config.json",
            "modeling_florence2.py",
            "processing_florence2.py",
            "model.safetensors"
        ]
        
        missing = []
        for file_name in required_files:
            file_path = model_path / file_name
            if file_path.exists():
                print(f" {file_name:30s} - OK")
            else:
                print(f"  {file_name:30s} - MISSING")
                missing.append(file_name)
        
        if missing:
            print(f"\n  Деякі файли моделі відсутні: {missing}")
            return False
        
        return True
    
    except Exception as e:
        print(f"  Помилка структури моделі: {e}")
        return False


def test_static_files():
    """Перевіряє наявність статичних файлів."""
    print("\n Тестування статичних файлів...")
    
    try:
        from config import STATIC_DIR
        from pathlib import Path
        
        static_path = Path(STATIC_DIR)
        index_html = static_path / "index.html"
        
        if not index_html.exists():
            print(f"  index.html не знайдено: {index_html}")
            print(f"  Файл повинен бути тут: static/index.html")
            return False
        
        print(f"  index.html знайдено: {index_html}")
        
        # Перевіряємо розмір файлу
        size_kb = index_html.stat().st_size / 1024
        print(f"  Розмір: {size_kb:.2f} KB")
        
        return True
    
    except Exception as e:
        print(f"  Помилка статичних файлів: {e}")
        return False


def test_api_endpoints():
    """Тестує API endpoints (потребує запущеного сервера)."""
    print("\nТестування API endpoints...")
    print("  (Цей тест потребує запущеного сервера на localhost:8000)")
    
    try:
        import requests
    except ImportError:
        print("  requests не встановлено. Пропущено.")
        print("     Install: pip install requests")
        return None
    
    endpoints = [
        ("GET", "http://127.0.0.1:8000/", "Головну сторінку"),
        ("GET", "http://127.0.0.1:8000/api/health", "Health check"),
        ("GET", "http://127.0.0.1:8000/api/info", "Info endpoint"),
    ]
    
    results = []
    
    for method, url, description in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 307]:  # 307 - redirect for GET /
                print(f"  {description:30s} - {response.status_code}")
                results.append(True)
            else:
                print(f"  {description:30s} - {response.status_code}")
                results.append(False)
        
        except requests.ConnectionError:
            print(f"  {description:30s} - CONNECTION ERROR")
            print(f"  Сервер не запущено або недоступний")
            results.append(False)
        
        except Exception as e:
            print(f"  {description:30s} - ERROR: {str(e)[:50]}")
            results.append(False)
    
    return all(results) if results else None


def run_basic_tests():
    """Запускає базові тести."""
    print("=" * 80)
    print(" PASSPORT READER API - BASIC TESTS")
    print("=" * 80)
    
    results = []
    
    # Тести
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("CUDA/GPU", test_cuda()))
    results.append(("Model Files", test_model_files()))
    results.append(("Static Files", test_static_files()))
    
    # Резюме
    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТИ ТЕСТУВАННЯ")
    print("=" * 80)
    
    all_ok = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name:30s} - {status}")
        if not result:
            all_ok = False
    
    print("\n" + "=" * 80)
    
    if all_ok:
        print(" ВСІ БАЗОВІ ТЕСТИ ПРОЙШЛИ")
        print("\n  Наступні кроки:")
        print("   1. Запустіть сервер: python api.py")
        print("   2. Відкрийте в браузері: http://127.0.0.1:8000")
        return True
    else:
        print(" ДЕЯКІ ТЕСТИ НЕ ПРОЙШЛИ")
        print("\n  Перевірте вихід вище для деталей і порад")
        return False


def main():
    """Головна функція."""
    
    parser = argparse.ArgumentParser(description="Passport Reader API - Test Suite")
    parser.add_argument("--endpoint-test", action="store_true", help="Тестувати API endpoints")
    parser.add_argument("--full", action="store_true", help="Повне тестування")
    
    args = parser.parse_args()
    
    # Базові тести
    basic_pass = run_basic_tests()
    
    # Тести endpoints (якщо сервер запущено)
    if args.endpoint_test or args.full:
        endpoint_results = test_api_endpoints()
        if endpoint_results is False:
            sys.exit(1)
    
    # Повне тестування (потребує запущеного сервера + приклад зображення)
    if args.full:
        print("\n  Повне тестування не реалізовано")
        print("    (потребує прикладу зображення паспорта)")
    
    # Вихід
    sys.exit(0 if basic_pass else 1)


if __name__ == "__main__":
    main()
import transformers
import numpy
import torch

print(f"PyTorch: {torch.__version__} (CUDA: {torch.version.cuda})")
print(f"Transformers: {transformers.__version__}")
print(f"NumPy: {numpy.__version__}")
print(f"GPU Available: {torch.cuda.is_available()}")
exit()
"""
Скрипт тестування Passport Reader API.

Цей скрипт допомагає перевірити, чи коректно налаштована система.

Використання:
    python test.py                    # Базова перевірка
    python test.py --endpoint-test    # Тестування endpoints
    python test.py --full             # Повне тестування з прикладом зображення
"""

import sys
import argparse
import json
from pathlib import Path
from io import BytesIO

# ============================================================================
# ТЕСТИ СИСТЕМИ
# ============================================================================

def test_imports():
    """Перевіряє всі необхідні імпорти."""
    print("\n Тестування імпортів...")
    
    imports_ok = True
    critical_modules = [
        ("torch", "PyTorch"),
        ("transformers", "HuggingFace Transformers"),
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("PIL", "Pillow"),
        ("uvicorn", "Uvicorn"),
    ]
    
    for module_name, display_name in critical_modules:
        try:
            __import__(module_name)
            print(f"  {display_name:30s} - OK")
        except ImportError as e:
            print(f"  {display_name:30s} - MISSING")
            print(f"     Install: pip install {module_name}")
            imports_ok = False
    
    return imports_ok


def test_config():
    """Перевіряє конфігурацію проекту."""
    print("\n  Тестування конфігурації...")
    
    try:
        from config import (
            get_config_summary, ensure_directories,
            MODEL_LOCAL_PATH, MODELS_DIR, STATIC_DIR
        )
        
        print(f"  Конфігурація загружена")
        
        # Гарантуємо директорії
        ensure_directories()
        print(f"  Директорії завірені/створені")
        
        # Показуємо конфіг
        summary = get_config_summary()
        print(f"\n  Параметры:")
        for key, value in summary.items():
            print(f"    {key:20s}: {value}")
        
        return True
    
    except Exception as e:
        print(f"  Помилка конфіґурації: {e}")
        return False


def test_cuda():
    """Перевіряє доступність CUDA/GPU."""
    print("\nТестування GPU/CUDA...")
    
    try:
        import torch
        
        cuda_available = torch.cuda.is_available()
        
        if cuda_available:
            print(f"  CUDA available - YES")
            print(f"  GPU count: {torch.cuda.device_count()}")
            print(f"  Current device: {torch.cuda.current_device()}")
            print(f"  Device name: {torch.cuda.get_device_name(0)}")
            
            # VRAM інформація
            total_memory = torch.cuda.get_device_properties(0).total_memory
            vram_gb = total_memory / (1024**3)
            print(f"  Total VRAM: {vram_gb:.2f} GB")
            
            if vram_gb < 4:
                print(f"  WARNING: VRAM менше 4GB (потребується мінімум 4GB)")
                return False
            
            return True
        else:
            print(f"  CUDA available - NO")
            print(f"  GPU не знайдено. Модель буде запущена на CPU (повільно)")
            return False  # Це попередження, але не критична помилка
    
    except Exception as e:
        print(f"  Помилка CUDA перевірки: {e}")
        return False


def test_model_files():
    """Перевіряє наявність файлів моделі."""
    print("\nТестування файлів моделі...")
    
    try:
        from config import MODEL_LOCAL_PATH
        from pathlib import Path
        
        model_path = Path(MODEL_LOCAL_PATH)
        
        if not model_path.exists():
            print(f"  Папка моделі не знайдена: {model_path}")
            print(f"  Виконайте: python model_setup.py")
            return False
        
        print(f"  Папка моделі знайдена: {model_path}")
        
        # Перевіряємо ключові файли
        required_files = [
            "config.json",
            "modeling_florence2.py",
            "processing_florence2.py",
            "model.safetensors"
        ]
        
        missing = []
        for file_name in required_files:
            file_path = model_path / file_name
            if file_path.exists():
                print(f"  {file_name:30s} - OK")
            else:
                print(f"  {file_name:30s} - MISSING")
                missing.append(file_name)
        
        if missing:
            print(f"\n  Деякі файли моделі відсутні: {missing}")
            return False
        
        return True
    
    except Exception as e:
        print(f"  Помилка структури моделі: {e}")
        return False


def test_static_files():
    """Перевіряє наявність статичних файлів."""
    print("\nТестування статичних файлів...")
    
    try:
        from config import STATIC_DIR
        from pathlib import Path
        
        static_path = Path(STATIC_DIR)
        index_html = static_path / "index.html"
        
        if not index_html.exists():
            print(f"  index.html не знайдено: {index_html}")
            print(f"  Файл повинен бути тут: static/index.html")
            return False
        
        print(f"  index.html знайдено: {index_html}")
        
        # Перевіряємо розмір файлу
        size_kb = index_html.stat().st_size / 1024
        print(f"  Розмір: {size_kb:.2f} KB")
        
        return True
    
    except Exception as e:
        print(f"  Помилка статичних файлів: {e}")
        return False


def test_api_endpoints():
    """Тестує API endpoints (потребує запущеного сервера)."""
    print("\nТестування API endpoints...")
    print("  (Цей тест потребує запущеного сервера на localhost:8000)")
    
    try:
        import requests
    except ImportError:
        print("  requests не встановлено. Пропущено.")
        print("     Install: pip install requests")
        return None
    
    endpoints = [
        ("GET", "http://127.0.0.1:8000/", "Головну сторінку"),
        ("GET", "http://127.0.0.1:8000/api/health", "Health check"),
        ("GET", "http://127.0.0.1:8000/api/info", "Info endpoint"),
    ]
    
    results = []
    
    for method, url, description in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 307]:  # 307 - redirect for GET /
                print(f"  {description:30s} - {response.status_code}")
                results.append(True)
            else:
                print(f"  {description:30s} - {response.status_code}")
                results.append(False)
        
        except requests.ConnectionError:
            print(f"  {description:30s} - CONNECTION ERROR")
            print(f"     Сервер не запущено або недоступний")
            results.append(False)
        
        except Exception as e:
            print(f"  {description:30s} - ERROR: {str(e)[:50]}")
            results.append(False)
    
    return all(results) if results else None


def run_basic_tests():
    """Запускає базові тести."""
    print("=" * 80)
    print("PASSPORT READER API - BASIC TESTS")
    print("=" * 80)
    
    results = []
    
    # Тести
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("CUDA/GPU", test_cuda()))
    results.append(("Model Files", test_model_files()))
    results.append(("Static Files", test_static_files()))
    
    # Резюме
    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТИ ТЕСТУВАННЯ")
    print("=" * 80)
    
    all_ok = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name:30s} - {status}")
        if not result:
            all_ok = False
    
    print("\n" + "=" * 80)
    
    if all_ok:
        print("ВСІ БАЗОВІ ТЕСТИ ПРОЙШЛИ")
        print("\n  Наступні кроки:")
        print("   1. Запустіть сервер: python api.py")
        print("   2. Відкрийте в браузері: http://127.0.0.1:8000")
        return True
    else:
        print("ДЕЯКІ ТЕСТИ НЕ ПРОЙШЛИ")
        print("\n  Перевірте вихід вище для деталей і порад")
        return False


def main():
    """Головна функція."""
    
    parser = argparse.ArgumentParser(description="Passport Reader API - Test Suite")
    parser.add_argument("--endpoint-test", action="store_true", help="Тестувати API endpoints")
    parser.add_argument("--full", action="store_true", help="Повне тестування")
    
    args = parser.parse_args()
    
    # Базові тести
    basic_pass = run_basic_tests()
    
    # Тести endpoints (якщо сервер запущено)
    if args.endpoint_test or args.full:
        endpoint_results = test_api_endpoints()
        if endpoint_results is False:
            sys.exit(1)
    
    # Повне тестування (потребує запущеного сервера + приклад зображення)
    if args.full:
        print("\n  Повне тестування не реалізовано")
        print("    (потребує прикладу зображення паспорта)")
    
    # Вихід
    sys.exit(0 if basic_pass else 1)


if __name__ == "__main__":
    main()
import transformers
import numpy
import torch

print(f"PyTorch: {torch.__version__} (CUDA: {torch.version.cuda})")
print(f"Transformers: {transformers.__version__}")
print(f"NumPy: {numpy.__version__}")
print(f"GPU Available: {torch.cuda.is_available()}")
exit()