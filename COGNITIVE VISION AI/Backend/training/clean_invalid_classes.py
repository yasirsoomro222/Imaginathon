"""
Remove label lines with class IDs outside the valid range.
For smoking dataset valid classes are 0 (cigarette) and 1 (vape).
This also removes corrupt lines.
"""
from pathlib import Path


def clean_dataset(dataset_dir, max_class_id, backup=True):
    dataset_dir = Path(dataset_dir)
    cleaned_count = 0

    for split in ["train", "valid", "test"]:
        lbl_dir = dataset_dir / split / "labels"
        if not lbl_dir.exists():
            continue

        for label_path in lbl_dir.glob("*.txt"):
            if label_path.suffix == ".poly_backup":
                continue

            lines = label_path.read_text().strip().splitlines()
            valid_lines = []

            for line in lines:
                if not line.strip():
                    continue
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                try:
                    cls_id = int(parts[0])
                except ValueError:
                    continue
                if 0 <= cls_id <= max_class_id:
                    valid_lines.append(line)

            if len(valid_lines) != len(lines):
                label_path.write_text("\n".join(valid_lines) + "\n")
                cleaned_count += 1

    print(f"[clean] cleaned {cleaned_count} label files")


if __name__ == "__main__":
    base = Path(__file__).parent.parent.parent
    clean_dataset(base / "smoking-datasets", max_class_id=1)
