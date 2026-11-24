import os
import logging

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)

NAMESPACE = "AnimalVision/ML"
REGION = "us-east-1"


def publish_metrics(metrics):

    # Permitir desactivar el monitoreo durante las pruebas
    if os.getenv("ENABLE_CLOUDWATCH_METRICS", "false").lower() != "true":
        return

    try:
        cloudwatch = boto3.client(
            "cloudwatch",
            region_name=REGION,
            config=Config(
                connect_timeout=2,
                read_timeout=2,
                retries={"total_max_attempts": 1}
            )
        )

        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=metrics
        )

        logger.info("Métricas enviadas a CloudWatch")

    except Exception:
        # Un error de monitoreo no debe detener la aplicación
        logger.exception("Error al publicar métricas en CloudWatch")


def record_prediction(result):

    animal = result.get("animal")

    metrics = [
        {
            "MetricName": "PredictionCount",
            "Dimensions": [
                {
                    "Name": "Animal",
                    "Value": str(animal) if animal else "Unidentified"
                }
            ],
            "Value": 1,
            "Unit": "Count"
        },
        {
            "MetricName": "PredictionErrors",
            "Value": 0,
            "Unit": "Count"
        }
    ]

    # Registrar confianza únicamente si se identificó un animal
    if animal:
        metrics.append(
            {
                "MetricName": "PredictionConfidence",
                "Value": float(result["confidence"]),
                "Unit": "Percent"
            }
        )

    publish_metrics(metrics)


def record_prediction_error():

    publish_metrics(
        [
            {
                "MetricName": "PredictionErrors",
                "Value": 1,
                "Unit": "Count"
            }
        ]
    )
