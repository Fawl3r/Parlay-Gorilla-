# Gorilla Bot - Render Production Deployment Guide

This guide covers deploying the Gorilla Bot feature to Render production.

## Prerequisites

- Render PostgreSQL database (created via `render.yaml` or manually)
- Render backend service configured
- OpenAI API key
- All standard Render deployment steps completed

## Step 1: Enable pgvector Extension on Render PostgreSQL

**⚠️ CRITICAL**: Render PostgreSQL does NOT have pgvector installed by default. You need to enable it manually.

### Option A: Using Render Dashboard (Recommended)

1. **Go to Render Dashboard** → Your PostgreSQL service
2. **Click "Connect"** → **"Connect via psql"** (or use any PostgreSQL client)
3. **Run this SQL command:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. **Verify it's enabled:**
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
   Should return a row with `extname = 'vector'`

### Option B: Using Render Shell

1. **Go to Render Dashboard** → Your backend service
2. **Click "Shell"** tab
3. **Connect to database and enable extension:**
   ```bash
   # Get connection string from Render dashboard
   psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

### Option C: Add to Migration (Automatic)

The migration `030_add_gorilla_bot_kb.py` already includes:
```python
if _is_postgres():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
```

However, **Render PostgreSQL requires superuser privileges** to create extensions, which may not be available. If the migration fails with "permission denied", you must enable it manually using Option A or B above.

## Step 2: Run Database Migration

After enabling pgvector, run the migration:

### Using Render Shell

1. **Go to Render Dashboard** → Your backend service
2. **Click "Shell"** tab
3. **Run migration:**
   ```bash
   cd backend
   alembic upgrade head
   ```

### Automatic on Deploy

The `render.yaml` already includes migrations in the start command via `start.sh`. Verify your `backend/start.sh` includes:

```bash
#!/bin/bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Step 3: Configure Environment Variables

Add these to your Render backend service environment variables:

### Required for Gorilla Bot

```env
# Enable Gorilla Bot
GORILLA_BOT_ENABLED=true

# OpenAI Configuration (required for embeddings and chat)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ENABLED=true

# Gorilla Bot Model Settings (optional, defaults shown)
GORILLA_BOT_MODEL=gpt-4o-mini
GORILLA_BOT_EMBEDDING_MODEL=text-embedding-3-small
GORILLA_BOT_EMBEDDING_BATCH_SIZE=48
GORILLA_BOT_EMBEDDING_TIMEOUT_SECONDS=30
GORILLA_BOT_CHAT_TIMEOUT_SECONDS=30
GORILLA_BOT_KB_PATH=docs/gorilla-bot/kb
GORILLA_BOT_MAX_CONTEXT_CHUNKS=6
GORILLA_BOT_MAX_RESPONSE_TOKENS=700
```

### Add to render.yaml (Optional)

You can also add these to your `render.yaml` for automatic configuration:

```yaml
services:
  - type: web
    name: parlay-gorilla-backend
    envVars:
      # ... existing vars ...
      - key: GORILLA_BOT_ENABLED
        value: "true"
      - key: GORILLA_BOT_MODEL
        value: "gpt-4o-mini"
      - key: GORILLA_BOT_EMBEDDING_MODEL
        value: "text-embedding-3-small"
      - key: GORILLA_BOT_KB_PATH
        value: "docs/gorilla-bot/kb"
```

## Step 4: Index Knowledge Base

The knowledge base must be indexed before users can chat with the bot.

### Using Render Shell (One-time Setup)

1. **Go to Render Dashboard** → Your backend service
2. **Click "Shell"** tab
3. **Run indexing script:**
   ```bash
   cd backend
   python scripts/gorilla_bot_index_kb.py
   ```

This will:
- Read all markdown files from `docs/gorilla-bot/kb/`
- Chunk the content into smaller pieces
- Generate embeddings using OpenAI
- Store in the database

**Expected output:**
```
Indexing knowledge base...
Found 5 documents
Processing overview.md...
Processing parlay-generator.md...
...
Indexed 5 documents with 42 chunks
```

### Re-indexing After Updates

If you update KB documents, re-run the indexing script:
```bash
python scripts/gorilla_bot_index_kb.py
```

