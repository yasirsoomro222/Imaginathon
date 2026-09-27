from AI_Engine.Agents.alert_agent import AlertAgent
from AI_Engine.Agents.logging_agent import LoggingAgent

class CoordinatorAgent:
    def __init__(self):
        self.alert_agent = AlertAgent()
        self.logging_agent = LoggingAgent()
        print("CoordinatorAgent initialized successfully!")

    def process_system_state(self, status):
        alerts = self.alert_agent.check_and_create_alert(status)
        for alert in alerts:
            self.logging_agent.log_event(alert["type"], alert["message"])
        return alerts