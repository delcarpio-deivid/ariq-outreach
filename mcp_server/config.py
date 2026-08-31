"""Configuration loaded from environment variables."""

from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
COUNTRY_CODE: str = os.getenv("COUNTRY_CODE", "51")
RATE_LIMIT_SECONDS: float = float(os.getenv("RATE_LIMIT_SECONDS", "4"))
SENDER_NAME: str = os.getenv("SENDER_NAME", "Consultor")
LEADS_CSV: str = os.getenv("LEADS_CSV", "data/leads_arequipa.csv")
PROCESSED_CSV: str = "data/processed_leads.csv"

SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "system_prompt.md"
VARIACIONES_PATH = PROJECT_ROOT / "prompts" / "variaciones.md"
