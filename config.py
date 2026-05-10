import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """Centralized config loaded from environment variables."""

    openweather_api_key: str | None = os.getenv("OPENWEATHER_API_KEY")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")

    default_currency: str = os.getenv("DEFAULT_CURRENCY", "INR")
    default_country: str = os.getenv("DEFAULT_COUNTRY", "IN")

    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"

    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def get_config() -> AppConfig:
    return AppConfig()


class MissingAPIKeyError(RuntimeError):
    pass


def require_keys(
    cfg: AppConfig,
    *,
    weather: bool = False,
    gemini: bool = False,
    groq: bool = False,
) -> None:
    missing: list[str] = []

    if weather and not cfg.openweather_api_key:
        missing.append("OPENWEATHER_API_KEY")

    if gemini and not cfg.gemini_api_key:
        missing.append("GEMINI_API_KEY")

    if groq and not cfg.groq_api_key:
        missing.append("GROQ_API_KEY")

    if missing:
        raise MissingAPIKeyError(
            "Missing required API key(s): "
            + ", ".join(missing)
            + ". Add them to your .env file or Streamlit Cloud Secrets."
        )