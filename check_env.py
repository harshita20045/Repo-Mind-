import os
from dotenv import load_dotenv

load_dotenv()

keys = ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "GITHUB_WEBHOOK_SECRET", "JWT_SECRET", "FERNET_KEY"]

for key in keys:
    val = os.environ.get(key)
    if val:
        print(f"{key}: CONFIGURED")
    else:
        print(f"{key}: MISSING")
