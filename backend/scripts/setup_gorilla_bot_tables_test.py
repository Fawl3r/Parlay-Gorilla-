#!/usr/bin/env python3
"""
Create Gorilla Bot tables for testing without pgvector requirement.
This is a temporary workaround for testing when pgvector isn't available.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database.session import engine, is_sqlite


async def setup_tables():
    """Create Gorilla Bot tables without vector extension."""
    print("Setting up Gorilla Bot tables for testing...")
    
    async with engine.begin() as conn:
        if is_sqlite:
            print("Using SQLite - creating tables...")
        else:
            print("Using PostgreSQL - creating tables (without pgvector)...")
        
        # Create conversations table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gorilla_bot_conversations (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                title VARCHAR(120),
                is_archived BOOLEAN NOT NULL DEFAULT false,
                last_message_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        print("✓ Created gorilla_bot_conversations table")
        
        # Create messages table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gorilla_bot_messages (
                id UUID PRIMARY KEY,
                conversation_id UUID NOT NULL,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                citations JSON,
                token_count INTEGER,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                FOREIGN KEY (conversation_id) REFERENCES gorilla_bot_conversations(id) ON DELETE CASCADE
            )
        """))
        print("✓ Created gorilla_bot_messages table")
        
        # Create KB documents table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gorilla_bot_kb_documents (
                id UUID PRIMARY KEY,
                source_path VARCHAR(255) NOT NULL UNIQUE,
                title VARCHAR(255) NOT NULL,
                source_url VARCHAR(500),
                checksum VARCHAR(64) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT true,
                last_indexed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
        """))
        print("✓ Created gorilla_bot_kb_documents table")
        
        # Create KB chunks table (without vector column for now)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gorilla_bot_kb_chunks (
                id UUID PRIMARY KEY,
                document_id UUID NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER,
                embedding_json JSON,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                FOREIGN KEY (document_id) REFERENCES gorilla_bot_kb_documents(id) ON DELETE CASCADE
            )
        """))
        print("✓ Created gorilla_bot_kb_chunks table (without vector column)")
        
        # Create indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_gorilla_bot_conversations_user_id 
            ON gorilla_bot_conversations(user_id)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_gorilla_bot_message_conversation_created 
            ON gorilla_bot_messages(conversation_id, created_at)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_gorilla_bot_kb_chunk_doc_index 
            ON gorilla_bot_kb_chunks(document_id, chunk_index)
        """))
        
        print("✓ Created indexes")
    
    print("\n✅ Gorilla Bot tables created successfully!")
    print("\n⚠️  Note: Vector search will not work without pgvector extension.")
    print("   For full functionality, install pgvector on your PostgreSQL server:")
    print("   https://github.com/pgvector/pgvector#installation")


if __name__ == "__main__":
    asyncio.run(setup_tables())
