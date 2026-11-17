import os
from typing import Any

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")


class APIClient:
    def __init__(self, token: str | None = None):
        self.base_url = API_BASE_URL
        self.token = token

    def check_health(self) -> dict[str, Any]:
        """Checks if the backend API server is healthy and reachable."""
        root_url = (
            self.base_url.rsplit("/api/v1", 1)[0]
            if "/api/v1" in self.base_url
            else self.base_url
        )
        endpoints_to_try = [
            f"{root_url}/health",
            f"{self.base_url}/health",
            f"{root_url}/",
        ]
        for url in endpoints_to_try:
            try:
                resp = requests.get(url, timeout=2.0)
                if resp.status_code == 200:
                    return {"healthy": True, "details": resp.json()}
            except Exception:
                continue
        return {"healthy": False, "details": None}

    def _headers(self) -> dict[str, str]:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, email: str, password: str) -> dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/auth/login", json={"email": email, "password": password}
        )
        resp.raise_for_status()
        return resp.json()

    def register(
        self, email: str, password: str, full_name: str, role: str = "creator"
    ) -> dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role,
                "organization_slug": "novatech",
            },
        )
        resp.raise_for_status()
        return resp.json()

    def get_me(self) -> dict[str, Any]:
        resp = requests.get(f"{self.base_url}/auth/me", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def list_users(self) -> list[dict[str, Any]]:
        resp = requests.get(f"{self.base_url}/auth/users", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def get_guidelines(self) -> dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/brand/guidelines", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def update_guidelines(self, data: dict[str, Any]) -> dict[str, Any]:
        resp = requests.put(
            f"{self.base_url}/brand/guidelines", json=data, headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def upload_guideline_document(
        self, file_bytes, filename: str, title: str | None = None
    ) -> dict[str, Any]:
        files = {"file": (filename, file_bytes)}
        data = {"document_title": title or filename}
        resp = requests.post(
            f"{self.base_url}/brand/guidelines/upload",
            files=files,
            data=data,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def list_documents(self) -> list[dict[str, Any]]:
        resp = requests.get(f"{self.base_url}/brand/documents", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def list_facts(self) -> list[dict[str, Any]]:
        resp = requests.get(f"{self.base_url}/brand/facts", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def create_fact(self, fact_data: dict[str, Any]) -> dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/brand/facts", json=fact_data, headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def delete_fact(self, fact_id: int) -> dict[str, Any]:
        resp = requests.delete(
            f"{self.base_url}/brand/facts/{fact_id}", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def submit_content(
        self,
        title: str,
        content_type: str = "text",
        original_text: str | None = None,
        file_bytes: bytes | None = None,
        filename: str | None = None,
    ) -> dict[str, Any]:
        data = {"title": title, "content_type": content_type}
        if original_text:
            data["original_text"] = original_text
        files = None
        if file_bytes and filename:
            files = {"file": (filename, file_bytes)}
        resp = requests.post(
            f"{self.base_url}/content/submit",
            data=data,
            files=files,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_submission(self, submission_id: int) -> dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/content/{submission_id}", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def list_submissions(
        self, status_filter: str | None = None
    ) -> list[dict[str, Any]]:
        params = {}
        if status_filter:
            params["status_filter"] = status_filter
        resp = requests.get(
            f"{self.base_url}/content/", params=params, headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def run_compliance_audit(self, submission_id: int) -> dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/compliance/audit/{submission_id}", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def update_finding_status(self, finding_id: int, new_status: str) -> dict[str, Any]:
        resp = requests.put(
            f"{self.base_url}/compliance/finding/{finding_id}/status",
            params={"new_status": new_status},
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def update_status(
        self, submission_id: int, new_status: str, comment: str | None = None
    ) -> dict[str, Any]:
        payload = {"new_status": new_status, "comment": comment}
        resp = requests.post(
            f"{self.base_url}/workflow/{submission_id}/status",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def add_comment(
        self, submission_id: int, comment: str, status_transition: str | None = None
    ) -> dict[str, Any]:
        payload = {"comment": comment, "status_transition": status_transition}
        resp = requests.post(
            f"{self.base_url}/workflow/{submission_id}/comment",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def save_revision(
        self,
        submission_id: int,
        content: str,
        version_label: str = "User Edit",
        changes_summary: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "content": content,
            "version_label": version_label,
            "changes_summary": changes_summary,
        }
        resp = requests.post(
            f"{self.base_url}/workflow/{submission_id}/revision",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_diff(
        self, submission_id: int, rev1: int | None = None, rev2: int | None = None
    ) -> dict[str, Any]:
        params = {}
        if rev1:
            params["rev1"] = rev1
        if rev2:
            params["rev2"] = rev2
        resp = requests.get(
            f"{self.base_url}/workflow/{submission_id}/diff",
            params=params,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_analytics(self) -> dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/analytics/dashboard", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()
