import datetime

class LoggingAgent:
    def __init__(self):
        print("LoggingAgent initialized successfully!")

    def log_event(self, event_type, details):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{event_type.upper()}] - {details}"
        print(log_entry)
        # Aap chahein toh isay file mein bhi save kar sakte hain
        return log_entry