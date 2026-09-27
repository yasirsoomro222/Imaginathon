"""
Convert polygon segmentation labels to YOLO bounding box labels.
Some datasets export class 1 as polygons (many x,y pairs).
YOLOv8 detection expects: <class> <xc> <yc> <w> <h>

Run this on smoking-datasets (or any dataset) before training.
"""
import shutil
from pathlib import Path


def polygon_to_bbox(points):
    """Return normalized (xc, yc, w, h) from a list of [x1, y1, x2, y2, ...]."""
    xs = points[0::2]
    ys = points[1::2]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    xc = (xmin + xmax) / 2.0
    yc = (ymin + ymax) / 2.0
    w = xmax - xmin
    h = ymax - ymin

    # Clamp
    xc = max(0.0, min(1.0, xc))
    yc = max(0.0, min(1.0, yc))
    w = max(0.0, min(1.0, w))
    h = max(0.0, min(1.0, h))

    return xc, yc, w, h


def fix_labels(dataset_dir, backup=True):
    dataset_dir = Path(dataset_dir)
    fixed_count = 0
    skipped_count = 0

    for split in ["train", "valid", "test"]:
        lbl_dir = dataset_dir / split / "labels"
        if not lbl_dir.exists():
            continue

        for label_path in lbl_dir.glob("*.txt"):
            lines = label_path.read_text().strip().splitlines()
            new_lines = []
            changed = False

            for line in lines:
                if not line.strip():
                    continue
                parts = line.strip().split()

                if len(parts) == 5:
                    # Already a bbox
                    new_lines.append(line)
                elif len(parts) > 5 and len(parts) % 2 == 1:
                    # Polygon: class + pairs
                    cls_id = parts[0]
                    coords = [float(p) for p in parts[1:]]
                    xc, yc, w, h = polygon_to_bbox(coords)
                    if w > 0 and h > 0:
                        new_lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
                    changed = True
                else:
                    skipped_count += 1
                    print(f"[fix] skipping weird line in {label_path}: {line}")

            if changed:
                if backup and not label_path.with_suffix(".txt.poly_backup").exists():
                    shutil.copy2(label_path, label_path.with_suffix(".txt.poly_backup"))
                label_path.write_text("\n".join(new_lines) + "\n")
                fixed_count += 1

    print(f"[fix] fixed {fixed_count} label files, skipped {skipped_count} lines")


if __name__ == "__main__":
    base = Path(__file__).parent.parent.parent
    fix_labels(base / "smoking-datasets")
