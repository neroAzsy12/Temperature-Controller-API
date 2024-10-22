import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
class Config:
    # Get the URI from the environment variable
    MONGO_URI = os.getenv('MONGO_URI')