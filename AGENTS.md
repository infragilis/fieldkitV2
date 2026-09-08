# Fieldkit — Agent Startup

Fieldkit is a Raspberry Pi field-service appliance for network-equipment work:
a local web UI for serial consoles, file handling, transfer services, a browser
shell, appliance settings, and field reference docs.

## Operating Rules (non-negotiable)

- The `service` and `fieldkit` default accounts documented in this repo are
  intentional, low-sensitivity defaults for easy setup and quick deploy. Users
  are expected to change them after first boot. Fieldkit's code carries no
  secrets that require heavy security.
- Stay inside the Fieldkit repo. Do not modify Legati, Tradify, Home Assistant,
  or any other project, repository, or infrastructure.
- Trust live code and current runtime behavior over older notes. Verify current
  state before acting.
- Check for an existing working solution before creating anything. Reuse proven
  scripts, procedures, libraries, and configs.
- Prefer the smallest reversible change. Do not overengineer. No temporary hacks
  or weird workarounds as permanent solutions.
- No blind trial-and-error. Diagnose from evidence, test the smallest change,
  and stop if it does not produce useful evidence.
- Do not fake, guess, or hide uncertainty. Ask focused questions when essential
  facts are unclear.
- Never expose credentials, tokens, or private keys. See `HANDOFF.md` for the
  security-sensitive rules (public email, default credentials, secret location).
- Genuine secrets — the server VM address, Cloudflare identifiers, deployment
  inventory, and non-default credentials — belong only in the private server
  repository and must never be committed to either repository. The private
  repository is an access-control boundary for operations, not for the
  `service`/`fieldkit` default accounts.
- Build, test, and run against the actual Fieldkit appliance, not the dev host.
  The dev host holds only the source checkout; deploy changed files to the
  appliance (see `docs/update-and-reload.md`) and never serve the app from the
  dev host.

## Where Things Live (canonical)

| Subject | Location |
|---|---|
| Infrastructure index | `docs/infrastructure.md` |
| Architecture | `docs/architecture.md` |
| Platform/hardware baseline | `docs/platform-baseline.md` |
| Install/deploy runbooks | `docs/{pi-setup,update-and-reload,golden-image-checklist}.md` |
| Per-domain facts | `bedrock/Memory/*.md` (start at `Memory/MEMORY.md`) |
| Decisions | `bedrock/Memory/decisions/decisions.md` |
| Current live state, access, priorities | `HANDOFF.md` (local-only) |
| History (diary) | `bedrock/History/` |
| Bedrock onboarding/maintenance | `docs/onboarding.md` |

## Load On Demand Only

Read a document only when the task matches it. Do not preload branch notes,
`History/`, `Evidence/`, or `Outputs/` at startup.

## Session Start

1. This file is already loaded.
2. Read `HANDOFF.md` if the task touches the live appliance or current work.
3. Read only the docs/branch notes the task actually needs.
4. If shell is available: `bedrock sync --project .`

## After Meaningful Work

Record newly verified, reusable facts in the correct canonical document (see
table). Follow the write-back procedure in `docs/onboarding.md`. Do not store
transient logs, guesses, or full session history as memory.
