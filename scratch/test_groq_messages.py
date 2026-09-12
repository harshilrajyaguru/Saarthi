import os
import sys
import json
import pathlib
from dotenv import load_dotenv

_ENV_PATH = pathlib.Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=str(_ENV_PATH), override=True)

sys.path.insert(0, os.path.abspath("."))

from agents.groq_model import GroqModel
from strands import Agent
from tools.progress_tools import get_history

def test():
    model = GroqModel(model_name="openai/gpt-oss-20b", reasoning_effort="low")
    agent = Agent(model=model, system_prompt="You are a helpful assistant", tools=[get_history])
    
    print("Running multi-turn agent test...")
    try:
        res = agent("Diagnose Grade 3 Math progress using history tool.")
        print("\nSUCCESS! Agent Result:", res)
    except Exception as e:
        print("\nFAILED with Exception:", type(e), e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
