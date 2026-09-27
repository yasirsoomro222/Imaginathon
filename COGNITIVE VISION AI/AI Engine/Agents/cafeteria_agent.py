from ultralytics import YOLO
import os

class CafeteriaAgent:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        smoking_path = os.path.join(base_dir, "../Models/smoking.pt")

        try:
            self.smoking_model = YOLO(smoking_path)
            print("CafeteriaAgent: Smoking Model loaded successfully!")
        except Exception as e:
            print(f"CafeteriaAgent smoking load error: {e}")
            self.smoking_model = None

    def process_frame(self, frame):
        smoking_found = False
        max_conf = 0.0
        detected_cls = "None"
        
        annotated_frame = frame.copy()

        # Cafeteria mein smoking detection par strict threshold rakhte hain taake false alarms na hon
        if self.smoking_model is not None:
            smoking_res = self.smoking_model(frame, conf=0.65, verbose=False)[0]
            if len(smoking_res.boxes) > 0:
                smoking_found = True
                for box in smoking_res.boxes:
                    conf = float(box.conf[0])
                    if conf > max_conf:
                        max_conf = conf
                        detected_cls = smoking_res.names[int(box.cls[0])]
                annotated_frame = smoking_res.plot(img=annotated_frame)

        status = {
            "cafeteria_smoking_detected": smoking_found,
            "confidence": round(max_conf, 2),
            "detected_class": detected_cls,
            "warning": "Smoking Alert in Cafeteria!" if smoking_found else "Normal"
        }

        return annotated_frame, status