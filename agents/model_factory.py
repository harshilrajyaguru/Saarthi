import os
import pathlib
from dotenv import load_dotenv

from strands.models import BedrockModel
from strands.models.openai import OpenAIModel  # Strands OpenAI-compatible wrapper

_ENV_PATH = pathlib.Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=str(_ENV_PATH), override=False)


def get_saarthi_model(**kwargs):
    """Returns either Groq or Bedrock based on cloud environment variables."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "bedrock":
        # Keep your existing Bedrock setup safe and untouched
        return BedrockModel(
            model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            **kwargs
        )
    else:
        # Default to Groq for current cloud deployment
        return OpenAIModel(
            client_args={
                "api_key": os.getenv("GROQ_API_KEY"),
                "base_url": "https://api.groq.com/openai/v1",
            },
            model_id=os.getenv("GROQ_MODEL_ID", "openai/gpt-oss-120b"),
            **kwargs
        )


def get_model(**kwargs):
    """Alias for get_saarthi_model."""
    return get_saarthi_model(**kwargs)
