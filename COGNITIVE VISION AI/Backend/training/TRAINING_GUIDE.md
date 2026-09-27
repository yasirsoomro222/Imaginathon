# YOLOv8 Training Guide for CampusGuard AI

## 1. Dataset Format (YOLOv8)

Each dataset folder should look like this:

```
dataset_name/
├── data.yaml
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

### `data.yaml` example

```yaml
train: train/images
val: valid/images
test: test/images

nc: 2
names: ['cigarette', 'vape']
```

### Label format

Each `.txt` file has one line per object:

```
<class_id> <x_center> <y_center> <width> <height>
```

All values are normalized (0 to 1).

## 2. Smoking Dataset

Your current dataset is at:

```
COGNITIVE VISION AI/smoking-datasets/
```

It has ~17k train images with classes `cigarette` and `vape`.

### Dataset cleanup (already done)

The original labels had two problems:

1. Some labels were **segmentation polygons** (many x,y points) instead of bounding boxes.
2. Some labels had invalid class IDs (2, 3) while `data.yaml` only allows 0 and 1.

I fixed both issues with these scripts:

```bash
venv\Scripts\python.exe Backend\training\fix_segmentation_labels.py
venv\Scripts\python.exe Backend\training\clean_invalid_classes.py
```

Backups of original labels are saved as `.txt.poly_backup`.

### Validate dataset

```bash
venv\Scripts\python.exe Backend\training\validate_dataset.py
```

### Improving smoking accuracy

To reduce false positives (shirt logos, pens, walls), add **negative examples**:

1. Collect 500-1000 images of:
   - People with pens/pencils in mouth
   - People with shirt logos / pocket designs
   - Empty classrooms / cafeteria walls
   - Hands near face without cigarette
   - Phones held like cigarettes
2. Put them in `smoking-datasets/negatives/`.
3. The training script `train_smoking.py` will automatically copy them into `train/images` with empty labels.
4. Re-run training.

## 3. ID Card Dataset

Your `AI Engine/Datasets/id_card/` folder is empty. You must create it.

### Step-by-step

1. Collect images/videos of students wearing ID cards.
2. Use a labeling tool like:
   - [Roboflow](https://roboflow.com/) (recommended, free)
   - [CVAT](https://cvat.org/)
   - [LabelImg](https://github.com/tzutalin/labelImg)
3. Draw bounding boxes around ID cards only.
4. Class name must be exactly: `id-card`
5. Export in **YOLOv8 format**.
6. Folder structure:

```
id_card/
├── data.yaml
├── train/images/  .jpg files
├── train/labels/  .txt files
├── valid/images/
├── valid/labels/
├── test/images/
└── test/labels/
```

### `data.yaml` for id_card

```yaml
train: train/images
val: valid/images
test: test/images

nc: 1
names: ['id-card']
```

**Important:** Do NOT include smoking images or any other class in the id_card dataset. Only `id-card` labels.

### Recommended minimum images

- Train: 500+ images
- Valid: 100+ images
- Test: 50+ images

Include variety:
- Different angles
- Different lighting
- Partially hidden ID cards
- People without ID cards (empty labels as negative examples)

## 4. Training Scripts

Run from project root:

```bash
venv\Scripts\python.exe Backend\training\train_smoking.py
venv\Scripts\python.exe Backend\training\train_id_card.py
```

Trained models will be saved in:

```
Backend/training/runs/detect/
```

Copy the best model to `Backend/`:

```bash
copy "Backend\training\runs\detect\smoking_model\weights\best.pt" "Backend\smoking.pt"
copy "Backend\training\runs\detect\id_card_model\weights\best.pt" "Backend\id_card.pt"
```

## 5. Training Tips

- Use GPU if available (CUDA). Training on CPU will be very slow.
- Start with `epochs=50` and increase if validation loss is still decreasing.
- If model overfits, reduce epochs or add more augmentation.
- Use `imgsz=640` for most cases.
- For ID card, if cards are small in frame, try `imgsz=1280` but it needs more GPU memory.

## 6. Validate Model

After training, run:

```bash
venv\Scripts\python.exe Backend\training\validate_models.py
```

This will show mAP, precision, recall for both models.
