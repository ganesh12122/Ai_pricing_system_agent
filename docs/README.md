# Documentation Hub

This folder contains both business-level and technical-level documentation for the RAG Sales Chatbot project.

## Recommended Reading Order

1. Start here (non-technical):
- [START_HERE.md](START_HERE.md)

2. Understand the full flow (plain English):
- [FLOW_WALKTHROUGH.md](FLOW_WALKTHROUGH.md)

3. Understand architecture and APIs (technical):
- [architecture.md](architecture.md)
- [api-contracts.md](api-contracts.md)
- [system-prompt.md](system-prompt.md)

4. Operate and troubleshoot:
- [RUNBOOK.md](RUNBOOK.md)

5. Background project references:
- [project_plan_shared_by_team.MD](project_plan_shared_by_team.MD)
- [reviced_plan_from_teammate.md](reviced_plan_from_teammate.md)

## Service-Level Documentation

Each microservice has its own docs file:
- [../services/chat_api/docs/README.md](../services/chat_api/docs/README.md)
- [../services/gateway_router/docs/README.md](../services/gateway_router/docs/README.md)
- [../services/embedding_service/docs/README.md](../services/embedding_service/docs/README.md)
- [../services/llm_service/docs/README.md](../services/llm_service/docs/README.md)
- [../services/pricing_api/docs/README.md](../services/pricing_api/docs/README.md)

## Audience Guide

- Non-technical stakeholders: Start with `START_HERE.md` and `FLOW_WALKTHROUGH.md`
- Integration/frontend developers: Read `api-contracts.md` and `services/chat_api/docs/README.md`
- Backend engineers: Read all service docs + `architecture.md`
- Operations/devops: Read `RUNBOOK.md`
