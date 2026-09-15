"""
Phase 5 — GitHub Integration Tests.
"""
import uuid
import os
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.github.encryption import encrypt_token, decrypt_token
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository



def _setup_user_and_org(client: TestClient, db_session, org_name: str = None) -> tuple[str, int, int]:
    """Register a user, return (token, org_id, user_id)."""
    from backend.app.auth.service import hash_password
    org = Organization(name=org_name or f"Org-{uuid.uuid4().hex[:6]}")
    db_session.add(org)
    db_session.flush()

    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=email, password_hash=hash_password("Testpass1!"))
    db_session.add(user)
    db_session.flush()

    membership = OrganizationMembership(user_id=user.id, organization_id=org.id, role=RoleEnum.ORG_ADMIN)
    db_session.add(membership)
    db_session.commit()

    login = client.post("/auth/login", json={"email": email, "password": "Testpass1!"})
    assert login.status_code == 200
    token = login.cookies.get("access_token")
    return token, org.id, user.id


class TestTokenEncryption:
    def test_roundtrip(self):
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        with patch("backend.app.github.encryption.settings") as mock_settings:
            mock_settings.FERNET_KEY = key
            plaintext = "ghp_super_secret_token"
            encrypted = encrypt_token(plaintext)
            assert encrypted != plaintext
            assert "ghp_" not in encrypted
            decrypted = decrypt_token(encrypted)
            assert decrypted == plaintext

    def test_encrypted_is_not_plaintext(self):
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        with patch("backend.app.github.encryption.settings") as mock_settings:
            mock_settings.FERNET_KEY = key
            token = "ghp_my_real_pat_12345"
            encrypted = encrypt_token(token)
            assert token not in encrypted

    def test_invalid_token_raises(self):
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        with patch("backend.app.github.encryption.settings") as mock_settings:
            mock_settings.FERNET_KEY = key
            with pytest.raises(ValueError):
                decrypt_token("definitely_not_valid_ciphertext")


class TestRepositoryConnect:
    def _create_project(self, client, token: str, org_id: int) -> int:
        r = client.post(
            f"/organizations/{org_id}/projects",
            json={"name": "TestProject"},
            cookies={"access_token": token},
        )
        assert r.status_code == 201, r.text
        return r.json()["id"]

    @patch("backend.app.github.service.GitHubClient")
    @patch("backend.app.github.encryption.settings")
    def test_connect_succeeds_and_token_not_returned(
        self, mock_settings, MockGitHubClient, client, db_session
    ):
        from cryptography.fernet import Fernet
        mock_settings.FERNET_KEY = Fernet.generate_key().decode()

        mock_client_instance = MagicMock()
        mock_client_instance.validate_repository_access.return_value = {
            "default_branch": "main",
            "id": 12345,
        }
        MockGitHubClient.return_value = mock_client_instance

        token, org_id, _ = _setup_user_and_org(client, db_session)
        self._create_project(client, token, org_id)

        response = client.post(
            f"/repositories/connect?organization_id={org_id}",
            json={
                "github_owner": "testowner",
                "github_name": "testrepo",
                "default_branch": "main",
                "pat": "ghp_fake_token_for_test",
            },
            cookies={"access_token": token},
        )

        assert response.status_code == 201, response.text
        data = response.json()
        assert "repository_id" in data
        assert "github_connection_id" in data
        response_text = str(data)
        assert "ghp_fake_token_for_test" not in response_text
        assert "ghp_" not in response_text

    @patch("backend.app.github.service.GitHubClient")
    def test_connect_requires_org_admin(self, MockGitHubClient, client, db_session):
        token_admin, org_id, _ = _setup_user_and_org(client, db_session)
        
        email_dev = f"dev_{uuid.uuid4().hex[:8]}@example.com"
        client.post(
            f"/organizations/{org_id}/members",
            json={"email": email_dev, "role": "developer"},
            cookies={"access_token": token_admin},
        )
        # We need to onboard dev manually using DB to skip onboarding flow for test speed
        from backend.app.auth.service import hash_password
        user = db_session.query(User).filter(User.email == email_dev).first()
        user.password_hash = hash_password("pass")
        user.invitation_token_hash = None
        db_session.commit()

        login_dev = client.post("/auth/login", json={"email": email_dev, "password": "pass"})
        token_dev = login_dev.cookies.get("access_token")

        response = client.post(
            f"/repositories/connect?organization_id={org_id}",
            json={
                "github_owner": "owner",
                "github_name": "repo",
                "pat": "ghp_fake",
            },
            cookies={"access_token": token_dev},
        )
        assert response.status_code == 403

    @patch("backend.app.github.service.GitHubClient")
    def test_connect_invalid_pat_returns_422(self, MockGitHubClient, client, db_session):
        from backend.app.github.client import GitHubAPIError
        mock_instance = MagicMock()
        mock_instance.validate_repository_access.side_effect = GitHubAPIError(401, "Bad credentials")
        MockGitHubClient.return_value = mock_instance

        token, org_id, _ = _setup_user_and_org(client, db_session)
        client.post(
            f"/organizations/{org_id}/projects",
            json={"name": "P"},
            cookies={"access_token": token},
        )

        response = client.post(
            f"/repositories/connect?organization_id={org_id}",
            json={"github_owner": "x", "github_name": "y", "pat": "ghp_bad"},
            cookies={"access_token": token},
        )
        assert response.status_code == 422


class TestPullRequestEndpoints:
    def test_list_prs_requires_auth(self, client):
        r = client.get("/repositories/999/pull-requests")
        assert r.status_code == 401

    def test_pr_isolation_cross_org(self, client, db_session):
        token_a, _, _ = _setup_user_and_org(client, db_session, "OrgA")
        token_b, org_b_id, _ = _setup_user_and_org(client, db_session, "OrgB")

        proj_b = client.post(
            f"/organizations/{org_b_id}/projects",
            json={"name": "ProjB"},
            cookies={"access_token": token_b},
        )
        repo_b = client.post(
            f"/projects/{proj_b.json()['id']}/repositories",
            json={"github_owner": "ob", "github_name": "rb", "default_branch": "main"},
            cookies={"access_token": token_b},
        )
        repo_b_id = repo_b.json()["id"]

        r = client.get(
            f"/repositories/{repo_b_id}/pull-requests",
            cookies={"access_token": token_a},
        )
        assert r.status_code == 404

    def test_get_pr_requires_org_membership(self, client):
        r = client.get("/pull-requests/1")
        assert r.status_code == 401
