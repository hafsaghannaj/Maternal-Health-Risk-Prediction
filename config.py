import os
import torch
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Security settings
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-12345")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-key-12345")
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "artemis_admin_key")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per day;50 per hour")

    # Data settings
    NUM_HOSPITALS = 3
    NUM_SAMPLES_PER_HOSPITAL = 1000
    NUM_FEATURES = 25
    TEST_SIZE = 0.2
    
    # Model settings
    INPUT_SIZE = 25
    HIDDEN_SIZE = 64
    OUTPUT_SIZE = 1
    DROPOUT_RATE = 0.3
    
    # Training settings
    BATCH_SIZE = 32
    NUM_EPOCHS = 10
    LEARNING_RATE = 0.001
    FEDERATED_ROUNDS = 5
    
    # Privacy settings
    MAX_GRAD_NORM = 1.0
    NOISE_MULTIPLIER = 1.1
    DELTA = 1e-5
    
    # Device
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Storage
    DB_PATH = os.path.join(BASE_DIR, "artemis.sqlite3")
    MODEL_DIR = os.path.join(BASE_DIR, "saved_models")
    
config = Config()
