# Repository workflow

## Branch policy

- Treat `dev` as the long-lived development and integration branch.
- Perform repository changes on `dev`. Do not commit directly to `main`.
- Keep the `dev` branch after every merge; never delete it as part of pull-request cleanup.
- Complete and verify one coherent change, then commit that change to `dev`.
- Push `dev` and open pull requests with `main` as the base branch and `dev` as the head branch.
- Merge reviewed pull requests into `main` with a merge commit unless the user explicitly requests another merge strategy.
- After a pull request is merged, synchronize `dev` with `origin/main` without rewriting published history, then continue development on `dev`.
- Do not force-push `dev` or `main`.

## Validation before a commit or pull request

- Run `./scripts/check-all.sh` after changing a skill, its references, scripts, templates, metadata, or tests.
- Inspect `git diff` and run `git diff --check` before committing.
- Keep unrelated changes out of the commit.
- Report any skipped, blocked, or failing validation instead of presenting the change as fully verified.

## Pull-request scope

- Prefer one coherent skill behavior change per pull request.
- Update the relevant tests and documentation when behavior or invocation changes.
- Treat external publication, production changes, payments, reciprocal-link changes, and credential use as separate actions requiring explicit user authorization.
