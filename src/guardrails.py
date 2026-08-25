from pathlib import Path
import logging
import re

from nemoguardrails import RailsConfig

from src.config import get_settings
from src.schemas import Role, UserContext

logger = logging.getLogger(__name__)

SALARY_PATTERNS = [r"\bsalary\b", r"\bcompensation\b", r"\bpayroll\b", r"\bbonus\b"]
INJECTION_PATTERNS = [
    r"ignore (all|previous) instructions",
    r"override (the )?system",
    r"reveal (the )?(system )?prompt",
    r"act as if you are",
    r"bypass (all )?rules",
]
OFF_TOPIC_PATTERNS = [
    r"\bweather\b",
    r"\bjoke\b",
    r"\btrivia\b",
    r"\bmovie\b",
    r"\bfootball\b",
    r"\bsmall talk\b",
]


def load_guardrails_config() -> RailsConfig:
    settings = get_settings()
    config_path = Path(settings.guardrails_config_dir)
    return RailsConfig.from_path(str(config_path))


def _matches_any_pattern(query: str, patterns: list[str]) -> bool:
    lowered_query = query.lower()
    return any(re.search(pattern, lowered_query, flags=re.IGNORECASE) for pattern in patterns)


def apply_guardrails(query: str, user_context: UserContext) -> tuple[bool, str]:
    try:
        load_guardrails_config()
    except Exception as exc:  # pragma: no cover - config load is best-effort for local tests
        logger.warning("Guardrails config could not be loaded: %s", exc)

    if _matches_any_pattern(query, INJECTION_PATTERNS):
        return False, "Blocked prompt injection attempt that tries to override system instructions or roles."

    if _matches_any_pattern(query, SALARY_PATTERNS) and user_context.role not in {Role.hr, Role.admin}:
        return False, "Blocked salary or compensation question for non-HR/admin users."

    if _matches_any_pattern(query, OFF_TOPIC_PATTERNS):
        return False, "Blocked off-topic question unrelated to company documents."

    return True, "Allowed"
