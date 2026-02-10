"""
Script for initializing the Florence-2-Large model.
Downloads the model from HuggingFace and removes the dependency on flash_attn.
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("[ERROR] Error: huggingface_hub not installed")
    print("Install: pip install huggingface-hub")
    sys.exit(1)

# ========== Конфігурація ==========
MODEL_ID = "microsoft/Florence-2-large"
LOCAL_DIR = "./models/florence2-large"

def setup_florence2():
    """Основна функція встановлення моделі."""
    
    print("=" * 70)
    print(" PASSPORT READER - MODEL SETUP")
    print("=" * 70)
    print(f"\n[INFO] Model: {MODEL_ID}")
    print(f"[INFO] Target Directory: {os.path.abspath(LOCAL_DIR)}")
    print(f"[INFO] Size: ~18 GB (safetensors)")
    print("\n[INFO] This may take 15-30 minutes...\n")
    
    # Перевіряємо місце на диску
    local_path = Path(LOCAL_DIR)
    if local_path.exists():
        print("[WARN] Folder already exists. Will be updated...")
    
    try:
        # 1. Завантаження моделі з HuggingFace
        print(f"[INFO] Downloading {MODEL_ID} from HuggingFace Hub...")
        print("   (ignoring: *.msgpack, *.bin, *.h5, *.onnx)\n")
        
        snapshot_download(
            repo_id=MODEL_ID, 
            local_dir=LOCAL_DIR, 
            repo_type="model",
            local_dir_use_symlinks=False,  # Без символічних посилань
            ignore_patterns=[
                "*.msgpack",      # MsgPack формати
                "*.bin",          # Старі TF бінарники
                "*.h5",           # Keras/TF формати
                "*.onnx",         # ONNX формати
                "*.pb",           # TensorFlow protobuf
            ],
            resume_download=True,  # Можна розпочати з точки перериву
        )
        
        print("\n[INFO] Download complete successfully!")
        
        # 2. Патчинг коду (видалення flash_attn залежності)
        _patch_model_code(LOCAL_DIR)
        
        # 3. Фінальна інформація
        _print_success_info(LOCAL_DIR)
        
    except Exception as e:
        print(f"\n[ERROR] Critical error: {str(e)}")
        print("\nTrobleshooting:")
        print("  1. Check internet connection")
        print("  2. Check disk space (requires ~20GB)")
        print("  3. Enable HuggingFace cookies")
        print("  4. Try again later (possible server issue)")
        sys.exit(1)


def _patch_model_code(model_dir):
    """Видаляє залежність від flash_attn (патчинг)."""
    
    modeling_file = os.path.join(model_dir, "modeling_florence2.py")
    
    if not os.path.exists(modeling_file):
        print("[WARN] File modeling_florence2.py not found, skipping patch")
        return
    
    print("\n[INFO] Patching architecture file...")
    
    try:
        with open(modeling_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_size = len(content)
        
        # Замінюємо імпорти flash_attn на pass
        content = content.replace("import flash_attn", "pass # import flash_attn")
        content = content.replace("from flash_attn", "pass # from flash_attn")
        
        # Деактивуємо перевірку наявності flash_attn
        content = content.replace("is_flash_attn_2_available()", "False")
        
        with open(modeling_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        new_size = len(content)
        
        print(f"   [INFO] File: {modeling_file}")
        print(f"   [INFO] flash_attn removed")
        print(f"   [INFO] is_flash_attn_2_available() deactivated")
        
    except Exception as e:
        print(f"[WARN] Patching error: {e}")
        print("   Try manually removing flash_attn from modeling_florence2.py")


def _print_success_info(model_dir):
    """Виводить інформацію про успішне встановлення."""
    
    print("\n" + "=" * 70)
    print(" SETUP COMPLETE!")
    print("=" * 70)
    
    # Інформація про модель
    config_file = os.path.join(model_dir, "config.json")
    if os.path.exists(config_file):
        print(f"\n[INFO] Model ready in folder:")
        print(f"   {os.path.abspath(model_dir)}")
    
    print("\n[INFO] Next steps:")
    print("   1. Install dependencies:")
    print("      pip install -r requirements.txt")
    print("\n   2. Start server:")
    print("      python api.py")
    print("\n   3. Open in browser:")
    print("      http://127.0.0.1:8000")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    setup_florence2()
"""
Script for initializing the Florence-2-Large model.
Downloads the model from HuggingFace and removes the dependency on flash_attn.
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("[ERROR] Error: huggingface_hub not installed")
    print("Install: pip install huggingface-hub")
    sys.exit(1)

