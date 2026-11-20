
import os
import boto3

# Conectar con Amazon Rekognition
rekognition = boto3.client(
    "rekognition",
    region_name="us-east-1"
)


def clasificar_animal(image_bytes):

    # Obtener el ARN de nuestro modelo
    model_arn = os.getenv("MODEL_VERSION_ARN")

    if not model_arn:
        raise RuntimeError(
            "No se configuró MODEL_VERSION_ARN"
        )

    # Enviar imagen al modelo entrenado
    response = rekognition.detect_custom_labels(
        ProjectVersionArn=model_arn,
        Image={"Bytes": image_bytes},
        MinConfidence=50,
        MaxResults=10
    )

    # Obtener las etiquetas detectadas
    labels = response.get("CustomLabels", [])

    if not labels:
        return {
            "animal": None,
            "confidence": 0,
            "message": "Animal no identificado"
        }

    # Obtener la predicción con mayor confianza
    best_label = max(
        labels,
        key=lambda label: label["Confidence"]
    )

    return {
        "animal": best_label["Name"],
        "confidence": round(best_label["Confidence"], 2)
    }