The script is idempotent - it will update existing documents and add new ones.

## Step 5: Verify Deployment

### Test Backend API

```bash
# Health check
curl https://your-backend.onrender.com/health

# Test Gorilla Bot endpoint (requires auth token)
curl -X POST https://your-backend.onrender.com/api/gorilla-bot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message":"What is Parlay Gorilla?"}'
```

### Test Frontend

1. Open your frontend URL: `https://your-frontend.onrender.com`
2. Log in to your account
3. Look for the Gorilla Bot chat button (floating button, typically bottom-right)
4. Click to open the chat widget
5. Try asking: "What is Parlay Gorilla?"

## Step 6: Monitor and Troubleshoot

### Check Logs

**Render Dashboard** → Your backend service → **Logs** tab

Look for:
- ✅ `Gorilla Bot enabled`
- ✅ `Knowledge base indexed: X documents`
- ❌ Any errors related to `pgvector` or `vector` extension
- ❌ Any OpenAI API errors

### Common Issues

#### 1. "extension vector does not exist"

**Solution**: Enable pgvector extension (Step 1)

#### 2. "permission denied to create extension"

**Solution**: Render PostgreSQL may require manual extension creation. Use Render Dashboard → PostgreSQL → Connect → psql, then run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 3. "relation gorilla_bot_kb_chunks does not exist"

**Solution**: Run migration (Step 2)

#### 4. "No knowledge base chunks found"

**Solution**: Index the knowledge base (Step 4)

#### 5. "OpenAI API error"

**Solution**: 
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has sufficient credits
- Verify `OPENAI_ENABLED=true`

#### 6. Chat returns "temporarily unavailable"

**Possible causes:**
- Knowledge base not indexed
- pgvector extension not enabled
- OpenAI API key invalid or rate-limited

## Production Checklist

Before going live, verify:

- [ ] pgvector extension enabled on Render PostgreSQL
- [ ] Migration `030_add_gorilla_bot_kb` applied successfully
- [ ] All environment variables set in Render dashboard
- [ ] Knowledge base indexed (check with: `SELECT COUNT(*) FROM gorilla_bot_kb_chunks;`)
- [ ] Backend health check passes
- [ ] Chat endpoint responds (test with authenticated request)
- [ ] Frontend widget appears and opens correctly
- [ ] Test conversation works end-to-end
- [ ] Monitor logs for any errors

## Cost Considerations

### OpenAI API Costs

- **Embeddings**: `text-embedding-3-small` costs ~$0.02 per 1M tokens
- **Chat**: `gpt-4o-mini` costs ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

**Estimated monthly costs** (1000 users, 10 chats/user/month):
- Embeddings (indexing): ~$0.10/month (one-time per KB update)
- Chat requests: ~$5-10/month (depends on message length)

### Optimization Tips

1. **Cache embeddings**: Re-index only when KB documents change
2. **Limit context chunks**: `GORILLA_BOT_MAX_CONTEXT_CHUNKS=6` (default)
3. **Use efficient model**: `gpt-4o-mini` is cost-effective
4. **Rate limiting**: Already implemented (`@rate_limit("60/hour")`)

## Maintenance

### Updating Knowledge Base

1. Edit markdown files in `docs/gorilla-bot/kb/`
2. Commit and push to GitHub
3. Re-deploy backend (or use Render Shell to re-index)
4. Run: `python scripts/gorilla_bot_index_kb.py`

### Monitoring Usage

Check conversation and message counts:
```sql
SELECT COUNT(*) FROM gorilla_bot_conversations;
SELECT COUNT(*) FROM gorilla_bot_messages;
```

### Performance Tuning

If chat responses are slow:

1. **Reduce context chunks**: Lower `GORILLA_BOT_MAX_CONTEXT_CHUNKS`
2. **Increase timeout**: Raise `GORILLA_BOT_CHAT_TIMEOUT_SECONDS`
3. **Check database indexes**: Verify HNSW index exists on `gorilla_bot_kb_chunks.embedding`

## Support

If you encounter issues:

1. Check Render logs for errors
2. Verify all environment variables are set
3. Test locally with Render database connection string
4. Check OpenAI API status and credits

For Render-specific PostgreSQL issues, contact Render support.
