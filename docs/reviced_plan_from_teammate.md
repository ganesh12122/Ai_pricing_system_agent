
# Node-by-Node n8n Workflow Plan (Conversational AI Sales Engineer)

---

## 1. User Input & Trigger
- **Node:** Webhook or Chat Trigger
	- Receives user message (requirement or question) from web/chat interface.

## 2. Intent & Requirement Extraction
- **Node:** LLM Node (e.g., Ollama Chat Model)
	- Classifies input as product/pricing request or general/document question.
	- Extracts structured requirements (modules, user count, compliance, etc.).
	- *Optional:* Use a Python node for custom parsing or pre-processing if LLM output needs refinement.

## 3. Branching Logic
- **Node:** IF or Switch Node
	- Routes the flow based on intent:
		- Product/pricing → Recommendation Flow
		- General/document → RAG Flow

## 4A. Product Recommendation & Pricing Flow
- **Node:** Embeddings Node
	- Converts requirements into a vector for semantic search.
- **Node:** Postgres PGVector Store (or custom Python script for DB access)
	- Searches for matching products/modules.
- **Node:** HTTP Request or Database Node
	- Fetches pricing info (REST API, SQL, or Python script for complex logic).
- **Node:** LLM Node
	- Generates a natural, conversational response explaining why each module is recommended and provides a pricing breakdown.

## 4B. RAG (Knowledge Q&A) Flow
- **Node:** Embeddings Node
	- Converts user question into a vector.
- **Node:** Postgres PGVector Store (or custom Python script for DB access)
	- Retrieves relevant document chunks.
- **Node:** LLM Node
	- Generates a friendly, fact-based answer, citing sources.

## 5. Follow-up Questions
- **Node:** LLM Node
	- If info is missing, generates a follow-up question.
- **Node:** Chat Memory or Database Node
	- Stores conversation state for context.

## 6. Unified Response
- **Node:** Merge Node (or Function/Python Node)
	- Combines outputs from both flows if needed.
- **Node:** Webhook/Chat Node
	- Sends the unified, conversational response back to the user.

## 7. Session Memory
- **Node:** Chat Memory or Database Node
	- Stores and retrieves conversation context for a seamless, human-like experience.

---

## **Where Python Scripts May Be Used**
- Custom parsing or pre/post-processing of LLM output.
- Advanced database queries or business logic not supported by n8n’s built-in nodes.
- Data formatting, aggregation, or enrichment before sending to the user.

---

## **Summary Table**
| Step                        | n8n Node/Tech           | Purpose                                      |
|-----------------------------|-------------------------|----------------------------------------------|
| User Input                  | Webhook/Chat Trigger    | Receive user message                         |
| Intent Extraction           | LLM Node                | Classify & extract requirements              |
| Branching                   | IF/Switch Node          | Route to correct flow                        |
| Semantic Search             | Embeddings Node         | Vectorize requirements/questions             |
| Vector Search               | PGVector Store/Python   | Find matching products/docs                  |
| Pricing Calculation         | HTTP/DB/Python Node     | Fetch pricing info                           |
| Conversational Response     | LLM Node                | Generate natural, explanatory reply          |
| Follow-up Questions         | LLM Node + Memory       | Ask for missing info, retain context         |
| Unified Response            | Merge/Function/Webhook  | Send answer to user                          |
| Session Memory              | Chat Memory/DB Node     | Store conversation state                     |
