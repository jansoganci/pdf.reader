from app.models import Usage


def estimate_cost(usage: Usage) -> float:
    million = 1_000_000
    return (
        usage.input_tokens * 2.0
        + usage.cache_creation_input_tokens * 2.5
        + usage.cache_read_input_tokens * 0.2
        + usage.output_tokens * 10.0
    ) / million
