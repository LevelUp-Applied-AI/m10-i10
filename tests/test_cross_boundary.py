"""Cross-boundary tests — Backend ↔ Frontend, Infra ↔ Backend.

Each test checks one of the role boundaries called out in
integration-task-spec.md (the per-role contribution surfaces).
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    p = REPO_ROOT / rel
    return p.read_text() if p.exists() else ""


# --- Backend ↔ Frontend ---------------------------------------------

def test_openapi_contract_matches_ts():
    """Catches buggy variant: Backend lead renames a Pydantic field;
    Frontend lead's lib/types.ts is stale → page renders nothing.

    Structural check: every Pydantic field name appearing in
    `api/models.py` for the three response shapes also appears in
    `web/lib/types.ts`. Catches camelCase drift and rename drift.
    """
    py = _read("api/models.py")
    ts = _read("web/lib/types.ts")
    if not py or not ts:
        # If the live integration repo has not yet bundled the lab's
        # api/web, the test cannot run — skip rather than fail.
        import pytest

        pytest.skip("api/models.py or web/lib/types.ts not bundled yet")
    required = ["chunk_id", "score", "answer", "citations", "confidence",
                "cypher", "rows", "count", "text", "label", "start", "end",
                "entities"]
    for field in required:
        assert field in ts, f"web/lib/types.ts missing field {field!r}"
        assert field in py, f"api/models.py missing field {field!r}"


# --- Infra ↔ Backend / Frontend -------------------------------------

def test_compose_healthz_reachable_from_web(compose_config):
    """Catches buggy variant: Infra lead misnames the `api` service or
    misconfigures the network → web container cannot resolve api DNS.

    Structural check: api service is on the default Compose network
    (no explicit network exclusion) and exposes port 8000 so the web
    container's `http://api:8000/healthz` URL resolves.
    """
    api = compose_config["services"]["api"]
    # ports field reveals the listener; absence of `network_mode: host`
    # ensures default-network DNS works.
    assert api.get("network_mode") != "host"
    # Either ports OR expose declares the listener — both are fine.
    ports = api.get("ports") or []
    expose = api.get("expose") or []
    has_8000 = any("8000" in str(p) for p in ports) or any("8000" in str(p) for p in expose)
    assert has_8000


def test_seed_weaviate_idempotent():
    """Catches buggy variant: Infra lead's seed script runs on every
    `up` and inserts on every run, polluting the index.

    Structural check: the Python seeder must contain an existence
    check (skip-if-exists) or a class-creation guard. We grep the
    actual seeder content; the lab's reference seed_weaviate.py has
    `schema.contains` and an `existing_ids` skip block.
    """
    p = REPO_ROOT / "api" / "seed_weaviate.py"
    if not p.exists():
        import pytest

        pytest.skip("seed_weaviate.py not bundled yet (lab carry-forward)")
    text = p.read_text()
    assert "schema.contains" in text or "existing_ids" in text or "exists_in_class" in text
