import inspect

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import approvals as approvals_routes
from app.api.v1 import runs as runs_routes
from app.api.v1 import workflows as workflow_routes
from app.agents.schemas import ValidatorOutput
from app.main import create_app
from app.services.store import STORE


@pytest.fixture(autouse=True)
def reset_store() -> None:
    STORE.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def generate(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/workflows/generate",
        json={
            "prompt": "Analyze this GitHub repository and generate issue drafts.",
            "repo_url": "https://github.com/example/repo",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_generate_workflow_success(client: TestClient) -> None:
    body = generate(client)
    assert body["workflow_id"]
    assert body["validation"]["valid"] is True


def test_generate_workflow_invalid_repo_url(client: TestClient) -> None:
    response = client.post(
        "/api/v1/workflows/generate", json={"prompt": "Audit", "repo_url": "not-a-url"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REPO_URL"


def test_generate_workflow_validation_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class BadValidator:
        async def run(self, payload: dict) -> ValidatorOutput:
            return ValidatorOutput(
                valid=False, issues=["bad graph"], corrected_graph=None
            )

    monkeypatch.setattr(
        "app.services.workflow_generation_service.ValidatorAgent",
        lambda: BadValidator(),
    )
    response = client.post(
        "/api/v1/workflows/generate",
        json={"prompt": "Audit", "repo_url": "https://github.com/example/repo"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "WORKFLOW_VALIDATION_FAILED"


def test_get_workflow_success(client: TestClient) -> None:
    workflow_id = generate(client)["workflow_id"]
    response = client.get(f"/api/v1/workflows/{workflow_id}")
    assert response.status_code == 200
    assert response.json()["workflow_id"] == workflow_id


def test_get_missing_workflow_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/workflows/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WORKFLOW_NOT_FOUND"


def test_run_workflow_starts_and_creates_run(client: TestClient) -> None:
    workflow_id = generate(client)["workflow_id"]
    response = client.post("/api/v1/workflows/run", json={"workflow_id": workflow_id})
    assert response.status_code == 200
    assert response.json()["run_id"] in STORE.runs


def test_get_run_returns_node_statuses(client: TestClient) -> None:
    workflow_id = generate(client)["workflow_id"]
    run_id = client.post(
        "/api/v1/workflows/run", json={"workflow_id": workflow_id}
    ).json()["run_id"]
    response = client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["nodes"]


def test_run_pauses_at_approval(client: TestClient) -> None:
    workflow_id = generate(client)["workflow_id"]
    run_id = client.post(
        "/api/v1/workflows/run", json={"workflow_id": workflow_id}
    ).json()["run_id"]
    body = client.get(f"/api/v1/runs/{run_id}").json()
    assert body["status"] == "waiting_for_approval"
    assert body["pending_approval"]["approval_id"]


def test_approve_resumes_run(client: TestClient) -> None:
    workflow_id = generate(client)["workflow_id"]
    run_id = client.post(
        "/api/v1/workflows/run", json={"workflow_id": workflow_id}
    ).json()["run_id"]
    approval_id = client.get(f"/api/v1/runs/{run_id}").json()["pending_approval"][
        "approval_id"
    ]
    response = client.post(f"/api/v1/approvals/{approval_id}/approve", json={})
    assert response.status_code == 200
    assert response.json()["run"]["status"] == "completed"


def test_reject_skips_issue_creator(client: TestClient) -> None:
    workflow_id = generate(client)["workflow_id"]
    run_id = client.post(
        "/api/v1/workflows/run", json={"workflow_id": workflow_id}
    ).json()["run_id"]
    approval_id = client.get(f"/api/v1/runs/{run_id}").json()["pending_approval"][
        "approval_id"
    ]
    body = client.post(f"/api/v1/approvals/{approval_id}/reject", json={}).json()["run"]
    issue_node = next(
        node for node in body["nodes"] if node["node_id"] == "github_issue_creator"
    )
    assert issue_node["status"] == "skipped"
    assert body["artifacts"]


def test_approve_double_call_controlled(client: TestClient) -> None:
    workflow_id = generate(client)["workflow_id"]
    run_id = client.post(
        "/api/v1/workflows/run", json={"workflow_id": workflow_id}
    ).json()["run_id"]
    approval_id = client.get(f"/api/v1/runs/{run_id}").json()["pending_approval"][
        "approval_id"
    ]
    assert (
        client.post(f"/api/v1/approvals/{approval_id}/approve", json={}).status_code
        == 200
    )
    response = client.post(f"/api/v1/approvals/{approval_id}/approve", json={})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "APPROVAL_ALREADY_RESOLVED"


def test_artifacts_appear_in_run_response(client: TestClient) -> None:
    workflow_id = generate(client)["workflow_id"]
    run_id = client.post(
        "/api/v1/workflows/run", json={"workflow_id": workflow_id}
    ).json()["run_id"]
    approval_id = client.get(f"/api/v1/runs/{run_id}").json()["pending_approval"][
        "approval_id"
    ]
    client.post(f"/api/v1/approvals/{approval_id}/approve", json={})
    body = client.get(f"/api/v1/runs/{run_id}").json()
    assert {artifact["filename"] for artifact in body["artifacts"]} >= {
        "repo_audit_report.md",
        "github_issue_drafts.md",
    }


def test_route_handlers_are_thin() -> None:
    sources = [
        inspect.getsource(handler)
        for handler in [
            workflow_routes.generate_workflow,
            workflow_routes.get_workflow,
            runs_routes.run_workflow,
            runs_routes.get_run,
            approvals_routes.approve,
            approvals_routes.reject,
        ]
    ]
    assert all("Service()" in source for source in sources)
    assert all("STORE" not in source for source in sources)


def test_api_errors_are_structured(client: TestClient) -> None:
    response = client.get("/api/v1/workflows/missing")
    assert set(response.json()) == {"error"}
    assert {"code", "message", "details"} <= set(response.json()["error"])


def test_health_endpoint_still_passes(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_backend_e2e_github_repo_audit_approval_completion(client: TestClient) -> None:
    workflow_id = generate(client)["workflow_id"]
    run_id = client.post(
        "/api/v1/workflows/run", json={"workflow_id": workflow_id}
    ).json()["run_id"]
    paused = client.get(f"/api/v1/runs/{run_id}").json()
    assert paused["status"] == "waiting_for_approval"
    approval_id = paused["pending_approval"]["approval_id"]
    approved = client.post(f"/api/v1/approvals/{approval_id}/approve", json={}).json()[
        "run"
    ]
    assert approved["status"] == "completed"
    assert approved["artifacts"]
    issue_node = next(
        node for node in approved["nodes"] if node["node_id"] == "github_issue_creator"
    )
    assert issue_node["output"]["mode"] == "mock"
