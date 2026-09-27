"""
Validate trained YOLO models on their test sets.
Run after training to see mAP, precision, recall.
"""
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).parent.parent

SMOKING_MODEL = BASE_DIR / "smoking.pt"
ID_CARD_MODEL = BASE_DIR / "id_card.pt"

SMOKING_DATA = BASE_DIR.parent / "smoking-datasets" / "data.yaml"
ID_CARD_DATA = BASE_DIR.parent / "AI Engine" / "Datasets" / "id_card" / "data.yaml"


def validate(model_path, data_yaml, name):
    if not Path(model_path).exists():
        print(f"[validate] model not found: {model_path}")
        return
    if not Path(data_yaml).exists():
        print(f"[validate] dataset not found: {data_yaml}")
        return

    print(f"\n=== Validating {name} ===")
    model = YOLO(str(model_path))
    metrics = model.val(data=str(data_yaml), split="test", verbose=False)

    print(f"mAP50-95: {metrics.box.map:.4f}")
    print(f"mAP50:    {metrics.box.map50:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall:    {metrics.box.mr:.4f}")


if __name__ == "__main__":
    validate(SMOKING_MODEL, SMOKING_DATA, "Smoking Model")
    validate(ID_CARD_MODEL, ID_CARD_DATA, "ID Card Model")
