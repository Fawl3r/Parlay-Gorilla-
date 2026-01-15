# Gorilla Bot - Production Deployment Checklist

Quick reference checklist for deploying Gorilla Bot to Render.

## Pre-Deployment

- [ ] **Code deployed** to GitHub (all Gorilla Bot files committed)
- [ ] **Render services created** (PostgreSQL, Backend, Frontend)
- [ ] **OpenAI API key** obtained and ready

## Database Setup

- [ ] **pgvector extension enabled** on Render PostgreSQL
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
- [ ] **Migration applied** (`030_add_gorilla_bot_kb`)
  - Check: `alembic current` shows `030_add_gorilla_bot_kb`
- [ ] **Tables verified**:
  ```sql
  SELECT COUNT(*) FROM gorilla_bot_conversations;  -- Should be 0 initially
  SELECT COUNT(*) FROM gorilla_bot_kb_chunks;      -- Should be 0 until indexed
  ```

## Environment Variables

Add to Render backend service:

- [ ] `GORILLA_BOT_ENABLED=true`
- [ ] `OPENAI_API_KEY=sk-...` (your key)
- [ ] `OPENAI_ENABLED=true`
- [ ] `GORILLA_BOT_MODEL=gpt-4o-mini` (optional, default)
- [ ] `GORILLA_BOT_EMBEDDING_MODEL=text-embedding-3-small` (optional, default)
- [ ] `GORILLA_BOT_KB_PATH=docs/gorilla-bot/kb` (optional, default)

## Knowledge Base Indexing

- [ ] **KB documents exist** in `docs/gorilla-bot/kb/`:
  - [ ] `overview.md`
  - [ ] `parlay-generator.md`
  - [ ] `custom-parlay-builder.md`
  - [ ] `credits-and-subscriptions.md`
  - [ ] `troubleshooting.md`
- [ ] **Indexing script run**:
  ```bash
  python scripts/gorilla_bot_index_kb.py
  ```
- [ ] **Chunks verified**:
  ```sql
  SELECT COUNT(*) FROM gorilla_bot_kb_chunks;  -- Should be > 0
  ```

## Testing

- [ ] **Backend health check**:
  ```bash
  curl https://your-backend.onrender.com/health
  ```
- [ ] **Chat endpoint test** (with auth token):
  ```bash
  curl -X POST https://your-backend.onrender.com/api/gorilla-bot/chat \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message":"What is Parlay Gorilla?"}'
  ```
- [ ] **Frontend widget visible** and functional
- [ ] **End-to-end conversation** works

## Post-Deployment

- [ ] **Monitor logs** for errors
- [ ] **Check OpenAI API usage** and costs
- [ ] **Verify rate limiting** is working
- [ ] **Test with real user account**

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| "extension vector does not exist" | Enable pgvector: `CREATE EXTENSION vector;` |
| "permission denied" | Use Render Dashboard → PostgreSQL → psql |
| "table does not exist" | Run: `alembic upgrade head` |
| "No chunks found" | Run: `python scripts/gorilla_bot_index_kb.py` |
| "OpenAI API error" | Check API key and credits |
| Chat returns "unavailable" | Check KB indexed and pgvector enabled |

## Rollback Plan

If deployment fails:

1. **Disable Gorilla Bot**:
   ```env
   GORILLA_BOT_ENABLED=false
   ```
2. **Redeploy backend**
3. **Investigate issues** in logs
4. **Fix and re-enable**

## Success Criteria

✅ All checklist items completed
✅ Chat endpoint returns valid responses
✅ Frontend widget opens and functions
✅ No errors in logs
✅ Knowledge base queries return relevant results

---

**Next Steps After Deployment:**
- Monitor usage and costs
- Gather user feedback
- Update knowledge base as needed
- Optimize based on usage patterns
