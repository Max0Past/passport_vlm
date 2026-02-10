# Passport Reader API - MVP

Local web service for automated passport data recognition using Vision-Language Model (VLM) [Microsoft Florence-2-Large](https://github.com/microsoft/Florence).

## Project Overview

    passport_api/
    |
    |-- api.py                    # FastAPI server (entry point)
    |-- inference.py              # Wrapper class for Florence-2 model
    |-- model_setup.py            # Script for downloading and patching the model
    |-- requirements.txt          # Python dependencies
    |-- README.md                 # This documentation
    |
    |-- models/
    |   `-- florence2-large/      # Local copy of the model (downloaded during setup)
    |       |-- config.json
    |       |-- modeling_florence2.py
    |       |-- processing_florence2.py
    |       |-- model.safetensors
    |       `-- ... (other model files)
    |
    `-- static/
        `-- index.html            # HTML web interface

## Quick Start

### 1. Install Dependencies

    # Install PyTorch with CUDA 12.1 (IMPORTANT: run this first!)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

    # Install other dependencies
    pip install -r requirements.txt

### 2. Download Model

    # Downloads Florence-2-Large and removes flash_attn dependency
    python model_setup.py

    # Wait approx. 15-30 minutes depending on network speed.

### 3. Run Server

    python api.py

    # Wait for the message:
    # Launching Passport Reader API at http://127.0.0.1:8000

    # Open in browser: http://127.0.0.1:8000

## Usage

### Web Interface

1. **Enter the absolute path** to the image file:
   - `D:\Images\passport_scan.jpg`
   - `C:\Users\User\Desktop\photo.png`
2. **Click "Process"**
3. **View Results:**
   - Processed image
   - Recognized passport number
   - Processing time

### API (cURL Examples)

#### Process Image

    curl -X POST http://127.0.0.1:8000/api/process \
      -H "Content-Type: application/json" \
      -d '{
        "file_path": "D:\\Images\\passport.jpg"
      }'

**Success Response (200):**

    {
      "status": "success",
      "passport_number": "001234567",
      "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
      "ocr_text": "Ukraine...",
      "processing_time": "0.45s",
      "error_message": null
    }

**Error (404):**

    {
      "detail": "File not found: D:\\Images\\passport.jpg"
    }

#### Health Check

    curl http://127.0.0.1:8000/api/health

**Response:**

    {
      "status": "ok",
      "model_loaded": true,
      "service": "passport_api",
      "version": "0.1.0"
    }

#### Service Info

    curl http://127.0.0.1:8000/api/info

## System Architecture

    +-----------------------------------------------------+
    |              Web Browser (HTML/JS)                  |
    |         (input file path + button "Process")        |
    +----------------------+------------------------------+
                           | HTTP (GET / POST)
                           v
    +-------------------------------------------------+
    |            FastAPI Server (api.py)              |
    |  +--------------------------------------+       |
    |  | GET /  -> Returns index.html         |       |
    |  | POST /api/process -> Process request |       |
    |  | GET /api/health  -> Server status    |       |
    |  | GET /api/info    -> Service INFO     |       |
    |  +--------------------------------------+       |
    +------------------+------------------------------+
                       | (PassportOCREngine class)
                       v
    +--------------------------------------------------+
    |       Inference Engine (inference.py)            |
    |  +---------------------------------------+       |
    |  | 1. Load image (PIL)                   |       |
    |  | 2. Run Florence-2 with <OCR>          |       |
    |  | 3. Remove special tokens              |       |
    |  | 4. Regex for passport number          |       |
    |  | 5. Base64 encode result               |       |
    |  +---------------------------------------+       |
    +------------------+-------------------------------+
                       |
                       v
    +--------------------------------------------------+
    |     Florence-2-Large Model (CUDA GPU)            |
    |  Parameters: 0.77B                               |
    |  Dtype: FP16 (float16)                           |
    |  Attention: SDPA (scaled_dot_product_attention)  |
    |  VRAM: ~2.5-3.5 GB                               |
    +--------------------------------------------------+

