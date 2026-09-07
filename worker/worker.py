# Worker entrypoint – polling placeholder

from backend.app.core.config import settings
# Placeholder import for DB engine (to be defined later)
# from sqlalchemy import create_engine

def poll_jobs():
    print("Worker started – polling placeholder")
    # In a real implementation, this would poll the job table.
    # For M0 we just keep the process alive.
    import time
    while True:
        time.sleep(5)
        print("Polling… (no jobs implemented yet)")

if __name__ == "__main__":
    poll_jobs()
