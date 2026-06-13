# `api/` is pre-implemented in the live template repo

At Step 9c, Claude copies the Lab's reference backend
(`m10-l10/api/` after reference implementation) into this directory
before pushing the template repo to GitHub.

In this staging snapshot, the `api/` body is intentionally a
placeholder — the Lab repo carries the canonical backend code. This
note exists only so the `api/` tree is non-empty at scaffold time and
the Infra-Integration lead's `docker-compose.yml` `build: ./api` line
has something to refer to.

If you (the team) need to extend the backend per the per-role rubric,
add files under `api/` as your Backend lead branch's work.
