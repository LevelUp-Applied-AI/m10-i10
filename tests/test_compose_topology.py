"""Compose topology + service-config structural tests.

Every test maps to a "Catches buggy variant" row in integration-task-spec.md
Test Plan.
"""
from pathlib import Path

import pytest

from tests.conftest import normalize_env

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_compose_declares_four_services(compose_config):
    """Catches buggy variant: learner omits a service."""
    services = compose_config.get("services") or {}
    for s in ("api", "web", "neo4j", "weaviate"):
        assert s in services, f"missing service {s!r}"


def test_neo4j_has_memory_caps(compose_config):
    """Catches buggy variant: OOM under load on 16 GB laptop."""
    env = normalize_env(compose_config["services"]["neo4j"].get("environment"))
    assert env.get("NEO4J_dbms_memory_heap_max__size") == "1G"
    assert env.get("NEO4J_dbms_memory_pagecache_size") == "512M"


def test_neo4j_has_named_volume(compose_config):
    """Catches buggy variant: anonymous volume → silent data loss on down -v."""
    svc = compose_config["services"]["neo4j"]
    volumes = svc.get("volumes") or []
    assert any("neo4j_data" in v and "/data" in v for v in volumes), volumes
    top_volumes = compose_config.get("volumes") or {}
    assert "neo4j_data" in top_volumes


def test_neo4j_has_healthcheck(compose_config):
    """Catches buggy variant: omitted healthcheck silently degrades
    `condition: service_healthy`."""
    hc = compose_config["services"]["neo4j"].get("healthcheck") or {}
    test_block = " ".join(hc.get("test", [])) if isinstance(hc.get("test"), list) else str(hc.get("test", ""))
    assert "cypher-shell" in test_block or "RETURN 1" in test_block


def test_weaviate_has_named_volume(compose_config):
    """Catches buggy variant: anonymous volume."""
    svc = compose_config["services"]["weaviate"]
    volumes = svc.get("volumes") or []
    assert any("weaviate_data" in v and "/var/lib/weaviate" in v for v in volumes)
    assert "weaviate_data" in (compose_config.get("volumes") or {})


def test_weaviate_has_healthcheck(compose_config):
    """Catches buggy variant: omitted."""
    hc = compose_config["services"]["weaviate"].get("healthcheck") or {}
    test_block = " ".join(hc.get("test", [])) if isinstance(hc.get("test"), list) else str(hc.get("test", ""))
    assert "v1/.well-known/ready" in test_block


def test_weaviate_has_vectorizer_module_none(compose_config):
    """Catches buggy variant: default vectorizer conflict — silent
    insert failures."""
    env = normalize_env(compose_config["services"]["weaviate"].get("environment"))
    assert env.get("DEFAULT_VECTORIZER_MODULE") == "none"


def test_api_depends_on_neo4j_and_weaviate_healthy(compose_config):
    """Catches buggy variant: bare depends_on list → race condition."""
    deps = compose_config["services"]["api"].get("depends_on")
    assert isinstance(deps, dict), "Use long-form depends_on with conditions"
    for backend in ("neo4j", "weaviate"):
        assert backend in deps
        assert deps[backend].get("condition") == "service_healthy"


def test_api_uri_uses_compose_dns(compose_config):
    """Catches buggy variant: learner copies localhost from Lab env into
    the api container."""
    env = normalize_env(compose_config["services"]["api"].get("environment"))
    assert env.get("NEO4J_URI") == "bolt://neo4j:7687"
    assert env.get("WEAVIATE_URL") == "http://weaviate:8080"


def test_web_depends_on_api_healthy(compose_config):
    """Catches buggy variant: bare or missing."""
    deps = compose_config["services"]["web"].get("depends_on")
    assert isinstance(deps, dict)
    assert deps.get("api", {}).get("condition") == "service_healthy"


def test_web_uses_localhost_api_url(compose_config):
    """Catches buggy variant: learner uses http://api:8000 — browser
    cannot resolve service-name DNS — OR learner sets the URL as a
    runtime environment variable instead of a Next.js build arg.

    Per the guide's Web service section: NEXT_PUBLIC_API_URL is **baked at
    build time** by Next.js into the client-side bundle, so it must be
    declared under `services.web.build.args` (not `environment`).
    """
    web_svc = compose_config["services"]["web"]
    build = web_svc.get("build")
    args = {}
    if isinstance(build, dict):
        args = build.get("args") or {}
        # Compose accepts args as a list of "KEY=value" entries too.
        if isinstance(args, list):
            args = dict(s.split("=", 1) for s in args if "=" in s)
    url = args.get("NEXT_PUBLIC_API_URL", "")
    assert url, (
        "NEXT_PUBLIC_API_URL must be declared as a build arg under "
        "`services.web.build.args` — Next.js bakes NEXT_PUBLIC_* values "
        "into the client bundle at build time, so a runtime "
        "`environment:` entry never reaches the browser."
    )
    assert "localhost" in url
    assert "//api:" not in url


def test_api_has_healthcheck(compose_config):
    """Catches buggy variant: omitted — web's depends_on degrades to
    container-start only."""
    hc = compose_config["services"]["api"].get("healthcheck") or {}
    assert hc.get("test")