## Passport Recognition Formats

### Ukrainian ID Card
- **Format:** 9 digits
- **Examples:** `123 456 789`, `123456789`

### Ukrainian Passport Booklet
- **Format:** 2 letters + 6 digits
- **Examples:** `AB 123456`, `AB123456`

### International Passport
- **Format:** 9 characters (letters + numbers)
- **Examples:** `NA1234567`, `XX9876543`

## Technical Parameters

### Required Stack
- **Python:** 3.10+
- **PyTorch:** 2.0.0+ (CUDA 12.1 support)
- **transformers:** 4.42.4
- **numpy:** <2.0
- **FastAPI:** 0.104+
- **Uvicorn:** 0.24+

### Hardware Requirements
- **GPU VRAM:** Minimum 4 GB, Recommended 6+ GB
- **System RAM:** Minimum 16 GB, Recommended 32 GB
- **CPU:** Quad-core minimum
- **Disk:** 5 GB minimum
- **GPU:** NVIDIA RTX 3050+

### Performance
- **Cold Start Time:** ~3-5 sec (first run)
- **Warm Inference Time:** <1.5 sec per image
- **Max Image Size:** ~2000x2000 px
- **Batch Processing:** 1 request / ~0.5 sec
- **VRAM Peak Usage:** ~3.5 GB

## Deployment Guide

### 1. Local Machine (Windows/Linux/macOS)
Easiest for development.
    
    # Install
    pip install torch --index-url https://download.pytorch.org/whl/cu121
    pip install -r requirements.txt
    python model_setup.py
    
    # Run
    python api.py

### 2. Docker Container
Recommended for production.

#### Dockerfile

    FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04
    
    RUN apt-get update && apt-get install -y \
        python3.10 python3.10-venv python3-pip git \
        && rm -rf /var/lib/apt/lists/*
    
    WORKDIR /app
    COPY requirements.txt .
    COPY . .
    
    RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    RUN pip install --no-cache-dir -r requirements.txt
    
    EXPOSE 8000
    CMD ["python", "api.py"]

#### Docker Compose

    version: '3.8'
    services:
      passport-api:
        build: .
        ports:
          - "8000:8000"
        volumes:
          - ./models:/app/models
          - ./logs:/app/logs
        environment:
          - CUDA_VISIBLE_DEVICES=0
        deploy:
          resources:
            reservations:
              devices:
                - driver: nvidia
                  count: 1
                  capabilities: [gpu]
        restart: unless-stopped

#### Run Docker

    docker-compose up -d

### 3. Cloud Deployment (AWS)
- **Instance:** EC2 p3.2xlarge or similar with GPU.
- **AMI:** Deep Learning AMI with CUDA 12.1.
- **Steps:** SSH into instance, clone repo, install requirements, run setup, run api.

## Production Security

1. **HTTPS (SSL/TLS):** Configure uvicorn with ssl_keyfile and ssl_certfile.
2. **Authentication:** Implement HTTPBearer or API keys in FastAPI.
3. **Rate Limiting:** Use slowapi.
4. **CORS:** Configure CORSMiddleware.

## Troubleshooting

### ModuleNotFoundError: No module named 'flash_attn'
- **Cause:** Dependency not removed during patching.
- **Solution:** Run `python model_setup.py` again.

### CUDA out of memory
- **Cause:** Insufficient VRAM or large image.
- **Solution:** Close other GPU apps, resize image (< 1024x1024), restart server.

### FileNotFoundError: Model folder not found
- **Cause:** Model not downloaded.
- **Solution:** Run `python model_setup.py`.

### Slow Processing (>2 sec)
- **Cause:** Large file or GPU contention.
- **Solution:** Optimize image size, check GPU usage.

## API Documentation (Swagger)
Open: `http://127.0.0.1:8000/docs`

## License
Educational purpose.
- **Florence-2 Model:** Published by Microsoft Research.
- **Code:** MIT License.
