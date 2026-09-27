import cv2
from ultralytics import YOLO

# Load your newly trained smoking model
model = YOLO('AI Engine/Models/smoking.pt')

# Start the webcam (0 is usually the default built-in camera)
cap = cv2.VideoCapture(0)

print("Live testing has started. Press 'q' on your keyboard to exit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Error: Could not read frame from webcam.")
        break

    # Run YOLOv8 inference on the frame
    results = model(frame)
    
    # Draw the bounding boxes on the frame
    annotated_frame = results[0].plot()

    # Display the live feed
    cv2.imshow("Smoking and Vaping Detection", annotated_frame)

    # Press 'q' to break out of the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()