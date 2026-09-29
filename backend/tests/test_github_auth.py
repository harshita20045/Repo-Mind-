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
