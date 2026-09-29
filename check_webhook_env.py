import os
from dotenv import load_dotenv

load_dotenv()

keys = ["GITHUB_WEBHOOK_SECRET", "GITHUB_WEBHOOK_URL"]

for key in keys:
    val = os.environ.get(key)
    if val:
        print(f"{key}: CONFIGURED")
    else:
        print(f"{key}: MISSING")
