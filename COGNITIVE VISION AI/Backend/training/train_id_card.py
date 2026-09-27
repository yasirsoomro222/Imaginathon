"""
Train YOLOv8 ID card detection model.
Expected dataset path: AI Engine/Datasets/id_card/data.yaml
"""
import os
import shutil
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR.parent / "AI Engine" / "Datasets" / "id_card"
DATA_YAML = DATASET_DIR / "data.yaml"

RUNS_DIR = BASE_DIR / "training" / "runs"


def validate_dataset():
    if not DATA_YAML.exists():
        raise FileNotFoundError(
            f"id_card dataset not found at {DATA_YAML}\n"
            "Create the dataset first. See Backend/training/TRAINING_GUIDE.md"
        )

    train_img_dir = DATASET_DIR / "train" / "images"
    if not train_img_dir.exists() or not any(train_img_dir.iterdir()):
        raise FileNotFoundError(
            f"No training images found in {train_img_dir}\n"
            "Add labeled images before training."
        )


def main():
    validate_dataset()

    model = YOLO("yolov8n.pt")

    print(f"[train] starting ID card model training from {DATA_YAML}")

    model.train(
        data=str(DATA_YAML),
        epochs=80,
        imgsz=640,
        batch=16,
        name="id_card_model",
        project=str(RUNS_DIR / "detect"),
        patience=15,
        device="0" if os.system("nvidia-smi > nul 2>&1") == 0 else "cpu",
        exist_ok=True,
    )

    best_path = RUNS_DIR / "detect" / "id_card_model" / "weights" / "best.pt"
    dest_path = BASE_DIR / "id_card.pt"
    if best_path.exists():
        shutil.copy2(best_path, dest_path)
        print(f"[train] copied best model to {dest_path}")
    else:
        print(f"[train] best model not found at {best_path}")


if __name__ == "__main__":
    main()
