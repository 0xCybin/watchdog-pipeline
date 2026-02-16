import anthropic
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from watchdog.config import settings
from watchdog.services.cost_tracker import track_expense

log = structlog.get_logger()

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
async def call_claude(
    prompt: str,
    operation: str,
    document_id: str | None = None,
    max_tokens: int = 2000,
    model: str | None = None,
) -> str:
    """Call Claude API with retry logic and cost tracking."""
    model = model or settings.claude_model
    client = get_client()

    log.debug("claude_api_call", operation=operation, model=model)

    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract text
    text = response.content[0].text if response.content else ""

    # Track cost
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    await track_expense(
        model=model,
        operation=operation,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        document_id=document_id,
    )

    log.info(
        "claude_api_response",
        operation=operation,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return text
