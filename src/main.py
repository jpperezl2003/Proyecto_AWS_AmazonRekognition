import logging
from io import BytesIO
from pathlib import Path
from typing import Literal

from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, StrictBool
from starlette.concurrency import run_in_threadpool

from src.predict import clasificar_animal
from src.monitoring import record_prediction, record_prediction_error, record_feedback

app = FastAPI(title="Animal Classifier API")
logger = logging.getLogger(__name__)
MAX_IMAGE_SIZE = 4 * 1024 * 1024
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

Animal = Literal["butterfly", "cat", "chicken", "cow", "dog", "elephant", "horse", "sheep", "spider", "squirrel"]
ActualAnimal = Literal["butterfly", "cat", "chicken", "cow", "dog", "elephant", "horse", "sheep", "spider", "squirrel", "other", "not_animal"]


class Feedback(BaseModel):
    correct: StrictBool
    predicted_animal: Animal
    actual_animal: ActualAnimal


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html", media_type="text/html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes JPG o PNG")
    image_bytes = await file.read(MAX_IMAGE_SIZE + 1)
    if not image_bytes or len(image_bytes) >= MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="La imagen debe ser menor a 4 MB")
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            if img.format not in ["JPEG", "PNG"]:
                raise ValueError("Formato no permitido")
            img.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="La imagen no es válida")
    try:
        result = await run_in_threadpool(clasificar_animal, image_bytes)
    except RuntimeError as error:
        await run_in_threadpool(record_prediction_error)
        raise HTTPException(status_code=503, detail=str(error))
    except (NoCredentialsError, PartialCredentialsError):
        await run_in_threadpool(record_prediction_error)
        raise HTTPException(status_code=503, detail="Credenciales AWS no configuradas")
    except ClientError:
        logger.exception("Error al consultar Amazon Rekognition")
        await run_in_threadpool(record_prediction_error)
        raise HTTPException(status_code=502, detail="Error de AWS. Revisa los permisos y el estado del modelo.")
    await run_in_threadpool(record_prediction, result)
    return {"filename": file.filename, "prediction": result}


@app.post("/feedback")
async def feedback(data: Feedback):
    if data.correct != (data.predicted_animal == data.actual_animal):
        raise HTTPException(status_code=400, detail="La evaluación no coincide con las categorías")
    published = await run_in_threadpool(record_feedback, data.correct)
    if not published:
        raise HTTPException(status_code=503, detail="No se pudo publicar la evaluación")
    logger.info("Feedback: predicted=%s actual=%s correct=%s", data.predicted_animal, data.actual_animal, data.correct)
    return {"status": "ok"}
