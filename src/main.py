
import logging
from io import BytesIO
from pathlib import Path

from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
)

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from src.predict import clasificar_animal


# --------------------------------------------------
# Configuración de FastAPI
# --------------------------------------------------

app = FastAPI(title="Animal Classifier API")

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 4 * 1024 * 1024


# --------------------------------------------------
# Configuración del frontend
# --------------------------------------------------

FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent / "frontend"
)

# Permitir que FastAPI cargue archivos CSS
app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


# --------------------------------------------------
# Página principal
# --------------------------------------------------

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(
        FRONTEND_DIR / "index.html",
        media_type="text/html"
    )


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# Predicción de animales con Amazon Rekognition
# --------------------------------------------------

@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    # Validar tipo de archivo
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten imágenes JPG o PNG"
        )

    # Leer imagen y comprobar tamaño
    image_bytes = await file.read(MAX_IMAGE_SIZE + 1)

    if not image_bytes or len(image_bytes) >= MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="La imagen debe ser menor a 4 MB"
        )

    # Validar que sea una imagen real
    try:
        with Image.open(BytesIO(image_bytes)) as img:

            if img.format not in ["JPEG", "PNG"]:
                raise ValueError("Formato no permitido")

            img.verify()

    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="La imagen no es válida"
        )

    # Enviar fotografía a Amazon Rekognition
    try:
        result = await run_in_threadpool(
            clasificar_animal,
            image_bytes
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    except (NoCredentialsError, PartialCredentialsError):
        raise HTTPException(
            status_code=503,
            detail="Credenciales AWS no configuradas"
        )

    except ClientError:
        logger.exception(
            "Error al consultar Amazon Rekognition"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Error de AWS. Revisa los permisos "
                "y el estado del modelo."
            )
        )

    # Devolver predicción real
    return {
        "filename": file.filename,
        "prediction": result
    }
