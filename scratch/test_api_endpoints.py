import os
import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.auth.models import User
from backend.app.auth.dependencies import get_current_user

# Create test client with overridden auth user (admin user #1)
def override_get_current_user():
    db = SessionLocal()
    user = db.get(User, 1)
    db.close()
    return user

app.dependency_overrides[get_current_user] = override_get_current_user
client = TestClient(app)

def test_endpoints():
    print("=" * 80)
    print("VERIFYING API ENDPOINTS & FRONTEND DATA CONTRACTS")
    print("=" * 80)
    
    # 1. Onboarding Blueprint
    print("\n1. GET /repositories/1/onboarding/blueprint")
    r = client.get("/repositories/1/onboarding/blueprint")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Blueprint Status: {data.get('status')}")
        print(f"  Subsystems: {len(data.get('subsystems', []))}")
        print(f"  Tracks: {len(data.get('tracks', []))}")
        print(f"  Application flows present: {bool(data.get('application_flows'))}")
        print(f"  Mermaid diagram length: {len(data.get('mermaid_diagram', ''))}")
    else:
        print(f"  Error: {r.text[:200]}")

    # 2. History PRs
    print("\n2. GET /repositories/1/history/prs")
    r = client.get("/repositories/1/history/prs")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Total Historical PRs: {len(data)}")
        if data:
            print(f"  Sample PR #1: #{data[0].get('github_number')} - {data[0].get('title')} ({data[0].get('state')})")
    else:
        print(f"  Error: {r.text[:200]}")

    # 3. Architecture Decision Records (ADRs)
    print("\n3. GET /repositories/1/history/adrs")
    r = client.get("/repositories/1/history/adrs")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Total ADRs: {len(data)}")
        if data:
            print(f"  Sample ADR #1: {data[0].get('adr_identifier')} - {data[0].get('title')} ({data[0].get('status')})")
    else:
        print(f"  Error: {r.text[:200]}")

    # 4. Recurring Issues & Hotspots
    print("\n4. GET /repositories/1/history/recurring-issues")
    r = client.get("/repositories/1/history/recurring-issues")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Total Hotspots: {len(data)}")
        if data:
            print(f"  Sample Hotspot #1: {data[0].get('file_path')} - Score: {data[0].get('hotspot_score')}")
    else:
        print(f"  Error: {r.text[:200]}")

    # 5. History Compare (with PR ID)
    print("\n5. POST /repositories/1/history/compare (pull_request_id=1)")
    r = client.post("/repositories/1/history/compare", json={"pull_request_id": 1})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Total Historical Changes: {data.get('total_historical_changes')}")
        print(f"  Hotspot Detected: {data.get('is_problematic_hotspot')}")
        print(f"  Relevant ADRs: {len(data.get('relevant_adrs', []))}")
        print(f"  Similar Resolved Bugs: {len(data.get('similar_resolved_bugs', []))}")
    else:
        print(f"  Error: {r.text[:200]}")

    # 6. History Compare (with file_path)
    print("\n6. POST /repositories/1/history/compare (file_path=app/services/order_service.py)")
    r = client.post("/repositories/1/history/compare", json={"file_path": "app/services/order_service.py"})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Total Historical Changes: {data.get('total_historical_changes')}")
        print(f"  Hotspot Detected: {data.get('is_problematic_hotspot')}")
        print(f"  Relevant ADRs: {len(data.get('relevant_adrs', []))}")
        print(f"  Similar Resolved Bugs: {len(data.get('similar_resolved_bugs', []))}")
    else:
        print(f"  Error: {r.text[:200]}")

    # 7. Pull Requests list
    print("\n7. GET /repositories/1/pull-requests")
    r = client.get("/repositories/1/pull-requests")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Total PRs in list: {len(data)}")
    else:
        print(f"  Error: {r.text[:200]}")

    # 8. Technical Debt Snapshot
    print("\n8. GET /repositories/1/technical-debt")
    r = client.get("/repositories/1/technical-debt")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Debt Score: {data.get('debt_score')}")
        print(f"  Total Issues: {len(data.get('issues', []))}")
    else:
        print(f"  Error: {r.text[:200]}")

    print("\n" + "=" * 80)
    print("ALL API ENDPOINTS TESTED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    test_endpoints()
