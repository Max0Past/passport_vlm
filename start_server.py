#!/usr/bin/env python
"""
Скрипт запуску сервера Passport Reader API.
Альтернатива: python api.py

Цей скрипт надає додаткові опції для налаштування запуску.
"""

import sys
import argparse
import logging
from pathlib import Path

import uvicorn

# Додаємо проект у path
sys.path.insert(0, str(Path(__file__).parent))

from config import API_HOST, API_PORT, API_CONFIG, get_config_summary, ensure_directories


def main():
    """Головна функція запуску сервера."""
    
    parser = argparse.ArgumentParser(
        description="Passport Reader API - FastAPI Server",
        epilog="Example: python start_server.py --host 0.0.0.0 --port 8000"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=API_HOST,
        help=f"Host для прослуховування (default: {API_HOST})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=API_PORT,
        help=f"Port для прослуховування (default: {API_PORT})"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Автоматичне перезавантаження при змінах коду (для розробки)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["critical", "error", "warning", "info", "debug"],
        default="info",
        help="Рівень логування (default: info)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Кількість воркерів (default: 1, рекомендується 1 для GPU)"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Показати інформацію про конфігурацію та вихід"
    )
    
    args = parser.parse_args()
    
    # Гарантуємо існування директорій
    ensure_directories()
    
    # Показуємо інформацію про конфігурацію
    print("\n" + "=" * 80)
    print(" PASSPORT READER API - SERVER STARTUP")
    print("=" * 80)
    
    config_info = get_config_summary()
    print("\n[INFO] Configuration:")
    for key, value in config_info.items():
        print(f"  {key:20s}: {value}")
    
    print("\n[INFO] Startup parameters:")
    print(f"  {'host':20s}: {args.host}")
    print(f"  {'port':20s}: {args.port}")
    print(f"  {'workers':20s}: {args.workers}")
    print(f"  {'reload':20s}: {args.reload}")
    print(f"  {'log_level':20s}: {args.log_level}")
    
    if args.info:
        print("\n" + "=" * 80)
        return
    
    # Виводимо інформацію про доступ
    protocol = "https" if args.port == 443 else "http"
    print(f"\n[INFO] Server will be available at:")
    print(f"  {protocol}://{args.host}:{args.port}")
    print(f"\n[INFO] Swagger documentation:")
    print(f"  {protocol}://{args.host}:{args.port}/docs")
    print(f"\n[INFO] Loading model on GPU... (this may take a few seconds)")
    print("=" * 80 + "\n")
    
    try:
        # Запускаємо сервер
        uvicorn.run(
            "api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            workers=args.workers if not args.reload else 1,  # Один воркер при reload
        )
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped by user (Ctrl+C)")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n[ERROR] Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Скрипт запуску сервера Passport Reader API.
Альтернатива: python api.py

Цей скрипт надає додаткові опції для налаштування запуску.
"""

import sys
import argparse
import logging
from pathlib import Path

import uvicorn

# Додаємо проект у path
sys.path.insert(0, str(Path(__file__).parent))

from config import API_HOST, API_PORT, API_CONFIG, get_config_summary, ensure_directories


def main():
    """Головна функція запуску сервера."""
    
    parser = argparse.ArgumentParser(
        description="Passport Reader API - FastAPI Server",
        epilog="Example: python start_server.py --host 0.0.0.0 --port 8000"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=API_HOST,
        help=f"Host для прослуховування (default: {API_HOST})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=API_PORT,
        help=f"Port для прослуховування (default: {API_PORT})"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Автоматичне перезавантаження при змінах коду (для розробки)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["critical", "error", "warning", "info", "debug"],
        default="info",
        help="Рівень логування (default: info)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Кількість воркерів (default: 1, рекомендується 1 для GPU)"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Показати інформацію про конфігурацію та вихід"
    )
    
    args = parser.parse_args()
    
    # Гарантуємо існування директорій
    ensure_directories()
    
    # Показуємо інформацію про конфігурацію
    print("\n" + "=" * 80)
    print(" PASSPORT READER API - SERVER STARTUP")
    print("=" * 80)
    
    config_info = get_config_summary()
    print("\n[INFO] Configuration:")
    for key, value in config_info.items():
        print(f"  {key:20s}: {value}")
    
    print("\n[INFO] Startup parameters:")
    print(f"  {'host':20s}: {args.host}")
    print(f"  {'port':20s}: {args.port}")
    print(f"  {'workers':20s}: {args.workers}")
    print(f"  {'reload':20s}: {args.reload}")
    print(f"  {'log_level':20s}: {args.log_level}")
    
    if args.info:
        print("\n" + "=" * 80)
        return
    
    # Виводимо інформацію про доступ
    protocol = "https" if args.port == 443 else "http"
    print(f"\n[INFO] Server will be available at:")
    print(f"  {protocol}://{args.host}:{args.port}")
    print(f"\n[INFO] Swagger documentation:")
    print(f"  {protocol}://{args.host}:{args.port}/docs")
    print(f"\n[INFO] Loading model on GPU... (this may take a few seconds)")
    print("=" * 80 + "\n")
    
    try:
        # Запускаємо сервер
        uvicorn.run(
            "api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            workers=args.workers if not args.reload else 1,  # Один воркер при reload
        )
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped by user (Ctrl+C)")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n[ERROR] Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
