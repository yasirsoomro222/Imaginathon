"""
Validate and clean a YOLOv8 dataset.
Checks:
- Every image has a matching label file (or empty label for negatives)
- Label class IDs are valid
- Bounding boxes are within [0, 1]
- No corrupt images
"""
import os
from pathlib import Path
from PIL import Image


def validate_dataset(dataset_dir, expected_classes=None):
    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        print(f"[validate] dataset not found: {dataset_dir}")
        return False

    splits = ["train", "valid", "test"]
    issues = []
    total_images = 0
    total_labels = 0

    for split in splits:
        img_dir = dataset_dir / split / "images"
        lbl_dir = dataset_dir / split / "labels"

        if not img_dir.exists():
            continue

        for img_path in img_dir.glob("*"):
            if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
                continue

            total_images += 1
            label_path = lbl_dir / (img_path.stem + ".txt")

            try:
                with Image.open(img_path) as im:
                    w, h = im.size
            except Exception as e:
                issues.append(f"corrupt image: {img_path} ({e})")
                continue

            if not label_path.exists():
                issues.append(f"missing label: {label_path}")
                continue

            lines = label_path.read_text().strip().splitlines()
            total_labels += len(lines)

            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                parts = line.strip().split()
                if len(parts) != 5:
                    issues.append(f"bad format {label_path} line {i+1}: {line}")
                    continue

                cls, xc, yc, bw, bh = parts
                try:
                    cls = int(cls)
                    xc, yc, bw, bh = float(xc), float(yc), float(bw), float(bh)
                except ValueError:
                    issues.append(f"non-numeric values {label_path} line {i+1}")
                    continue

                if expected_classes is not None and cls not in range(expected_classes):
                    issues.append(f"invalid class {cls} in {label_path} line {i+1}")

                if not (0 <= xc <= 1 and 0 <= yc <= 1 and 0 <= bw <= 1 and 0 <= bh <= 1):
                    issues.append(f"out-of-range bbox {label_path} line {i+1}")

    print(f"[validate] images: {total_images}, labels: {total_labels}")
    if issues:
        print(f"[validate] {len(issues)} issues found:")
        for issue in issues[:30]:
            print(f"  - {issue}")
        if len(issues) > 30:
            print(f"  ... and {len(issues) - 30} more")
        return False
    else:
        print("[validate] dataset looks good!")
        return True


if __name__ == "__main__":
    import sys

    base = Path(__file__).parent.parent.parent

    print("\n=== Smoking Dataset ===")
    validate_dataset(base / "smoking-datasets", expected_classes=2)

    print("\n=== ID Card Dataset ===")
    validate_dataset(base / "AI Engine" / "Datasets" / "id_card", expected_classes=1)
