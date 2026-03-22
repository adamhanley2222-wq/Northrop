# MD Strategic Review AI

Current status: **Phase 1–4 foundation** with ingestion, enrichment, canonical mapping, and hybrid query retrieval.

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Dev login

- `admin@example.com`
- `admin1234`

## Pinecone + embedding configuration

Set these in `backend/.env`:
- `OPENAI_API_KEY`
- `OPENAI_EMBEDDING_MODEL` (default `text-embedding-3-large`)
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_NAMESPACE`
- `EMBEDDING_DIMENSION`
- `ENABLE_SEMANTIC_RETRIEVAL=true`

If OpenAI/Pinecone keys are missing, deterministic fallback embedding logic is used for local development.

## Indexing and re-index workflow

- Publish a document: `POST /api/documents/{id}/publish`
  - marks chunks as published
  - indexes published chunks in Pinecone
- Reparse a document: `POST /api/documents/{id}/reparse`
  - replaces stale sections/chunks
  - removes stale vectors for that document
- Manual reindex: `POST /api/documents/{id}/reindex`
- Manual enrichment: `POST /api/documents/{id}/enrich`
- Manual canonical mapping: `POST /api/documents/{id}/map-canonical`

## Phase 4 query behavior

`POST /api/query` now uses hybrid retrieval:
1. intent classification
2. refined entity/filter resolution (including quarter/year extraction)
3. metadata + text retrieval from DB
4. semantic retrieval from Pinecone (if configured)
5. score merge/ranking and grounded evidence selection
6. structured answer synthesis with explicit separation of:
   - source-backed statements
   - inferred observations
   - weak evidence and omissions

Comparison questions (e.g. `Q1 vs Q2`) explicitly retrieve quarter-specific evidence and include comparison debug context.

## Debug visibility

Query response contains `debug` fields including:
- intent
- matched filters
- retrieval stats (`candidate_count`, `semantic_match_count`, selected chunk IDs)
- comparison period retrieval debug where applicable

## Current limits

- Enrichment and mapping are still heuristic-first; improved precision depends on richer reference data and stronger prompts/models.
- Hybrid retrieval is pragmatic and grounded, but not yet a full ranking stack with learned relevance tuning.
- Phase 5 is expected to expand strategic reasoning depth and cross-period intelligence quality.
