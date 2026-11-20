
from types import SimpleNamespace

import src.predict as predict_module


# Prueba 9: Seleccionar la etiqueta
# con mayor confianza
def test_clasificar_animal(monkeypatch):

    monkeypatch.setenv(
        "MODEL_VERSION_ARN",
        "arn:aws:rekognition:us-east-1:123456789012:"
        "project/test/version/test.1/123"
    )

    def respuesta_simulada(**kwargs):
        assert kwargs["Image"]["Bytes"] == b"imagen_prueba"

        return {
            "CustomLabels": [
                {
                    "Name": "cat",
                    "Confidence": 75.0
                },
                {
                    "Name": "dog",
                    "Confidence": 98.5
                }
            ]
        }

    cliente_falso = SimpleNamespace(
        detect_custom_labels=respuesta_simulada
    )

    monkeypatch.setattr(
        predict_module,
        "rekognition",
        cliente_falso
    )

    resultado = predict_module.clasificar_animal(
        b"imagen_prueba"
    )

    assert resultado["animal"] == "dog"
    assert resultado["confidence"] == 98.5


# Prueba 10: Sin animales detectados
def test_sin_animales_detectados(monkeypatch):

    monkeypatch.setenv(
        "MODEL_VERSION_ARN",
        "arn:aws:rekognition:us-east-1:123456789012:"
        "project/test/version/test.1/123"
    )

    cliente_falso = SimpleNamespace(
        detect_custom_labels=lambda **kwargs: {
            "CustomLabels": []
        }
    )

    monkeypatch.setattr(
        predict_module,
        "rekognition",
        cliente_falso
    )

    resultado = predict_module.clasificar_animal(
        b"imagen_prueba"
    )

    assert resultado["animal"] is None
    assert resultado["confidence"] == 0
