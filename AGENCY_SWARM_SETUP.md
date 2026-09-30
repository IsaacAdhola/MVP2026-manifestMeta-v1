# Agency Swarm Framework Documentation

This project runs on **Agency Swarm v1.x** (OpenAI Agents SDK / Responses API).
Installed pin: `agency-swarm>=1.11,<2` (see `requirements.txt` in this folder and the repo root).

Do **not** follow v0.x patterns (`agency_chart`, `get_completion`, Assistants API thread IDs).
Prefer the `/examples` tree and the migration guide over older `/docs` snippets that may still mention v0.

## Installation & Setup

- **Installation**: https://agency-swarm.ai/welcome/installation
- **Migration Guide (v0 → v1)**: https://agency-swarm.ai/migration/guide

## Getting Started Guides

- **From Scratch guide**: https://agency-swarm.ai/welcome/getting-started/from-scratch
- **Cursor IDE workflow**: https://agency-swarm.ai/welcome/getting-started/cursor-ide
- **Starter Template**: https://agency-swarm.ai/welcome/getting-started/starter-template

## Core Framework Documentation (GitHub README “Learn More”)

- **Tools overview**: https://agency-swarm.ai/core-framework/tools/overview
- **Agents overview**: https://agency-swarm.ai/core-framework/agents/overview
- **Agencies overview**: https://agency-swarm.ai/core-framework/agencies/overview
- **Communication flows**: https://agency-swarm.ai/core-framework/agencies/communication-flows
- **Running an agency**: https://agency-swarm.ai/core-framework/agencies/running-agency
- **Agent Swarm CLI / TUI**: https://agency-swarm.ai/core-framework/agencies/agent-swarm-cli
- **Observability**: https://agency-swarm.ai/additional-features/observability

## This product’s wiring

| Piece | Path |
|-------|------|
| Agency entry | `agency.py` (`Agency(ceo, communication_flows=..., shared_instructions=...)`) |
| Shared instructions | `agency_manifesto.md` |
| CEO entry agent | `MetaMarkCEO/` |
| Client turn helper | `client_gateway.run_client_turn` → `get_response_sync` |
| Slack HTTP | `app.py` + `slack_app.py` |
| Gradio UI | `agency.demo_gradio` (default); set `MANIFEST_AI_UI=tui` or `copilot` for official UIs |
| Customer channels | Workspace-root `docs/CUSTOMER_CHANNELS.md` — Slack live; Gradio/TUI/Copilot/web optional now; Telegram optional later. Same `run_client_turn`. |

## Examples & Resources

- **Official examples**: https://github.com/VRSEN/agency-swarm/tree/main/examples
- **Agency Code example**: https://github.com/VRSEN/Agency-Code
- **Source Code**: https://github.com/VRSEN/agency-swarm
- **Official Documentation**: https://agency-swarm.ai
