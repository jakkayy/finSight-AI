import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


def groq_retry(func):
    """Decorator: retry on Groq rate-limit or transient errors with exponential backoff."""
    return retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=lambda rs: logger.warning(
            "Retrying %s (attempt %d)...", rs.fn.__name__, rs.attempt_number
        ),
    )(func)
