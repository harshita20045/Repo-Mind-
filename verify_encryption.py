import sys
import os

sys.path.append(os.path.abspath('.'))

# Import all models to register with Base
from backend.app.auth.models import *
from backend.app.organizations.models import *
from backend.app.github.models import *

from backend.app.db import SessionLocal
from backend.app.github.encryption import decrypt_token

def verify():
    db = SessionLocal()
    cred = db.query(GitHubCredential).first()
    
    if not cred:
        print("No credential found.")
        return
        
    enc = cred.encrypted_access_token
    print(f"Encrypted token starts with: {enc[:7]}")
    
    try:
        dec = decrypt_token(enc)
        print(f"Decrypted successfully. Starts with: {dec[:4]}")
        
        # Now verify repository discovery via API request simulation
    except Exception as e:
        print(f"Decryption failed: {e}")

if __name__ == "__main__":
    verify()
