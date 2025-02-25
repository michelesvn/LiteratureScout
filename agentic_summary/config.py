import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Azure OpenAI API configuration settings
API_KEY = os.getenv("API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")
API_VERSION = os.getenv("API_VERSION")

# Project's root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Paths to input and output directories
INPUT_PATH = os.path.join(PROJECT_ROOT, "scraper", "output")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "agentic_summary", "output")

# Additional configuration settings for PDF processing and AI model parameters
PDF_DPI = 300
IMAGE_QUALITY = 80

# AI model configuration settings
MAX_TOKENS = 10000
TEMPERATURE = 0.0
TOP_P = 0.95
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0

# PDF batching limit
MAX_PDFS_PER_FILE = 50
