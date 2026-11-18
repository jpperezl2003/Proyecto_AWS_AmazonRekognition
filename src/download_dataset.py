
from datasets import load_dataset
from pathlib import Path
import random

# Configuración
IMAGES_PER_CLASS = 200
TRAIN_RATIO = 0.8
random.seed(42)

# Cargar dataset
dataset = load_dataset(
    "Rapidata/Animals-10",
    split="train"
)

# Obtener todas las categorías
classes = dataset.features["label"].names

print("Categorías:", classes)

# Organizar imágenes por categoría
for class_id, class_name in enumerate(classes):

    indices = [
        i for i, label in enumerate(dataset["label"])
        if label == class_id
    ]

    random.shuffle(indices)

    # Seleccionar imágenes
    if IMAGES_PER_CLASS is not None:
        indices = indices[:IMAGES_PER_CLASS]

    # Dividir train y test
    train_size = int(len(indices) * TRAIN_RATIO)

    splits = {
        "train": indices[:train_size],
        "test": indices[train_size:]
    }

    for split, selected_indices in splits.items():

        folder = Path("data") / split / class_name.lower()
        folder.mkdir(parents=True, exist_ok=True)

        for idx in selected_indices:
            image = dataset[idx]["image"]

            image = image.convert("RGB")

            image.save(
                folder / f"{class_name.lower()}_{idx}.jpg",
                format="JPEG"
            )

    print(f"{class_name}: {len(indices)} imágenes")

print("Dataset preparado correctamente")
