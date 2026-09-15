from google import genai
from google.genai import types

try:
    client = genai.Client(api_key="TEST")
    config = types.GenerateContentConfig(system_instruction="system prompt")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
