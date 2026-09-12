import os
import pathlib
from dotenv import load_dotenv

_ENV_PATH = pathlib.Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=str(_ENV_PATH), override=True)

import groq

client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
try:
    models = client.models.list()
    print("Available Groq models:")
    for m in models.data:
        print(" -", m.id)
except Exception as e:
    print("Error listing models:", e)
