"""Locust load and stress scenario for mailtmapi API."""

from __future__ import annotations

from locust import HttpUser, between, task

ROOT_KEY = "test-secret-load-test-key-32bytes!"


class MailTMUser(HttpUser):
    """Simulates realistic mixed workload against mailtmapi server."""

    wait_time = between(0.01, 0.05)

    def on_start(self):
        self.headers = {"X-API-Key": ROOT_KEY}

    @task(5)
    def probe_health(self):
        """High frequency health & status checks (cached/in-memory)."""
        self.client.get("/health", name="[GET] /health")

    @task(3)
    def probe_domain_cache(self):
        """Read domain cache overview."""
        self.client.get(
            "/v1/admin/domain-cache",
            headers=self.headers,
            name="[GET] /v1/admin/domain-cache",
        )

    @task(3)
    def list_mailboxes(self):
        """Query active mailboxes from SQLite database."""
        self.client.get(
            "/v1/mailboxes",
            headers=self.headers,
            name="[GET] /v1/mailboxes",
        )

    @task(2)
    def verify_auth_principal(self):
        """Verify token authentication and scope resolution under concurrency."""
        self.client.get(
            "/v1/admin/keys/me",
            headers=self.headers,
            name="[GET] /v1/admin/keys/me",
        )

    @task(1)
    def query_admin_keys(self):
        """Query issued keys list."""
        self.client.get(
            "/v1/admin/keys",
            headers=self.headers,
            name="[GET] /v1/admin/keys",
        )

    @task(1)
    def rejected_unauthorized_probe(self):
        """Probe auth rejection path (expect 401, verify fast denial)."""
        with self.client.get(
            "/v1/admin/keys",
            headers={"X-API-Key": "invalid-secret-key"},
            name="[GET] /v1/admin/keys (Auth Denial)",
            catch_response=True,
        ) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Expected 401 but got {response.status_code}")
