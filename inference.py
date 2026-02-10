"""
Модуль інференсу Florence-2 для розпізнавання паспортних даних.
Обгортка навколо моделі з оптимізацією для обмежених ресурсів GPU (4GB VRAM).
"""

import re
import torch
from pathlib import Path
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
from typing import Optional, Tuple, Dict, Any

from config import MODEL_CONFIG, VERBOSE_INFERENCE, REGEX_PATTERNS


class PassportOCREngine:
    """Клас для роботи з Florence-2 моделлю для розпізнавання паспортних даних."""

    def __init__(self, model_path: str = "./models/florence2-large"):
        """
        Ініціалізація моделі Florence-2.

        Args:
            model_path: Шлях до локальної копії моделі
        """
        self.model_path = Path(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = None
        self.model = None

        print(f"[INFO] Initializing PassportOCREngine... (Device: {self.device})")
        self._load_model()

    def _load_model(self) -> None:
        """Завантажує модель і процесор з локальної копії."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"[ERROR] Model folder not found: {self.model_path.absolute()}\n"
                f"Execute: python model_setup.py"
            )

        print(f"[INFO] Loading model from {self.model_path}...")

        try:
            # Завантажуємо процесор
            self.processor = AutoProcessor.from_pretrained(
                str(self.model_path),
                trust_remote_code=True,
            )

            # Завантажуємо модель з оптимізацією для обмежених ресурсів
            # Використовуємо параметри з config.py
            torch_dtype = torch.float16 if MODEL_CONFIG["torch_dtype"] == "float16" else torch.float32
            
            # Florence-2 does not support device_map="auto" well without custom _no_split_modules
            # So we manually move it to device
            self.model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                torch_dtype=torch_dtype,
                attn_implementation=MODEL_CONFIG["attn_implementation"],
                # device_map=MODEL_CONFIG["device_map"], # REMOVED to fix crash
                trust_remote_code=MODEL_CONFIG["trust_remote_code"],
            ).to(self.device).eval()

            print(f"[INFO] Model successfully loaded on {self.device}")

        except Exception as e:
            raise RuntimeError(f"[ERROR] Model loading error: {str(e)}")

    def _load_image(self, image_path: str) -> Image.Image:
        """
        Завантажує зображення з диска.

        Args:
            image_path: Абсолютний шлях до зображення

        Returns:
            PIL Image об'єкт

        Raises:
            FileNotFoundError: Файл не знайдено
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"[ERROR] File not found: {image_path}")

        try:
            image = Image.open(image_path).convert("RGB")
            print(f"[INFO] Image loaded: {image_path.name} ({image.size})")
            return image
        except Exception as e:
            raise RuntimeError(f"[ERROR] Image loading error: {str(e)}")

    def _extract_passport_number(self, ocr_text: str) -> Optional[str]:
        """
        Вилучає номер паспорта зі сирого тексту OCR.

        Формати:
        - Українська ID-картка: 9 цифр (xxx xxx xxx або xxxxxxxxx)
        - Паспортна книжечка: 2 літери + 6 цифр (XX 123456 або XX123456)
        - Міжнародний паспорт: 9 символів (літери + цифри)

        Args:
            ocr_text: Сирий текст з OCR

        Returns:
            Знайдений номер паспорта або None
        """
        if not ocr_text:
            return None

        # Видаляємо зайві пропуски та переносимо на нові рядки
        cleaned_text = re.sub(r"\s+", " ", ocr_text).upper()

        # ID-картка: 9 цифр у форматі XXX XXX XXX або xxxxxxxxx
        pattern = REGEX_PATTERNS.get("ukrainian_id_card")
        match = re.search(pattern, cleaned_text)
        if match:
            passport = match.group(1).replace(" ", "")
            if passport.isdigit() and len(passport) == 9:
                if VERBOSE_INFERENCE:
                    print(f"[DEBUG] Found ID card: {passport}")
                return passport

        # Паспортна книжечка: 2 літери + 6 цифр у форматі XX 123456 або XX123456
        pattern = REGEX_PATTERNS.get("passport_book")
        match = re.search(pattern, cleaned_text)
        if match:
            passport = match.group(1).replace(" ", "")
            if VERBOSE_INFERENCE:
                print(f"[DEBUG] Found passport book: {passport}")
            return passport

        # Міжнародний паспорт: 9 символів загального формату
        pattern = REGEX_PATTERNS.get("international")
        match = re.search(pattern, cleaned_text)
        if match:
            passport = match.group(1)
            if VERBOSE_INFERENCE:
                print(f"[DEBUG] Found international passport: {passport}")
            return passport

        if VERBOSE_INFERENCE:
            print("[WARN] Passport number not recognized in OCR text")
        return None

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Обробляє зображення для вилучення номера паспорта.

        Args:
            image_path: Абсолютний шлях до зображення

        Returns:
            Словник з результатами:
            {
                "passport_number": str або None,
                "ocr_text": str (сирий текст),
                "confidence": float (умовна впевненість),
                "image": PIL.Image,
                "processing_time": float
            }

        Raises:
            FileNotFoundError: Файл не знайдено
            RuntimeError: Помилка при інференсу (GPU OOM тощо)
        """
        import time

        process_start = time.time()
        print(f"\n[INFO] Starting processing: {Path(image_path).name}")

        # Завантажуємо зображення
        image = self._load_image(image_path)

        try:
            # 1. OCR Step
            prompt_ocr = "<OCR>"
            inputs_ocr = self.processor(
                text=prompt_ocr,
                images=image,
                return_tensors="pt",
            ).to(self.device, dtype=torch.float16 if self.device == "cuda" else torch.float32)

            print("[INFO] Running OCR inference...")
            with torch.no_grad():
                generated_ids_ocr = self.model.generate(
                    input_ids=inputs_ocr["input_ids"],
                    pixel_values=inputs_ocr["pixel_values"],
                    max_new_tokens=MODEL_CONFIG.get("max_new_tokens", 256),
                    do_sample=False,
                )

            ocr_text = self.processor.batch_decode(
                generated_ids_ocr, skip_special_tokens=False
            )[0]
            ocr_text = ocr_text.replace("<OCR>", "").replace("</OCR>", "").strip()
            print(f"[DEBUG] Raw OCR text: {ocr_text[:100]}...")

            # 2. Face Detection Step
            print("[INFO] Running Face Detection...")
            task_prompt = "<CAPTION_TO_PHRASE_GROUNDING>"
            phrases = ["face", "portrait"] # Primary and fallback prompts
            
            face_box = None
            
            for phrase in phrases:
                prompt_text = task_prompt + phrase
                
                inputs_face = self.processor(
                    text=prompt_text,
                    images=image,
                    return_tensors="pt",
                ).to(self.device, dtype=torch.float16 if self.device == "cuda" else torch.float32)

                with torch.no_grad():
                    generated_ids_face = self.model.generate(
                        input_ids=inputs_face["input_ids"],
                        pixel_values=inputs_face["pixel_values"],
                        max_new_tokens=1024,
                        do_sample=False,
                    )
                
                face_result_text = self.processor.batch_decode(
                    generated_ids_face, skip_special_tokens=False
                )[0]
                
                parsed_result = self.processor.post_process_generation(
                    face_result_text, 
                    task=task_prompt, 
                    image_size=(image.width, image.height)
                )
                
                # Check results
                if parsed_result and task_prompt in parsed_result:
                    data = parsed_result[task_prompt]
                    bboxes = data.get('bboxes', [])
                    
                    # Filter valid boxes
                    valid_bboxes = [b for b in bboxes if (b[2] > b[0] and b[3] > b[1])]
                    
                    if valid_bboxes:
                         # Found valid face
                         print(f"[INFO] Face detected with phrase '{phrase}'")
                         best_box = max(valid_bboxes, key=lambda box: (box[2]-box[0]) * (box[3]-box[1]))
                         
                         # Expand box slightly (padding) for better crop
                         x1, y1, x2, y2 = best_box
                         w, h = x2 - x1, y2 - y1
                         padding_x = w * 0.1
                         padding_y = h * 0.1
                         
                         x1 = max(0, x1 - padding_x)
                         y1 = max(0, y1 - padding_y)
                         x2 = min(image.width, x2 + padding_x)
                         y2 = min(image.height, y2 + padding_y)
                         
                         face_box = (int(x1), int(y1), int(x2), int(y2))
                         break # Stop searching if found
            
            # Crop image
            if face_box:
                x1, y1, x2, y2 = face_box
                if (x2 - x1) > 10 and (y2 - y1) > 10:
                    face_image = image.crop((x1, y1, x2, y2))
                    print(f"[INFO] Cropped face: ({x1}, {y1}, {x2}, {y2})")
                else:
                    print(f"[WARN] Detected face too small: {face_box}. Returning full image.")
                    face_image = image
            else:
                print("[WARN] No face detected with any prompt. Returning full image.")
                face_image = image

            # Вилучаємо номер паспорта
            passport_number = self._extract_passport_number(ocr_text)

            processing_time = time.time() - process_start

            print(
                f"[INFO] Processing complete in {processing_time:.2f}s. "
                f"Passport: {passport_number or 'Not found'}"
            )

            return {
                "passport_number": passport_number,
                "ocr_text": ocr_text,
                "confidence": 0.85 if passport_number else 0.0,
                "image": face_image, # Return cropped face
                "processing_time": processing_time,
            }

        except torch.cuda.OutOfMemoryError:
            raise RuntimeError(
                "[ERROR] CUDA Out of Memory! Image size too large or insufficient VRAM.\n"
                "Try a smaller image or close other applications."
            )
        except Exception as e:
            raise RuntimeError(f"[ERROR] Inference error: {str(e)}")

    def cleanup(self) -> None:
        """Очищає VRAM від моделі."""
        if self.model is not None:
            del self.model
        if self.processor is not None:
            del self.processor
        torch.cuda.empty_cache()
        print("[INFO] Model cleared from VRAM")
