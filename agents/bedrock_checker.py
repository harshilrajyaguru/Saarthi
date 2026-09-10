import os
import boto3
from botocore.config import Config

_BEDROCK_AVAILABLE = None

def is_bedrock_available() -> bool:
    """
    Fast pre-flight check and process-wide circuit breaker for Amazon Bedrock API calls.
    Returns True if Bedrock credentials/session are valid and reachable, False otherwise.
    Caches result for fast subsequent calls.
    """
    global _BEDROCK_AVAILABLE
    if _BEDROCK_AVAILABLE is not None:
        return _BEDROCK_AVAILABLE

    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials or not getattr(credentials, "access_key", None):
            _BEDROCK_AVAILABLE = False
            return False

        # Fast STS call with 1-second connection timeout to avoid blocking
        fast_config = Config(connect_timeout=0.5, read_timeout=0.5, retries={"max_attempts": 0})
        sts = session.client("sts", region_name="us-east-1", config=fast_config)
        sts.get_caller_identity()
        _BEDROCK_AVAILABLE = True
        return True
    except Exception:
        _BEDROCK_AVAILABLE = False
        return False

def mark_bedrock_unavailable():
    global _BEDROCK_AVAILABLE
    _BEDROCK_AVAILABLE = False