# ========== Конфігурація ==========
MODEL_ID = "microsoft/Florence-2-large"
LOCAL_DIR = "./models/florence2-large"

def setup_florence2():
    """Основна функція встановлення моделі."""
    
    # Перевіряємо місце на диску
    local_path = Path(LOCAL_DIR)
    if local_path.exists():
        print("[WARN] Folder already exists. Will be updated...")
    
    try:
        # 1. Завантаження моделі з HuggingFace
        print(f"[INFO] Downloading {MODEL_ID} from HuggingFace Hub...")
        print("   (ignoring: *.msgpack, *.bin, *.h5, *.onnx)\n")
        
        snapshot_download(
            repo_id=MODEL_ID, 
            local_dir=LOCAL_DIR, 
            repo_type="model",
            local_dir_use_symlinks=False,  # Без символічних посилань
            ignore_patterns=[
                "*.msgpack",      # MsgPack формати
                "*.bin",          # Старі TF бінарники
                "*.h5",           # Keras/TF формати
                "*.onnx",         # ONNX формати
                "*.pb",           # TensorFlow protobuf
            ],
            resume_download=True,  # Можна розпочати з точки перериву
        )
        
        print("\n[INFO] Download complete successfully!")
        
        # 2. Патчинг коду (видалення flash_attn залежності)
        _patch_model_code(LOCAL_DIR)
        
        # 3. Фінальна інформація
        _print_success_info(LOCAL_DIR)
        
    except Exception as e:
        print(f"\n[ERROR] Critical error: {str(e)}")
        print("\nTrobleshooting:")
        print("  1. Check internet connection")
        print("  2. Check disk space (requires ~20GB)")
        print("  3. Enable HuggingFace cookies")
        print("  4. Try again later (possible server issue)")
        sys.exit(1)


def _patch_model_code(model_dir):
    """Видаляє залежність від flash_attn (патчинг)."""
    
    modeling_file = os.path.join(model_dir, "modeling_florence2.py")
    
    if not os.path.exists(modeling_file):
        print("[WARN] File modeling_florence2.py not found, skipping patch")
        return
    
    print("\n[INFO] Patching architecture file...")
    
    try:
        with open(modeling_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_size = len(content)
        
        # Замінюємо імпорти flash_attn на pass
        content = content.replace("import flash_attn", "pass # import flash_attn")
        content = content.replace("from flash_attn", "pass # from flash_attn")
        
        # Деактивуємо перевірку наявності flash_attn
        content = content.replace("is_flash_attn_2_available()", "False")
        
        with open(modeling_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        new_size = len(content)
        
        print(f"   [INFO] File: {modeling_file}")
        print(f"   [INFO] flash_attn removed")
        print(f"   [INFO] is_flash_attn_2_available() deactivated")
        
    except Exception as e:
        print(f"[WARN] Patching error: {e}")
        print("   Try manually removing flash_attn from modeling_florence2.py")


def _print_success_info(model_dir):
    """Виводить інформацію про успішне встановлення."""
    
    print("\n" + "=" * 70)
    print(" SETUP COMPLETE!")
    print("=" * 70)
    
    # Інформація про модель
    config_file = os.path.join(model_dir, "config.json")
    if os.path.exists(config_file):
        print(f"\n[INFO] Model ready in folder:")
        print(f"   {os.path.abspath(model_dir)}")
    
    print("\n[INFO] Next steps:")
    print("   1. Install dependencies:")
    print("      pip install -r requirements.txt")
    print("\n   2. Start server:")
    print("      python api.py")
    print("\n   3. Open in browser:")
    print("      http://127.0.0.1:8000")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    setup_florence2()