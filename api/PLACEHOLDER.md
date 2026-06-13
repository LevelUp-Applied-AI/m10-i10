# `api/` is pre-implemented in the live template repo

> **Step 9c materialization gap — not yet closed.** The plan is that
> Claude copies the Lab's reference backend (`m10-l10/api/` after
> reference implementation) into this directory before pushing the
> template repo to GitHub. The Lab repo's reference implementation
> (complete FastAPI app with `/extract`, `/kg/query`, `/rag/answer`,
> `lifespan` wiring, settings, models, error mapping, seeding scripts)
> does not yet exist — the Lab ships as a starter with TODOs. Until the
> Lab reference is authored, this directory remains a placeholder and
> the live template repo cannot bring the stack up end-to-end. Tracked
> as a Round-3 carry-forward; the 9c-vi gate blocks publication of
> learner-facing template-repo URLs until this is closed.

In this staging snapshot, the `api/` body is intentionally a
placeholder — the Lab repo carries the canonical backend code. This
note exists only so the `api/` tree is non-empty at scaffold time and
the Infra-Integration lead's `docker-compose.yml` `build: ./api` line
has something to refer to.

If you (the team) need to extend the backend per the per-role rubric,
add files under `api/` as your Backend lead branch's work.
