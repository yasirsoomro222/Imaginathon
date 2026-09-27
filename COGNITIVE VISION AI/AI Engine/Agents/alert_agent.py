class AlertAgent:
    def __init__(self):
        print("AlertAgent initialized successfully!")

    def check_and_create_alert(self, detection_status):
        alerts = []
        if detection_status.get("smoking_detected"):
            alerts.append({"type": "Smoking Violation", "severity": "High", "message": "Smoking detected in the monitored area!"})
        if not detection_status.get("id_card_detected") and detection_status.get("confidence", 0) > 0:
            alerts.append({"type": "ID Card Missing", "severity": "Medium", "message": "Person detected without an ID card."})
        return alerts