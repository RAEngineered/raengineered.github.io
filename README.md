# raengineered.github.io

Portfolio site. Static, no dependencies, built by `build.py`.

## How it works

```
content.json ──┐
               ├──> build.py ──> index.html          (deployed to Pages)
board.json ────┘                 PROFILE_README.md   (copied to the profile repo)
  (optional)
```

`content.json` is the hand-maintained source of truth and is always present.
`board.json` is optional; when the org Project board sync lands it will be written
at build time and merged by project `id`, with board fields winning.

## The publication gate

A project renders **only** when `"publish": true`. Everything else stays in the
file, unrendered. Private repos are described but never linked — `"repo": null`
plus `"visibility": "private"` produces a card with no link.

Nothing reaches the public site without that flag being flipped by hand.

## Local build

```bash
python build.py && start index.html
```

## Deploy

Push to `main`, or run the workflow manually. It also rebuilds nightly so that
board-sourced changes appear without a push.

## Not yet wired

Board sync (`sync_board.py`) is Phase 2 — see `../PLAN.md`. When it lands the
workflow gains a step before `Build site`, and a read-only fine-grained PAT is
added as a repository secret. The trigger restrictions at the top of
`deploy.yml` exist for that reason and must not be relaxed.
