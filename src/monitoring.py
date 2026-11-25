import os
import logging
import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)
NAMESPACE = "AnimalVision/ML"
REGION = "us-east-1"


def publish_metrics(metrics):
    if os.getenv("ENABLE_CLOUDWATCH_METRICS", "false").lower() != "true":
        return False
    try:
        cloudwatch = boto3.client(
            "cloudwatch", region_name=REGION,
            config=Config(connect_timeout=2, read_timeout=2,
                          retries={"total_max_attempts": 1}),
        )
        cloudwatch.put_metric_data(Namespace=NAMESPACE, MetricData=metrics)
        logger.info("Métricas enviadas a CloudWatch")
        return True
    except Exception:
        logger.exception("Error al publicar métricas en CloudWatch")
        return False


def count_metric(name, value, dimensions=None):
    metric = {"MetricName": name, "Value": value, "Unit": "Count"}
    if dimensions:
        metric["Dimensions"] = dimensions
    return metric


def record_prediction(result):
    animal = result.get("animal")
    metrics = [
        count_metric("PredictionCount", 1, [
            {"Name": "Animal", "Value": str(animal) if animal else "Unidentified"}
        ]),
        count_metric("PredictionErrors", 0),
    ]
    if animal:
        metrics.append({"MetricName": "PredictionConfidence",
                        "Value": float(result["confidence"]), "Unit": "Percent"})
    publish_metrics(metrics)


def record_prediction_error():
    publish_metrics([count_metric("PredictionErrors", 1)])


def record_feedback(correct):
    return publish_metrics([
        count_metric("CorrectPredictions", int(correct)),
        count_metric("IncorrectPredictions", int(not correct)),
        count_metric("UserFeedbackCount", 1),
    ])
