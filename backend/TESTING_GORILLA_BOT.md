# Gorilla Bot Testing Summary

## Current Status

✅ **Backend Services**: Running successfully
- Backend API: `http://localhost:8000` ✓
- Frontend: `http://localhost:3000` ✓

✅ **Database Tables**: Created successfully
- `gorilla_bot_conversations` ✓
- `gorilla_bot_messages` ✓
- `gorilla_bot_kb_documents` ✓
- `gorilla_bot_kb_chunks` ✓

✅ **API Endpoints**: Partially working
- Health check: ✓
- Authentication: ✓
- List conversations: ✓
- Chat endpoint: ⚠️ (requires pgvector for full functionality)

## Known Issues

### 1. pgvector Extension Not Installed

The Gorilla Bot requires the `pgvector` PostgreSQL extension for vector similarity search. Without it:

- **Current State**: Tables are created but vector search is unavailable
- **Impact**: Chat endpoint may fail or return fallback responses
- **Solution**: Install pgvector on your PostgreSQL server

#### Installing pgvector

**On Ubuntu/Debian:**
```bash
sudo apt install postgresql-16-pgvector  # Adjust version as needed
```

**On macOS (Homebrew):**
```bash
brew install pgvector
```

**On Windows:**
- Download from: https://github.com/pgvector/pgvector/releases
- Or use a PostgreSQL distribution that includes pgvector

**After installation, enable the extension:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Knowledge Base Not Indexed

The knowledge base documents need to be indexed before the bot can answer questions:

```bash
cd backend
python scripts/gorilla_bot_index_kb.py
```

This will:
- Read markdown files from `docs/gorilla-bot/kb/`
- Chunk the content
- Generate embeddings using OpenAI
- Store in the database

## Testing

### Run Test Suite

```bash
cd backend
python scripts/test_gorilla_bot.py
```

### Manual Testing

1. **Start Backend:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test API:**
   ```bash
   # Register/Login to get token
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123!"}'
   
   # Chat with Gorilla Bot
   curl -X POST http://localhost:8000/api/gorilla-bot/chat \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"message":"What is Parlay Gorilla?"}'
   ```

## Next Steps

1. **Install pgvector** on your PostgreSQL server
2. **Run the migration** to add the vector column:
   ```bash
   cd backend
   python -m alembic upgrade head
   ```
3. **Index the knowledge base**:
   ```bash
   python scripts/gorilla_bot_index_kb.py
   ```
4. **Test the chat endpoint** again

## Frontend Integration

The Gorilla Bot widget is integrated into the `MobileShell` component and will appear as a floating chat button when:
- User is authenticated
- Backend is running
- Gorilla Bot is enabled

The widget can be tested by:
1. Opening the frontend at `http://localhost:3000`
2. Logging in
3. Clicking the Gorilla Bot chat button (bottom right)
