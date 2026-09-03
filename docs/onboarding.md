# Bedrock Memory — Onboarding & Maintenance

Fieldkit uses Project Bedrock for persistent project memory, kept local at
`./bedrock/` (gitignored). This file ships with the repo so a fresh checkout can
bootstrap the system; the running state lives in `./bedrock/STATUS.md`.

The canonical startup layer is `AGENTS.md`. Read that first, always.

## First-Time Onboarding

Check `./bedrock/STATUS.md`. If it is missing or shows `onboarding: pending`:

1. Inspect project structure: manifests, package files, CI/CD config, docs.
2. Inspect project-local tool config: `.cursor/`, `.claude/`, `.codex/` if present.
3. Review recent git history (last ~50 commits, key branches).
4. Import findings into `Evidence/raw/` using `bedrock import`.
5. Infer the project ontology from the repo's own functional domains
   (e.g. networking, serial, storage) — not generic categories.
6. Create one branch note per functional domain, each under ~150 lines.
7. Link related notes with relative markdown links.
8. Update `Memory/MEMORY.md` with links to all new branches.
9. Set `onboarding: complete` in `./bedrock/STATUS.md`.

## Branch Convention

Use the same-name branch-note pattern:

```
Memory/
  MEMORY.md                    # root -- always read first
  stack.md                     # flat note when no subtopics needed
  perception/
    perception.md              # entry note = same name as folder
    fusion.md                  # subtopic note
  decisions/
    decisions.md               # decision log
```

Rules:

- Each branch = one focused functional domain from the project.
- Use the project's own terminology, not generic templates.
- Each note stays under ~150 lines. If a topic is too big, split it.
- Link related notes with relative markdown links.
- Small topic with no subtopics: one flat note (`stack.md`).
- Bigger topic: folder + same-name entry note (`perception/perception.md`).
- Do not create deep trees automatically; grow only when justified.
- Do NOT lump unrelated subsystems into a single "architecture" note.

## Onboarding Rules

- Only write confirmed facts to `Memory/` — never speculate.
- Keep raw/extracted material in `Evidence/`, not `Memory/`.
- Keep generated views in `Outputs/` — never treat them as canonical.
- Do NOT redo onboarding if `STATUS.md` already shows `onboarding: complete`.

## Session Start

If the shell is available, run at session start:

```bash
bedrock sync --project .
```

## Memory Maintenance

After meaningful work, update `./bedrock/Memory/` directly:

1. Edit the relevant branch note:
   - Update `Current State` with confirmed facts (replace stale entries, no duplicates).
   - Add a `YYYY-MM-DD -- what changed` line to `Recent Changes`.
2. If any architectural/design/tooling decision was made, add it to
   `Memory/decisions/decisions.md` using the existing numbered format.
3. Update `Memory/MEMORY.md` if branch one-line summaries changed.
4. Run `bedrock sync --project .` to propagate and refresh indexes.

Write to memory when a feature/command/module completed, an architectural
decision changed, a gotcha/constraint was confirmed, or test/CI config changed.
Skip writeback for read-only sessions, speculative changes, or session-only
context. Do not store transient logs, guesses, or full session history.

## Knowledge Structure

- `Memory/` — curated, durable project knowledge (source of truth)
- `Evidence/` — imported/extracted material (not curated truth)
- `Outputs/` — generated helper views (never canonical)
- `History/` — lightweight diary (non-canonical)
- `archive/` — archived/stale material (recoverable, not loaded)
- `STATUS.md` — onboarding and maintenance state
- `.agent-project.yaml` — project configuration

## Reading Order

1. `Memory/MEMORY.md` — always read first.
2. Relevant branch entry notes.
3. Leaf notes only if the specific detail is needed.
4. Keep context lean — do not read branches unrelated to the current task.
