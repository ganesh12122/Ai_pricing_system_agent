# Start Here (Non-Technical Guide)

## What this project does

This project is an AI Sales Engineer chatbot.

A user can ask questions like:
- "Which plan fits my business?"
- "What will it cost for 50 users?"
- "Which modules should I choose?"

The system responds with:
- Recommendations tailored to user needs
- Explanations of why each recommendation fits
- Pricing taken from the database (not guessed by AI)

## Why this is reliable

- The AI does not invent pricing numbers.
- Pricing is always fetched from the `pricing_api`, which reads real pricing rules from PostgreSQL.
- Product/module knowledge comes from indexed documentation (RAG), not only model memory.

## High-Level Flow

1. User sends a message to `POST /chat`.
2. The workflow decides if this is a pricing question or a general product question.
3. It retrieves relevant knowledge and pricing data.
4. It asks the LLM service to generate a human-friendly response.
5. It stores conversation history for continuity.
6. It returns one final response to the user.

## Main Components (Simple View)

- chat_api: Public door for incoming chat messages
- n8n: Workflow coordinator (traffic controller)
- gateway_router: Decides intent (pricing vs general)
- embedding_service: Converts text to vectors for search
- pricing_api: Returns exact pricing from database
- llm_service: Generates final response text
- PostgreSQL + pgvector: Stores data, vectors, history, and pricing rules

## Who uses what

- Business/operations: review this file + `FLOW_WALKTHROUGH.md`
- Integration team: call `POST /chat` only
- Backend team: service docs under `services/*/docs/README.md`

## Where to go next

- End-to-end behavior in plain English: [FLOW_WALKTHROUGH.md](FLOW_WALKTHROUGH.md)
- Technical architecture: [architecture.md](architecture.md)
- API specs: [api-contracts.md](api-contracts.md)
- Run/troubleshooting guide: [RUNBOOK.md](RUNBOOK.md)
