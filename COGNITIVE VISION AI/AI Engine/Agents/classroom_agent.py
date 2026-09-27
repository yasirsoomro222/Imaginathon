from ultralytics import YOLO
import cv2
import os

class ClassroomAgent:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        id_path = os.path.join(base_dir, "../Models/id_card.pt")
        smoking_path = os.path.join(base_dir, "../Models/smoking.pt")

        try:
            self.id_model = YOLO(id_path)
            print("ClassroomAgent: ID Card Model loaded!")
        except Exception as e:
            print(f"ID Card load error: {e}")
            self.id_model = None

        try:
            self.smoking_model = YOLO(smoking_path)
            print("ClassroomAgent: Smoking Model loaded!")
        except Exception as e:
            print(f"Smoking load error: {e}")
            self.smoking_model = None

    def process_frame(self, frame):
        smoking_found = False
        id_card_found = False  
        max_conf = 0.0
        detected_cls = "None"
        
        if frame is None:
            return frame, {}

        annotated_frame = frame.copy()

        try:
            # --- 1. ID CARD DETECTION ---
            if self.id_model is not None:
                id_res = self.id_model(frame, conf=0.20, verbose=False)[0]
                if len(id_res.boxes) > 0:
                    id_card_found = True
                    detected_cls = "ID_Card"
                    annotated_frame = id_res.plot(img=annotated_frame)
                else:
                    id_card_found = False

            # --- 2. SMOKING DETECTION (WITH LABELS AND BOXES) ---
            if self.smoking_model is not None:
                # Confidence 0.45 rakhi hai taake asani se pakre aur label show ho
                smoking_res = self.smoking_model(frame, conf=0.45, verbose=False)[0]
                valid_smoking_boxes = []
                
                for box in smoking_res.boxes:
                    xyxy = box.xyxy[0].tolist()
                    bx1, by1, bx2, by2 = xyxy[0], xyxy[1], xyxy[2], xyxy[3]
                    b_width = bx2 - bx1
                    b_height = by2 - by1
                    
                    if b_width > 0 and b_height > 0:
                        aspect_ratio = b_height / b_width if b_height >= b_width else b_width / b_height
                        
                        # Light filter taake bohat hi barhi ajeeb shape ignore ho, baqi sab detect ho
                        if aspect_ratio > 4.0 or b_width > 300 or b_height > 300:
                            continue
                        
                        valid_smoking_boxes.append(box)
                        smoking_found = True
                        conf = float(box.conf[0])
                        if conf > max_conf:
                            max_conf = conf
                            detected_cls = self.smoking_model.names[int(box.cls[0])]

                if len(valid_smoking_boxes) > 0:
                    smoking_res.boxes = valid_smoking_boxes
                    annotated_frame = smoking_res.plot(img=annotated_frame)

        except Exception as e:
            print(f"Processing error in ClassroomAgent: {e}")
            annotated_frame = frame

        missing_id_alert = not id_card_found

        status = {
            "smoking_detected": smoking_found,
            "id_card_detected": id_card_found,
            "missing_id_alert": missing_id_alert,
            "confidence": round(max_conf, 2),
            "detected_class": detected_cls
        }

        return annotated_frame, status