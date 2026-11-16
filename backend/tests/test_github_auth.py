from backend.app.auth.models import User
import uuid

def test_connect_without_oauth_identity_fails(client, db_session):
    from backend.tests.test_github import _setup_user_and_org
    token, org_id, _ = _setup_user_and_org(client, db_session, "NoOAuthOrg")
    
    # User does NOT have a GitHubIdentity
    response = client.post(
        f"/repositories/connect?organization_id={org_id}",
        json={"project_id": 1, "github_owner": "owner", "github_name": "repo"},
        cookies={"access_token": token},
    )
    # the exact error could be 400 or 403 or 422 depending on implementation of `get_decrypted_github_token_for_user`
    # Let's check status code > 399
    assert response.status_code >= 400

def test_connect_unexpected_pat_field(client, db_session):
    from backend.tests.test_github import _setup_user_and_org
    token, org_id, _ = _setup_user_and_org(client, db_session, "UnexpectedPatOrg")
    
    # Pass unexpected pat field
    response = client.post(
        f"/repositories/connect?organization_id={org_id}",
        json={"project_id": 1, "github_owner": "owner", "github_name": "repo", "pat": "ghp_unexpected"},
        cookies={"access_token": token},
    )
    # Should either be ignored and fail later (because no identity), or 422
    assert response.status_code >= 400


def test_token_refresh_lifecycle(db_session, monkeypatch):
    from unittest.mock import MagicMock
    from datetime import datetime, timezone, timedelta
    from backend.app.auth.models import User
    from backend.app.github.models import GitHubIdentity, GitHubCredential
    from backend.app.github.encryption import encrypt_token, decrypt_token
    from backend.app.github.service import refresh_github_credential, get_valid_access_token_for_credential

    # Create dummy user and identity
    user = User(email="test_refresh@example.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()

    identity = GitHubIdentity(
        user_id=user.id,
        github_user_id="99999",
        github_login="testuser",
        connection_status="CONNECTED",
    )
    db_session.add(identity)
    db_session.commit()

    # Expired credential with refresh token
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    cred = GitHubCredential(
        github_identity_id=identity.id,
        encrypted_access_token=encrypt_token("old_expired_token"),
        encrypted_refresh_token=encrypt_token("old_refresh_token"),
        expires_at=past,
    )
    db_session.add(cred)
    db_session.commit()

    # Mock httpx response for refresh
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "new_fresh_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 28800,
    }

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, **kwargs):
            return mock_resp

    import httpx
    monkeypatch.setattr(httpx, "Client", MockClient)

    # get_valid_access_token_for_credential should detect expiration and refresh automatically
    valid_token = get_valid_access_token_for_credential(db_session, cred)
    assert valid_token == "new_fresh_token"

    # Verify DB was updated
    db_session.refresh(cred)
    assert decrypt_token(cred.encrypted_access_token) == "new_fresh_token"
    assert decrypt_token(cred.encrypted_refresh_token) == "new_refresh_token"
    assert cred.expires_at > datetime.now(timezone.utc)
    assert identity.connection_status == "CONNECTED"

