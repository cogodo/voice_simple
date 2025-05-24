"""
Configuration settings for the Voice Agent backend.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
# Get the project root directory (parent of the backend directory)
backend_dir = os.path.dirname(os.path.abspath(__file__))  # config directory
backend_parent = os.path.dirname(backend_dir)  # backend directory
project_root = os.path.dirname(backend_parent)  # project root directory
env_path = os.path.join(project_root, '.env')

# Try to load .env file
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✓ Loaded .env file from: {env_path}")
else:
    print(f"⚠️  WARNING: No .env file found at: {env_path}")
    print(f"Please create a .env file with your API keys:")
    print(f"OPENAI_API_KEY=your_openai_key_here")
    print(f"CARTESIA_API_KEY=your_cartesia_key_here")
    print(f"")
    print(f"You can copy .env.example and fill in your keys.")
    response = input("Continue anyway? (y/N): ")
    if response.lower() != 'y':
        exit(1)

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.urandom(24)
    
    # API Keys
    CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Audio settings
    TEMP_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "temp_audio")
    AUDIO_QUALITY_THRESHOLD = float(os.getenv("AUDIO_QUALITY_THRESHOLD", "0.1"))
    MAX_AUDIO_DURATION = int(os.getenv("MAX_AUDIO_DURATION", "60"))  # seconds
    
    # Whisper settings
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")
    
    # OpenAI settings
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
    
    # Voice synthesis settings
    DEFAULT_VOICE_ID = os.getenv("DEFAULT_VOICE_ID", "79a125e8-cd45-4c13-8a67-188112f4dd22")
    VOICE_SPEED = float(os.getenv("VOICE_SPEED", "1.0"))
    VOICE_EMOTION = os.getenv("VOICE_EMOTION", "neutral")
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is set."""
        errors = []
        
        if not cls.CARTESIA_API_KEY:
            errors.append("CARTESIA_API_KEY environment variable is not set")
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY environment variable is not set")
        
        return errors

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class based on environment."""
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    
    return config.get(config_name, DevelopmentConfig) 