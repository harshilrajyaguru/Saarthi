import os
import sys
import pathlib
from dotenv import load_dotenv

_ENV_PATH = pathlib.Path(__file__).resolve().parent.parent / ".parent" / ".env"
load_dotenv(dotenv_path=str(_ENV_PATH), override=True)

sys.path.insert(0, os.path.abspath("."))

from agents.groq_model import GroqModel
from strands import Agent
from tools.progress_tools import get_history

class DebugGroqModel(GroqModel):
    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        print("\n=== DEBUG GROQ MODEL STREAM INVOKED ===")
        print(f"Messages count: {len(messages)}")
        for i, m in enumerate(messages):
            print(f"\nMessage #{i}: type={type(m)}, role={getattr(m, 'role', m.get('role') if isinstance(m, dict) else None)}")
            content = getattr(m, 'content', m.get('content') if isinstance(m, dict) else None)
            print(f"  Content type: {type(content)}")
            if isinstance(content, list):
                for j, b in enumerate(content):
                    print(f"    Block #{j}: type={type(b)}, dir={[attr for attr in dir(b) if not attr.startswith('_')]}")
                    if hasattr(b, "__dict__"):
                        print(f"      __dict__={b.__dict__}")
                    elif isinstance(b, dict):
                        print(f"      dict={b}")
        async for item in super().stream(messages, tool_specs, system_prompt, **kwargs):
            yield item

def main():
    model = DebugGroqModel(model_name="openai/gpt-oss-20b", reasoning_effort="low")
    agent = Agent(model=model, system_prompt="You are a helpful assistant", tools=[get_history])
    res = agent("Diagnose Grade 3 Math progress using history tool.")
    print("Result:", res)

if __name__ == "__main__":
    main()
