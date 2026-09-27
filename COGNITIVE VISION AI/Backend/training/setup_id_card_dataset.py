"""
Create the empty folder structure and data.yaml for the id_card dataset.
After running this, add your labeled images to train/valid/test folders.
"""
from pathlib import Path

base = Path(__file__).parent.parent.parent
id_card_dir = base / "AI Engine" / "Datasets" / "id_card"

for split in ["train", "valid", "test"]:
    (id_card_dir / split / "images").mkdir(parents=True, exist_ok=True)
    (id_card_dir / split / "labels").mkdir(parents=True, exist_ok=True)

yaml_path = id_card_dir / "data.yaml"
yaml_path.write_text("""train: train/images
val: valid/images
test: test/images

nc: 1
names: ['id-card']
""")

print(f"[setup] created id_card dataset structure at: {id_card_dir}")
print("[setup] next steps:")
print("  1. Add labeled images to train/images, valid/images, test/images")
print("  2. Add YOLO .txt labels to train/labels, valid/labels, test/labels")
print("  3. Run: venv\\Scripts\\python.exe Backend\\training\\train_id_card.py")
