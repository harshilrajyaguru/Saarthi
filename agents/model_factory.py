import os
import pathlib
from dotenv import load_dotenv

from strands.models import BedrockModel
from strands.models.openai import OpenAIModel  # Strands OpenAI-compatible wrapper

_ENV_PATH = pathlib.Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=str(_ENV_PATH), override=False)


def get_saarthi_model(tier: str = "smart", **kwargs):
    """Returns either Groq or Bedrock based on cloud environment variables and requested tier ('smart' or 'fast')."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "bedrock":
        # Keep Bedrock setup intact for both tiers
        if tier == "fast":
            model_id = os.getenv("BEDROCK_MODEL_ID_FAST") or os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
        else:
            model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

        return BedrockModel(
            model_id=model_id,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            **kwargs
        )
    else:
        # Default to Groq for current cloud deployment
        if tier == "fast":
            model_id = os.getenv("GROQ_MODEL_ID_FAST", "llama-3.1-8b-instant")
        else:
            model_id = os.getenv("GROQ_MODEL_ID", "llama-3.1-8b-instant")

        return OpenAIModel(
            client_args={
                "api_key": os.getenv("GROQ_API_KEY"),
                "base_url": "https://api.groq.com/openai/v1",
            },
            model_id=model_id,
            **kwargs
        )


def get_model(tier: str = "smart", **kwargs):
    """Alias for get_saarthi_model."""
    return get_saarthi_model(tier=tier, **kwargs)
