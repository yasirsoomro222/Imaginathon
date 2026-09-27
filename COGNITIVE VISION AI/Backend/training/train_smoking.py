"""
Train YOLOv8 smoking detection model.
Adds negative examples automatically if a 'negatives' folder exists.
"""
import os
import shutil
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR.parent / "smoking-datasets"
NEGATIVES_DIR = BASE_DIR.parent / "smoking-datasets" / "negatives"
DATA_YAML = DATASET_DIR / "data.yaml"

RUNS_DIR = BASE_DIR / "training" / "runs"


def add_negatives():
    """Copy negative-example images into train/images with empty label files."""
    if not NEGATIVES_DIR.exists():
        print(f"[train] no negatives folder found at {NEGATIVES_DIR}")
        return

    train_img_dir = DATASET_DIR / "train" / "images"
    train_lbl_dir = DATASET_DIR / "train" / "labels"
    train_img_dir.mkdir(parents=True, exist_ok=True)
    train_lbl_dir.mkdir(parents=True, exist_ok=True)

    added = 0
    for img_path in NEGATIVES_DIR.glob("*"):
        if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
            continue
        dest_img = train_img_dir / img_path.name
        shutil.copy2(img_path, dest_img)

        label_name = img_path.stem + ".txt"
        label_path = train_lbl_dir / label_name
        label_path.write_text("")  # empty label = no objects
        added += 1

    print(f"[train] added {added} negative examples")


def main():
    if not DATA_YAML.exists():
        raise FileNotFoundError(f"data.yaml not found at {DATA_YAML}")

    add_negatives()

    # Load a pretrained YOLOv8n model (small & fast)
    model = YOLO("yolov8n.pt")

    print(f"[train] starting smoking model training from {DATA_YAML}")

    model.train(
        data=str(DATA_YAML),
        epochs=50,
        imgsz=640,
        batch=16,
        name="smoking_model",
        project=str(RUNS_DIR / "detect"),
        patience=10,
        device="0" if os.system("nvidia-smi > nul 2>&1") == 0 else "cpu",
        exist_ok=True,
    )

    best_path = RUNS_DIR / "detect" / "smoking_model" / "weights" / "best.pt"
    dest_path = BASE_DIR / "smoking.pt"
    if best_path.exists():
        shutil.copy2(best_path, dest_path)
        print(f"[train] copied best model to {dest_path}")
    else:
        print(f"[train] best model not found at {best_path}")


if __name__ == "__main__":
    main()
