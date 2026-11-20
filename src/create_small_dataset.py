from pathlib import Path
import random
import shutil

# Configuración
IMAGES_PER_CLASS = 40
random.seed(42)

# Rutas del proyecto
ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "data" / "animals-10" / "train"
DESTINATION = ROOT / "data" / "animals-10" / "train-10"

CLASSES = [
    "butterfly", "cat", "chicken", "cow", "dog",
    "elephant", "horse", "sheep", "spider", "squirrel"
]

if DESTINATION.exists():
    raise SystemExit(
        "La carpeta train-10 ya existe. Revísala antes de repetir."
    )

total = 0

for animal in CLASSES:
    source_folder = SOURCE / animal
    destination_folder = DESTINATION / animal

    images = sorted(
        image for image in source_folder.iterdir()
        if image.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )

    if len(images) < IMAGES_PER_CLASS:
        raise ValueError(f"No hay suficientes imágenes de {animal}")

    selected = random.sample(images, IMAGES_PER_CLASS)

    destination_folder.mkdir(parents=True, exist_ok=True)

    for image in selected:
        shutil.copy2(image, destination_folder / image.name)

    total += len(selected)
    print(f"{animal}: {len(selected)} imágenes")

print(f"Total seleccionado: {total}")
