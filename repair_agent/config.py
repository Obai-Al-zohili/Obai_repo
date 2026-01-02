# config.py
import os
from dotenv import load_dotenv


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
MAX_ITER = 3

PATCH_MARKER_START = "PATCH-START"
PATCH_MARKER_END = "PATCH-END"
