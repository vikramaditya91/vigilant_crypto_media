import asyncio
from media.utils.general import MediaEnum


def lambda_handler(event: dict,
                   context: dict) -> dict:
    """
    AWS Lambda handler entry
    Args:
        event: Dictionary with keys: lower, upper, reference
        context:

    Returns:
        Dictionary of coins in between the limits
    """
    event_type = event["type"]
    assert event_type in MediaEnum, f"Event was {event}"
    print(event)
    return {}


if __name__ == "__main__":
    lambda_handler({}, {})
