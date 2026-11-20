
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from botocore.exceptions import ClientError

import src.main as main_module


client = TestClient(main_module.app)


# Crear una imagen de prueba en memoria
def crear_imagen():
    imagen = Image.new("RGB", (100, 100), "white")

    buffer = BytesIO()
    imagen.save(buffer, format="JPEG")

    return buffer.getvalue()


# Prueba 1: Health Check
def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# Prueba 2: Imagen válida y predicción simulada
def test_predict_correcto(monkeypatch):

    def prediccion_falsa(image_bytes):
        return {
            "animal": "dog",
            "confidence": 98.5
        }

    monkeypatch.setattr(
        main_module,
        "clasificar_animal",
        prediccion_falsa
    )

    response = client.post(
        "/predict",
        files={
            "file": (
                "perro.jpg",
                crear_imagen(),
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 200

    resultado = response.json()

    assert resultado["prediction"]["animal"] == "dog"
    assert resultado["prediction"]["confidence"] == 98.5


# Prueba 3: Rechazar archivos no permitidos
def test_archivo_no_permitido():

    response = client.post(
        "/predict",
        files={
            "file": (
                "documento.txt",
                b"Hola mundo",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400


# Prueba 4: Rechazar imágenes corruptas
def test_imagen_invalida():

    response = client.post(
        "/predict",
        files={
            "file": (
                "imagen.jpg",
                b"Esto no es una imagen real",
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 400


# Prueba 5: Rechazar archivos de 4 MB o más
def test_imagen_demasiado_grande():

    imagen_grande = b"x" * (4 * 1024 * 1024)

    response = client.post(
        "/predict",
        files={
            "file": (
                "grande.jpg",
                imagen_grande,
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 400


# Prueba 6: Solicitud sin archivo
def test_sin_archivo():

    response = client.post("/predict")

    assert response.status_code == 422


# Prueba 7: Error de configuración del modelo
def test_error_modelo(monkeypatch):

    def modelo_no_disponible(image_bytes):
        raise RuntimeError("Modelo no configurado")

    monkeypatch.setattr(
        main_module,
        "clasificar_animal",
        modelo_no_disponible
    )

    response = client.post(
        "/predict",
        files={
            "file": (
                "perro.jpg",
                crear_imagen(),
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 503


# Prueba 8: Error al consultar AWS
def test_error_aws(monkeypatch):

    def aws_falla(image_bytes):
        raise ClientError(
            {
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "Sin permisos"
                }
            },
            "DetectCustomLabels"
        )

    monkeypatch.setattr(
        main_module,
        "clasificar_animal",
        aws_falla
    )

    response = client.post(
        "/predict",
        files={
            "file": (
                "perro.jpg",
                crear_imagen(),
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 502
