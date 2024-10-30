import os
from pathlib import Path
from dotenv import load_dotenv

# Get the absolute path to the .env file
env_path = Path(__file__).parent / '.env'

# Load environment variables from .env file
load_dotenv(dotenv_path=env_path, override=True)

class Config:
    # Reddit Configuration
    REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

    # Azure Cosmos DB Configuration
    COSMOS_ENDPOINT = os.environ.get('COSMOS_ENDPOINT')
    COSMOS_KEY = os.environ.get('COSMOS_KEY')
    COSMOS_DATABASE = os.environ.get('COSMOS_DATABASE')

    @classmethod
    def validate(cls):
        missing = []
        for key, value in vars(cls).items():
            if not key.startswith('_') and isinstance(value, (str, int)) and value is None:
                missing.append(key)
        if missing:
            print(f"Missing configuration values: {', '.join(missing)}")
            return False
        return True

    @classmethod
    def print_config(cls):
        print("\nCurrent Configuration:")
        for key, value in vars(cls).items():
            if not key.startswith('_') and isinstance(value, (str, int)):
                if 'KEY' in key or 'SECRET' in key:
                    print(f"{key}: ********")
                else:
                    print(f"{key}: {value}")
        print()
