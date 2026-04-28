# Documentation Hub

This is the navigation index for all project documentation.

## Who are you?

**New to the project / non-technical?**
→ Start with [START_HERE.md](START_HERE.md), then [FLOW_WALKTHROUGH.md](FLOW_WALKTHROUGH.md)

**Developer setting up the project?**
→ Start with [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)

**Developer working on a specific service?**
→ Go to `services/<service_name>/docs/README.md`

**Integration team / frontend calling the API?**
→ Read [api-contracts.md](api-contracts.md) — chat_api section only

**Setting up or debugging n8n workflows?**
→ Read [N8N_WORKFLOWS.md](N8N_WORKFLOWS.md)

**Understanding or modifying the database?**
→ Read [DATABASE.md](DATABASE.md)

**Planning enhancements or the next phase?**
→ Read [../ROADMAP.md](../ROADMAP.md)

**Troubleshooting a running system?**
→ Read [RUNBOOK.md](RUNBOOK.md)

---

## Full Document Map

### Root Level
| File | Purpose |
|------|---------|
| [../README.md](../README.md) | Project overview and quick start |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | How to contribute |
| [../CHANGELOG.md](../CHANGELOG.md) | What has been built and changed |
| [../ROADMAP.md](../ROADMAP.md) | Enhancement and scale plan |

### docs/ (this folder)
| File | Audience | Purpose |
|------|----------|---------|
| START_HERE.md | Everyone | Plain-English intro |
| FLOW_WALKTHROUGH.md | Everyone | Request lifecycle |
| DEVELOPMENT_GUIDE.md | Developers | Full setup guide |
| N8N_WORKFLOWS.md | Developers | n8n import + node reference |
| DATABASE.md | Developers | Schema + useful queries |
| architecture.md | Developers | Architecture diagrams |
| api-contracts.md | Integration team | API specs per service |
| system-prompt.md | Developers | AI Sales Engineer persona |
| RUNBOOK.md | Operations | Run + troubleshoot |

### Service Docs
| Service | Doc | Port |
|---------|-----|------|
| chat_api | [services/chat_api/docs/README.md](../services/chat_api/docs/README.md) | 8000 |
| gateway_router | [services/gateway_router/docs/README.md](../services/gateway_router/docs/README.md) | 8001 |
| embedding_service | [services/embedding_service/docs/README.md](../services/embedding_service/docs/README.md) | 8002 |
| llm_service | [services/llm_service/docs/README.md](../services/llm_service/docs/README.md) | 8003 |
| pricing_api | [services/pricing_api/docs/README.md](../services/pricing_api/docs/README.md) | 8004 |

### Background Reference
| File | Purpose |
|------|---------|
| project_plan_shared_by_team.MD | Original management requirements |
| reviced_plan_from_teammate.md | Teammate's initial n8n workflow plan |

