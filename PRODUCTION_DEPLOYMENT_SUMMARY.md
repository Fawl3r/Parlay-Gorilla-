# Gorilla Bot - Production Deployment Summary

## What Needs to Be Done for Render Production

### 1. Enable pgvector Extension ⚠️ CRITICAL

Render PostgreSQL does NOT have pgvector installed by default. You must enable it manually:

**Method 1: Via Render Dashboard (Easiest)**
1. Go to Render Dashboard → Your PostgreSQL service
2. Click "Connect" → "Connect via psql"
3. Run: `CREATE EXTENSION IF NOT EXISTS vector;`
4. Verify: `SELECT * FROM pg_extension WHERE extname = 'vector';`

**Method 2: Via Render Shell**
```bash
# In backend service shell
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Why this is critical:** Without pgvector, the migration will fail and vector search won't work.

### 2. Run Database Migration

The migration will run automatically on deploy (via `start.sh`), but you can also run manually:

```bash
# In Render backend service shell
cd backend
alembic upgrade head
```

This creates:
- `gorilla_bot_conversations` table
- `gorilla_bot_messages` table
- `gorilla_bot_kb_documents` table
- `gorilla_bot_kb_chunks` table (with vector column)

### 3. Set Environment Variables

Add these to your Render backend service:

**Required:**
```env
GORILLA_BOT_ENABLED=true
OPENAI_API_KEY=your_key_here
OPENAI_ENABLED=true
```

**Optional (defaults shown):**
```env
GORILLA_BOT_MODEL=gpt-4o-mini
GORILLA_BOT_EMBEDDING_MODEL=text-embedding-3-small
GORILLA_BOT_KB_PATH=docs/gorilla-bot/kb
GORILLA_BOT_MAX_CONTEXT_CHUNKS=6
GORILLA_BOT_MAX_RESPONSE_TOKENS=700
```

**Note:** The `render.yaml` has been updated to include these automatically.

### 4. Index Knowledge Base

**One-time setup** (after deployment):

```bash
# In Render backend service shell
cd backend
python scripts/gorilla_bot_index_kb.py
```

This will:
- Read markdown files from `docs/gorilla-bot/kb/`
- Chunk the content
- Generate embeddings using OpenAI
- Store in database

**Re-index when KB documents are updated:**
- Edit files in `docs/gorilla-bot/kb/`
- Commit and push
- Re-run indexing script

### 5. Verify Deployment

**Test backend:**
```bash
curl https://your-backend.onrender.com/health
curl -X POST https://your-backend.onrender.com/api/gorilla-bot/chat \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is Parlay Gorilla?"}'
```

**Test frontend:**
1. Open your frontend URL
2. Log in
3. Look for Gorilla Bot chat button (bottom-right)
4. Open and test a conversation

## Quick Start Commands

**After deploying to Render:**

```bash
# 1. Enable pgvector (in PostgreSQL service)
CREATE EXTENSION IF NOT EXISTS vector;

# 2. Verify migration (in backend service shell)
cd backend && alembic current

# 3. Index knowledge base (in backend service shell)
cd backend && python scripts/gorilla_bot_index_kb.py

# 4. Verify chunks created
# (In PostgreSQL service)
SELECT COUNT(*) FROM gorilla_bot_kb_chunks;
```

## Files Updated for Production

1. **`render.yaml`** - Added Gorilla Bot environment variables
2. **`backend/start.sh`** - Already includes migrations (no changes needed)
3. **`docs/deploy/GORILLA_BOT_RENDER_DEPLOYMENT.md`** - Complete deployment guide
4. **`docs/deploy/GORILLA_BOT_PRODUCTION_CHECKLIST.md`** - Quick checklist

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Migration fails: "extension vector does not exist" | Enable pgvector first (Step 1) |
| Migration fails: "permission denied" | Use Render Dashboard → PostgreSQL → psql (superuser access) |
| Chat returns "temporarily unavailable" | Index knowledge base (Step 4) |
| "No chunks found" | Run indexing script |
| OpenAI API errors | Check API key and credits |

## Cost Estimates

**OpenAI API costs** (1000 users, 10 chats/user/month):
- Embeddings (one-time indexing): ~$0.10
- Chat requests: ~$5-10/month

**Optimization:**
- Use `gpt-4o-mini` (already configured)
- Limit context chunks to 6 (default)
- Rate limiting: 60 requests/hour per user

## Documentation

- **Full Guide**: `docs/deploy/GORILLA_BOT_RENDER_DEPLOYMENT.md`
- **Checklist**: `docs/deploy/GORILLA_BOT_PRODUCTION_CHECKLIST.md`
- **Testing**: `backend/TESTING_GORILLA_BOT.md`

## Next Steps

1. ✅ Deploy code to Render
2. ✅ Enable pgvector extension
3. ✅ Set environment variables
4. ✅ Run migration (automatic or manual)
5. ✅ Index knowledge base
6. ✅ Test and verify
7. ✅ Monitor and optimize

---

**Important:** The pgvector extension MUST be enabled before the migration runs, otherwise the migration will fail.
