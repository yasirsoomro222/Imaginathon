import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    HOST = "127.0.0.1"
    PORT = 8000
    DEBUG = True
    ID_CARD_MODEL_PATH = os.path.join(BASE_DIR, "Backend", "id_card.pt")
    SMOKING_MODEL_PATH = os.path.join(BASE_DIR, "Backend", "smoking.pt")